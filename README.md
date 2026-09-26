# 素材库MCP

远端 Teedy 素材检索、预览和下载 MCP。MCP 工具可以运行在 WorkBuddy 或 Codex 本机，使用用户配置的 Teedy Reader 或 ADMIN 账号通过 HTTPS 访问素材库。MCP 工具本身没有上传、修改或删除文档的操作。

## 安装

把公开仓库链接发给 WorkBuddy 或 Codex：

```text
请帮我安装这个 MCP：https://github.com/akechi0819-lgtm/material-library-mcp 。先阅读项目使用说明，再引导我完成后续配置。
```

Agent 读取 [`docs/mcp_employee_setup.md`](docs/mcp_employee_setup.md)，然后在对话中询问 Teedy HTTPS 地址、用户名和密码，并通过安装器完成本机运行环境、登录验证和客户端注册。密码不进入命令行参数或 GitHub 文件；凭据写入本机权限受限的配置文件。Agent 不得在回复中复述密码。

对话中提交的密码会留在该 Agent 的会话记录中。Teedy ADMIN 账号也可登录 Teedy 网页/API 并执行管理操作；MCP 的只读约束只作用于 MCP 工具调用。

## 使用

在一个新对话中明确写 `$素材库MCP`，例如：

```text
$素材库MCP 找几条适合家长了解 KET 考试时间的小红书素材
```

工具会列出标签、检索素材并提供预览、单文件下载链接和 ZIP 链接。保存素材到本机时，Agent 调用 `download_file`。浏览器打开 Teedy 链接前需要登录同一个 Teedy 服务器。
