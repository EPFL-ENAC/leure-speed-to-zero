.PHONY: run up sync format lint test docker-build docker-run

# Define Python version and name
PYTHON_VERSION = 3.12
NAME = backend-web-rest-api

# Sync dependencies
sync:
	@echo "Syncing dependencies"
	uv sync
	uv export > requirements.txt

run:
	@echo "Starting FastAPI development server..."
	@echo "Open your browser at http://localhost:8000/docs"
	@if command -v uv >/dev/null 2>&1; then \
		echo "Using uv..."; \
		uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "uv not found, using virtual environment..."; \
		.venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000; \
	fi

up:
	docker compose build --pull
	docker compose up -d --remove-orphans
	@echo "Open your browser at http://localhost:8081"

format:
	@if command -v uv >/dev/null 2>&1; then \
		uv run black src; \
	else \
		.venv/bin/black src; \
	fi

lint:
	@if command -v uv >/dev/null 2>&1; then \
		uv run flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics; \
		uv run flake8 src --count --exit-zero --max-complexity=15 --max-line-length=127 --statistics; \
	else \
		.venv/bin/flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics; \
		.venv/bin/flake8 src --count --exit-zero --max-complexity=15 --max-line-length=127 --statistics; \
	fi

test:
	@if command -v uv >/dev/null 2>&1; then \
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