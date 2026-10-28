# Docker Web Deploy

部署任何 Docker 网站时，阅读并遵循仓库根目录的 `AGENTS.md`。

核心要求：

1. 先运行 `python scripts/deploy.py check` 体检，再决定动作。
2. 安装软件、修改系统设置、停止进程前先征得用户同意。
3. 用 `python scripts/deploy.py extract "<zip>"` 解压，不要覆盖已有目录。
4. 用 `python scripts/deploy.py inspect "<project_root>"` 获取服务名与宿主机端口。
5. 启动命令：`docker compose up -d --build`。
6. 用 `python scripts/deploy.py verify --url "http://localhost:<port>"` 验证。
7. 失败时阅读 `references/troubleshooting.md`。
8. 不要修改项目源码，不要主动暴露公网。
