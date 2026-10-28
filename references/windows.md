# Windows 部署指南

## 前置条件

| 项目 | 要求 |
| --- | --- |
| 系统 | Windows 10 22H2（19045）以上，或 Windows 11，64 位 |
| CPU | 已开启虚拟化（BIOS 中 VT-x / AMD-V） |
| 内存 | ≥ 4 GB（建议 8 GB） |
| 磁盘 | 剩余 ≥ 3 GB |
| 权限 | 安装 Docker Desktop 需要管理员 |

## 1. 先确认系统与虚拟化

- 版本：`Win + R` → `winver`
- 虚拟化：`Ctrl + Shift + Esc` → 性能 → CPU → 右下角「虚拟化」

如果虚拟化显示「已禁用」，重启进 BIOS：
- Intel：开启 **VT-x / Intel Virtualization Technology**
- AMD：开启 **SVM Mode**

## 2. 安装 Docker Desktop

下载地址：

```
https://www.docker.com/products/docker-desktop/
```

直链（AMD64）：

```
https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
```

也可以用 winget：

```powershell
winget install -e --id Docker.DockerDesktop
```

安装时保持勾选 **Use WSL 2 instead of Hyper-V**。
装完重启电脑，打开 Docker Desktop，等左下角变成绿色 **Engine running**。

## 3. 安装 WSL 2

Docker Desktop 在 Windows 上依赖 WSL 2。

### 3.1 正常情况

管理员 PowerShell：

```powershell
wsl --install
```

然后**重启电脑**。

### 3.2 `wsl --install` 报 403 / 已禁止

说明微软商店或更新服务被网络/策略拦截，改用离线方式。

**第一步：用 DISM 开启功能（管理员 PowerShell）**

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

看到「操作成功完成」后**重启电脑**。

**第二步：安装 WSL2 内核（重启后）**

下载并双击安装：

```
https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
```

如果该地址被拦，从 GitHub 下载文件名形如 `wsl.2.x.x.x.x64.msi` 的安装包：

```
https://github.com/microsoft/WSL/releases
```

**第三步：设为默认版本**

```powershell
wsl --set-default-version 2
wsl --status
```

正常显示默认版本 2。此时没有 Linux 发行版是正常的，Docker 会自己创建 `docker-desktop`。

### 3.3 功能状态检查

```powershell
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux, VirtualMachinePlatform | Select-Object FeatureName, State
```

- `Enabled`：功能已开
- `EnablePending`：重启一次
- `Disabled` 且 DISM 报错：可能被组策略禁用，需要管理员或安全软件放行

## 4. 启动并验证

```powershell
docker --version
docker compose version
docker info
docker ps
```

能输出 `Server Version` 即引擎正常。

然后进入项目目录：

```powershell
cd <项目根目录>
docker compose up -d --build
```

浏览器访问 `http://localhost:8080`。

## 5. 手机 / 平板访问

手机与电脑连同一 WiFi，手机浏览器访问：

```
http://<电脑局域网IP>:8080
```

查 IP：`ipconfig` →「无线局域网适配器 WLAN」→ IPv4 地址。

如果打不开，管理员 PowerShell 放行 8080：

```powershell
New-NetFirewallRule -DisplayName "GPR-8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow -Profile Private
```

校园网/公司网可能开启 AP 隔离，此时改用手机热点。

## 6. 常见问题

| 现象 | 处理 |
| --- | --- |
| `docker` 不是内部或外部命令 | Docker Desktop 没启动；或重开终端。仍不行时用完整路径 `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin\docker.exe` |
| `Docker Desktop is unable to start` | 见 `troubleshooting.md`，多数是 WSL 未装 |
| 安装时 UAC 取消 | 重新运行安装包，右键「以管理员身份运行」 |
| 端口 8080 被占用 | `netstat -ano \| findstr :8080` 查 PID，再决定停进程或改端口 |
| 构建时拉镜像超时 | 检查网络/代理，重试；必要时配置 Docker Desktop 的镜像加速 |
| 中文路径构建失败 | 把项目复制到纯英文路径（如 `C:\gpr-map-system`）再构建 |
