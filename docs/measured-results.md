# Measured Results

Real measurements from a Windows investigation (2026-08). Machine: Windows 10/11, ChatGPT/Codex Desktop, 16GB RAM.

## Startup window (plugin/skill related)

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
