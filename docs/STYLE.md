# Documentation Style / 文档风格

本仓库所有 Markdown 文档遵循同一风格；新增或修改文档时请遵守本约定。

## 规则 / Rules

- 正文用中文；代码、命令、字段名、issue/PR 链接保持英文原样。
- 章节标题用「English / 中文」双语（英文在前、中文在后），例如 `## Why / 背景`、`## Hard rules / 红线`、`## Steps / 步骤`。
- 文件最外层标题（`#`）同样用双语；纯数据附录（如 `docs/measured-results.md`）可保留英文正文，但标题需双语。
- 不提交真实绝对路径、API 令牌、会话正文；示例路径用 `$env:USERPROFILE` / `os.path.expanduser` 或相对路径。
- 每个修复/操作须说明备份与回滚；诊断类内容优先只读。

## 检查 / Check

- 合并前运行 `git diff --check`。
- 如引入 `scripts/07_check_doc_style.py`，一并运行以校验标题双语、且无真实绝对路径。