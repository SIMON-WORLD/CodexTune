# Machine B Execution Status / 第二台机器实际执行状态

Updated: 2026-08-02 by Machine B. This supplements `machine-b-cleanup-plan.md` with the actual results and adaptations.

更新时间：2026-08-02，由第二台机器补充，记录实际结果与偏差。

## Step 1: Skill cleanup / Skill 清理 - done (adapted)

- Scanned all 426 session rollouts for skill names; quarantined 20 zero-reference skills under user `.codex\skills` (420 -> 400).
- Project `.agents\skills` (49) was intentionally untouched.
- `omitted_skills` / `truncated skill metadata` lines were not present in Machine B logs; used SKILL.md counts and `skills/list` RPC counts instead.
- After restart: `skills/list` rows in startup logs dropped from 122 to 80.

## Step 2: Plugin quarantine / 插件隔离 - done

- All 180 staged plugin dirs were moved to `.codex\.tmp\plugins\quarantine-20260802-151712`; none matched the 11 enabled plugin ids.
- After restart: staged plugin dirs stayed at 0 (not re-materialized); `plugin/list` rows in startup logs 13 -> 12.

## Step 3: MCP trim / MCP 精简 - done

- Removed `connector-proxy`: nothing listens on 127.0.0.1:5157, no service/installer/usage records, and logs showed only retry failures (not intermittent 502s).
- Changed `stata-mcp` args to `--from mcp-stata@latest --with mcp<2 mcp-stata`.
- After restart: connector-proxy/5157 errors = 0, mcp-stata crash = 0, model refresh failures = 0.

## Step 4: Disk space / C 盘空间 - partial

- npm cache cleaned: freed 2.14 GB.
- Removed 505 orphaned `.tmp*` dirs in `AppData\Local\uv\cache`: freed 10.61 GB.
- C: free: 9.25 GB -> 21.74 GB.
- `uv cache archive-v0` / `builds-v0` retained (legit package cache); `uv cache clean` and `uv cache prune` both hung on this machine, so targeted cleanup was used instead.

## Step 5: Large session / 大会话 - pending

- Largest rollout is 541.61 MB; handoff summary + app archive still to do from the user side.

## Notes / 备注

- Quarantines were kept on the C: volume (`.codex\.tmp`) for same-volume rollback; recovery manifests are outside the repo.
- Evidence packages remain private and are not committed.

## Loopback exemptions / loopback 豁免 - false alarm

- Non-elevated `CheckNetIsolation LoopbackExempt -s` showed `AppContainer NOT FOUND` for 5 entries.
- Elevated check resolved all 5: `microsoft.desktopappinstaller`, `microsoft.windowsstore`, `microsoft.storepurchaseapp`, `microsoft.xboxidentityprovider`, `microsoft.xbox.tcui` (all `_8wekyb3d8bbwe`).
- No entries were deleted; the earlier cleanup-plan item is corrected.

## Update 2026-08-03 / 2026-08-03 进展

### Skill cleanup round 2 / skill 第二轮清理 - done

- Re-scanned session records after the first round; user skills in `.codex\skills` went 400 -> 256:
  - 23 malformed SKILL.md files (missing YAML frontmatter) were quarantined.
  - 121 zero-reference, non-system skills were quarantined (recoverable).
- 27 malformed SKILL.md files were found in total: 24 under `.codex\skills` (23 quarantined, 1 path no longer exists) and 3 under a secondary skill root (`.cc-switch\skills`).
- The 3 secondary-root files were fixed instead of quarantined:
  - `stata`: valid frontmatter but UTF-8 BOM; BOM removed (matches openai/codex#13918).
  - `literature-parser` / `paper-recommendation`: no YAML frontmatter; minimal `name`/`description` frontmatter added.
- After the next restart, `missing YAML frontmatter` errors are expected to drop from 572 to 0.

### Restart verification 2026-08-03 / 重启验证

- After restart: `skills/list` = 12 (previously ~516 in 1.5h), `plugin/list` = 13.
- Missing-frontmatter errors dropped to 12, all from the secondary root before the fix.
- Model refresh failures, MCP transport errors, connector-proxy/5157 errors: all 0.
- User skills: 256; staged plugins: 0; C: free: 20.13 GB.

### Proxy / network verification / 代理与网络复核

- Sandboxed PowerShell network tools can false-negative (fake "no listener"/SSL failures). Verify with native `netstat` and an elevated HTTPS probe.
- Native check: local proxy ports are listening; elevated HTTPS probes through the proxy complete TLS and return expected 403/401 for unauthenticated requests.
- `analytics-events` and `plugins/suggested` intermittently fail with transport errors / empty responses (`EOF while parsing a value at line 1 column 0`). This is an intermittent chatgpt.com backend path issue through the current proxy node, not a local config or proxy problem.

### Remaining / 剩余

- `logs_2.sqlite` (662 MB) safe move-aside rebuild still pending (see playbook 05).
- 7 active rollouts exceed 496 MB in one research project; handoff + archive still recommended.

## Update 2026-08-04 / 2026-08-04 进展

### Config safety / 配置安全 - done (research + tooling)

- Added `playbooks/06-config-safety.md` and `scripts/05_check_codex_config.py` (read-only config.toml checker).
- Confirmed root causes:
  - `wire_api = "chat"` is removed upstream (openai/codex#7782); a crash file on Machine B had this value.
  - cc-switch is a source of truth and rewrites live config on switch: MCP servers, model catalog, base_url.
  - cc-switch regenerates `cc-switch-model-catalog.json` from provider `modelCatalog`; without `input_modalities`, image support is lost.
  - Mojibake path entries came from double-encoded UTF-8 writes by older Windows tooling.

### cc-switch fixes / cc-switch 修复 - done (Machine B)

- Disabled `connector-proxy` in cc-switch MCP table (`enabled_codex=1 -> 0`).
- Updated `stata-mcp` args to `--from mcp-stata@latest --with mcp<2 mcp-stata`.
- Both persisted after cc-switch and Codex restarts.
- Backups recorded privately (not committed).

### Mojibake cleanup / 乱码清理 - done

- Removed 3 double-encoded path entries from cc-switch common config and live `config.toml`; correct Unicode paths kept.
- Verified with `scripts/05_check_codex_config.py` and `tomllib`.

### Vision bridge handoff / 视觉桥交接 - handed off

- Instruction doc written for the other session: durable fix is to add `input_modalities: ["text","image"]` to the DeepSeek provider `modelCatalog` in the cc-switch DB.
- Live config currently points to a custom catalog with image support; cc-switch sync can still overwrite it until the DB fix lands.

### PowerShell / 终端确认

- Codex sandbox logs show current shell commands run via `pwsh.exe` (PowerShell 7.6.3); June logs used Windows PowerShell 5.1.

### Parked / 暂缓

- PR #8 (TRACE storm tooling) closed per user instruction; branch `feat/log-db-trace-trigger` retained and can be reopened.
- Remaining: `logs_2.sqlite` (662 MB) rebuild, 7 large rollouts, vision-bridge durable catalog fix.
