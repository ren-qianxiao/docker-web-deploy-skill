# macOS 部署指南

## 前置条件

| 项目 | 要求 |
| --- | --- |
| 系统 | macOS 12（Monterey）以上 |
| 芯片 | Intel 或 Apple Silicon 均可 |
| 磁盘 | 剩余 ≥ 3 GB |

## 1. 安装 Docker Desktop

下载地址：

```
https://www.docker.com/products/docker-desktop/
```

选择对应芯片：
- Apple Silicon（M 系列）→ **Apple Chip**
- Intel → **Intel Chip**

或用 Homebrew：

```bash
brew install --cask docker
```

安装后打开 Docker Desktop，等菜单栏鲸鱼图标稳定、状态显示 **Engine running**。

也可以使用 colima（轻量替代）：

```bash
brew install colima docker docker-compose
colima start
```

## 2. 验证

```bash
docker --version
docker compose version
docker info
```

`docker info` 能输出 Server Version 即可。

## 3. 启动项目

```bash
cd <项目根目录>
docker compose up -d --build
```

浏览器打开 `http://localhost:8080`。

## 4. 常见问题

| 现象 | 处理 |
| --- | --- |
| `Cannot connect to the Docker daemon` | Docker Desktop 没启动：`open -a Docker`，等 Engine running |
| `docker: command not found` | 没装 Docker，或 PATH 未包含 `/usr/local/bin`、`/opt/homebrew/bin` |
| 端口被占用 | `lsof -nP -iTCP:8080 -sTCP:LISTEN` 查进程；`kill <PID>` 或改端口 |
| Apple Silicon 上镜像架构不匹配 | 本项目使用官方多架构镜像（python/nginx），一般无需处理；如遇平台警告，加 `DOCKER_DEFAULT_PLATFORM=linux/arm64` |
| 权限问题 | Docker Desktop 不需要 sudo；若用过 colima，确认 `docker context ls` 指向 colima |

## 5. 手机 / 平板访问

手机与 Mac 连同一 WiFi：

```bash
ipconfig getifaddr en0
```

手机浏览器访问 `http://<该IP>:8080`。

## 6. 停止与重启

```bash
docker compose down        # 停止
docker compose up -d       # 再次启动
docker compose up -d --build   # 改了代码/数据后
```
