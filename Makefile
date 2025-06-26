.PHONY: install install-backend install-frontend clean uninstall help run run-backend run-frontend wait-for-backend up

# Default target
help:
	@echo "Available commands:"
	@echo "  install           - Install all dependencies (backend + frontend) and set up git hooks"
	@echo "  install-backend   - Install backend dependencies only"
	@echo "  install-frontend  - Install frontend dependencies only"
	@echo "  clean             - Clean node_modules and package-lock.json"
	@echo "  uninstall         - Remove git hooks and clean dependencies"
	@echo "  run               - Run backend and frontend locally (waits for backend health check)"
	@echo "  run-backend       - Run backend only"
	@echo "  run-frontend      - Run frontend only"
	@echo "  wait-for-backend  - Wait for backend health endpoint to respond"
	@echo "  up                - Run docker compose with rebuild and no cache"
	@echo "  help              - Show this help message"


# Install dependencies and set up git hooks
install: install-backend install-frontend
	@echo "Installing git hooks with lefthook..."
	npx lefthook install
	@echo "Setup complete!"

# Install backend dependencies
install-backend:
	@echo "Installing backend dependencies..."
	@cd backend && \
	if uv --version >/dev/null 2>&1; then \
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

# Install frontend dependencies
install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Frontend dependencies installed!"

# Clean dependencies
clean:
	@echo "Cleaning dependencies..."
	rm -rf node_modules
	rm -f package-lock.json

# Uninstall hooks and clean
uninstall:
	@echo "Uninstalling git hooks..."
	npx lefthook uninstall || true
	$(MAKE) clean
	@echo "Uninstall complete!"


lint:
	@echo "Running linter..."
	npx prettier --check .
	@echo "Linting complete!"

format:
	@echo "Running formatter..."
	npx prettier --write .
	@echo "Formatting complete!"

# Wait for backend health check
wait-for-backend:
	@echo "Waiting for backend to be healthy..."
	@timeout=60; \
	while [ $$timeout -gt 0 ]; do \
		if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then \
			echo "Backend is healthy!"; \
			break; \
		fi; \
		echo "Backend not ready yet, waiting... ($$timeout seconds left)"; \
		sleep 2; \
		timeout=$$((timeout - 2)); \
	done; \
	if [ $$timeout -le 0 ]; then \
		echo "Timeout waiting for backend to be healthy"; \
		exit 1; \
	fi

# Run backend and frontend locally via recursive makefiles
run:
	@echo "Starting local development servers..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:9000 (Quasar default)"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill $$(jobs -p) 2>/dev/null || true' EXIT; \
	$(MAKE) -C backend run & \
	$(MAKE) wait-for-backend && \
	cd frontend && npm run dev & \
	wait

# Run backend only
run-backend:
	@echo "Starting backend development server..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	$(MAKE) -C backend run

# Run frontend only
run-frontend:
	@echo "Starting frontend development server..."
	@echo "Frontend will be available at http://localhost:9000 (Quasar default)"
	cd frontend && npm run dev

# Run docker compose with rebuild and no cache
up:
	@echo "Building and starting Docker containers..."
	docker compose build --no-cache --pull
	docker compose up -d --force-recreate
	@echo "Containers started!"
	@echo "Frontend available at https://lgb-trsc.localhost"
	@echo "Backend API available at https://lgb-trsc.localhost/api"
	@echo "Traefik dashboard available at http://localhost:8080"