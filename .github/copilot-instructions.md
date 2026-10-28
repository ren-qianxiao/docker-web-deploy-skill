# Docker Web Deploy

This repository is a deployment assistant for any Dockerized website.

When asked to run, deploy, or troubleshoot a Docker project:

- Read `AGENTS.md` and follow its workflow.
- Run `python scripts/deploy.py check` first.
- Ask before installing software, changing system settings, or stopping processes.
- Extract zips with `python scripts/deploy.py extract "<zip>"`; never overwrite existing directories.
- Inspect with `python scripts/deploy.py inspect "<project_root>"`.
- Start with `docker compose up -d --build`.
- Verify with `python scripts/deploy.py verify --url "http://localhost:<port>"`.
- Use `references/troubleshooting.md` for errors.

Do not modify the deployed project's source. Do not expose services publicly without explicit consent.
