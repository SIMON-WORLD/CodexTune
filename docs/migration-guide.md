# Migration Guide / 第二台电脑迁移指南

This guide explains how to apply CodexTune on a second machine and how the two machines collaborate through GitHub issues and PRs.

本指南说明如何在第二台电脑应用 CodexTune，以及两台电脑如何通过 GitHub Issue 与 PR 协作。

## Prerequisites / 前置条件

- Both machines logged into the same GitHub account (e.g. `SIMON-WORLD`), with `gh` CLI authenticated.
  两台电脑已登录同一 GitHub 账号（如 `SIMON-WORLD`），且 `gh` CLI 已认证。
- CodexTune repository cloned on the second machine.
  第二台已克隆 CodexTune 仓库。

## Step 1: Clone / 克隆

```powershell
git clone https://github.com/SIMON-WORLD/CodexTune.git
```

## Step 2: Install the skill / 安装 skill

Copy `SKILL.md` into the second machine's skill directory:

将 `SKILL.md` 复制到第二台电脑的 skill 目录：

```powershell
# Project-level / 项目级
Copy-Item .\SKILL.md "$env:USERPROFILE\.codex\skills\codextune\SKILL.md" -Force
# or user-level / 或用户级
```

Then ask Codex: "Use the codextune skill to diagnose performance issues on this machine."

然后让 Codex：使用 codextune skill 诊断这台机器的性能问题。

## Step 3: Collect evidence / 采集证据

Run the read-only collector and keep the output LOCAL (never commit it):

运行只读采集器，输出保留在本地（不要提交）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\01_collect_evidence.ps1
```

The evidence package contains: process list, skill counts, plugin staging counts, database sizes, and suspicious MCP config lines.

证据包包含：进程列表、skill 数量、插件暂存数量、数据库大小、可疑 MCP 配置行。

## Step 4: Let Codex dig deeper / 让 Codex 深入排查

This machine's issues may differ from machine #1. Do NOT assume the same fixes apply. Let the skill run its own investigation, especially:

这台机器的问题可能与第一台不同。不要假设相同修复直接适用。让 skill 自行排查，重点关注：

- Cold start logs (`codex_models_manager`, `plugin/list`, `skills/list`, manifest parse warnings) / 冷启动日志
- MCP servers (config audit, repeated failures, `--refresh`, version conflicts) / MCP 服务
- Skill context budget (`truncated skill metadata ... total_skills=...`) / skill 上下文预算
- Old-thread loading (largest rollout files) / 旧任务加载
- Memory pressure (e.g. OneDrive.Sync.Service) / 内存压力

## Step 5: Raise findings via GitHub / 通过 GitHub 提交发现

Open an issue per distinct finding, with the evidence summary and before/after numbers if available:

每个独立发现开一个 Issue，附证据摘要与前后数据（如有）：

```powershell
gh issue create --repo SIMON-WORLD/CodexTune --title "Machine2: <symptom>" --body "<evidence>"
```

Workflow / 协作流程：

1. Issue describes the problem on machine #2. / Issue 描述第二台机器的问题。
2. A PR proposes one fix with backup + rollback. / PR 提出一处修复，带备份与回滚。
3. Both machines verify the fix; measured results are added to `docs/measured-results.md`. / 两台机器验证修复，实测数据补充进 measured-results。
4. Merge only after both machines confirm. / 两台机器都确认后才合并。

## Multi-machine diff template / 两机差异模板

```markdown
## Machine / 机器
- #1: Windows 10/11, 16GB RAM, Codex Desktop <version>
- #2: <OS>, <RAM>, Codex Desktop <version>

## Common symptoms / 共同症状
- ...

## Machine #1 only / 仅 #1
- ...

## Machine #2 only / 仅 #2
- ...

## Evidence / 证据
- scripts/01_collect_evidence.ps1 output, sanitized / 脱敏后的采集输出
```

## Privacy / 隐私红线

- Evidence packages and logs are git-ignored; never push them. / 证据包与日志已被 .gitignore 忽略，禁止推送。
- Sanitize paths (`C:\Users\...` -> `%USERPROFILE%`, drive letters -> placeholders) before adding anything to issues/PRs. / 提交前脱敏路径。
- Never include API keys, tokens, or conversation contents. / 绝不包含 API 密钥、令牌或会话内容。
