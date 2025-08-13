.PHONY: install run up format lint test docker-build docker-run cleanup

# Define Python version and name
PYTHON_VERSION = 3.12
NAME = backend-web-rest-api

# Install backend dependencies
install:
	@echo "Installing backend dependencies..."
	@if uv --version >/dev/null 2>&1; then \
		echo "Using uv for backend dependencies..."; \
		uv sync; \
	else \
		echo "uv not available in current environment, using virtual environment and pip..."; \
		if [ ! -d ".venv" ]; then \
			python -m venv .venv && \
			.venv/bin/pip install --upgrade pip; \
		fi && \
		.venv/bin/pip install -r requirements.txt; \
		echo "Virtual environment ready at backend/.venv"; \
	fi
	@echo "Backend dependencies installed!"

# Cleanup any lingering processes
cleanup:
	@echo "Cleaning up any lingering FastAPI processes..."
	@pkill -f "uvicorn src.main:app" 2>/dev/null || true
	@pkill -f "WatchFiles" 2>/dev/null || true
	@echo "Cleanup complete!"

run:
	@echo "Starting FastAPI development server..."
	@echo "Open your browser at http://localhost:8000/docs"
	@echo "Press Ctrl+C to stop the server"
	@if uv --version >/dev/null 2>&1; then \
		echo "Using uv..."; \
		uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "uv not found, using virtual environment..."; \
		.venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000; \
	fi
	@echo "Backend server stopped."


up:
	docker compose build --pull
	docker compose up -d --remove-orphans
	@echo "Open your browser at http://localhost:8081"

format:
	@if uv --version >/dev/null 2>&1; then \
		uv run black src; \
	else \
		.venv/bin/black src; \
	fi

lint:
	@if uv --version >/dev/null 2>&1; then \
		uv run flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics; \
		uv run flake8 src --count --exit-zero --max-complexity=15 --max-line-length=127 --statistics; \
	else \
		.venv/bin/flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics; \
		.venv/bin/flake8 src --count --exit-zero --max-complexity=15 --max-line-length=127 --statistics; \
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