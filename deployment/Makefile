export COMPOSE_PROJECT_NAME=bims
export COMPOSE_FILE=docker-compose.dev.yml

dev:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in dev mode"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} up -d dev

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Build dev mode"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} build dev
