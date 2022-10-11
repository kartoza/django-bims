export COMPOSE_PROJECT_NAME=bims
export COMPOSE_FILE=docker-compose.dev.yml

dev:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in dev mode"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} up -d dev worker

dev-test:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in DEVELOPMENT mode"
	@echo "------------------------------------------------------------------"

	@docker-compose ${ARGS} exec -T dev python manage.py test --settings=core.settings.test_docker --keepdb --noinput

down:
	# Synonymous with kill rm
	@docker-compose  ${ARGS} down

rm-only: kill
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Removing production instance!!! "
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} rm

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

reset-search-results:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Reset search results"
	@echo "------------------------------------------------------------------"
	@docker-compose exec dev python /home/web/django_project/manage.py clear_search_results
	@docker-compose ${ARGS} restart worker
	@docker-compose ${ARGS} restart cache
