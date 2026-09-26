# 素材库MCP 安装与使用

员工电脑运行本机 stdio MCP，MCP 通过 HTTPS 访问远端 Teedy。GitHub 仓库提供安装器和代码；登录兼容 Teedy Reader 和 ADMIN 账号。Teedy 密码只能由安装器在交互终端隐藏收取，凭据保存在本机用户配置目录，不进入 GitHub、命令行参数或 Agent 对话。

## 管理员准备

Teedy 的用户创建接口要求管理员权限，没有公开自助注册或邀请码流程。游客登录是单独的管理员开关，不是注册入口；管理员应关闭游客登录，并为员工创建个人账号。普通员工通常加入 `readers` 组；拥有 Teedy ADMIN 权限的账号也可用于 MCP。

`readers` 组可查看、预览和下载；`ingesters` 组用于素材入仓。管理员账户默认加入 `ingesters`，新员工账号同步到 `readers`。`readers` 账号的附件配额设为0，Teedy 会拒绝非空附件上传；`ingesters` 成员保留至少100GB附件配额。MCP 工具始终只提供检索、预览和下载，不会因为账号是 ADMIN 而增加写工具。

首次配置和新建员工账号后，由管理员运行下面的脚本。它会创建缺少的用户组，把现有普通账号加入 `readers`，同步入仓配额，并为所有现有标签和文档授予组级 `READ` ACL：

```bash
.venv/bin/python scripts/provision_teedy_readers.py --base-url https://<teedy-host>
```

该脚本不会创建员工账号。要授权员工入仓，在 Teedy 将该账号加入 `ingesters` 组后重跑脚本；撤销时将其移出 `ingesters` 并重跑。`ingesters` 只表示素材入仓权限，不授予 Teedy 用户、组或服务器设置的管理员权限。

## GitHub 链接安装

员工把仓库链接交给 WorkBuddy 或 Codex，并要求它按仓库 `AGENTS.md` 安装“素材库MCP”。可以直接发送：

```text
请从 <GitHub 仓库链接> 安装“素材库MCP”。先阅读仓库的 AGENTS.md 和 docs/mcp_employee_setup.md，再引导我完成终端安装和检索测试。
```

Agent 克隆仓库后，在交互终端运行：

```bash
python3 scripts/install_material_mcp.py --client workbuddy
```

Codex 安装时改为 `--client codex`。安装器提示输入远端 Teedy HTTPS 地址、用户名和密码。密码通过终端隐藏提示收取，不回显；不要在聊天中索要或发送密码。安装器验证登录及 Reader/ADMIN 权限；不会在安装阶段检索素材。验证成功后，它会：

- 将 MCP 程序复制到用户数据目录，避免依赖临时工作区。
- 把 Teedy 凭据写入用户私有配置目录，并设置本机文件权限。
- 在当前 WorkBuddy 或 Codex 用户配置中注册名为 `material-library` 的 MCP，并安装触发技能。
- WorkBuddy 首次连接时，提示在「专家·技能·连接器 → 连接器 → 自定义连接器」里信任并启用 `material-library`。
- 提示开启一个新对话，然后明确输入 `$素材库MCP`。

验证失败时，安装器不会启用这组凭据；提示检查账号权限和 Teedy 地址。

WorkBuddy 使用用户级 `~/.workbuddy-ai/.mcp.json`，技能安装到 `~/.workbuddy-ai/skills/material-library/`。Codex 使用用户级 MCP 配置和 `~/.agents/skills/material-library/`。

WorkBuddy 首次连接时会提示「首次连接此 MCP 服务需要您的信任确认」。在自定义连接器里点击「信任」，并确认 `material-library` 已启用、显示 4/4 个工具后，再新建对话测试。

## 使用与触发

在对话里明确写 `$素材库MCP`，例如：

```text
$素材库MCP 找几条适合家长了解 KET 考试时间的小红书素材
```

MCP 会先列标签，再按标签和关键词搜索；需要更多细节时查看素材详情。结果包括预览、单文件下载链接和 `zip_url`。需要保存到本机时调用 `download_file`。在浏览器打开链接前，先登录同一台远端 Teedy。未写 `$素材库MCP` 时不调用素材工具。

撤销 Reader 员工权限时，在 Teedy 停用账号或将其移出 `readers` 组。ADMIN 账号仍具有 Teedy 管理能力；MCP 工具只提供读取和下载操作。

## Teedy 实现依据

Teedy 用户创建接口要求 `ADMIN`；游客登录由另一个管理员接口控制；ACL 的 `READ` 权限允许下载。[Teedy 用户接口](https://github.com/sismics/docs/blob/v1.10/docs-web/src/main/java/com/sismics/docs/rest/resource/UserResource.java)、[游客登录设置](https://github.com/sismics/docs/blob/v1.10/docs-web/src/main/java/com/sismics/docs/rest/resource/AppResource.java)、[权限枚举](https://github.com/sismics/docs/blob/v1.10/docs-core/src/main/java/com/sismics/docs/core/constant/PermType.java)、[文件与 ZIP 接口](https://github.com/sismics/docs/blob/v1.10/docs-web/src/main/java/com/sismics/docs/rest/resource/FileResource.java)。
