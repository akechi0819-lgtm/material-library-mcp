# 素材库MCP

- 只在用户本轮明确写下 `$素材库MCP` 时调用检索工具。
- 登录兼容 Teedy Reader/`READ` 和 `ADMIN` 账号。
- MCP 工具只提供列标签、检索、查看详情、预览和下载；不要通过 MCP 上传、改标签或删除文档。
- 安装时在对话中询问远端 Teedy HTTPS 地址、用户名和密码；不要复述密码，也不要放进命令行参数。按 `docs/mcp_employee_setup.md` 使用安装器的 JSON 标准输入模式。
- 凭据只写入用户本机权限受限文件，不写入 GitHub、MCP 客户端 JSON 或 Agent 回复。
- 检索结果返回受 Teedy 登录和 ACL 保护的预览图、单文件下载链接和 `zip_url`，不返回匿名 share token。
- 不编造素材或生成新文案。
