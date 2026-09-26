# 素材库MCP 安装与使用

员工电脑运行本机 stdio MCP，MCP 通过 HTTPS 访问远端 Teedy。GitHub 仓库提供安装器和代码；Teedy 地址、用户名和密码由 WorkBuddy/Codex Agent 在安装对话中询问。密码不进入命令行参数或 GitHub 文件，Agent 不得在回复中复述。凭据会写入本机用户配置目录；对话中输入的密码仍会留在该 Agent 的会话记录中。

## 管理员准备

Teedy 的用户创建接口要求管理员权限，没有公开自助注册或邀请码流程。游客登录是单独的管理员开关，不是注册入口；管理员应关闭游客登录，并通过 Teedy 创建员工个人账号。

MCP 登录兼容 `readers` 组中的 Reader 账号和 ADMIN 账号。`readers` 可查看、预览和下载；`ingesters` 可入仓。管理员账户默认加入 `ingesters`，新员工账号同步到 `readers`。`readers` 账号的附件配额设为0，Teedy 会拒绝非空附件上传；`ingesters` 成员保留至少100GB附件配额。MCP 只提供检索、详情、预览和下载工具，并在 HTTP 客户端中阻止写请求。使用 ADMIN 账号时，该限制只约束 MCP；账号本身仍可直接在 Teedy 网页/API 管理内容和权限。

首次配置和新建员工账号后，由管理员运行下面的脚本。它会创建缺少的用户组，把现有普通账号加入 `readers`，同步入仓配额，并为所有现有标签和文档授予组级 `READ` ACL：

```bash
.venv/bin/python scripts/provision_teedy_readers.py --base-url https://<teedy-host>
```

该脚本不会创建员工账号。要授权员工入仓，在 Teedy 将该账号加入 `ingesters` 组后重跑脚本；撤销时将其移出 `ingesters` 并重跑。`ingesters` 只表示素材入仓权限，不授予 Teedy 用户、组或服务器设置的管理员权限。MCP 工具仍只提供检索和下载操作。

## GitHub 链接安装

员工把仓库链接交给 WorkBuddy 或 Codex，并要求它按仓库 `AGENTS.md` 安装“素材库MCP”。可以直接发送：

```text
请从 <GitHub 仓库链接> 安装“素材库MCP”。先阅读仓库的 README 和 docs/mcp_employee_setup.md，再引导我完成配置和检索。
```

Agent 克隆仓库后，询问用户的远端 Teedy HTTPS 地址、用户名和密码，然后用 JSON 标准输入调用安装器：

```bash
python3 scripts/install_material_mcp.py --client workbuddy --credentials-json-stdin <<'TEEDY_CREDENTIALS'
{"base_url":"https://<teedy-host>","username":"<teedy-user>","password":"<teedy-password>"}
TEEDY_CREDENTIALS
```

Codex 安装时把 `--client workbuddy` 改为 `--client codex`。安装器不会从终端读取密码，也不会把密码放在进程参数中。

密码不得放进命令行参数或回复内容。安装器会验证登录及 ADMIN/READ 权限；不会在安装阶段检索素材。验证成功后，它会：

- 将 MCP 程序复制到用户数据目录，避免依赖临时工作区。
- 把 Teedy 凭据写入用户私有配置目录，并设置本机文件权限。
- 在当前 Codex 或 WorkBuddy 用户配置中注册名为 `material-library` 的 MCP，并把触发技能安装到对应客户端的用户技能目录。
- 提示开启一个新对话以加载技能和 MCP。

验证失败时，安装器不会启用这组凭据；提示检查账号、READ 权限和 Teedy 地址。

### WorkBuddy 或其他 MCP 客户端

安装器会更新 WorkBuddy 用户级 `~/.workbuddy-ai/mcp.json`，保留其他 MCP 配置，并安装触发技能到 `~/.workbuddy-ai/skills/material-library/`。按前面的 JSON 标准输入示例运行时，使用 `--client workbuddy`；完成后刷新 MCP 设置并开一个新对话。

腾讯 WorkBuddy 文档也将此路径列为用户级 MCP 配置。[WorkBuddy MCP 文档](https://www.workbuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide)

其他 MCP 客户端可用下面的方式让安装器显示 `command`、`args` 和 `YUKI_TEEDY_CREDENTIALS_FILE`，再手动复制到客户端设置：

```bash
python3 scripts/install_material_mcp.py --client manual --credentials-json-stdin <<'TEEDY_CREDENTIALS'
{"base_url":"https://<teedy-host>","username":"<teedy-user>","password":"<teedy-password>"}
TEEDY_CREDENTIALS
```

客户端配置只包含程序路径和凭据文件路径，不包含密码。凭据文件默认放在 macOS 的 `~/Library/Application Support/material-library-mcp/`、Windows 的用户 `AppData`，或 Linux 的 XDG 用户配置目录。

## 使用与触发

在对话里明确写 `$素材库MCP`，例如：

```text
$素材库MCP 找几条适合家长了解 KET 考试时间的小红书素材
```

MCP 会先列标签，再按标签和关键词搜索；需要更多内容时查看素材详情。结果包括预览、单文件下载链接和 `zip_url`。需要保存到本机时调用 `download_file`。在浏览器打开链接前，先登录同一台远端 Teedy。未写 `$素材库MCP` 时不调用素材工具。

撤销 Reader 员工权限时，在 Teedy 停用账号或将其移出 `readers` 组。ADMIN 账号的管理能力仍由 Teedy 自身账号和权限控制，不由 MCP 工具限制。

## Teedy 实现依据

Teedy 用户创建接口要求 `ADMIN`；游客登录由另一个管理员接口控制。文件下载检查文档 `READ` ACL，文件上传还会检查个人存储配额。[Teedy 用户接口](https://github.com/sismics/docs/blob/master/docs-web/src/main/java/com/sismics/docs/rest/resource/UserResource.java)、[用户配额校验](https://github.com/sismics/docs/blob/master/docs-core/src/main/java/com/sismics/docs/core/util/FileUtil.java)、[文件与 ZIP 接口](https://github.com/sismics/docs/blob/master/docs-web/src/main/java/com/sismics/docs/rest/resource/FileResource.java)。
