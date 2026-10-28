# 各 AI 工具的加载方式

本仓库不依赖某一个工具。核心是两块：

1. **流程说明**：`SKILL.md`（Claude）、`AGENTS.md`（通用）、`PROMPT.md`（纯对话）
2. **可执行脚本**：`scripts/deploy.py`（任何终端）

## Claude Code

把整个仓库复制到 skills 目录：

```bash
# macOS / Linux
cp -r docker-web-deploy-skill ~/.claude/skills/docker-web-deploy

# Windows (Git Bash)
cp -r docker-web-deploy-skill "$USERPROFILE/.claude/skills/docker-web-deploy"
```

或导入打包好的 `docker-web-deploy.skill`。

安装后可以直接说：
- "把 D 盘那个网站压缩包跑起来"
- "Docker 起不来，帮我看看"

## Trae

Trae 会读取项目里的规则文件。两种方式：

- 用 Trae 打开本仓库，`.trae/rules/project_rules.md` 会自动生效
- 或把 `AGENTS.md` 的内容粘贴到 Trae 的 Rules / 自定义指令中

然后在 Trae 的终端里执行 `python scripts/deploy.py ...`。

## WorkBuddy

WorkBuddy 若支持自定义指令/知识库：

1. 把 `PROMPT.md` 全文粘贴到自定义指令
2. 或把 `AGENTS.md` 加入项目知识库
3. 确保它能执行终端命令（脚本需要 Python 3）

如果它不能执行命令，就把 `PROMPT.md` 当成人工操作清单，自己按步骤复制命令运行。

## Cursor

仓库内的 `.cursor/rules/docker-web-deploy.mdc` 会被自动加载。
也可以用 `@AGENTS.md` 引用。

## GitHub Copilot

`.github/copilot-instructions.md` 会自动作为仓库指令。

## Codex / 其他 Agent

读取 `AGENTS.md` 即可。大多数现代编码 Agent 都支持这个约定。

## 纯聊天工具（ChatGPT / Kimi / 豆包等）

把 `PROMPT.md` 整段粘贴，并把压缩包路径告诉它。
它无法直接执行命令时，让它逐步给出命令，你复制到终端运行。

## 通用兜底

不用任何 AI 工具，直接看：

```bash
python scripts/deploy.py check
python scripts/deploy.py extract "<zip>"
python scripts/deploy.py inspect "<project_root>"
cd "<project_root>" && docker compose up -d --build
python scripts/deploy.py verify --url http://localhost:8080
```

每一步的输出都是 JSON，按字段判断即可。
