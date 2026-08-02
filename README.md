# CodexTune

Diagnose and optimize your ChatGPT Codex environment.

## Features

- Startup diagnostics
- Skill management
- Plugin cleanup
- MCP troubleshooting
- Workspace optimization
- Performance benchmarking

## Quick start

1. Run the read-only diagnostic script (see `scripts/`).
2. Read the matching playbook under `playbooks/`.
3. Apply fixes one at a time, then re-measure.

## Repo layout

- `scripts/` – read-only diagnostic collectors and measurement tools
- `playbooks/` – step-by-step troubleshooting guides
- `SKILL.md` – optional skill entry so Codex can follow the same process on any machine

## Privacy

- Never commit API keys, tokens, real paths, or conversation contents.
- All scripts are read-only unless a fix script explicitly says otherwise, and every fix must support backup + rollback.

## Status

Work in progress, built from a real Windows performance investigation.
