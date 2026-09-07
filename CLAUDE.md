# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TransitionCompassViz (speed-to-zero) is an interactive climate pathway visualization platform for modeling and simulating policy impacts on emissions, energy, and environmental indicators across multiple sectors (Buildings, Transport, Energy, Agriculture, Forestry).

- **Production**: https://transition-compass.epfl.ch/
- **Development**: https://transition-compass-dev.epfl.ch/

## Commands

### Development (from root)

```bash
make install           # Install all dependencies (backend + frontend) and git hooks
make run               # Run both backend (port 8000) and frontend (port 9000) - RECOMMENDED
make run-backend       # Backend only (cache disabled)
make run-frontend      # Frontend only
make lint              # Check code quality (ESLint, Prettier, Python ruff)
make format            # Auto-fix formatting issues
```

### Backend (from /backend)

```bash
make install           # Create venv and install dependencies (uses uv if available, pip fallback)
make run               # Start uvicorn server
make lint              # Run ruff check
make format            # Run ruff format
make test              # Run pytest
```

### Frontend (from /frontend)

```bash
npm run dev            # Start Quasar dev server
npm run build          # Production build
npm run lint           # ESLint check
npm run format         # Prettier format
```

## Architecture

### Tech Stack

- **Frontend**: Vue.js 3 (Composition API) + TypeScript + Quasar 2 + Vite
- **Backend**: FastAPI + Python 3.12 + Pandas/NumPy + Pydantic
- **State**: Pinia store (`leversStore.ts`)
- **Charts**: ECharts via vue-echarts
- **i18n**: vue-i18n (German, English, French)

### Key Data Flow

```
Vue Components → Pinia Store (leversStore) → modelService API client → Backend /api/v1/...
```

### Frontend Structure

- `src/stores/leversStore.ts` - Central state: levers, modelResults, pathways, autoRun
- `src/services/modelService.ts` - API client (runModel, getLeverData, getDatamatrix)
- `src/config/levers.ts` - Lever definitions
- `src/config/sectors.ts` - Sector configuration
- `src/pages/sectors/` - Sector tab components (OverallTab, BuildingsTab, etc.)
- `src/components/graphs/` - ECharts chart components
- `src/composables/` - Reusable composition functions

### Backend Structure

- `src/main.py` - FastAPI app entry point with Redis/in-memory cache fallback
- `src/api/routes.py` - API endpoints (/v1/run-model, /v1/lever-data/{name}, etc.)
- `transition-compass-model` - Climate model, installed as a Python package (not in this repo)

### Regional Configuration

`model_config.json` (root level) defines:

- `MODEL_PRIMARY_REGION`: Default region (can override via env var)
- `AVAILABLE_REGIONS`: ["Vaud", "Switzerland", "EU27"]
- `SECTORS_TO_RUN`: Sector dependency mapping for efficient model execution

## Routing

```
/              → redirect to /overall
/overall       → OverallTab (DashboardLayout)
/buildings     → BuildingsTab
/transport     → TransportTab
/energy        → EnergyTab
/forestry      → ForestryTab
/agriculture   → AgricultureTab
/about         → AboutPage (MainLayout)
/legal         → LegalPage
```

## Code Style

### Frontend

- Vue 3 Composition API with `<script setup lang="ts">`
- Single File Components, max ~300 lines
- Pinia for global state, refs/reactive for local
- Define interfaces for props, emits, and state
- Extract reusable logic into composables

### Backend

- Python 3.12+, FastAPI, Pydantic validation
- Ruff for formatting and linting
- `@conditional_cache` decorator for caching

