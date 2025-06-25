.PHONY: install clean uninstall help run up

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies and set up git hooks"
	@echo "  clean      - Clean node_modules and package-lock.json"
	@echo "  uninstall  - Remove git hooks and clean dependencies"
	@echo "  run        - Run backend and frontend locally"
	@echo "  up         - Run docker compose with rebuild and no cache"
	@echo "  help       - Show this help message"


# Install dependencies and set up git hooks
install:
	@echo "Installing npm dependencies..."
	npm install
	@echo "Installing git hooks with lefthook..."
	npx lefthook install
	@echo "Setup complete!"

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

# Run backend and frontend locally via recursive makefiles
run:
	@echo "Starting local development servers..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:9000 (Quasar default)"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill $$(jobs -p) 2>/dev/null || true' EXIT; \
	$(MAKE) -C backend/backend run & \
	cd frontend && npm run dev & \
	wait

# Run docker compose with rebuild and no cache
up:
	@echo "Building and starting Docker containers..."
	docker compose build --no-cache --pull
	docker compose up -d --force-recreate
	@echo "Containers started!"
	@echo "Frontend available at https://lgb-trsc.localhost"
	@echo "Backend API available at https://lgb-trsc.localhost/api"
	@echo "Traefik dashboard available at http://localhost:8080"