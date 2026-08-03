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
