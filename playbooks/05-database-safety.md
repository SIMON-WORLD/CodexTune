# 05 - Database Safety / 数据库安全

## Why / 背景

Local SQLite databases (`logs_2.sqlite`, `state_5.sqlite`) can grow without bound and become a real startup/performance blocker. Community and upstream evidence:

- `logs_2.sqlite` / `state_5.sqlite` grow unbounded; once the DBs exceed roughly 500 MB combined, users report write-lock contention and auto-restart loops (openai/codex#16270). Upstream added incremental VACUUM maintenance (openai/codex#16330), but existing bloated DBs may not shrink automatically.
- A slow-profile investigation found about 50 s of fixed local-DB overhead before the model was even called (openai/codex#25715).
- Stale or long-lived Codex processes can hold shared SQLite locks and block the next launch (openai/codex#26454).
- App updates can trigger sqlx migration checksum / CRLF errors that prevent launch; users often recover by moving the DB aside and letting the app rebuild it (openai/codex#23777, #23863, #23917). A non-destructive repair tool also exists: `xdifu/codex-repair`.

本地 SQLite 数据库（`logs_2.sqlite`、`state_5.sqlite`）可能无限膨胀并成为启动/性能瓶颈，上游与社区有多起真实案例。

## Hard rules / 红线

- Never touch the SQLite files while any Codex/ChatGPT/codex/app-server process is alive.
- Never delete the DB files. Move them aside with backups.
- Always back up the main file together with its `-wal` and `-shm` sidecars.
- Session content lives in `.codex\sessions\*.jsonl`, not in the log DB, so rebuilding the log DB does not lose conversations.

任何 Codex 进程存活时禁止操作数据库；禁止直接删除，必须连同 `-wal`/`-shm` 一起备份后移走；会话正文在 JSONL，不在日志库。

## Safe procedure / 安全流程

1. Fully quit Codex and verify no `ChatGPT`, `codex`, `codex-app-manager`, or `app-server` processes remain (a visible window can be closed while background processes keep running).
2. Back up `logs_2.sqlite`, `logs_2.sqlite-wal`, `logs_2.sqlite-shm` (and the `state_5.sqlite*` set if also needed) to a private location with SHA-256 recorded.
3. Move (rename) the originals aside, do not delete.
4. Start Codex and let it rebuild the DB.
5. Verify the thread list and sessions still appear (they come from JSONL).
6. Keep the backup until the app has worked correctly for at least one full restart.
7. If a migration checksum error appears, the usual root cause is an app update / CRLF mismatch; use the non-destructive repair tool or move-aside rebuild instead of repeatedly deleting files.

## Notes / 备注

- Do not copy a bloated DB back after the app has rebuilt and works, or you undo the cleanup.
- If the DB is actively written (WAL/SHM present), it is in use; stop all Codex processes first.
- Evidence and backups contain local paths/conversation metadata: keep them out of the repository.
