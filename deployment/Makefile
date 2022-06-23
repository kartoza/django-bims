export COMPOSE_PROJECT_NAME=bims
export COMPOSE_FILE=docker-compose.dev.yml

dev:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in dev mode"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} up -d dev

geoserver:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running geoserver"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} up -d geoserver

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Build dev mode"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} build dev
