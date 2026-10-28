# Linux 部署指南

适用于 Ubuntu / Debian / Fedora / Arch 等主流发行版。

## 前置条件

- 内核支持 cgroups v2（现代发行版默认支持）
- 磁盘剩余 ≥ 3 GB
- 有 sudo 权限

## 1. 安装 Docker Engine 与 Compose 插件

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
```

如果发行版仓库版本过旧，使用 Docker 官方源：

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### Fedora

```bash
sudo dnf install -y docker docker-compose-plugin
```

### Arch

```bash
sudo pacman -S docker docker-compose
```

## 2. 启动服务并授权

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

**重新登录**（或 `newgrp docker`）后，普通用户才能直接使用 docker。

验证：

```bash
docker --version
docker compose version
docker info
```

## 3. 启动项目

```bash
cd <项目根目录>
docker compose up -d --build
```

访问 `http://localhost:8080`。

## 4. 防火墙

如果外部设备需要访问：

```bash
sudo ufw allow 8080/tcp      # Ubuntu/Debian
sudo firewall-cmd --add-port=8080/tcp --permanent && sudo firewall-cmd --reload   # Fedora/CentOS
```

云服务器还需在安全组放行 8080。

## 5. 常见问题

| 现象 | 处理 |
| --- | --- |
| `permission denied ... /var/run/docker.sock` | 没加入 docker 组：`sudo usermod -aG docker $USER`，重新登录 |
| `Cannot connect to the Docker daemon` | `sudo systemctl start docker` |
| 端口被占用 | `ss -ltnp \| grep :8080` 查进程；停掉或改端口 |
| SELinux 阻止挂载 | 本项目不挂载卷，一般不受影响 |
| 内存不足 | 构建阶段 pandas 需要约 500 MB；`free -h` 检查 |

## 6. 手机 / 平板访问

```bash
hostname -I
```

手机浏览器访问 `http://<该IP>:8080`。
