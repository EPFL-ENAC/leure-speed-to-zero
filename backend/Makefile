.PHONY: install install-local run up format lint test docker-build docker-run cleanup check-model

# Define Python version and name
PYTHON_VERSION = 3.12
NAME = backend-web-rest-api

# CI/CD install (uses PyPI package from lock)
install:
	@echo "Installing backend dependencies..."
	uv sync --frozen
	@echo "Backend dependencies installed!"

# Local dev install: installs from PyPI (lock), then overrides model with local editable
install-local:
	@echo "Installing backend dependencies (local mode - editable)..."
	uv sync --frozen
	@if [ -d "../../transition-compass-model" ]; then \
		echo "Local model found, installing as editable..."; \
		uv pip install --editable ../../transition-compass-model; \
	else \
		echo "Local model not found at ../../transition-compass-model, using PyPI version"; \
	fi
	@echo "Backend dependencies installed!"

# Cleanup any lingering processes
cleanup:
	@echo "Cleaning up any lingering FastAPI processes..."
	@pkill -f "uvicorn src.main:app" 2>/dev/null || true
	@pkill -f "WatchFiles" 2>/dev/null || true
	@echo "Cleanup complete!"

check-model:
	@uv run --no-sync python -c "import transition_compass_model; print('Model source:', transition_compass_model.__file__)"

run:
	@echo "Starting FastAPI development server..."
	@echo "Open your browser at http://localhost:8000/docs"
	@echo "Press Ctrl+C to stop the server"
	@echo "Model source: $$(uv run --no-sync python -c 'import transition_compass_model; print(transition_compass_model.__file__)')"
	uv run --no-sync uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
	@echo "Backend server stopped."


up:
	docker compose build --pull
	docker compose up -d --remove-orphans
	@echo "Open your browser at http://localhost:8081"

format:
	@if uv --version >/dev/null 2>&1; then \
		uv run ruff format src; \
		uv run ruff check --fix src; \
	else \
		ruff format src; \
		ruff check --fix src; \
	fi

lint:
	@if uv --version >/dev/null 2>&1; then \
		uv run ruff check src; \
	else \
		ruff check src; \
	fi

test:
	@if uv --version >/dev/null 2>&1; then \
		uv run pytest; \
	else \
		.venv/bin/pytest; \
	fi

docker-build:
	@echo "Building docker image"
	docker build -t $(NAME) .

docker-run: docker-build
	@echo "Running docker image"
	@echo "Open your browser at http://localhost:8081"
	docker run -p 8081:8081 $(NAME):latest

scout:
	docker scout cves local://$(NAME):latest