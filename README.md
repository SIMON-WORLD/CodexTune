<div align="center">

# CodexTune

**Diagnose and optimize your ChatGPT Codex environment.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**中文版：[README.zh-CN.md](README.zh-CN.md)**

</div>

CodexTune is a collection of read-only diagnostic tools, playbooks, and a reusable skill for finding and fixing performance problems in ChatGPT/Codex Desktop — slow cold start, slow old-thread loading, skill/plugin context pressure, MCP failures, workspace bloat, and memory pressure.

Everything here is based on real Windows investigations on two machines; measured before/after data lives in [docs/measured-results.md](docs/measured-results.md).

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Repo Layout](#repo-layout)
- [Playbooks](#playbooks)
- [Known Issues](#known-issues)
- [Multi-Machine Workflow](#multi-machine-workflow)
- [Privacy & Safety](#privacy--safety)
- [Contributing](#contributing)
- [License](#license)

## Features

| Feature | What it does |
|---|---|
| Startup diagnostics | Collects evidence on cold-start bottlenecks (plugin/list, manifest parsing, model refresh, MCP init) |
| Skill management | Finds unused or malformed skills that eat context budget |
| Plugin cleanup | Identifies and quarantines unenabled staged plugins |
| MCP troubleshooting | Audits MCP config, version conflicts, `--refresh` re-downloads, dead endpoints |
| Workspace optimization | Finds large sessions, disk pressure, and memory hogs |
| Performance benchmarking | Measures before/after with reproducible scripts |

## Quick Start

### Use as a skill

Copy `SKILL.md` into your project or user skills directory, then ask Codex to run a performance diagnosis.

### Run diagnostics manually

```powershell
# Read-only. Writes evidence JSON to ./reports/<timestamp>/
powershell -ExecutionPolicy Bypass -File scripts/01_collect_evidence.ps1

# Optional: include the current project's .agents/skills and extended metrics
powershell -ExecutionPolicy Bypass -File scripts/01_collect_evidence.ps1 -ProjectRoot . -IncludeExtended
```

```powershell
# Analyze the local log DB (read-only)
python scripts/02_analyze_logs.py
python scripts/02_analyze_logs.py --since "2026-08-02 15:33:30"
python scripts/02_analyze_logs.py --json
```

## Repo Layout

```text
CodexTune/
├── README.md               # English / 英文
├── README.zh-CN.md         # 中文
├── SKILL.md                # Reusable skill entry
├── LICENSE                 # MIT
├── docs/
│   ├── measured-results.md      # Real before/after measurements
│   ├── migration-guide.md       # Second-machine onboarding
│   └── known-issues.md          # Confirmed issues & recovery
├── playbooks/              # Step-by-step troubleshooting guides
└── scripts/
    ├── 01_collect_evidence.ps1  # Read-only evidence collector
    └── 02_analyze_logs.py       # Read-only log DB analyzer
```

## Playbooks

Pick the playbook that matches your symptom:

| Symptom | Playbook |
|---|---|
| Cold start is slow (~30s) | [01-startup-slow.md](playbooks/01-startup-slow.md) |
| Old threads load slowly | [02-old-thread-slow.md](playbooks/02-old-thread-slow.md) |
| Skill/plugin context over budget | [03-skill-bloat.md](playbooks/03-skill-bloat.md) |
| MCP failures / version conflicts | [04-mcp-and-plugins.md](playbooks/04-mcp-and-plugins.md) |
| Database bloat / safe recovery | [05-database-safety.md](playbooks/05-database-safety.md) |

## Known Issues

App-level failures that look like permission problems but are actually caused by broken local config (e.g. the "Finish Windows setup / one-time permission" gate when config.toml fails to load). Confirmed root causes and recovery steps: [docs/known-issues.md](docs/known-issues.md).

## Multi-Machine Workflow

Both machines log into the same GitHub account. The second machine clones this repo, runs the same diagnostics, and raises its own findings:

1. Clone: `git clone https://github.com/SIMON-WORLD/CodexTune.git`
2. Run: `scripts/01_collect_evidence.ps1`
3. Compare: diff the two evidence packages
4. Fix: one change per PR, with backup + rollback
5. Learn: issues and PRs become the shared knowledge base

See [docs/migration-guide.md](docs/migration-guide.md) for the full onboarding guide.

## Privacy & Safety

- Never commit API keys, tokens, real paths, or conversation contents.
- All scripts are read-only unless explicitly stated.
- Every fix must support backup + rollback.
- Global `.codex` changes require user confirmation first.

## Contributing

Found a new issue or a better fix? Open an issue or submit a PR. Measured data with before/after numbers is highly appreciated. See [CONTRIBUTING.md](CONTRIBUTING.md) for the PR checklist.

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
