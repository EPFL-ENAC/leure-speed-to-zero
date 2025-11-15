# SpeedToZero - Interactive Climate Pathway Visualization Platform

Interactive platform for climate pathway modeling and visualization. Enables real-time exploration of policy impacts on emissions, energy, and environmental indicators across sectors.

## 📚 Tutorials

- **[Adding a New Sector](TUTORIAL_NEW_SECTOR.md)** - Create new sectors with charts and subtabs
- **[Adding a New Lever](TUTORIAL_NEW_LEVER.md)** - Add policy controls to sectors

## 🌍 Live Platforms

- **Production**: [https://speed-to-zero.epfl.ch/](https://speed-to-zero.epfl.ch/)
- **Development**: [https://speed-to-zero-dev.epfl.ch/](https://speed-to-zero-dev.epfl.ch/)

## 🏗️ Architecture

**Frontend**: Vue.js 3 + TypeScript, Quasar, ECharts, Pinia, Vite  
**Backend**: FastAPI (Python 3.12), Pandas, NumPy, Redis (optional), Pydantic  
**Infrastructure**: Docker, Traefik, nginx

### Project Structure

```
speed-to-zero/
├── frontend/                 # Vue.js 3 application
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   ├── graphs/       # Chart components
│   │   │   ├── kpi/          # KPI widgets
│   │   │   └── levers/       # Policy controls
│   │   ├── pages/            # Route components
│   │   ├── stores/           # Pinia stores
│   │   └── utils/            # Utility functions
│   └── public/               # Static assets
├── backend/                  # FastAPI application
│   ├── src/
│   │   ├── api/              # API endpoints
│   │   ├── config/           # Configuration
│   │   └── utils/            # Backend utilities
│   ├── model/                # Climate calculation modules
│   │   ├── agriculture_module.py
│   │   ├── buildings_module.py
│   │   ├── transport_module.py
│   │   ├── industry_module.py
│   │   ├── power_module.py
│   │   ├── emissions_module.py
│   │   └── interactions.py
│   └── _database/            # Data processing
│       ├── data/             # Datasets
│       └── pre_processing/   # Data preparation
├── model_config.json         # Regional configuration
├── docker-compose.yml        # Development setup
└── Makefile                  # Build automation
```

## 🚀 Quick Start

**Prerequisites**: Node.js 22+, Python 3.12+, Docker (optional)

```bash
git clone https://github.com/EPFL-ENAC/leure-speed-to-zero.git
cd leure-speed-to-zero

# Install dependencies and setup git hooks
make install

# Start both services
make run
```

**Services**: Frontend (http://localhost:9000) | Backend API (http://localhost:8000) | Docs (http://localhost:8000/docs)

## ⚙️ Configuration

**Region**: Edit `model_config.json`, in both folders `frontend/` and `backend/`  
**Redis**: Optional caching - `docker compose up -d redis`

## 🛠️ Development

**Commands**: `make clean` | `make lint` | `make format` | `make run-backend` | `make run-frontend`  
**Quality**: Lefthook hooks, Conventional Commits, ESLint + Prettier, Python linting

## 🔧 API & Model

**Key Endpoints**: `/api/calculate` (POST) | `/api/regions/{region}/data` (GET) | `/api/config` (GET)  
**Modules**: Agriculture, Buildings, Transport, Industry, Power, Emissions  
**Docs**: http://localhost:8000/docs

## 📊 Data

**Sources**: Eurostat, World Bank, JRC, national statistics  
**Pipeline**: Ingestion → Regional filtering → Validation → Model integration  
**Caching**: Redis with region namespacing

## 🧪 Testing

**Run**: `make lint` | `cd frontend && npm test` | `cd backend && python -m pytest`  
**Workflow**: Feature branch → Conventional commits → PR

## 🐳 Docker

**Dev**: `docker compose up -d`  
**Prod**: `docker compose -f docker-compose.prod.yml up -d`

## 🔍 Troubleshooting

**Ports**: 9000 (frontend), 8000 (backend), 6379 (redis)  
**WSL2**: `git config --global core.autocrlf input && dos2unix Makefile`  
**Python**: Activate venv, verify `requirements.txt`  
**Node**: Version 22+, try `rm -rf node_modules && npm install`

## 📄 License

[GNU General Public License v3.0](LICENSE)

## 🤝 Contributing

Fork → Feature branch → Conventional commits → Tests → PR  
**Standards**: TypeScript, Pydantic validation, error handling, performance optimization

---

**Support**: [GitHub Issues](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues)
