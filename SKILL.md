---
name: docker-web-deploy
description: 在 Windows/macOS/Linux 上检测并配置 Docker/WSL 环境，安全解压任意网站项目压缩包，自动解析 docker-compose.yml，构建启动并验证网站可访问。只要用户提到"把这个网站/项目跑起来""Docker 起不来""Docker Desktop is unable to start""WSL 未安装 / wsl --install 报 403""端口 8080 被占用""把压缩包部署到另一台电脑""docker compose up 报错"，就必须使用本 Skill。适用于任何 zip + Dockerfile/docker-compose 的网站项目，不限于某一个具体项目；内置 GPR 地图作业预设。
---

# Docker 网站部署助手

把「体检 → 修复环境 → 解压 → 识别项目 → 构建 → 启动 → 验证」做成一条可重复的路径。
适用于任何带 `docker-compose.yml`（或 `Dockerfile`）的网站项目；不同设备真正有差异的只有 Docker/WSL 的安装方式，按操作系统分流。

## 核心原则

- **先体检，再动手。** 不要凭猜测让用户重装 Docker。
- **安装软件、改系统设置、需要管理员权限的操作，先说明并等待用户同意。** 用户可能是零基础，命令一条一条给。
- **绝不覆盖用户已有目录。** 解压脚本会自动生成不冲突的新目录。
- **不修改项目源码。** 部署只需要解压、构建、启动。
- **不主动把服务暴露到公网**（除非用户明确要求，并提醒无鉴权）。
- 用中文回复（除非用户使用其他语言）；非技术用户给「点哪里、输入什么」级别的步骤。

## 第 0 步：确认目标

先判断用户要做什么：

1. **完整部署**：给出 zip 路径或项目目录。
2. **只修环境**：Docker 起不来、WSL 没装、端口冲突。
3. **只验证**：项目已在运行，确认是否正常。

没给路径就先问，不要假设文件在固定位置。

## 第 1 步：环境体检

```bash
python <skill_dir>/scripts/deploy.py check
```

Windows 上 `python` 不可用时试 `py -3`；都没有则按 `references/` 里的命令手工检查。

输出为 JSON，重点字段：

| 字段 | 含义 | 异常时 |
| --- | --- | --- |
| `docker_cli` | 是否找到 docker | 安装 Docker（见对应系统 reference） |
| `compose.ok` | compose 是否可用 | 安装插件或升级 Docker Desktop |
| `daemon.running` | 引擎是否运行 | 启动 Docker Desktop / docker 服务 |
| `daemon.error` | 引擎报错原文 | 按 `references/troubleshooting.md` 匹配 |
| `wsl.available`（Windows） | WSL 是否启用 | `references/windows.md` |
| `virtualization` | CPU 虚拟化 | 引导进 BIOS 开启 VT-x / AMD-V |
| `port_8080.in_use` | 8080 是否被占用 | 看 `owner`，征得同意后换端口或停进程 |
| `disk_free_gb` | 磁盘剩余 | < 3 GB 提醒清理 |

把结果用一两句话讲给用户，不要直接甩 JSON。

## 第 2 步：修复环境

按系统读对应文件，只读需要的部分：

- Windows → `references/windows.md`
- macOS → `references/macos.md`
- Linux → `references/linux.md`
- 任何报错 → `references/troubleshooting.md`

Windows 最常见链路：**Docker 起不来 → WSL 没装 → `wsl --install` 报 403 → DISM + 离线 MSI**。
完整命令在 `references/windows.md` 的「WSL 未安装 / 403」。

修完必须重新体检。

## 第 3 步：解压或定位项目

zip：

```bash
python <skill_dir>/scripts/deploy.py extract "<zip路径>"
```

脚本会解压到 zip 同目录的 `<zip名>-extracted`（已存在则自动加 `-2`），防御 zip-slip，并自动定位项目根。

已有目录：

```bash
python <skill_dir>/scripts/deploy.py find-project "<目录>"
```

返回的 `project_root` 就是后续工作目录。

## 第 4 步：识别项目

```bash
python <skill_dir>/scripts/deploy.py inspect "<project_root>"
```

输出包含：

