#!/usr/bin/env python3
"""CodexTune - 04_install_log_trigger.py

Safe installer for the `drop_non_warn_error_logs` trigger in Codex's
logs_2.sqlite. This trigger blocks TRACE/DEBUG inserts before they hit the
log DB, which prevents the per-SSE TRACE write storm from recurring.

Safety rules:
  - Dry-run by default; pass --apply to modify the DB.
  - Refuses to run while any Codex/ChatGPT/codex/app-server process is alive
    unless --force is passed.
  - Backs up logs_2.sqlite + -wal + -shm with SHA-256 before applying.

Usage:
  python scripts/04_install_log_trigger.py --dry-run
  python scripts/04_install_log_trigger.py --apply
  python scripts/04_install_log_trigger.py --apply --level error-only
"""

import argparse
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import time


def check_codex_processes():
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-Process | Where-Object { $_.ProcessName -match 'ChatGPT|codex|app-server' } | Select-Object -ExpandProperty ProcessName",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ["(unable to check)"]
    return [line.strip() for line in out.splitlines() if line.strip()]


def backup(db_path, backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    paths = []
    for suffix in ("", "-wal", "-shm"):
        src = db_path + suffix
        if os.path.exists(src):
            dst = os.path.join(backup_dir, os.path.basename(src) + "." + stamp + ".bak")
            shutil.copy2(src, dst)
            digest = hashlib.sha256(open(dst, "rb").read()).hexdigest()
            with open(dst + ".sha256", "w", encoding="ascii") as fh:
                fh.write(f"{digest}  {dst}\n")
            paths.append(dst)
    return paths


def trigger_sql(level):
    if level == "error-only":
        condition = "NEW.level != 'ERROR'"
    else:
        condition = "NEW.level NOT IN ('WARN', 'ERROR')"
    return (
        "DROP TRIGGER IF EXISTS drop_non_warn_error_logs;\n"
        "CREATE TRIGGER drop_non_warn_error_logs\n"
        "BEFORE INSERT ON logs\n"
        f"WHEN {condition}\n"
        "BEGIN\n"
        "  SELECT RAISE(IGNORE);\n"
        "END;"
    )


def main():
    parser = argparse.ArgumentParser(description="Install TRACE-dropping trigger for logs_2.sqlite")
    parser.add_argument(
        "--db",
        default=os.path.join(os.path.expanduser("~"), ".codex", "logs_2.sqlite"),
    )
    parser.add_argument(
        "--level",
        choices=["warn-error", "error-only"],
        default="warn-error",
        help="Which levels to keep (default: WARN+ERROR)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry run (default behavior)")
    parser.add_argument("--apply", action="store_true", help="Actually modify the DB")
    parser.add_argument("--force", action="store_true", help="Skip the running-process check")
    parser.add_argument("--backup-dir", default=None, help="Backup destination (default: beside the DB)")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: {args.db} not found", file=sys.stderr)
        sys.exit(1)

    sql = trigger_sql(args.level)
    print("Trigger SQL:")
    print(sql)
    print()

    if not args.apply:
        print("DRY-RUN: no changes made. Re-run with --apply to install.")
        return

    if not args.force:
        procs = check_codex_processes()
        if procs:
            print(
                "ABORT: Codex processes are still running: "
                + ", ".join(sorted(set(procs)))
                + ". Fully quit Codex first, or pass --force.",
                file=sys.stderr,
            )
            sys.exit(1)

    backup_dir = args.backup_dir or os.path.join(os.path.dirname(args.db), "codextune-backups")
    made = backup(args.db, backup_dir)
    print("Backups:")
    for p in made:
        print("  " + p)

    con = sqlite3.connect(args.db, timeout=30)
    con.execute("PRAGMA busy_timeout=20000")
    con.executescript(sql)
    con.commit()
    exists = con.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' AND name='drop_non_warn_error_logs'"
    ).fetchone()
    con.close()
    print("Trigger installed and verified." if exists else "ERROR: trigger verification failed")
    sys.exit(0 if exists else 1)


if __name__ == "__main__":
    main()
