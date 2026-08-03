<div align="center">

# CodexTune

**诊断并优化你的 ChatGPT Codex 环境。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**English：[README.md](README.md)**

</div>

CodexTune 是一套只读诊断工具、排查手册和可复用 skill，用于发现并修复 ChatGPT/Codex Desktop 的性能问题：冷启动慢、旧任务加载慢、skill 与插件上下文超预算、MCP 故障、工作区膨胀与内存压力。

方案基于两台 Windows 电脑的真实排查，前后对照数据见 [docs/measured-results.md](docs/measured-results.md)。

---

## 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [仓库结构](#仓库结构)
- [排查手册](#排查手册)
- [多机协作流程](#多机协作流程)
- [隐私与安全](#隐私与安全)
- [参与贡献](#参与贡献)
- [许可证](#许可证)

## 功能特性

| 功能 | 说明 |
|---|---|
| 启动诊断 | 采集冷启动瓶颈证据（plugin/list、manifest 解析、模型刷新、MCP 初始化） |
| Skill 管理 | 找出占用上下文预算的未使用或异常 skill |
| 插件清理 | 识别并隔离未启用的暂存插件 |
| MCP 故障排查 | 审计 MCP 配置、版本冲突、`--refresh` 重复下载、死端点 |
| 工作区优化 | 发现大会话、磁盘压力与内存大户 |
| 性能基准测量 | 用可复现脚本测量前后效果 |

## 快速开始

### 作为 skill 使用

将 `SKILL.md` 复制到项目或用户级 skills 目录，然后让 Codex 执行一次性能诊断。

### 手动运行诊断

```powershell
# 只读操作，证据输出到 ./reports/<时间戳>/
powershell -ExecutionPolicy Bypass -File scripts/01_collect_evidence.ps1

# 可选：纳入当前项目的 .agents/skills 和扩展指标
powershell -ExecutionPolicy Bypass -File scripts/01_collect_evidence.ps1 -ProjectRoot . -IncludeExtended
```

```powershell
# 只读分析日志库，统计模型刷新/MCP/skill 相关日志次数
python scripts/02_analyze_logs.py
python scripts/02_analyze_logs.py --since "2026-08-02 15:33:30"
python scripts/02_analyze_logs.py --json
```

## 仓库结构

```text
CodexTune/
├── README.md               # 英文
├── README.zh-CN.md         # 中文
├── SKILL.md                # 可复用 skill 入口
├── LICENSE                 # MIT
├── docs/
│   ├── measured-results.md      # 实测前后数据
│   └── migration-guide.md       # 第二台电脑接入指南
├── playbooks/              # 分步排查手册
└── scripts/
    ├── 01_collect_evidence.ps1  # 只读证据采集
    └── 02_analyze_logs.py       # 只读日志库分析
```

## 排查手册

按症状选择对应手册：

| 症状 | 手册 |
|---|---|
| 冷启动慢（约 30 秒） | [01-startup-slow.md](playbooks/01-startup-slow.md) |
| 旧任务加载慢 | [02-old-thread-slow.md](playbooks/02-old-thread-slow.md) |
| skill 与插件上下文超预算 | [03-skill-bloat.md](playbooks/03-skill-bloat.md) |
| MCP 故障 / 版本冲突 | [04-mcp-and-plugins.md](playbooks/04-mcp-and-plugins.md) |
| 数据库膨胀与安全恢复 | [05-database-safety.md](playbooks/05-database-safety.md) |

## 多机协作流程

两台电脑登录同一 GitHub 账号。第二台克隆本仓库、运行相同诊断，并提交自己的发现：

1. 克隆：`git clone https://github.com/SIMON-WORLD/CodexTune.git`
2. 运行：`scripts/01_collect_evidence.ps1`
3. 对比：对比两份证据包
4. 修复：每个 PR 只改一处，带备份与回滚
5. 沉淀：Issue 与 PR 沉淀为共同经验库

完整接入指南见 [docs/migration-guide.md](docs/migration-guide.md)。

## 隐私与安全

- 绝不提交 API 密钥、令牌、真实路径或会话内容。
- 所有脚本默认只读。
- 每个修复都必须支持备份与回滚。
- 修改全局 `.codex` 前必须先征得用户确认。

## 参与贡献

发现新问题或更好的修复？欢迎提交 Issue 或 PR。附上前后对照的实测数据最佳。PR 检查清单见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目使用 **MIT 许可证**。详见 [LICENSE](LICENSE)。