### Commits

Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`, `chore:`

## Branch Strategy

```
main (production) ← dev (staging) ← feature/*, fix/*
```

Model research is done in the separate [transition-compass-model](https://github.com/2050Calculators/transition-compass-model) repository. App changes go through feature branches into `dev`.

## API Endpoints

- `GET /health` - Health check
- `GET /v1/run-model?levers=...&sector=...&country=...` - Run climate model
- `GET /v1/lever-data/{leverName}` - Get lever visualization data
- `GET /v1/datamatrix/{name}` - Get raw datamatrix
- `GET /docs` - Swagger UI

## Dev servers and worktrees

Every checkout (the main one and each git worktree under `.claude/worktrees/<branch>`)
gets its own tmux session `leure-speed-to-zero/<branch>` (the name comes from the git
remote, not from the directory) with one `dev` window of four titled panes: `claude`
(the left half, focused on attach), `backend`, `frontend` and `shell` stacked on the
right (`scripts/tmux-dev.sh`, or `make tmux-dev-all`; `make go
BRANCH=feat/x` creates the worktree and attaches, `wt create` alone starts it detached
through `.wt.toml`). Full guide: `docs/worktree-env.md`.

- **Know where you are**: you are in a worktree exactly when `.env.worktree` exists at
  the repo root (same thing, your path contains `.claude/worktrees/`). The tmux panes,
  the claude one included, start with that file exported, so `echo $WT_BRANCH
$BACKEND_PORT $FRONTEND_PORT` orients you instantly. In a shell without them, run
  `set -a; . .env.worktree; set +a` first.
- **Ports**: a worktree's `.env.worktree` holds its `BACKEND_PORT` / `FRONTEND_PORT`
  (hashed from `<repo>/<branch>`, 18xxx/19xxx, stepping past a pair another worktree
  holds); the main checkout uses 8000/9000. Read them from that file, never guess, and
  never start a second server on a port that is already served.
  `scripts/wt-open.sh [frontend|backend]` prints and opens the URL.
- **Reuse before starting**: the tmux session already runs both servers in its `backend`
  and `frontend` panes. If you must start one yourself, `set -a; . .env.worktree;
set +a` first so uvicorn and quasar pick the worktree's values.
- **Finish** a frontend or backend change by printing its URL:
  `http://localhost:$FRONTEND_PORT/` or `http://127.0.0.1:$BACKEND_PORT/docs`. Use the
  app through the frontend port only: it proxies `/api` to this worktree's backend
  (`frontend/quasar.config.ts`).
- **Checking your work**: read-only `curl` against your own `localhost` / `127.0.0.1`
  ports is pre-allowed in the common forms (bare, `-s`, `-sS`, `-fsS`, `-i`, `-I`), so
  hit your servers freely; write forms still prompt. The backend and frontend panes
  mirror their output to `.wt-logs/backend.log` and `.wt-logs/frontend.log` in the
  checkout root. When a server is down or misbehaving, read those (the tmux socket is
  outside your sandbox, so `tmux` commands will fail, the log files are the supported
  path).

### The model, transition-compass-model

The backend imports `transition_compass_model`. `backend/pyproject.toml` pins the PyPI
release, and every checkout overrides it with an editable install of a local clone.
`TCM_PATH` in `.env.worktree` says which clone; `make -C backend check-model` prints the
file the running backend actually imports.

- **`TCM_BRANCH` empty**: `TCM_PATH` is the model's **main checkout**, shared read-only
  with every other worktree. Read it, never write in it. A task that needs model changes
  wants its own model worktree, ask for one.
- **`TCM_BRANCH` set**: this worktree is paired with a model worktree on that branch
  (`wtgo <branch> --model <model-branch>`). It is yours to edit and commit, under the
  same one-branch rule as this repo, and the backend reloads on its `.py` changes.
- **Never `uv sync` or a bare `uv run` in `backend/`**: both re-install the PyPI model
  over the editable one. `UV_NO_SYNC=1` comes from `.env.worktree` for that reason; in a
  shell without it, use `uv run --no-sync`. If the model import looks wrong, re-run
  `scripts/wt-setup.sh`.

### Working in a worktree, rules

- **You own exactly one branch**: the worktree's. Commit and push to it freely. Never
  push `dev` or `main`, never push another branch, never force-push.
  `scripts/git-push-guard.sh` refuses it in git itself (the shared `pre-push` hook), and
  the session's deny rules refuse it before that. Landing into `dev` is a human's job,
  from the main checkout, with `scripts/wt-land.sh`.
- **Never tag**: a `v*` tag here deploys, and a tag on the model repo publishes to PyPI
  and opens a bump PR here. Releases are release-please's job.
- **Network**: read the web freely. Anything that writes outward (`curl -X POST`,
  `gh pr create`, and so on) or runs downloaded code (`curl … | sh`, `npx -y …`) prompts
  the user by design. Do not work around a prompt.
