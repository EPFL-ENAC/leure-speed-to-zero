# SpeedToZero - Interactive Climate Pathway Visualization Platform

Interactive web-based platform for climate pathway modeling and visualization using PyCalc computational models. Enables real-time exploration of policy impacts on emissions, energy consumption, and environmental indicators across multiple sectors.

## 🌍 Live Platforms

- **Production**: [https://speed-to-zero.epfl.ch/](https://speed-to-zero.epfl.ch/)
- **Development**: [https://speed-to-zero-dev.epfl.ch/](https://speed-to-zero-dev.epfl.ch/)

## 🏗️ Architecture

### Tech Stack

**Frontend**

- [Vue.js 3](https://vuejs.org/) with Composition API + TypeScript
- [Quasar Framework](https://quasar.dev/) for UI components
- [ECharts](https://echarts.apache.org/) for data visualization
- [Pinia](https://pinia.vuejs.org/) for state management
- [Vite](https://vitejs.dev/) for build tooling

**Backend**

- [FastAPI](https://fastapi.tiangolo.com/) with Python 3.12
- [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) for data processing
- [Redis](https://redis.io/) for caching (optional)
- [Pydantic](https://docs.pydantic.dev/) for data validation

**Infrastructure**

- [Docker](https://www.docker.com/) with multi-stage builds
- [Traefik](https://traefik.io/) reverse proxy
- [nginx](https://nginx.org/) for static assets

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

## 🚀 Development Setup

### Prerequisites

- Node.js 22+
- Python 3.12+
- Docker (optional, for Redis)

### Quick Setup (Linux/macOS)

```bash
git clone https://github.com/EPFL-ENAC/leure-speed-to-zero.git
cd leure-speed-to-zero

# Install dependencies and setup git hooks
make install

# Start both services
make run
```

Services will be available at:

- **Frontend**: http://localhost:9000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Manual Setup

**Install Dependencies:**

```bash
# Root dependencies (git hooks)
npm install

# Frontend dependencies
cd frontend && npm install && cd ..

# Backend dependencies
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**Configure Git Hooks:**

```bash
npx lefthook install
```

**Start Services:**

```bash
# Terminal 1 - Backend
cd backend && source .venv/bin/activate
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

## ⚙️ Configuration

### Regional Configuration

Edit `model_config.json` to change target region:

```json
{
  "MODEL_PRIMARY_REGION": "Vaud",
  "AVAILABLE_REGIONS": ["Vaud", "Switzerland", "EU27"]
}
```

Apply configuration changes:

```bash
make install-config
# Restart services
```

### Redis Caching (Optional)

Enable Redis for improved performance:

```bash
docker compose up -d redis
```

Benefits:

- Faster response times for repeated calculations
- Shared cache across development team
- Region-specific namespacing
- Automatic fallback to in-memory cache

## 🛠️ Development Tools

### Available Commands

```bash
make clean        # Clean dependencies
make lint         # Run code quality checks
make format       # Format code
make run-backend  # Backend only
make run-frontend # Frontend only
```

### Code Quality

- **Git Hooks**: [Lefthook](https://github.com/evilmartians/lefthook) for automated checks
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) with [Commitlint](https://commitlint.js.org/)
- **Frontend**: [ESLint](https://eslint.org/) + [Prettier](https://prettier.io/)
- **Backend**: Python linting and formatting

## 🔧 API Overview

### Core Endpoints

**Model Calculation:**

```http
POST /api/calculate
Content-Type: application/json

{
  "levers": {
    "buildings_efficiency": 0.8,
    "transport_electrification": 0.6,
    "industry_carbon_capture": 0.4
  },
  "region": "Vaud"
}
```

**Regional Data:**

```http
GET /api/regions/{region}/data
GET /api/regions/{region}/baseline
```

**Configuration:**

```http
GET /api/config
GET /api/levers/definitions
```

### Model Modules

**Agriculture** (`agriculture_module.py`):

- Crop emissions and land use changes
- Livestock methane calculations
- Fertilizer impact modeling

**Buildings** (`buildings_module.py`):

- Residential/commercial energy consumption
- Heating system transitions
- Appliance efficiency modeling

**Transport** (`transport_module.py`):

- Vehicle emissions by type
- Modal shift analysis
- Fuel transition scenarios

**Industry** (`industry_module.py`):

- Manufacturing process emissions
- Material flow analysis
- Carbon capture technology integration

**Power** (`power_module.py`):

- Electricity generation mix
- Renewable energy integration
- Grid emissions factors

**Emissions** (`emissions_module.py`):

- Cross-sector aggregation
- CO2, CH4, N2O calculations
- Climate impact assessment

## 📊 Data Processing

### Regional Data Pipeline

Data sources: Eurostat, World Bank, JRC, national statistics

Processing workflow:

1. **Raw Data Ingestion** (`_database/data/`)
2. **Regional Filtering** (automatic scaling)
3. **Data Validation** (consistency checks)
4. **Model Integration** (format conversion)

### Cache Management

Redis namespacing by region:

```python
cache_key = f"{region}:{calculation_hash}"
```

Cache invalidation on:

- Model parameter changes
- Regional data updates
- Configuration modifications

## 🧪 Testing & Quality

### Running Tests

```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && python -m pytest

# Lint all code
make lint
```

### Development Workflow

1. **Feature Branch**: `git checkout -b feature/your-feature`
2. **Code Changes**: Follow existing patterns
3. **Commit**: Conventional commits enforced by hooks
4. **Push**: `git push origin feature/your-feature`
5. **PR**: Create with clear technical description

## 🐳 Docker Deployment

### Development Environment

```bash
docker compose up -d
```

Services:

- `frontend`: Vue.js dev server with hot reload
- `backend`: FastAPI with auto-reload
- `redis`: Caching layer

### Production Build

```bash
# Build images
docker compose -f docker-compose.prod.yml build

# Deploy
docker compose -f docker-compose.prod.yml up -d
```

## 🔍 Troubleshooting

### Common Issues

**Port Conflicts:**

- Frontend: 9000
- Backend: 8000
- Redis: 6379

**WSL2 Line Endings:**

```bash
git config --global core.autocrlf input
dos2unix Makefile
find . -name "*.sh" -exec dos2unix {} \;
```

**Module Import Errors:**

- Ensure virtual environment is activated
- Verify `requirements.txt` installation
- Check Python path configuration

**Frontend Build Issues:**

- Node.js version 22+ required
- Clear `node_modules`: `rm -rf node_modules && npm install`
- Check for TypeScript errors

## 📄 License

[GNU General Public License v3.0](LICENSE)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Follow code standards (enforced by git hooks)
4. Write tests for new functionality
5. Submit PR with technical description

**Development Standards:**

- Conventional Commits for clear history
- TypeScript for frontend type safety
- Pydantic for backend data validation
- Comprehensive error handling
- Performance optimization for large datasets

---

**Technical Support**: [GitHub Issues](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues)
