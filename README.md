# Docker Web Deploy

跨平台的 Docker 网站部署助手：**体检 → 修复环境 → 解压 → 识别项目 → 构建 → 启动 → 验证**。

不绑定某一个 AI 工具，也不绑定某一个项目。任何「zip + Dockerfile / docker-compose.yml」的网站都能用。

> A tool-agnostic deployment assistant for any Dockerized website.
> Works with Claude Code, Trae, Cursor, WorkBuddy, Codex, Copilot, or a plain terminal.

## 解决什么问题

- 别人的电脑没有 Docker / WSL，不知道从哪开始
- 报错看不懂：`Docker Desktop is unable to start`、`wsl --install` 403、`port is already allocated`
- 项目换了名字、端口、服务名，固定脚本就失效
- 每次交付都要重新讲一遍步骤

## 能做什么

| 能力 | 说明 |
| --- | --- |
| 环境体检 | Docker / Compose / 引擎 / WSL / 虚拟化 / 端口 / 磁盘 |
| 环境修复 | Windows WSL2（含 403 离线方案）、macOS、Linux |
| 安全解压 | 防 zip-slip，不覆盖已有目录，自动定位项目根 |
| 项目识别 | 解析 compose 的服务名、宿主机端口、build 配置 |
| 构建启动 | `docker compose up -d --build` |
| 访问验证 | 首页 + 任意附加路径（`--path` 可重复） |
| 排错 | 按报错原文匹配常见故障 |
| 项目预设 | 内置 GPR 地图作业（额外校验数据接口） |

## 安装

### Claude Code

```bash
cp -r docker-web-deploy-skill ~/.claude/skills/docker-web-deploy
```

或导入 `docker-web-deploy.skill`。

### Trae / Cursor / Copilot / Codex

打开本仓库即可：`.trae/rules/`、`.cursor/rules/`、`.github/copilot-instructions.md`、`AGENTS.md` 都是现成的。

### WorkBuddy / 纯聊天工具

把 `PROMPT.md` 粘贴到自定义指令，或让 AI 读取 `AGENTS.md`。

### 不用 AI

```bash
python scripts/deploy.py check
python scripts/deploy.py extract "路径/项目.zip"
python scripts/deploy.py inspect "<project_root>"
cd "<project_root>" && docker compose up -d --build
python scripts/deploy.py verify --url http://localhost:8080
```

## 使用示例

对 AI 说：

- "把我 D 盘这个网站压缩包部署到这台电脑"
- "Docker 起不来，提示 Docker Desktop is unable to start"
- "wsl --install 报 403"
- "项目跑起来了，帮我确认 8080 是否正常"
- "把这个项目部署到朋友的 Mac 上"

## 支持的环境

| 系统 | 最低版本 | Docker 形态 |
| --- | --- | --- |
| Windows | Win10 22H2 (19045) / Win11 | Docker Desktop + WSL2 |
| macOS | 12 Monterey | Docker Desktop 或 colima |
| Linux | 主流发行版 | Docker Engine + compose 插件 |

## 目录结构

```
docker-web-deploy-skill/
├── SKILL.md                 # Claude Code 技能入口
├── AGENTS.md                # 通用 Agent 指南
├── PROMPT.md                # 可直接粘贴的提示词
├── scripts/deploy.py        # check / extract / find-project / inspect / verify
├── references/
│   ├── windows.md
│   ├── macos.md
│   ├── linux.md
│   ├── troubleshooting.md
│   └── tools.md             # 各 AI 工具的加载方式
├── .trae/rules/
├── .cursor/rules/
├── .github/copilot-instructions.md
├── README.md
└── LICENSE
```

## GPR 预设

项目包含 `data/gpr_monthly.json` 与 `data/world.geojson` 时：

```bash
python scripts/deploy.py verify \
  --url http://localhost:8080 \
  --path /data/gpr_monthly.json \
  --path /data/world.geojson
```

## 安全边界

- 只读体检，不改系统
- 解压到新目录，不覆盖文件
- 安装软件 / 改设置 / 停进程前先征得同意
- 不自动暴露公网
- 不修改项目源码

## License

MIT
