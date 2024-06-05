.PHONY: backup-dump run run-local
# Get the current HEAD tag
TAG := $(shell git describe --tags --abbrev=0)
# Set the IMAGE_VERSION environment variable
DOCKER_CONFIG_PATH := $(shell pwd)
export IMAGE_VERSION := $(TAG)

login:
	@echo "Logging in to GHCR"
	@echo ${DOCKER_CONFIG_PATH}
	@export DOCKER_CONFIG=$(DOCKER_CONFIG_PATH); \
	docker login ghcr.io

run:
	@make login
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --pull=always -d --remove-orphans

run-local:
	docker compose build --pull
	docker compose up -d --remove-orphans

backup-dump:
	docker compose cp backend-ghg-model:/app/database/ ${DEST_FOLDER}/
