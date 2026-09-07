.PHONY: install install-dev install-config install-backend install-backend-local install-frontend clean uninstall help run run-backend run-backend-with-cache run-frontend wait-for-backend up tmux-dev-all new go wt-land wt-done wt-open

# Per-checkout ports. A git worktree exports its own pair from .env.worktree
# (scripts/wt-setup.sh, see docs/worktree-env.md); the main checkout keeps these.
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 9000

# Default target
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         TransitionCompass - Development Commands                    ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup:"
	@echo "  make install           - Install all dependencies using git source (CI/CD mode)"
	@echo "  make install-dev       - Install all dependencies using local model (dev mode)"
	@echo "  make install-backend   - Install backend dependencies only (git source)"
	@echo "  make install-frontend  - Install frontend dependencies only"
	@echo "  make clean             - Clean node_modules and package-lock.json"
	@echo "  make uninstall         - Remove git hooks and clean dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run               - Run backend + frontend locally (RECOMMENDED)"
	@echo "  make run-backend       - Run backend only (cache disabled)"
	@echo "  make run-frontend      - Run frontend only"
	@echo "  make run-backend-with-cache - Run backend with cache enabled (for testing)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              - Check code quality (ESLint, Prettier, Python linting)"
	@echo "  make format            - Auto-fix formatting issues"
	@echo ""
	@echo "Docker:"
	@echo "  make up                - Run docker compose with rebuild and no cache"
	@echo ""
	@echo "Documentation:"
	@echo "  CONTRIBUTING.md        - Git workflow, branches, PR process"
	@echo "  TUTORIAL_NEW_SECTOR.md - Add new sectors to the model"
	@echo "  TUTORIAL_NEW_LEVER.md  - Add new policy levers"
	@echo ""
	@echo "Typical workflow:"
	@echo "  1. git checkout dev && git pull                 (sync with latest)"
	@echo "  2. git checkout -b feature/my-change            (create branch)"
	@echo "  3. [make changes to code]"
	@echo "  4. make lint && make format                     (check quality)"
	@echo "  5. make run                                     (test locally)"
	@echo "  6. git add . && git commit -m 'feat: ...'      (commit changes)"
	@echo "  7. git push origin feature/my-change            (push to remote)"
	@echo "  8. Create PR: feature/* → dev on GitHub         (request review)"
	@echo ""
	@echo "See CONTRIBUTING.md for complete workflow details"


# Install dependencies using git source (CI/CD mode)
install: install-config install-backend install-frontend
	@echo "Installing root dependencies and git hooks..."
	npm install
	@echo "Setup complete!"

# Install dependencies using local transition-compass-model (dev mode)
install-dev: install-config install-backend-local install-frontend
	@echo "Installing root dependencies and git hooks..."
	npm install
	@echo "Setup complete! (using local transition-compass-model)"

# Install configuration (placeholder for future config setup)
install-config:
	@echo "Configuration setup..."
	@# Add any config file generation here if needed
	@echo "Configuration ready!"


# Install backend dependencies (git source / CI mode)
install-backend:
	@echo "Installing backend dependencies..."
	$(MAKE) -C backend install

# Install backend dependencies (local editable model override)
install-backend-local:
	@echo "Installing backend dependencies (local model)..."
	$(MAKE) -C backend install-local

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
		if curl -f -s http://localhost:$(BACKEND_PORT)/health >/dev/null 2>&1; then \
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
	@echo "Backend will be available at http://localhost:$(BACKEND_PORT)"
	@echo "Frontend will be available at http://localhost:$(FRONTEND_PORT)"
	@echo "⚠️  Cache is DISABLED in development mode"
	@echo "Press Ctrl+C to stop both servers"
	@set -e; \
	SHUTDOWN_FLAG="/tmp/shutdown_$$$$"; \
	kill_tree() { \
		for child in $$(pgrep -P $$1 2>/dev/null || true); do kill_tree $$child; done; \
		kill -TERM $$1 2>/dev/null || true; \
	}; \
	cleanup_servers() { \
		if [ ! -f "$$SHUTDOWN_FLAG" ]; then \
			touch "$$SHUTDOWN_FLAG"; \
			echo ""; \
			echo "Shutting down servers..."; \
			kill_tree $$BACKEND_PID; \
			kill_tree $$FRONTEND_PID; \
			echo "Waiting for processes to finish..."; \
			sleep 2; \
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
	@echo "Backend will be available at http://localhost:$(BACKEND_PORT)"
	@echo "API docs available at http://localhost:$(BACKEND_PORT)/docs"
	@echo "⚠️  Cache is DISABLED in development mode"
	ENABLE_CACHE=false $(MAKE) -C backend run

# Run backend with cache enabled (for testing cache behavior)
run-backend-with-cache:
	@echo "Starting backend development server WITH cache..."
	@echo "Backend will be available at http://localhost:$(BACKEND_PORT)"
	@echo "API docs available at http://localhost:$(BACKEND_PORT)/docs"
	@echo "✅ Cache is ENABLED"
	ENABLE_CACHE=true $(MAKE) -C backend run

# Run frontend only
run-frontend:
	@echo "Starting frontend development server..."
	@echo "Frontend will be available at http://localhost:$(FRONTEND_PORT)"
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

# --- git worktrees (docs/worktree-env.md)
# One branch = one worktree = one tmux session = one Claude Code agent, with its
# own ports and its own model checkout. Tab completion: source scripts/wt-go.bash.

tmux-dev-all:           ## tmux session "<repo>/<branch>" with claude, backend, frontend and shell panes
	scripts/tmux-dev.sh

new:                    ## make new BRANCH=feat/x [BASE=origin/dev] [MODEL=feat/y] [PROMPT=brief.md] : worktree + deps + session, attached
	scripts/wt-new.sh $(BRANCH) $(BASE) $(if $(MODEL),--model '$(MODEL)') $(if $(PROMPT),--prompt '$(PROMPT)')

go: new                 ## make go BRANCH=feat/x : jump to the branch's session, creating branch/worktree/session as needed (tab completion: wtgo)

wt-land:                ## make wt-land BRANCH=feat/x [MODE=--local] : rebase, PR + squash-merge into dev, clean up
	scripts/wt-land.sh $(BRANCH) $(MODE)

wt-done:                ## make wt-done BRANCH=feat/x : kill the session + remove the worktree, keep the branch
	scripts/wt-done.sh $(BRANCH)

wt-open:                ## make wt-open [TARGET=frontend|backend] [BRANCH=feat/x] : print and open the URL
	scripts/wt-open.sh $(or $(TARGET),frontend) $(BRANCH)
