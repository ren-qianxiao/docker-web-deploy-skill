# Docker Web Deploy — 通用 Agent 指南

本文件面向所有 AI 编程助手（Trae、Cursor、WorkBuddy、Codex、Copilot 等）。
Claude Code 用户请优先使用 `SKILL.md`。

## 目标

把任意「zip + Dockerfile / docker-compose.yml」的网站项目，在一台陌生电脑上跑起来，
并验证可访问。不要假定项目名、端口或技术栈。

## 硬性规则

1. 先体检，再动手；不要一上来就让用户重装 Docker。
2. 安装软件、改系统设置、需要管理员权限、停止他人进程之前，先说明并等待同意。
3. 解压到新目录，绝不覆盖已有文件。
4. 不修改项目源码。
5. 不主动把服务暴露到公网。
6. 用用户的语言回复；非技术用户给「点哪里、输入什么」级别的步骤。

## 工作流

### 1. 确认目标

- 有 zip 路径 / 项目目录 → 完整部署
- 只报错 → 环境修复
- 已在运行 → 只验证

没有路径就先问。

### 2. 体检

```bash
python scripts/deploy.py check
```

Windows 无 `python` 时用 `py -3`。

判读：

- `docker_cli` 为空 → 安装 Docker
- `daemon.running` 为 false → 启动引擎（Windows/macOS 打开 Docker Desktop；Linux `sudo systemctl start docker`）
- Windows `wsl.available` 为 false → 安装 WSL2
- `virtualization` 为 false → BIOS 开 VT-x/AMD-V
- `port_8080.in_use` 为 true → 查占用，征得同意后换端口或停进程

### 3. 修复环境

按系统阅读：

- Windows → `references/windows.md`
- macOS → `references/macos.md`
- Linux → `references/linux.md`
- 报错 → `references/troubleshooting.md`

Windows 高频链路：Docker 起不来 → WSL 未装 → `wsl --install` 403 → DISM + 离线 MSI。

修完重新体检。

### 4. 解压 / 定位

```bash
python scripts/deploy.py extract "<zip>"
# 或
python scripts/deploy.py find-project "<dir>"
```

取返回的 `project_root`。

### 5. 识别项目

```bash
python scripts/deploy.py inspect "<project_root>"
```

读取 `services` 与 `host_port`。没有端口映射时询问用户或查看 Dockerfile 的 EXPOSE。

### 6. 启动

```bash
cd "<project_root>"
docker compose up -d --build
```

首次构建 2–5 分钟属正常。改代码后也要 `--build`。

### 7. 验证

```bash
python scripts/deploy.py verify --url "http://localhost:<host_port>"
```

需要时追加 `--path /api/health`、`--path /data/app.json`（可重复）。

**GPR 地图预设**：若存在 `data/gpr_monthly.json` 与 `data/world.geojson`，追加：

```bash
--path /data/gpr_monthly.json --path /data/world.geojson
```

### 8. 交付

- 地址：`http://localhost:<host_port>`
- 停止：`docker compose down`
- 重启：`docker compose up -d`
- 局域网：`http://<本机IP>:<host_port>`，手机与电脑同一 WiFi
- 公网演示：`cloudflared tunnel --url http://localhost:<port>`（提醒无鉴权）

## 失败处理

| 报错 | 处理 |
| --- | --- |
| `Docker Desktop is unable to start` | 查 WSL；Quit 后重开；Troubleshoot → Restart |
| `wsl --install` 403 / 已禁止 | DISM 开功能 + 离线 WSL2 MSI |
| `port is already allocated` | 查 PID，停进程或改端口 |
| `permission denied docker.sock` | `sudo usermod -aG docker $USER`，重新登录 |
| 页面白屏 | 确认用 http 访问；看 `docker compose logs` |
| 改了代码没变化 | `docker compose up -d --build` + 浏览器强刷 |

## 汇报格式

```
环境：<OS> / Docker <版本> / Compose <版本>
项目：<project_root>
服务：<service> / 端口 <host_port>
验证：首页 200 / 附加路径 200
访问：http://localhost:<host_port>
```

只报事实；未验证通过不要写「应该可用」。
