# Measured Results

Real measurements from Windows investigations (2026-08). Machine: Windows 10/11, ChatGPT/Codex Desktop, 16GB RAM.

## Startup window (plugin/skill related) - Machine A

| Metric | Before | After |
|---|---|---|
| Staged plugin packages in `.codex\.tmp\plugins\plugins` | 180 | 1 |
| Plugin manifest parse warnings in startup window | 41 | 18 |
| `plugin/list` RPC calls in startup window | 16-18 | 13 |
| `skills/list` RPC calls in startup window | 12 | 0 |
| Skills enumerated in context (`total_skills`) | 294 | 233 |
| Skills omitted due to budget (`omitted_skills`) | 74 | 24 |
| Model refresh timeout | present | absent |

Actions applied: removed 61 unused project skills, quarantined 179 unenabled staged plugins, removed unused MCP servers, fixed `mcp-stata` version conflict.

## MCP findings

- `mcp-stata` declared `mcp>=1.0.0` with no upper bound; uv resolved `mcp 2.0.0`, which removed `mcp.server.fastmcp` -> server crashed.
  Fix: `args = ["--from", "mcp-stata@latest", "--with", "mcp<2", "mcp-stata"]` (avoids repeated 50MB re-downloads too).
- `uvx --refresh` forces a full re-download every launch; removing it relies on the uv cache.
- A local aggregator MCP (`connector-proxy`) produced repeated HTTP 502 at startup; removing unused MCP servers removed that noise.

## Memory findings

- `OneDrive.Sync.Service` ballooned to ~21GB private memory after reboot and starved the system (keyboard input also failed while RAM was exhausted). Stopping it restored ~10GB of available RAM.
- Large conversation rollouts (up to 113MB, mostly image-generation events and tool outputs) dominate old-thread open time. Archiving moves them out of the active list but does not shrink the file.

## Skill cleanup note

- 61 of 101 project skills showed catalog-only presence (never referenced in ~75k conversation lines) and were moved out (recoverable backup).
- Context budget after cleanup: `total_skills=233, included=209, omitted=24` (was 294/220/74).

## Second machine baseline (2026-08-02) - Machine B

Baseline collected before any cleanup on the second machine with the extended collector (`-ProjectRoot . -IncludeExtended`).

| Metric | Value |
|---|---|
| Staged plugin packages in `.codex\.tmp\plugins\plugins` | 180 |
| SKILL.md files: user `.codex\skills` | 420 |
| SKILL.md files: user `.agents\skills` | 5 |
| SKILL.md files: project `.agents\skills` (Project Test) | 49 |
| SKILL.md files: plugin cache | 73 |
| `plugin/list` rows in `logs_2.sqlite` | 546 |
| `skills/list` rows in `logs_2.sqlite` | 3556 |
| Model refresh failures in `logs_2.sqlite` | 4822 |
| MCP transport failures | present (`http://127.0.0.1:5157/mcp`, latest 2026-08-02) |
| `logs_2.sqlite` size | 662.58 MB |
| Active sessions | 6.82 GB / 423 files |
| Archived sessions | 2.00 GB / 66 files |
| Largest session JSONL | 541.61 MB |
| C: free | 9.25 GB |
| Proxy env | `http://127.0.0.1:7897` |
| Loopback exemptions | stale `AppContainer NOT FOUND` entries |
| `config.toml` MCP servers | 8 |
| `stata-mcp` launch flags | `--refresh --refresh-package mcp-stata@latest` |

Actions applied: none yet (baseline only). The same `180` staged plugin count and the same `stata-mcp` flag pattern were observed on Machine A before cleanup, so both machines should apply the same controlled cleanup sequence and measure startup seconds before/after each change.

## Second machine after cleanup (2026-08-03) - Machine B

Collected with the extended collector after the first cleanup round (`-ProjectRoot . -IncludeExtended`).

| Metric | Before | After |
|---|---|---|
| Staged plugin packages in `.codex\.tmp\plugins\plugins` | 180 | 0 |
| SKILL.md files: user `.codex\skills` | 420 | 400 |
| `plugin/list` rows in startup window after restart | 13 | 12 |
| `skills/list` rows in startup window after restart | 122 | 80 |
| Model refresh failures after restart | 4822 (cumulative) | 0 |
| connector-proxy / `127.0.0.1:5157` errors after restart | present | 0 |
| `logs_2.sqlite` size | 662.58 MB | 662.58 MB (unchanged; safe rebuild pending, see playbook 05) |
| Active sessions | 6.82 GB / 423 files | 5.80 GB / 435 files |
| Archived sessions | 2.00 GB / 66 files | 3.04 GB / 69 files |
| Largest session JSONL | 541.61 MB | unchanged (kept in use) |
| C: free | 9.25 GB | 20.92 GB |
| `config.toml` MCP servers | 8 | 5 |
| `stata-mcp` launch flags | `--refresh --refresh-package mcp-stata@latest` | `--from mcp-stata@latest --with mcp<2 mcp-stata` |
| Loopback exemptions | non-elevated view showed `NOT FOUND` | false alarm: 5 valid Microsoft Store/Xbox entries, unchanged |

Actions applied: removed dead `connector-proxy`; fixed `stata-mcp` flags; quarantined 180 unenabled staged plugins and 20 zero-reference user skills; cleaned npm cache and 505 orphaned uv `.tmp*` dirs (about 12.75 GB freed). Remaining: safe `logs_2.sqlite` rebuild (pending), and analytics send failures tied to the proxy path still appear occasionally.
