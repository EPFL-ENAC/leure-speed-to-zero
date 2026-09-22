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

Every branch has its own git worktree, tmux session and agent. The session is
`leure-speed-to-zero/<branch>` and its panes are `agent`, `backend`, `frontend`, `shell`.

- Ports are per worktree and live in `.env.worktree`, which every pane exports.
  Never hardcode a port, read `BACKEND_PORT`, `FRONTEND_PORT` from the environment.
- The dev servers are already running in their own panes. Do not start them
  again. Read `.wt-logs/*.log` to see what they are doing, the sandbox cannot
  reach the tmux socket.
- `wtx curl <family> [path] [curl args]` is how you reach them. It fills in this
  worktree's port and never prompts, whatever the method: `wtx curl backend
/api/health`. Plain curl to localhost works for a GET and prompts past that.
- Work on this branch only. Never push `dev` and `main`. When the work is ready, say
  so and a human runs `wtx land <branch>` from the main checkout.
- A pre-push hook enforces this. If it refuses a push, that is the design, not a
  bug to work around.

### Directories outside this repo

- `k8s` at `~/code/enack8s-app-config/epfl-{lab}/speed-to-zero`, access `pair`.
- `lgb-trsc` at `../lgb-trsc`, access `read`.
- `transition-compass-model` at `../transition-compass-model`, access `pair`.

A `read` directory is yours to read as much as you like, with no prompt, and you
may never write in it. To change one, ask for a paired worktree instead: a human
runs `wtx go <branch> --with <name>=<branch>`, and the change lands through that
repo's own pull request.
