.PHONY: install install-config install-backend install-frontend clean uninstall help run run-backend run-backend-with-cache run-frontend wait-for-backend up

# Default target
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         TransitionCompass - Development Commands                    ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Setup:"
	@echo "  make install           - Install all dependencies (backend + frontend) and git hooks"
	@echo "  make install-backend   - Install backend dependencies only"
	@echo "  make install-frontend  - Install frontend dependencies only"
	@echo "  make clean             - Clean node_modules and package-lock.json"
	@echo "  make uninstall         - Remove git hooks and clean dependencies"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make run               - Run backend + frontend locally (RECOMMENDED)"
	@echo "  make run-backend       - Run backend only (cache disabled)"
	@echo "  make run-frontend      - Run frontend only"
	@echo "  make run-backend-with-cache - Run backend with cache enabled (for testing)"
	@echo ""
	@echo "✨ Code Quality:"
	@echo "  make lint              - Check code quality (ESLint, Prettier, Python linting)"
	@echo "  make format            - Auto-fix formatting issues"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make up                - Run docker compose with rebuild and no cache"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  CONTRIBUTING.md        - Git workflow, branches, PR process"
	@echo "  TUTORIAL_NEW_SECTOR.md - Add new sectors to the model"
	@echo "  TUTORIAL_NEW_LEVER.md  - Add new policy levers"
	@echo ""
	@echo "🔄 Typical workflow:"
	@echo "  1. git checkout model && git merge origin/dev  (sync with latest)"
	@echo "  2. [make changes to code]"
	@echo "  3. make lint && make format                    (check quality)"
	@echo "  4. make run                                    (test locally)"
	@echo "  5. git add . && git commit -m 'feat: ...'     (commit changes)"
	@echo "  6. git push origin model                       (push to remote)"
	@echo "  7. Create PR: model → dev on GitHub            (request review)"
	@echo ""
	@echo "💡 See CONTRIBUTING.md for complete workflow details"


# Install dependencies and set up git hooks
install: install-config install-backend install-frontend
	@echo "Installing root dependencies and git hooks..."
	npm install
	@echo "Setup complete!"

# Install configuration (placeholder for future config setup)
install-config:
	@echo "Configuration setup..."
	@# Add any config file generation here if needed
	@echo "Configuration ready!"


# Install backend dependencies
install-backend:
	@echo "Installing backend dependencies..."
	$(MAKE) -C backend install

# Install frontend dependencies
install-frontend:
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
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
	@echo "Running linter on frontend..."
	npx prettier --check .
	@echo "Running linter on backend..."
	$(MAKE) -C backend lint
	@echo "Linting complete!"

format:
	@echo "Running formatter on frontend..."
	npx prettier --write .
	@echo "Running formatter on backend..."
	$(MAKE) -C backend format
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
	@echo "⚠️  Cache is DISABLED in development mode"
	@echo "Press Ctrl+C to stop both servers"
	@set -e; \
	SHUTDOWN_FLAG="/tmp/shutdown_$$$$"; \
	cleanup_servers() { \
		if [ ! -f "$$SHUTDOWN_FLAG" ]; then \
			touch "$$SHUTDOWN_FLAG"; \
			echo ""; \
			echo "Shutting down servers..."; \
			for uvicorn_pid in $$(pgrep -f "uvicorn src.main:app" 2>/dev/null || true); do \
				kill -TERM $$uvicorn_pid 2>/dev/null || true; \
				for child_pid in $$(pgrep -P $$uvicorn_pid 2>/dev/null || true); do \
					kill -TERM $$child_pid 2>/dev/null || true; \
				done; \
			done; \
			pkill -f "quasar dev" 2>/dev/null || true; \
			pkill -f "npm run dev" 2>/dev/null || true; \
			pkill -f "esbuild" 2>/dev/null || true; \
			pkill -f "vite" 2>/dev/null || true; \
			echo "Waiting for processes to finish..."; \
			sleep 4; \
			echo "All servers stopped."; \
			rm -f "$$SHUTDOWN_FLAG" 2>/dev/null || true; \
		fi; \
		exit 0; \
	}; \
	trap 'cleanup_servers' INT TERM EXIT; \
	ENABLE_CACHE=false $(MAKE) -C backend run & \
	BACKEND_PID=$$!; \
	$(MAKE) wait-for-backend; \
	cd frontend && npm run dev & \
	FRONTEND_PID=$$!; \
	echo "Both servers are running. Press Ctrl+C to stop."; \
	wait $$BACKEND_PID $$FRONTEND_PID 2>/dev/null || true



# Run backend only
run-backend:
	@echo "Starting backend development server..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	@echo "⚠️  Cache is DISABLED in development mode"
	ENABLE_CACHE=false $(MAKE) -C backend run

# Run backend with cache enabled (for testing cache behavior)
run-backend-with-cache:
	@echo "Starting backend development server WITH cache..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	@echo "✅ Cache is ENABLED"
	ENABLE_CACHE=true $(MAKE) -C backend run

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