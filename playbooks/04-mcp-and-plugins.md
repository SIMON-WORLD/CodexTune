# 04 - MCP 与插件清理

## MCP 常见坑

- `uvx --refresh` / `--refresh-package`：每次启动强制重新解析下载，可能数十 MB。去掉后靠缓存启动。
- 版本冲突：`--from pkg@latest` 可能解析到不兼容的最新依赖（例：mcp-stata 需要 mcp<2）。用 `--with mcp<2` 或锁定版本。
- HTTP 型 MCP（本地代理/远端）：启动时反复 502 会阻塞。不常用的直接移除配置段。

## 修改 config.toml 的红线（真实事故教训）

> 事故：本机曾用固定行号注释 `[mcp_servers.stata-mcp]`，行号偏移误注释了下一段 `[mcp_servers.node_repl]` 的表头，导致 node_repl 的 `command`/`args` 并入上一段 http 类型段落，报 `url is not supported for stdio`，**整个 config.toml 解析失败，Codex 打不开**。

1. **不要随便修改 config.toml**。除非必要，否则保持原样；先想清楚再动手。
2. 修改前先备份：复制到任务目录并记录 SHA-256（备份含 API 令牌，禁止入仓）。
3. 禁用某段 MCP 时，按**表头边界**整段注释：从 `[mcp_servers.xxx]` 行到下一个 `[mcp_servers.yyy]` 或 `[其他]` 表头之间的所有行（含空行）全部加 `#`，且**绝不能**注释到下一段的表头。
4. 每次只改一个 MCP，改完立即用 TOML 解析器验证（Python 3.11+ `tomllib`，或结构检查：stdio 段落不得有 url，http 段落必须有 url）。
5. 完全退出应用后重启验证；发现打不开立即用备份回滚。
6. 改坏时不要反复试：先恢复备份，再按表头边界重做。

## 插件暂存目录

`.codex\.tmp\plugins\plugins` 是市场目录的本地物化副本；只有与已启用列表匹配的目录是需要的。未启用目录移出后，下次同步可能被重新物化——需实测确认。

## 日志库隔离（可选）

`logs_2.sqlite` 过大时：完全退出应用 -> 备份三个文件（sqlite/-wal/-shm）-> 移出原文件 -> 启动让应用重建 -> 验证会话仍在 -> 复测。不要删除，随时可恢复。

## 应用打不开：「一次性权限」门禁且无 UAC 弹窗

症状：应用卡在「完成 Windows 设置 / ChatGPT 需要一次性权限才能在你电脑上运行」，点击重试失败且系统无真实 UAC 弹窗。

已确认根因（2026-08-04 第二台电脑）：最常见原因是 config.toml 加载失败（引用的模型目录文件缺失、MCP 段残留旧管道、插件未安装等），被应用错误路由到该门禁界面。恢复与预防详见 [docs/known-issues.md](../docs/known-issues.md)。
