# Machine B Cleanup Plan / 第二台机器清理计划

Status: proposed plan for the second machine. Execute steps in order; measure startup seconds before and after each step. / 状态：第二台机器的建议计划。按顺序执行，每步前后测量启动秒数。

## Context / 背景

Machine B baseline (2026-08-02, extended collector). It shares the same problems as Machine A before cleanup:

第二台机器基线（2026-08-02，扩展采集）。与第一台清理前有相同问题：

| Item / 项目 | Machine A (before) | Machine B |
|---|---|---|
| Staged plugins in `.codex\.tmp\plugins\plugins` | 180 | 180 |
| `stata-mcp` flags | `--refresh --refresh-package @latest` | same / 相同 |
| `logs_2.sqlite` | 578.61 MB | 662.58 MB |

## Machine B unique findings / 第二台独有发现

These need their own attention and should be tracked as issues:

这些需要单独处理，建议分别开 Issue 跟进：

1. **Model refresh failures / 模型刷新失败**: 4822 rows in `logs_2.sqlite` (`failed to refresh available models`). Way more than Machine A. Check network/proxy stability and the models catalog path. / 日志库中 4822 条模型刷新失败记录，远多于第一台。检查网络/代理稳定性与模型目录路径。
2. **Largest session / 最大会话**: 541.61 MB single rollout. Plan a handoff + new thread; archive it. / 单个会话 541.61 MB。建议精简交接 + 新建会话后归档。
3. **C: free space / C 盘空间**: only 9.25 GB free. Clean the uv cache, npm cache, and temporary plugin staging before further work. / 仅剩 9.25 GB。先清理 uv/npm 缓存与插件暂存目录。
4. **Stale loopback exemptions / 过期 loopback 豁免**: `CheckNetIsolation LoopbackExempt -s` shows stale `AppContainer NOT FOUND` entries. Remove stale entries carefully. / loopback 豁免存在过期的 AppContainer 条目，需谨慎清理。

## Fix sequence / 修复顺序

Each step: backup -> apply -> restart -> measure. One PR per step with before/after numbers.

每一步：备份 -> 修改 -> 重启 -> 测量。每步一个 PR，附前后数据。

### Step 1: Skill cleanup / Skill 清理

Target scope / 目标范围: user-level `.codex\skills` (project `.agents\skills` may be left untouched if actively used) / 用户级 `.codex\skills`（项目级 `.agents\skills` 如在使用中可保留不动）。

1. Collect evidence / 采集证据:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\01_collect_evidence.ps1 -ProjectRoot . -IncludeExtended
   ```
2. Analyze actual skill usage from session records (catalog-only presence = unused) / 分析会话记录中的实际 skill 使用（仅目录出现 = 未使用）。
3. Move unused skills to a recoverable backup / 将未使用 skill 移到可恢复备份。
4. Measure / 测量: prefer `total_skills` / `omitted_skills` from logs (`truncated skill metadata`); if those rows are absent on this machine, use SKILL.md counts plus `skills/list` RPC counts as the before/after metric / 优先用日志中的 total_skills / omitted_skills；如本机日志无此行，改用 SKILL.md 数量加 skills/list RPC 次数作为前后指标。

### Step 2: Plugin quarantine / 插件隔离

1. Keep only enabled plugins (match `plugin.json` id against `config.toml` enabled list) / 仅保留已启用插件。
2. Move the rest of `.codex\.tmp\plugins\plugins` to a recoverable backup / 其余移出到可恢复备份。
3. Restart and verify: count of staged dirs stays low; `plugin/list` and manifest-parse warnings drop / 重启验证：暂存目录不回升、plugin/list 与 manifest 警告下降。

### Step 3: MCP trim / MCP 精简

1. Backup `config.toml` (contains tokens - keep private) / 备份 config.toml（含令牌，注意保密）。
2. `stata-mcp`: remove `--refresh --refresh-package`, add `--with mcp<2` (mcp-stata 3.3.0 requires mcp 1.x; mcp 2.x removed `mcp.server.fastmcp`) / 去掉 --refresh 并加 mcp<2 约束。
3. Remove unused MCP servers. `connector-proxy` was confirmed dead on Machine B: nothing listens on 127.0.0.1:5157 and no service/installer/usage records exist, so it is a dead HTTP endpoint, not just intermittent 502s / 移除不用的 MCP 服务。第二台确认 connector-proxy 为死端点：127.0.0.1:5157 无监听、无服务/安装/使用记录，并非只是间歇性 502。
4. Rebuild the uv cache once with `--refresh`, then verify a non-refresh launch works / 一次性 --refresh 重建缓存，再验证不带 --refresh 可启动。

### Step 4: Disk space / C 盘空间

1. `uv cache clean` or targeted uv cache cleanup / uv 缓存清理。
2. `npm cache clean --force` if npm is used / 如使用 npm 则清理 npm 缓存。
3. Remove stale `.codex\.tmp` staging leftovers / 清理 .codex\.tmp 暂存残留。
4. Keep quarantined backups on a non-C: drive if possible; keeping them on C: (e.g. `.codex\.tmp`) is also acceptable for same-volume rollback and to avoid cloud sync, with recovery manifests kept in the task dir / 隔离备份尽量放非 C 盘；保留在 C 盘（如 .codex\.tmp）也可接受，便于同卷回滚、避免云同步，恢复清单放在任务目录。

### Step 5: Large session / 大会话

1. Create a compact handoff summary (goal, progress, key files, todos) / 建精简交接摘要。
2. Continue in a new thread / 在新会话继续。
3. Archive the 541.61 MB thread / 归档 541.61 MB 会话。
4. Do not keep reopening it / 不要反复打开。

## Expected results / 预期结果

Based on Machine A after cleanup / 参照第一台清理后：

| Metric / 指标 | Before | After (Machine A) |
|---|---|---|
| `total_skills` | 294 | 233 |
| `omitted_skills` | 74 | 24 |
| Staged plugin dirs / 暂存插件目录 | 180 | 1 |
| Model refresh timeout / 模型刷新超时 | present | absent |

## PR workflow / PR 流程

- One Issue per finding (use `.github/ISSUE_TEMPLATE/performance-issue.md`) / 每个发现一个 Issue。
- One PR per fix with backup + rollback + before/after numbers / 每个修复一个 PR，附备份回滚与前后数据。
- Both machines verify before merge / 两台机器都验证后才合并。

## Privacy / 隐私

- Evidence packages contain local paths; never commit them / 证据包含本地路径，禁止提交。
- Sanitize before pasting into issues/PRs / 粘贴到 Issue/PR 前脱敏。
- `config.toml` backups contain tokens; keep them out of the repo / config 备份含令牌，禁止入仓。
