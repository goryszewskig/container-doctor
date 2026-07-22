# Container Doctor

An AI agent that watches your Docker containers in real-time, diagnoses errors with Claude, and auto-fixes (restarts) them when safe.

Based on the freeCodeCamp article: [Docker Container Doctor: How I Built an AI Agent That Monitors and Fixes My Containers](https://www.freecodecamp.org/news/docker-container-doctor-how-i-built-an-ai-agent-that-monitors-and-fixes-my-containers/) by Balajee Asish Brahmandam.

## How it works

1. Runs in its own container with the Docker socket mounted
2. Every `CHECK_INTERVAL` seconds, pulls the last `LOG_LINES` lines from each target container
3. Scans logs for error patterns (`error`, `traceback`, `fatal`, `oomkiller`, ...)
4. Sends matching logs to Claude with a structured JSON prompt
5. Claude returns: root cause, severity, suggested fix, and whether auto-restart is safe
6. On **high** severity + `auto_restart_safe`, restarts the container (max 3 restarts/hour/container)
7. Sends a Slack notification with the full diagnosis
8. Exposes `/health` and `/history` endpoints on port 8080

Built-in cost protection: error deduplication (hash of recent log tail) + a cap of `MAX_DIAGNOSES_PER_HOUR` Claude calls.

## Setup

```bash
cp .env.example .env
# fill in ANTHROPIC_API_KEY and (optionally) SLACK_WEBHOOK_URL
docker compose up -d --build
```

## Config (`.env`)

| Variable | Default | Description |
|---|---|---|
| `TARGET_CONTAINERS` | — | Comma-separated container names to monitor |
| `CHECK_INTERVAL` | 10 | Seconds between checks (30-60 recommended for prod) |
| `LOG_LINES` | 50 | Log tail size sent for analysis |
| `AUTO_FIX` | true | Global kill-switch for auto-restarts |
| `MAX_DIAGNOSES_PER_HOUR` | 20 | Claude API rate limit |
| `SLACK_WEBHOOK_URL` | — | Optional Slack incoming webhook |

## Endpoints

```bash
curl http://localhost:8080/health   # doctor status, fixes applied, rate limit remaining
curl http://localhost:8080/history  # last 50 diagnoses
```

## Run locally (without Docker)

```bash
pip install -r requirements.txt
python container_doctor.py
```

Requires access to a Docker daemon (`/var/run/docker.sock` or `DOCKER_HOST`).

## Security notes

- Mounting `/var/run/docker.sock` grants root-equivalent access to the Docker daemon — consider [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) to restrict API calls.
- Never bake `.env` into the image; pass secrets via compose environment.
- The agent is outbound-only: it reads logs, restarts containers, calls Claude and Slack. It never execs into containers or accepts external commands.

## Git tips: shipping a hotfix with WIP changes

When you have lots of uncommitted work and a critical issue appears:

```bash
# 1. Save your WIP aside (-u includes untracked files, -m labels the stash)
git stash push -u -m "wip: feature X in progress"

# 2. Working tree is now clean — create a hotfix branch
git checkout -b hotfix/critical-issue
# ...make the fix...
git add <fixed-files>
git commit -m "fix: critical issue"
git push -u origin hotfix/critical-issue

# 3. Go back and restore your work
git checkout <your-feature-branch>
git stash pop
```

`git stash push -u -m "msg"` breakdown: `stash push` stores staged + unstaged changes and reverts files to the last commit; `-u` also stashes new untracked files; `-m "msg"` labels it so it's identifiable in `git stash list`. Restore later with `git stash pop`.

Alternatives:
- **Fix in different files than your WIP**: just `git add` only the fixed files and commit — uncommitted WIP is never pushed. Use `git add -p` to stage selected hunks within one file.
- **`git worktree`**: `git worktree add ../hotfix-folder -b hotfix/x` gives you a separate clean directory for the fix without touching your WIP.

Always verify with `git status` and `git diff --staged` before committing.
