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

## TRACE storm mitigation / TRACE 写盘风暴缓解

`logs_2.sqlite` can be hammered by TRACE-level streaming events (full SSE `response.completed`, `output_text.delta`, etc.). Upstream reduced noise by ~85% in `rust-v0.142/0.143` (original issue openai/codex#28224 closed), but openai/codex#35092 (per-SSE TRACE still written in 0.145/0.146) and #31142 (Windows desktop WAL) remain open.

`logs_2.sqlite` 会被 TRACE 流式事件高频写入；官方 0.142/0.143 降噪约 85%（#28224 关闭），但 #35092、#31142 仍未根治。

### 1. Check health / 健康检查（只读）

```powershell
python scripts/03_check_log_db.py --sample-seconds 20
```

Watch for:

- `max(id)` far above `rows` -> historical TRACE storm (e.g. 13.9M vs 41k on Machine B).
- File size much larger than estimated content -> SQLite pages not reclaimed without VACUUM.
- `triggers` list missing `drop_non_warn_error_logs` -> TRACE writes are not being filtered.

### 2. Install the filter trigger / 安装过滤触发器

The trigger drops non-WARN/ERROR rows before they hit the log DB. Dry-run first; apply only after Codex is fully closed.

```powershell
python scripts/04_install_log_trigger.py --dry-run
python scripts/04_install_log_trigger.py --apply
# ERROR-only variant:
python scripts/04_install_log_trigger.py --apply --level error-only
```

Equivalent SQL (WARN+ERROR variant):

```sql
DROP TRIGGER IF EXISTS drop_non_warn_error_logs;
CREATE TRIGGER drop_non_warn_error_logs
BEFORE INSERT ON logs
WHEN NEW.level NOT IN ('WARN', 'ERROR')
BEGIN
  SELECT RAISE(IGNORE);
END;
```

### 3. Rebuild the bloated DB safely / 安全重建膨胀数据库

Important: the trigger lives inside the DB. If you move the DB aside and let Codex rebuild it, the trigger is lost; reinstall it after the rebuild.

1. Fully quit Codex and verify no `ChatGPT`, `codex`, `codex-app-manager`, or `app-server` processes remain.
2. Back up `logs_2.sqlite`, `logs_2.sqlite-wal`, `logs_2.sqlite-shm` (SHA-256 recorded).
3. Move (rename) the originals aside, do not delete.
4. Start Codex and let it rebuild the DB.
5. Reinstall the trigger with `scripts/04_install_log_trigger.py --apply`.
6. Verify the thread list and sessions still appear (they come from JSONL).
7. Keep the backup until the app has worked correctly for at least one full restart.

重建后必须重新安装触发器；否则 TRACE 高频写盘会随新库恢复。

### 4. Long-term expectation / 长期预期

The trigger stops the TRACE storm, but it does not make the DB stay tiny forever:

- Machine B current content is about 215 MiB (41k rows: ~209 MiB ERROR + ~6 MiB WARN), while the file is 662 MiB because SQLite keeps freed pages unless VACUUM runs.
- After a rebuild, the file starts small, but WARN/ERROR rows will refill the retention window over time. Without periodic VACUUM, the file can grow back toward hundreds of MiB.
- To keep it small long-term: use the ERROR-only trigger, and/or run a VACUUM while Codex is fully closed (backup first), and monitor with `scripts/03_check_log_db.py`.

触发器阻止 TRACE 风暴，但不会让库永远很小：重建后文件会从小开始，WARN/ERROR 会随时间重新填满保留窗口；没有定期 VACUUM 时文件仍可能涨回数百 MiB。长期方案是 ERROR-only 触发器 + 定期在 Codex 关闭时收缩（先备份），并用 `03_check_log_db.py` 监控。

## Safe procedure / 安全流程（通用）

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
