# TransitionCompassViz — Interactive Climate Pathway Visualization Platform

Interactive platform for climate pathway modeling and visualization. Enables real-time exploration of policy impacts on emissions, energy, and environmental indicators across sectors.

## Live Platforms

- **Production**: [https://transition-compass.epfl.ch/](https://transition-compass.epfl.ch/)
- **Development**: [https://transition-compass-dev.epfl.ch/](https://transition-compass-dev.epfl.ch/)

## Dual-Repository Architecture

This project is split into two repositories:

| Repository                                                                                  | Purpose                                                                  |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **[speed-to-zero](https://github.com/EPFL-ENAC/leure-speed-to-zero)** (this repo)           | Web application — frontend UI, backend API, deployment                   |
| **[transition-compass-model](https://github.com/2050Calculators/transition-compass-model)** | Climate calculation engine — sector modules, data matrices, optimization |

The app imports the model as a Python package. The backend calls the model's `runner()` function with lever settings and receives time-series results and KPIs to serve to the frontend.

```
Vue UI  →  Pinia Store  →  modelService  →  FastAPI backend  →  transition-compass-model
```

### Who works where?

- **App developers** (frontend, API, charts, UI): work in this repo
- **Model researchers** (sector calculations, data, parameters): work in the [transition-compass-model](https://github.com/2050Calculators/transition-compass-model) repo

## Tech Stack

**Frontend**: Vue.js 3 + TypeScript, Quasar 2, ECharts (vue-echarts), Pinia, Vite, vue-i18n (DE/EN/FR)
**Backend**: FastAPI, Python 3.12, Pandas, NumPy, Redis (optional), Pydantic
**Infrastructure**: Docker, Traefik, nginx

### Project Structure

```
speed-to-zero/
├── frontend/                 # Vue.js 3 application
│   ├── src/
│   │   ├── components/       # UI components (graphs/, kpi/, levers/)
│   │   ├── pages/            # Route/sector tab components
│   │   ├── stores/           # Pinia stores (leversStore.ts)
│   │   ├── services/         # API client (modelService.ts)
│   │   ├── composables/      # Reusable composition functions
│   │   └── config/           # Lever and sector definitions
│   └── public/
├── backend/                  # FastAPI application
│   ├── src/
│   │   ├── main.py           # App entry point (Redis/in-memory cache)
│   │   ├── api/routes.py     # API endpoints
│   │   └── utils/
│   └── pyproject.toml        # Dependencies (includes transition-compass-model)
├── model_config.json         # Regional configuration
├── docker-compose.yml
└── Makefile
```

The model code is **not** in this repo — it is installed as a dependency via `transition-compass-model`.

## Quick Start

**Prerequisites**: Node.js 22+, Python 3.12+, Docker (optional)

```bash
git clone https://github.com/EPFL-ENAC/leure-speed-to-zero.git speed-to-zero
cd speed-to-zero

make install       # Install all dependencies using git source (CI/CD mode)
make run           # Start backend (port 8000) + frontend (port 9000)
```

**Services**: Frontend ([localhost:9000](http://localhost:9000)) | Backend API ([localhost:8000](http://localhost:8000)) | API docs ([localhost:8000/docs](http://localhost:8000/docs))

### Working with a local model (for researchers)

If you're developing the model and want to see changes reflected in the app in real time, clone both repos as siblings and use the local install:

```
parent-dir/
├── speed-to-zero/                  ← this repo
└── transition-compass-model/       ← model repo
```

```bash
# From speed-to-zero/
make install-dev   # Installs deps and links to local model (editable)
make run           # Changes in ../transition-compass-model/ are reflected immediately
```

`make install-dev` runs `make install-local` in the backend, which detects the sibling model directory and installs it as an editable package. Verify with:

```bash
cd backend && make check-model
# Local mode:  path points to ../../transition-compass-model/
# Remote mode: path points inside .venv/lib/.../site-packages/
```

To switch back to the remote (git-pinned) model: `make install`.

See the [transition-compass-model DEVELOPMENT.md](https://github.com/2050Calculators/transition-compass-model/blob/main/DEVELOPMENT.md) for full details.

## Development

| Command             | Description                                 |
| ------------------- | ------------------------------------------- |
| `make install`      | Install all dependencies (git source)       |
| `make install-dev`  | Install all dependencies (local model)      |
| `make run`          | Run backend + frontend                      |
| `make run-backend`  | Backend only (cache disabled)               |
| `make run-frontend` | Frontend only                               |
| `make lint`         | Check code quality (ESLint, Prettier, ruff) |
| `make format`       | Auto-fix formatting                         |
| `make up`           | Docker compose build and start              |

**Code quality**: Lefthook pre-commit hooks, Conventional Commits (`feat:`, `fix:`, `docs:`, etc.), ESLint + Prettier (frontend), ruff (backend).

## Branch Workflow

```
main (production) ← dev (staging) ← feature/*, fix/*
```

- **`main`**: Production-ready, deployed to [transition-compass.epfl.ch](https://transition-compass.epfl.ch/)
- **`dev`**: Integration/staging, deployed to [transition-compass-dev.epfl.ch](https://transition-compass-dev.epfl.ch/)
- **`feature/*`, `fix/*`**: Short-lived branches for specific changes, PR into `dev`

See [Contributing Guide](CONTRIBUTING.md) for the full workflow.

## Model Updates

When a new version of `transition-compass-model` is tagged (e.g. `v1.2.3`), a GitHub Actions workflow automatically creates a PR in this repo (`chore/bump-model-v1.2.3 → dev`) that updates the dependency and regenerates the lock file. Review and merge to deploy.

## API

| Endpoint                                              | Description              |
| ----------------------------------------------------- | ------------------------ |
| `GET /health`                                         | Health check             |
| `GET /v1/run-model?levers=...&sector=...&country=...` | Run climate model        |
| `GET /v1/lever-data/{leverName}`                      | Lever visualization data |
| `GET /v1/datamatrix/{name}`                           | Raw datamatrix           |
| `GET /docs`                                           | Swagger UI               |

## Configuration

**Region**: Edit `model_config.json` (available: Vaud, Switzerland, EU27)
**Redis**: Optional caching — `docker compose up -d redis`

## Docker

**Dev**: `docker compose up -d`
**Prod**: `docker compose -f docker-compose.prod.yml up -d`
**Ports**: 9000 (frontend), 8000 (backend), 6379 (redis)

## Documentation

- [Contributing Guide](CONTRIBUTING.md) — Git workflow, branches, PR process
- [Adding a New Sector](TUTORIAL_NEW_SECTOR.md) — Create new sectors with charts and subtabs
- [Adding a New Lever](TUTORIAL_NEW_LEVER.md) — Add policy controls to sectors
- [Adding a Region Flag](TUTORIAL_ADD_REGION_FLAG.md) — Add or change country/region flag symbols

## License

[Apache License 2.0](LICENSE)

---

**Support**: [GitHub Issues](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues)
