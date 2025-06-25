.PHONY: run run-local

run:
	@echo "Running the app locally by cd to the backend folder and run make run"

run-local:
	docker compose build --pull
	docker compose up -d --remove-orphans
	@echo "Open your browser at http://localhost:8081"