# 06 - Config.toml & cc-switch Safety / 配置安全

## Why / 背景

`~/.codex/config.toml` is the runtime configuration for Codex, but it is not the only writer. Codex itself, cc-switch, and third-party bridge tools can all rewrite the same file. Real incidents on two machines:

- `wire_api = "chat"` was removed upstream; any config still using it fails to start with `wire_api = "chat" is no longer supported` (openai/codex#7782).
- A vision bridge's `setup` replaced `model_provider` and wrote `wire_api = "chat"`, breaking Codex.
- cc-switch keeps its own database (provider config, common config, MCP servers) and rewrites live `config.toml` on provider switches. Edits made only to the live file can be overwritten.
- Non-ASCII paths were written as double-encoded UTF-8 by older Windows PowerShell tooling, producing mojibake entries in `[projects.*]` and desktop preferences.
- cc-switch regenerates its model catalog on sync; if the provider database has no `input_modalities`, image-capable model entries are rewritten back to text-only.

`config.toml` 是 Codex 的运行配置，但不是唯一写手：Codex、cc-switch、第三方桥接工具都会写它。任何只改 live 文件的操作都可能被下一次同步覆盖。

## Hard rules / 红线

- Never let agents auto-edit global `.codex` / `.cc-switch` config without explicit user confirmation and a backup.
- Never set `wire_api = "chat"`; use `"responses"`.
- Edit provider / MCP / common config / model catalog inside cc-switch, not only in the live `config.toml`, because cc-switch is the source of truth and will rewrite on the next switch.
- Always validate TOML after an edit (`scripts/05_check_codex_config.py`, or the official JSON schema via `#:schema https://developers.openai.com/codex/config-schema.json`).
- Keep `auth.json` untouched when the goal is to preserve official ChatGPT login; cc-switch's "preserve official auth on switch" does exactly that.

## Read-only check / 只读检查

```powershell
python scripts/05_check_codex_config.py
python scripts/05_check_codex_config.py --json
```

The script reports:

- TOML parse errors.
- `wire_api = "chat"` anywhere.
- `model_provider` that does not exist in `[model_providers]`.
- `base_url` pointing to a localhost port that is not listening.
- `model_catalog_json` missing or unreadable.
- Mojibake (double-encoded UTF-8) path lines.
- Localhost MCP endpoints that are not listening.

## Safe procedure / 安全流程

1. Fully quit Codex/ChatGPT and cc-switch (tray exit) before editing any config source.
2. Back up `config.toml`, the active model catalog file, and (if editing providers) `cc-switch.db`; record SHA-256 and keep backups private.
3. Run `scripts/05_check_codex_config.py` to snapshot current findings.
4. Fix the source, not just the live file:
   - Provider / model / MCP: edit in cc-switch or its database.
   - Common config: edit cc-switch's common config snippet.
   - Model image capability: add `"input_modalities": ["text","image"]` to the provider's `modelCatalog.models[]` in the cc-switch database so every generated catalog keeps image support.
   - Mojibake: remove only the double-encoded path entries; keep the correct Unicode paths.
5. Re-run the checker until no errors remain.
6. Reopen cc-switch, switch the provider once, then restart Codex and verify the live config still matches.
7. Keep the backups until at least one full restart has passed.

## Who writes what / 字段归属表

| Config area / 配置区域 | Main writer / 主要写入方 | Notes / 说明 |
|---|---|---|
| `model_provider` / `model_providers.*` / `base_url` / `wire_api` | cc-switch (provider switch), third-party bridge tools | cc-switch DB is the source of truth; live-only edits get overwritten |
| `model_catalog_json` + model catalog file | cc-switch (`modelCatalog`) | cc-switch regenerates the fixed catalog filename and rewrites the pointer on sync |
| `[mcp_servers.*]` | cc-switch MCP table | rebuilt from the DB on sync |
| `[marketplaces.*]` | cc-switch common config / Codex desktop | local sources can become dead paths after moves |
| `[projects.*]` trust | Codex when opening new dirs | can contain mojibake path keys from old tooling |
| `[desktop.*]`, avatar, theme | Codex desktop app | UI state; usually harmless |
| `notify`, `[shell_environment_policy.set]` | cc-switch common config / Codex desktop/runtime | paths/values may change with app updates |
| `wire_api = "chat"` | legacy third-party tools | removed upstream; must not exist |

配置段/字段归属：cc-switch 管 provider、MCP、模型目录与公共配置（含市场与 shell 环境注入）；桌面应用管市场刷新、信任、主题与头像；第三方桥接工具可能临时改 `base_url`/`model_provider`；用户手工修改应只在备份后进行，并以 cc-switch 数据库为准。

## Notes / 备注

- Project-scoped `.codex/config.toml` cannot override provider/auth/notify/telemetry keys; those belong in the user-level file.
- Legacy `[profiles]` tables and top-level `profile = "..."` are no longer supported; use `<name>.config.toml` files selected with `--profile`.
- `model_catalog_json` relative paths resolve from `CODEX_HOME` (`~/.codex`).
- cc-switch only treats the exact filename `cc-switch-model-catalog.json` as owned; other catalog files are treated as user-owned and preserved when no `modelCatalog` is present.
- Evidence and backups contain local paths and possibly tokens: keep them out of the repository.
