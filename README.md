<div align="center">

# CodexTune

**Diagnose and optimize your ChatGPT Codex environment. / 诊断并优化你的 ChatGPT Codex 环境。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## Overview / 简介

CodexTune is a collection of read-only diagnostic tools, playbooks, and a reusable skill for diagnosing and fixing performance problems in ChatGPT/Codex Desktop environments:

- Slow cold start (e.g. ~30s)
- Slow old-thread loading
- Skill/plugin context over budget
- MCP server failures and version conflicts
- Workspace bloat and memory pressure

CodexTune 是一套只读诊断工具、排查手册和可复用 skill，用于诊断和修复 ChatGPT/Codex Desktop 环境的性能问题：冷启动慢（如约 30 秒）、旧任务加载慢、skill/插件上下文超预算、MCP 服务故障与版本冲突、工作区膨胀与内存压力。

The findings and fixes are based on real Windows investigations; measured data is in [docs/measured-results.md](docs/measured-results.md).

方案与修复基于真实的 Windows 排查，前后对照数据见 [docs/measured-results.md](docs/measured-results.md)。

## Features / 功能

| English | 中文 |
|---|---|
| Startup diagnostics | 启动诊断 |
| Skill management | Skill 管理 |
| Plugin cleanup | 插件清理 |
| MCP troubleshooting | MCP 故障排查 |
| Workspace optimization | 工作区优化 |
| Performance benchmarking | 性能基准测量 |

## Quick Start / 快速开始

### 1. Use as a skill / 作为 skill 使用

Copy `SKILL.md` into your project or user skills directory, then ask Codex to run a performance diagnosis.

将 `SKILL.md` 复制到项目或用户级 skills 目录，然后让 Codex 执行一次性能诊断。

### 2. Run diagnostics manually / 手动运行诊断

```powershell
# Read-only. Writes evidence JSON to ./reports/<timestamp>/
# 只读操作。证据输出到 ./reports/<时间戳>/
powershell -ExecutionPolicy Bypass -File scripts/01_collect_evidence.ps1

# Optional: include the current project's .agents/skills and extended metrics
# (session size, disk free, OneDrive memory, proxy, loopback, config summary)
# 可选：纳入当前项目的 .agents/skills 和扩展指标
# （会话体积、磁盘剩余、OneDrive 内存、代理、loopback、配置摘要）
powershell -ExecutionPolicy Bypass -File scripts/01_collect_evidence.ps1 -ProjectRoot . -IncludeExtended
```

### 3. Follow the playbooks / 按手册排查

Pick the playbook that matches your symptom / 按症状选择对应手册：

- [01-startup-slow.md](playbooks/01-startup-slow.md) – cold start / 冷启动慢
- [02-old-thread-slow.md](playbooks/02-old-thread-slow.md) – old thread loading / 旧任务加载慢
- [03-skill-bloat.md](playbooks/03-skill-bloat.md) – skill/plugin context / skill/插件超预算
- [04-mcp-and-plugins.md](playbooks/04-mcp-and-plugins.md) – MCP & plugin cleanup / MCP 与插件清理

## Repo Layout / 仓库结构

```text
CodexTune/
├── README.md
├── SKILL.md                 # Reusable skill entry / 可复用 skill 入口
├── LICENSE                  # MIT
├── docs/
│   └── measured-results.md  # Real measured before/after data / 实测前后数据
├── playbooks/               # Step-by-step troubleshooting guides / 排查手册
└── scripts/
    └── 01_collect_evidence.ps1  # Read-only evidence collector / 只读证据采集
```

## Multi-Machine Workflow / 多机协作流程

Both machines log into the same GitHub account. The second machine clones this repo, runs the same diagnostics, and raises its own findings:

两台电脑登录同一 GitHub 账号。第二台克隆本仓库、运行相同诊断，并提交自己的发现：

1. Clone / 克隆：`git clone https://github.com/SIMON-WORLD/CodexTune.git`
2. Run / 运行：`scripts/01_collect_evidence.ps1`
3. Compare / 对比：diff the two evidence packages / 对比两份证据包
4. Fix / 修复：one change per PR, with backup + rollback / 每个 PR 只改一处，带备份与回滚
5. Learn / 沉淀：issues and PRs become the shared knowledge base / Issue 与 PR 沉淀为共同经验库

See [docs/migration-guide.md](docs/migration-guide.md).

详见 [docs/migration-guide.md](docs/migration-guide.md)。

## Privacy & Safety / 隐私与安全

- Never commit API keys, tokens, real paths, or conversation contents. / 绝不提交 API 密钥、令牌、真实路径或会话内容。
- All scripts are read-only unless explicitly stated. / 所有脚本默认只读。
- Every fix must support backup + rollback. / 每个修复都必须支持备份与回滚。
- Global `.codex` changes require user confirmation first. / 修改全局 `.codex` 前必须先征得用户确认。

## Contributing / 参与贡献

Found a new issue or a better fix? Open an issue or submit a PR. Measured data with before/after numbers is highly appreciated.

发现新问题或更好的修复？欢迎提交 Issue 或 PR。附上前后对照的实测数据最佳。

## License / 许可证

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

本项目使用 **MIT 许可证**。详见 [LICENSE](LICENSE)。
