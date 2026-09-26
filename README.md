# 素材库MCP

远端 Teedy 素材检索、预览和下载 MCP。MCP 工具可以运行在 WorkBuddy 或 Codex 本机，使用用户配置的 Teedy Reader 或 ADMIN 账号通过 HTTPS 访问素材库。MCP 工具本身没有上传、修改或删除文档的操作。

## 安装

把公开仓库链接交给 WorkBuddy 或 Codex，并让它按安装说明引导：

```text
请帮我安装这个 MCP：https://github.com/akechi0819-lgtm/material-library-mcp 。先阅读项目使用说明，再引导我完成配置。
```

Agent 读取 [`docs/mcp_employee_setup.md`](docs/mcp_employee_setup.md)，准备依赖与客户端配置，并引导用户在交互终端运行安装器。Teedy 地址、用户名可在终端输入；密码使用隐藏提示，不在聊天中提交，也不放入命令行参数。凭据保存在本机权限受限文件。

Reader 和 ADMIN 均受支持。MCP 工具只提供读取和下载；ADMIN 账号在 Teedy 网页/API 中的权限仍由 Teedy 自身控制。

## 使用

在一个新对话中明确写 `$素材库MCP`，例如：

```text
$素材库MCP 找几条适合家长了解 KET 考试时间的小红书素材
```

工具会列出标签、检索素材并提供预览、单文件下载链接和 ZIP 链接。保存素材到本机时，Agent 调用 `download_file`。浏览器打开 Teedy 链接前需要登录同一个 Teedy 服务器。
