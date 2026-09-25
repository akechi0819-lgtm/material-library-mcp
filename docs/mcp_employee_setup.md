# 素材库MCP 安装与使用

员工电脑运行本机 stdio MCP，MCP 通过 HTTPS 访问远端 Teedy。GitHub 仓库提供安装器和代码；每位员工的 Teedy 凭据只保存在自己的用户配置目录，不进入仓库、GitHub 或代理对话。

## 管理员准备

Teedy v1.10/v1.11 的 `PUT /api/user` 创建接口要求管理员权限，没有公开自助注册或邀请码流程。游客登录是单独的管理员开关，不是注册入口；管理员应关闭游客登录，并通过 Teedy 创建员工个人账号、加入 `readers` 组。

给素材与标签授予 `readers` 组 `READ` 权限。Teedy ACL 只有 `READ` 和 `WRITE`；`READ` 已支持预览和下载。上传中的素材会在 `readers` 组存在时获得组级 `READ` ACL。现有素材可由管理员运行：

```bash
.venv/bin/python scripts/provision_teedy_readers.py --base-url https://<teedy-host>
```

该脚本检查所有现有素材和标签，不创建员工账号。员工账号必须是非管理员；普通 Teedy 用户仍可以通过 Teedy 自身界面创建自己的文档，但 MCP 工具不会提供写入操作。

## GitHub 链接安装

员工把仓库链接交给 Codex，并要求它按仓库 `AGENTS.md` 安装“素材库MCP”。可以直接发送：

```text
请从 <GitHub 仓库链接> 安装“素材库MCP”。先阅读仓库的 AGENTS.md 和 docs/mcp_employee_setup.md，然后在交互终端运行安装器。Teedy 地址、账号和密码由安装器在终端提示我输入；不要在聊天中索要、接收或复述密码。安装器完成 Teedy 验证并配置当前 MCP 客户端后告诉我结果。
```

Agent 克隆仓库后，在**交互终端**运行：

```bash
python3 scripts/install_material_mcp.py --client codex
```

安装器会创建本机运行环境，并提示输入远端 Teedy HTTPS 地址、员工用户名和密码。密码在终端输入时不回显；不要把密码发在聊天中。安装器会验证登录、确认账号不是管理员且属于 `readers` 组；如果仓库已有可读文件，还会检查预览数据接口。验证成功后，它会：

- 将 MCP 程序复制到用户数据目录，避免依赖临时工作区。
- 把 Teedy 凭据写入用户私有配置目录，并设置本机文件权限。
- 在 Codex 中注册名为 `material-library` 的 MCP，并安装触发技能。
- 提示开启一个新对话以加载技能和 MCP。

验证失败时，安装器不会启用这组凭据；提示管理员检查账号、`readers` 组成员关系和 Teedy 地址。

### WorkBuddy 或其他 MCP 客户端

安装器会更新 WorkBuddy 5.5.2 当前界面显示的用户级 `~/.workbuddy-ai/mcp.json`，保留其他 MCP 配置；完成后在 WorkBuddy 刷新 MCP 设置。指定 WorkBuddy 的命令是：

```bash
python3 scripts/install_material_mcp.py --client workbuddy
```

腾讯 WorkBuddy 文档也将此路径列为用户级 MCP 配置。[WorkBuddy MCP 文档](https://www.workbuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide)

其他 MCP 客户端可用下面的方式让安装器显示 `command`、`args` 和 `YUKI_TEEDY_CREDENTIALS_FILE`，再手动复制到客户端设置：

```bash
python3 scripts/install_material_mcp.py --client manual
```

客户端配置只包含程序路径和凭据文件路径，不包含密码。凭据文件默认放在 macOS 的 `~/Library/Application Support/material-library-mcp/`、Windows 的用户 `AppData`，或 Linux 的 XDG 用户配置目录。

## 使用与触发

在对话里明确写 `$素材库MCP`，例如：

```text
$素材库MCP 找几条适合家长了解 KET 考试时间的小红书素材
```

MCP 会先列标签，再按标签和关键词搜索；需要更多内容时查看素材详情。结果包括预览、单文件下载链接和 `zip_url`。需要保存到本机时调用 `download_file`。在浏览器打开链接前，先登录同一台远端 Teedy。未写 `$素材库MCP` 时不调用素材工具。

撤销员工权限时，在 Teedy 停用账号或将其移出 `readers` 组。员工账号验证完成后，管理员可停用旧共享 `mcpreader`；确认旧链接不再使用后，再撤销历史 `mcp-read` 匿名分享。

## Teedy 实现依据

Teedy v1.10/v1.11 的用户创建接口要求 `ADMIN`；游客登录由另一个管理员接口控制；ACL 只有 `READ` 和 `WRITE`，文件数据和 ZIP 下载接口都检查 `READ`。[Teedy 用户接口](https://github.com/sismics/docs/blob/v1.10/docs-web/src/main/java/com/sismics/docs/rest/resource/UserResource.java)、[游客登录设置](https://github.com/sismics/docs/blob/v1.10/docs-web/src/main/java/com/sismics/docs/rest/resource/AppResource.java)、[权限枚举](https://github.com/sismics/docs/blob/v1.10/docs-core/src/main/java/com/sismics/docs/core/constant/PermType.java)、[文件与 ZIP 接口](https://github.com/sismics/docs/blob/v1.10/docs-web/src/main/java/com/sismics/docs/rest/resource/FileResource.java)。
