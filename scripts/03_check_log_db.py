#!/usr/bin/env python3
"""CodexTune - 03_check_log_db.py

Read-only health check for Codex's logs_2.sqlite:
file size, WAL/SHM size, max(id), row count, level distribution, triggers,
and an optional short write-rate sample.

Usage:
  python scripts/03_check_log_db.py
  python scripts/03_check_log_db.py --sample-seconds 20
  python scripts/03_check_log_db.py --json
"""

import argparse
import json
import os
import sqlite3
import sys
import time


def snapshot(db_path, cur):
    return {
        "max_id": cur.execute("SELECT MAX(id) FROM logs").fetchone()[0],
        "rows": cur.execute("SELECT COUNT(*) FROM logs").fetchone()[0],
        "levels": {
            level: count
            for level, count in cur.execute(
                "SELECT level, COUNT(*) FROM logs GROUP BY level ORDER BY level"
            )
        },
        "triggers": [
            {"name": name, "sql": sql}
            for name, sql in cur.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name"
            )
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only logs_2.sqlite health check")
    parser.add_argument(
        "--db",
        default=os.path.join(os.path.expanduser("~"), ".codex", "logs_2.sqlite"),
        help="Path to logs_2.sqlite",
    )
    parser.add_argument(
        "--sample-seconds",
        type=int,
        default=10,
        help="Measure row growth over this many seconds (0 to disable)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: {args.db} not found", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True, timeout=30)
    con.execute("PRAGMA busy_timeout=20000")
    cur = con.cursor()

    size = os.path.getsize(args.db)
    wal = args.db + "-wal"
    shm = args.db + "-shm"

    before = snapshot(args.db, cur)
    if args.sample_seconds > 0:
        time.sleep(args.sample_seconds)
        after = snapshot(args.db, cur)
        delta = {
            "seconds": args.sample_seconds,
            "new_rows": after["rows"] - before["rows"],
            "max_id_delta": after["max_id"] - before["max_id"],
        }
    else:
        after = before
        delta = {"seconds": 0, "new_rows": 0, "max_id_delta": 0}

    result = {
        "db": args.db,
        "size_mb": round(size / 1024 / 1024, 2),
        "wal_size_mb": round(os.path.getsize(wal) / 1024 / 1024, 2) if os.path.exists(wal) else None,
        "shm_size_mb": round(os.path.getsize(shm) / 1024 / 1024, 2) if os.path.exists(shm) else None,
        "before": before,
        "after": after,
        "write_rate_sample": delta,
    }
    con.close()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"db: {args.db}")
    print(f"size: {result['size_mb']} MiB | WAL: {result['wal_size_mb']} MiB | SHM: {result['shm_size_mb']} MiB")
    print(f"max(id): {before['max_id']} | rows: {before['rows']}")
    print("levels:", ", ".join(f"{k}={v}" for k, v in sorted(before["levels"].items())))
    print("triggers:", ", ".join(t["name"] for t in before["triggers"]) or "(none)")
    print(f"write rate sample: {delta['new_rows']} new rows / {delta['seconds']}s, max_id delta={delta['max_id_delta']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
