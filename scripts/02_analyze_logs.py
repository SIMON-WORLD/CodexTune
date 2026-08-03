#!/usr/bin/env python3
"""CodexTune - 02_analyze_logs.py

Read-only analyzer for Codex Desktop's logs_2.sqlite. Counts the log
patterns that correlate with startup slowness, MCP failures, model refresh
failures, and skill/plugin context pressure. Does not modify anything.

Usage:
  python scripts/02_analyze_logs.py
  python scripts/02_analyze_logs.py --since "2026-08-02 15:33:30"
  python scripts/02_analyze_logs.py --json
"""

import argparse
import datetime
import json
import sqlite3
import sys

PATTERNS = {
    "plugin/list": "%plugin/list%",
    "skills/list": "%skills/list%",
    "model_refresh_failures": "%failed to refresh available models%",
    "stream_disconnected": "%stream disconnected%",
    "child_timeout": "%timeout waiting for child process to exit%",
    "mcp_transport_errors": "%worker quit with fatal%",
    "connector_proxy_errors": "%connector-proxy%",
    "local_mcp_5157_errors": "%127.0.0.1:5157%",
    "analytics_send_failures": "%failed to send events request%",
    "recommended_plugins_failures": "%failed to load recommended plugins%",
    "skill_budget_lines": "%truncated skill metadata%",
    "total_skills_logs": "%total_skills%",
    "omitted_skills_logs": "%omitted_skills%",
}


def parse_since(value):
    text = value.replace("Z", "+00:00")
    dt = datetime.datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt.timestamp()


def analyze(db_path, since_ts):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
    cur = con.cursor()
    where = "WHERE ts > ?" if since_ts else ""
    params = (since_ts,) if since_ts else ()
    result = {
        "db": db_path,
        "since_epoch": since_ts,
        "since_local": (
            datetime.datetime.fromtimestamp(since_ts).strftime("%Y-%m-%d %H:%M:%S")
            if since_ts
            else None
        ),
        "total_rows": cur.execute(f"SELECT COUNT(*) FROM logs {where}", params).fetchone()[0],
    }
    result["levels"] = {
        row[0]: row[1]
        for row in cur.execute(
            f"SELECT level, COUNT(*) FROM logs {where} GROUP BY level ORDER BY level", params
        )
    }
    result["patterns"] = {}
    for key, like in PATTERNS.items():
        where_and = "WHERE ts > ? AND" if since_ts else "WHERE"
        sql = f"SELECT COUNT(*) FROM logs {where_and} feedback_log_body LIKE ?"
        result["patterns"][key] = cur.execute(sql, params + (like,)).fetchone()[0]
    con.close()
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only logs_2.sqlite analyzer")
    parser.add_argument(
        "--db",
        default=r"C:\Users\Administrator\.codex\logs_2.sqlite",
        help="Path to logs_2.sqlite",
    )
    parser.add_argument("--since", help="Only count rows after this local time, e.g. '2026-08-02 15:33:30'")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    since_ts = parse_since(args.since) if args.since else None
    result = analyze(args.db, since_ts)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"db: {result['db']}")
    print(f"since: {result['since_local'] or 'all time'}")
    print(f"total rows: {result['total_rows']}")
    print("levels:", ", ".join(f"{k}={v}" for k, v in sorted(result['levels'].items())))
    print("patterns:")
    for key, value in result["patterns"].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # keep the tool non-fatal for diagnostics
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
