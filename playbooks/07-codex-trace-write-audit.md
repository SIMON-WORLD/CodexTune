# 07 - Trace Write Audit / TRACE 写盘审计

## Why / 背景

`logs_2.sqlite` 可能因 TRACE 级日志高频写入而快速膨胀：`response.output_text.delta`、`agentMessage`、`delta` 等消息会逐 token 落库，造成写放大、WAL 增大、启动/锁竞争。上游与社区有多个仍未关闭的 issue：#29674、#29798、#30405、#31142、#35092、#41085。

本机实测（Codex 26.820.71523，Windows）：当 TRACE 被正确处理时，`logs_2.sqlite` 只保留 WARN/ERROR，不含上述 delta 字段；45 秒抽样文件大小零增长；日写入约 0.5–1.2 MB。本手册用于复发时快速判定是否 TRACE 写放大，以及是否值得走 `05-database-safety` 重建。

## Hard rules / 红线

- 只读诊断。任何 Codex/ChatGPT/codex/app-server 进程存活时禁止写入、改动或删除该库。
- 如需处理，备份必须连同 `-wal` / `-shm` 一起，绝不直接删除。
- 仓库内不提交真实路径、会话正文、令牌。

## Diagnostic steps / 诊断步骤

1. 确认日志级别分布：是否只剩 WARN/ERROR，有无 `output_text.delta` / `agentMessage` / `delta` 字段。
2. 抽样文件大小：间隔 45 秒，观察大小是否基本不变。
3. 估算日写入量（MB/天）。
4. 若健康（无 delta、45s 零增长、<约 2MB/天）→ 不需要处理。
5. 若被 TRACE 淹没（delta 大量出现、WAL 快速膨胀、日写入数十 MB）→ 与用户确认后，按 `05-database-safety` 走“备份后移走重建”；或参考 TRACE 过滤触发器方案（仓库 PR #8 分支保留，未合并）。

## 只读采样示例（Windows PowerShell）

```powershell
# 1) 只读统计：按 level 计数 + 是否存在 delta 字段（路径使用环境变量，不写死绝对路径）
python -c "import sqlite3,os;p=os.path.join(os.path.expanduser('~'),'.codex','logs_2.sqlite');c=sqlite3.connect('file:'+p.replace('\\','/')+'?mode=ro',uri=True);print('levels:',c.execute('SELECT level, COUNT(*) FROM logs GROUP BY level').fetchall());r=c.execute('SELECT COUNT(*) FROM logs WHERE feedback_log_body LIKE ?',('%output_text.delta%',)).fetchone()[0];print('delta rows:',r);c.close()"

# 2) 45 秒抽样文件大小
$f = Join-Path $env:USERPROFILE '.codex\logs_2.sqlite'
$a = (Get-Item -LiteralPath $f).Length
Start-Sleep -Seconds 45
$b = (Get-Item -LiteralPath $f).Length
"size delta bytes: $($b - $a)"
```

## Use with playbook 05 / 与 05 配合

- 本手册只负责“是否 TRACE 写放大”的判定。
- 一旦确认需要处理，回到 `playbooks/05-database-safety.md`：完全退出 Codex → 备份（含 `-wal`/`-shm`）→ 移走原库 → 启动重建 → 验证线程仍存在 → 保留备份若干天。
- 只读分析也可先跑 `python scripts/02_analyze_logs.py` 做计数快速定位。