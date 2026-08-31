---
name: codextune
description: Use when Codex/ChatGPT Desktop 启动慢、旧任务加载慢，或 config.toml、cc-switch、skill、插件、MCP 引发性能或配置加载问题。
---

# CodexTune

系统化排查 Codex 桌面端性能问题。核心原则：先证据、后修复；每个修复都带备份与回滚。

## Workflow / 流程

1. 收集证据：运行 `scripts/01_collect_evidence.ps1`，把输出保存到任务目录。
2. 配置专项：涉及 `config.toml` 或 cc-switch 时，先运行只读检查器，再进入 `playbooks/06-config-safety.md`：

   ```powershell
   python scripts/05_check_codex_config.py
   python scripts/05_check_codex_config.py --json
   ```

   检查器需要 Python 3.11+；更旧版本需在隔离环境中提供 `tomli`。
3. 定位现象：冷启动慢 / 旧任务慢 / 每轮变重 / MCP 反复失败，对号入座到 `playbooks/`。
4. 对照实验：每次只改一个变量（插件、MCP、skill、日志库），改前备份、改后复测。
5. 完成前验证：修复是否生效以实测为准，不以“看起来对”为准。

## Red Lines / 红线

- 只读诊断优先，不直接删除任何数据。
- 全局 `.codex` 配置修改前必须备份并征得用户确认。
- API 令牌、真实路径、会话正文不得写入仓库。
