# Contributing / 参与贡献

Thanks for helping CodexTune improve! / 感谢你帮助改进 CodexTune！

## How to contribute / 如何贡献

1. **Report a problem** / 报告问题：Open an issue with the symptom, evidence summary, and environment info. / 开 Issue，附症状、证据摘要和环境信息。
2. **Propose a fix** / 提出修复：Create a branch, make ONE change, add before/after measurements, open a PR. / 建分支、只改一处、附前后数据、开 PR。
3. **Improve docs** / 改进文档：Playbooks and measured results are always welcome. / 欢迎完善手册和实测数据。

## Rules / 规则

- Every fix must support backup + rollback. / 每个修复必须支持备份与回滚。
- Scripts are read-only unless explicitly stated. / 脚本默认只读。
- Sanitize all paths and never commit secrets. / 路径脱敏，绝不提交敏感信息。
- Measured before/after data is preferred over speculation. / 优先附实测数据，不做猜测。

## PR checklist / PR 检查清单

- [ ] Single logical change / 单一逻辑改动
- [ ] Backup + rollback described / 说明备份与回滚
- [ ] Before/after measurement included / 附前后实测数据
- [ ] No secrets, no real paths / 无敏感信息与真实路径
- [ ] README/docs updated if needed / 必要时更新文档
