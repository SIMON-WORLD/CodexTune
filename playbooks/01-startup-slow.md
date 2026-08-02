# 01 - 冷启动慢（约 30 秒）

## 现象

点击图标后应用长时间无响应；日志中常见 `codex_models_manager::manager ... timeout waiting for child process to exit`。

## 排查顺序

1. **插件清单解析**：检查 `.codex\.tmp\plugins\plugins` 目录数与 `plugin/list` 调用次数（`logs_2.sqlite` 中按 `rpc.method="plugin/list"` 统计）。未启用插件过多会拖慢启动。
2. **远端插件目录同步**：日志中 `recommended_plugins_mode_for_config ... failed to load recommended plugins` 表示网络不佳，启动期间反复重试。
3. **MCP 服务启动**：`stata-mcp` 若带 `--refresh` 会每次下载约 50MB；`connector-proxy` 若 502 会反复重试。见 `04-mcp-and-plugins.md`。
4. **模型刷新超时**：网络到模型目录慢会叠加。换稳定节点后复测。
5. **日志库膨胀**：`logs_2.sqlite` 过大时可能阻塞启动握手（社区见 issue #27741），隔离方法见 playbook 04。

## 对照实验

每次只改一个变量：先测基线 -> 改一项 -> 重启 -> 复测。记录启动秒数。
