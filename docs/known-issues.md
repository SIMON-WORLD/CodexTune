# Known Issues / 已知问题

Real issues confirmed during multi-machine debugging, with recovery steps. Each entry is written after the root cause was verified, not guessed.

多机排查中确认过的真实问题及恢复步骤。每条均为根因验证后的记录，而非猜测。

---

## 1. App won't open: “ChatGPT needs one-time permission to run on your computer” (no UAC dialog)

## 1. 应用打不开：提示「ChatGPT 需要一次性权限才能在你电脑上运行」，且无 UAC 弹窗

### Symptom / 症状

- Windows 上 ChatGPT/Codex 桌面版卡在「完成 Windows 设置」门禁界面：ChatGPT 需要一次性权限才能在你电脑上运行。
- 点击「重试」立即失败，系统不会弹出真实的 UAC 提权框（界面里画的 UAC 对话框只是插图，不是真实请求）。
- 卸载重装无效。

### Root cause / 根因

The most common real cause (confirmed on Machine B, 2026-08-04) is `%USERPROFILE%\.codex\config.toml` failing to load (syntax corruption, missing referenced files such as the model catalog, or dead paths like stale named pipes / missing MCP executables). The app routes the config load failure to the sandbox setup gate instead of showing the real error.

最常见的真实根因（第二台电脑 2026-08-04 已确认）是 `%USERPROFILE%\.codex\config.toml` 无法加载（语法损坏、引用的文件缺失如模型目录、失效路径如旧命名管道或缺失的 MCP 可执行程序）。应用把配置加载失败错误地路由到了沙箱安装门禁界面，而不是显示真实报错。

Other known causes (in decreasing order of likelihood):

其他已知原因（按概率排序）：

1. OAuth 会话失效 / refresh token 被撤销 → 云端配置拉取 401 → 沙箱安装接口失败 → 同样被路由到该门禁（改名 `auth.json` 后重新登录解决）。
2. 系统侧限制：UAC 被设为「从不通知」、AppInfo 服务被禁用、安全软件或企业策略拦截提权。
3. 应用已知 bug：某个版本的 setup helper 丢失 UAC manifest（对应 openai/codex PR #25949，CreateProcess 报 error 740）。

### Recovery (reversible, in order) / 恢复步骤（可回滚，按顺序）

```powershell
# 1. 完全退出应用；不要卸载重装
# 2. 备份并移走配置（只改名，不删除）
Rename-Item "$env:USERPROFILE\.codex\config.toml" "config.toml.bak"
# 3. 重新启动应用
```

- If the app opens with default config → the config file was the problem. Rebuild it from the backup section by section, validating TOML after each change (see [playbooks/04](playbooks/04-mcp-and-plugins.md) red lines).
  如果能打开 → 就是配置文件问题。从备份逐段重建，每改一处校验 TOML（红线见 playbooks/04）。
- If it still won't open: rename `auth.json` → `auth.json.bak`, relaunch, and sign in again to refresh the session.
  仍打不开：改名 `auth.json` → `auth.json.bak`，重启后重新登录刷新会话。
- If still stuck: check UAC level (must not be "Never notify"), confirm `Get-Service Appinfo` is Running, and read `%USERPROFILE%\.codex\.sandbox\sandbox.log` for error codes 740 / 1385 / 401.
  仍然卡住：检查 UAC 级别（不能是「从不通知」）、确认 `Get-Service Appinfo` 处于 Running、查看 `%USERPROFILE%\.codex\.sandbox\sandbox.log` 中的错误码 740 / 1385 / 401。

### Prevention / 预防

- Never edit config.toml by fixed line numbers; comment whole sections at table-header boundaries only. 不要用固定行号改 config.toml；只能按表头边界整段注释。
- Keep the file UTF-8; avoid mixed encodings and mojibake path keys. 保持 UTF-8 编码，避免混合编码和乱码路径键。
- Validate TOML after every edit (Python 3.11+ `tomllib`). 每次修改后用 TOML 解析器校验。
- Back up before every change. Backups contain API tokens — never commit them. 每次修改前备份。备份含 API 令牌，严禁入仓。
