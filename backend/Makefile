.PHONY: install install-local run up format lint test docker-build docker-run cleanup check-model

# Per-checkout overrides. A git worktree exports these from .env.worktree
# (scripts/wt-setup.sh, see docs/worktree-env.md); the main checkout keeps the
# defaults. TCM_PATH must be absolute from a worktree: the relative default
# only resolves from a checkout sitting next to the model repo.
BACKEND_PORT ?= 8000
TCM_PATH ?= ../../transition-compass-model
TCM_BRANCH ?=

# Only a worktree paired with a model worktree (wtgo --model) watches the model
# for reloads: with the shared main checkout, someone else's edit would restart
# every backend on the machine. Naming any --reload-dir drops uvicorn's default
# (the working directory), so src has to be listed too.
RELOAD_DIRS =
ifneq ($(strip $(TCM_BRANCH)),)
RELOAD_DIRS = --reload-dir src --reload-dir $(TCM_PATH)/transition_compass_model
endif

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
	@if [ -d "$(TCM_PATH)" ]; then \
		echo "Local model found at $(TCM_PATH), installing as editable..."; \
		uv pip install --editable $(TCM_PATH); \
	else \
		echo "Local model not found at $(TCM_PATH), using PyPI version"; \
	fi
	@echo "Backend dependencies installed!"

# Cleanup any lingering processes
# Only this checkout's port: pkill by process name also killed the backends of
# every other worktree on the machine.
cleanup:
	@echo "Freeing this checkout's backend port ($(BACKEND_PORT))..."
	@fuser -k -n tcp $(BACKEND_PORT) 2>/dev/null || true
	@echo "Cleanup complete!"

check-model:
	@uv run --no-sync python -c "import transition_compass_model; print('Model source:', transition_compass_model.__file__)"

run:
	@echo "Starting FastAPI development server..."
	@echo "Open your browser at http://localhost:$(BACKEND_PORT)/docs"
	@echo "Press Ctrl+C to stop the server"
	@echo "Model source: $$(uv run --no-sync python -c 'import transition_compass_model; print(transition_compass_model.__file__)')"
	uv run --no-sync uvicorn src.main:app --reload $(RELOAD_DIRS) --host 0.0.0.0 --port $(BACKEND_PORT)
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