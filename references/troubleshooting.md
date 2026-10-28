# 故障排查

先跑体检，再按报错原文匹配：

```bash
python <skill_dir>/scripts/gpr.py check
```

## 一、引擎起不来

### `Docker Desktop is unable to start`

Windows 上最常见的原因是 **WSL 未安装或未启用**。

1. 管理员 PowerShell：`wsl --status`
2. 若提示未安装 → 按 `windows.md` 的「WSL 未安装 / 403」处理
3. 若 WSL 正常 → 托盘右键 Quit Docker Desktop，等 10 秒重开
4. 仍不行 → Docker Desktop 右上角虫子图标 → Troubleshoot → Restart
5. 最后手段 → Reset to factory defaults（清空镜像，项目文件不受影响）

### `Cannot connect to the Docker daemon`

- Windows/macOS：Docker Desktop 没启动，打开并等 Engine running
- Linux：`sudo systemctl start docker`

### `WSL 2 installation is incomplete`

安装 WSL2 内核包：

```
https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
```

### `wsl --install` 报 403 / 已禁止

商店或更新服务被拦。用 DISM 开功能 + 离线 MSI，见 `windows.md`。

### 虚拟化未开启

任务管理器 → 性能 → CPU → 虚拟化。显示「已禁用」时进 BIOS 开 VT-x/SVM。

## 二、启动与构建

### `port is already allocated` / `address already in use`

查占用：

```bash
# Windows
netstat -ano | findstr :8080
# macOS
lsof -nP -iTCP:8080 -sTCP:LISTEN
# Linux
ss -ltnp | grep :8080
```

二选一（先征得用户同意）：
- 停掉占用进程
- 改 `docker-compose.yml` 的 `"8080:80"` 为 `"8081:80"`，重新 `up -d`

### `permission denied while trying to connect to the Docker daemon socket`

Linux：

```bash
sudo usermod -aG docker "$USER"
```

重新登录后生效。

### 构建时 `TLS handshake timeout` / `failed to solve`

网络问题。检查代理，重试；国内网络可在 Docker Desktop 设置里加镜像加速器。

### 中文或含空格路径构建异常

把项目复制到纯英文路径（如 `C:\gpr-map-system`）再构建。
路径含空格时命令里要加引号。

### `no such file or directory: docker-compose.yml`

终端不在项目根目录。先 `cd` 到包含 `docker-compose.yml` 的目录，或用：

```bash
python <skill_dir>/scripts/gpr.py find-project "<目录>"
```

## 三、运行时

### 容器启动后立刻退出

```bash
docker compose logs --tail=100
```

常见原因：
- 端口冲突
- 镜像构建失败（看构建日志）
- 磁盘满

### `docker compose up -d` 后页面还是旧内容

Compose 复用了旧镜像。用：

```bash
docker compose up -d --build
```

浏览器再按 `Ctrl + F5` 强制刷新。

### 页面白屏 / 一直转圈

1. `docker ps` 确认容器是 `Up`，端口映射含 `8080->80`
2. 确认访问的是 `http://localhost:8080`，**不是** `file://` 打开 html
3. `docker compose logs --tail=50`
4. 浏览器开发者工具 Console / Network 看哪个资源失败

### 数据接口 404

项目里必须有：

```
html/index.html
data/gpr_monthly.json
data/world.geojson
```

如果缺失，重新构建镜像（构建阶段会生成 JSON）：

```bash
docker compose up -d --build
```

### 页面能开但地图不显示

- 浏览器 Console 是否报错
- `world.geojson` 是否 200
- 是否拦截了本地脚本（广告拦截插件）

## 四、访问与网络

### 手机打不开 `localhost:8080`

`localhost` 指手机自己。改用电脑的局域网 IP：

```
http://<电脑IP>:8080
```

并确认：
- 手机与电脑同一 WiFi
- 防火墙放行 8080
- 路由器未开启 AP 隔离

### 外网无法访问

本项目默认只在本机/局域网可用。公网演示需要端口映射或隧道：

```bash
cloudflared tunnel --url http://localhost:8080
```

提醒用户：链接无鉴权，用完关闭。

## 五、清理与重来

```bash
docker compose down            # 停止并删除容器，镜像保留
docker compose down --rmi local   # 连镜像一起删
docker system prune -f         # 清理无用资源（谨慎，先征得同意）
```

重新部署：

```bash
docker compose up -d --build
```