- `services`：服务名、镜像、是否使用 build
- `host_port`：宿主机端口（用于拼访问地址）
- `compose_file`：实际使用的 compose 文件

如果 `host_port` 为空，说明 compose 没写端口映射，需要用户补充或查看 Dockerfile 的 EXPOSE。

## 第 5 步：构建并启动

在 `project_root` 下：

```bash
docker compose up -d --build
```

- 首次会拉取基础镜像，2–5 分钟，提前告诉用户「第一次慢是正常的」。
- 之后改代码/数据也要带 `--build`，否则复用旧镜像。
- Linux 报 `permission denied` → `references/linux.md` 的 docker 用户组。
- 端口被占用且用户同意换端口：把 compose 里的 `"8080:80"` 改成 `"8081:80"`，重新 `up -d`。

## 第 6 步：验证

```bash
python <skill_dir>/scripts/deploy.py verify --url "http://localhost:<host_port>"
```

验收标准：

1. `docker ps` 里有对应容器，状态 `Up`，端口映射正确
2. `verify` 的 `index.ok` 为 true
3. 浏览器能看到页面

需要额外健康检查时加 `--path`（可重复）：

```bash
python <skill_dir>/scripts/deploy.py verify \
  --url http://localhost:8080 \
  --path /api/health \
  --path /data/app.json
```

### 内置预设：GPR 地图作业

当项目包含 `data/gpr_monthly.json` 与 `data/world.geojson` 时，追加：

```bash
python <skill_dir>/scripts/deploy.py verify \
  --url http://localhost:8080 \
  --path /data/gpr_monthly.json \
  --path /data/world.geojson
```

预期：三个端点均 200，`gpr_monthly.json` 的 `json_keys` 含 `months`、`countries`。

失败时：

```bash
docker compose logs --tail=50
```

## 第 7 步：交付说明

- 访问地址：`http://localhost:<host_port>`
- 停止：`docker compose down`
- 再次启动：`docker compose up -d`（改代码用 `--build`）
- 项目目录：`<project_root>`

手机/平板访问：同一 WiFi，用电脑局域网 IP：

- Windows：`ipconfig` 看 WLAN 的 IPv4
- macOS：`ipconfig getifaddr en0`
- Linux：`hostname -I`

访问 `http://<IP>:<host_port>`，打不开多半是防火墙没放行。

公网临时演示（非必要）：`cloudflared tunnel --url http://localhost:<port>` 或 `ngrok http <port>`，提醒无鉴权、用完即关。

## 失败处理

读 `references/troubleshooting.md`，按报错原文匹配。高频五类：

| 报错关键词 | 根因 | 去处 |
| --- | --- | --- |
| `Docker Desktop is unable to start` | WSL 未装 / 引擎未启动 | windows.md |
| `wsl --install` 报 403 | 商店或更新被拦 | windows.md 离线安装 |
| `port is already allocated` | 端口被占用 | 第 5 步 |
| `permission denied ... docker.sock` | 用户不在 docker 组 | linux.md |
| 页面白屏 / `file://` | 没用 HTTP 访问 | troubleshooting.md |

## 非 Claude 工具中使用

本仓库同时提供通用入口，不依赖 Claude：

- **Trae**：打开本仓库，`.trae/rules/project_rules.md` 会被读取；或直接读 `AGENTS.md`
- **Cursor**：`.cursor/rules/docker-web-deploy.mdc`
- **GitHub Copilot**：`.github/copilot-instructions.md`
- **Codex / 其他 Agent**：`AGENTS.md`
- **WorkBuddy / 纯聊天工具**：把 `PROMPT.md` 的内容粘贴进去，或让它读 `AGENTS.md`
- **任何终端**：直接运行 `scripts/deploy.py`

各工具的加载方式见 `references/tools.md`。

## 完成后的汇报格式

```
环境：Windows 11 / Docker 29.9.1 / Compose v5.6.0
项目：E:\...\project
服务：web（build）/ 宿主机端口 8080
容器：web  Up 2 minutes  0.0.0.0:8080->80/tcp
验证：首页 200 / 健康检查 200
访问：http://localhost:8080
```

只报事实，不要把「应该可以」当成「已经可用」。
