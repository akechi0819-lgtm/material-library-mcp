# 素材库MCP

远端 Teedy 素材检索 MCP。员工在自己的 Codex 或 WorkBuddy 安装本组件，使用个人 Teedy 账号搜索、预览和下载有权限的素材。

## 安装

从 GitHub 克隆后，在交互终端运行：

```bash
python3 scripts/install_material_mcp.py
```

安装器会让你选择 Codex、WorkBuddy 或其他 MCP 客户端，然后提示填写远端 Teedy HTTPS 地址和员工账号。密码通过隐藏输入收取，登录验证通过后凭据保存在本机用户配置目录；不要在聊天中发送密码。Teedy 管理员需预先创建非管理员账号并加入 `readers` 组。

详细流程见 [`docs/mcp_employee_setup.md`](docs/mcp_employee_setup.md)。

## 使用

```text
$素材库MCP 帮我找几条适合家长了解 KET 考试时间的小红书素材
```

工具会列出标签、搜索素材，返回预览和下载链接。浏览器打开直链前需要登录同一台 Teedy。需要将文件保存到本机时调用 `download_file`。
