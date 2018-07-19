export COMPOSE_PROJECT_NAME=bims
export COMPOSE_FILE=deployment/docker-compose.yml:deployment/docker-compose.override.yml
export ANSIBLE_PROJECT_SETUP_DIR=deployment/ansible

SHELL := /bin/bash

# ----------------------------------------------------------------------------
#    S E T U P     C O M M A N D S
# ----------------------------------------------------------------------------

setup:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building dist file "
	@echo "------------------------------------------------------------------"
	@python setup.py sdist

ansible-check:
	@echo "Check ansible command"
	@ansible -i ${ANSIBLE_PROJECT_SETUP_DIR}/development/hosts all -m ping
	@ansible-playbook -i ${ANSIBLE_PROJECT_SETUP_DIR}/development/hosts ${ANSIBLE_PROJECT_SETUP_DIR}/development/site.yml --list-tasks --list-hosts $(ANSIBLE_ARGS)

setup-ansible:
	@echo "Setup configurations using ansible"
	@ansible-playbook -i ${ANSIBLE_PROJECT_SETUP_DIR}/development/hosts ${ANSIBLE_PROJECT_SETUP_DIR}/development/site.yml $(ANSIBLE_ARGS)

flake8-check:
	@echo "Flake8 check"
	@flake8 --config .flake8 .

# ----------------------------------------------------------------------------
#    P R O D U C T I O N     C O M M A N D S
# ----------------------------------------------------------------------------
default: web
run: build permissions web migrate collectstatic

deploy: run
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Bringing up fresh instance "
	@echo "You can access it on http://localhost:63200"
	@echo "------------------------------------------------------------------"

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building in production mode"
	@echo "------------------------------------------------------------------"
	@git submodule init
	@git submodule update
	@docker-compose ${ARGS} build bims_uwsgi
	@docker-compose ${ARGS} build uwsgi

web:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} up -d web
	@# Dont confuse this with the dbbackup make command below
	@# This one runs the postgis-backup cron container
	@# We add --no-recreate so that it does not destroy & recreate the db container
	@docker-compose ${ARGS} up --no-recreate --no-deps -d dbbackups

up: web
	# Synonymous with web

permissions:
	# Probably we want something more granular here....
	# Your sudo password will be needed to set the file permissions
	# on logs, media, static and pg dirs
	@if [ ! -d "logs" ]; then mkdir logs; fi
	@if [ ! -d "media" ]; then mkdir media; fi
	@if [ ! -d "static" ]; then mkdir static; fi
	@if [ ! -d "backups" ]; then mkdir backups; fi
	@if [ -d "logs" ]; then sudo chmod -R a+rwx logs; fi
	@if [ -d "media" ]; then sudo chmod -R a+rwx media; fi
	@if [ -d "static" ]; then sudo chmod -R a+rwx static; fi
	@if [ -d "pg" ]; then sudo chmod -R a+rwx pg; fi
	@if [ -d "backups" ]; then sudo chmod -R a+rwx backups; fi

db:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running db in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose up -d db

nginx:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running nginx in production mode"
	@echo "Normally you should use this only for testing"
	@echo "In a production environment you will typically use nginx running"
	@echo "on the host rather if you have a multi-site host."
	@echo "------------------------------------------------------------------"
	@docker-compose up -d nginx
	@echo "Site should now be available at http://localhost"

migrate:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running migrate static in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py migrate

update-migrations:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running update migrations in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose ${ARGS} exec uwsgi python manage.py makemigrations

collectstatic:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Collecting static in production mode"
	@echo "------------------------------------------------------------------"
	#@docker-compose run --rm uwsgi python manage.py collectstatic --noinput
	#We need to run collect static in the same context as the running
	# uwsgi container it seems so I use docker exec here
	# no -it flag so we can run over remote shell
	@docker-compose ${ARGS} exec uwsgi python manage.py collectstatic --noinput ${CMD_ARGS} -i geoexplorer

reload:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Reload django project in production mode"
	@echo "------------------------------------------------------------------"
	# no -it flag so we can run over remote shell
	@docker-compose exec uwsgi uwsgi --reload  /tmp/django.pid

rebuildindex:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running rebuild_index in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose run --rm uwsgi python manage.py rebuild_index

updateindex:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running update_index in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose run --rm uwsgi python manage.py update_index

kill:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Killing in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose kill

rm: dbbackup rm-only

down:
	# Synonymous with kill rm
	@docker-compose down


rm-only: kill
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Removing production instance!!! "
	@echo "------------------------------------------------------------------"
	@docker-compose rm

logs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing uwsgi logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose logs -f --tail=30 uwsgi

dblogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing db logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose logs -f --tail=30 db

nginxlogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing nginx logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose logs -f --tail=30 web

shell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Shelling in in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi /bin/bash

superuser:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Creating a superuser in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py createsuperuser

dbbash:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Bashing in to production database"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db /bin/bash

dbsnapshot:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Grab a quick snapshot of the database and place in the host filesystem"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db /bin/bash -c "PGPASSWORD=docker pg_dump -Fc -h localhost -U docker -f /tmp/$(COMPOSE_PROJECT_NAME)-snapshot.dmp gis"
	@docker cp $(COMPOSE_PROJECT_NAME)-db:/tmp/$(COMPOSE_PROJECT_NAME)-snapshot.dmp .
	@docker-compose exec db /bin/bash -c "rm /tmp/$(COMPOSE_PROJECT_NAME)-snapshot.dmp"
	@ls -lahtr *.dmp

dbschema:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Print the database schema to stdio"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db /bin/bash -c "PGPASSWORD=docker pg_dump -s -h localhost -U docker gis"

dbshell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Shelling in in production database"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db psql -U docker -h localhost gis

dbrestore:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Restore dump from backups/latest.dmp in production mode"
	@echo "------------------------------------------------------------------"
	@# - prefix causes command to continue even if it fails
	-@docker-compose exec db su - postgres -c "dropdb gis"
	@docker-compose exec db su - postgres -c "createdb -O docker -T template_postgis gis"
	@docker-compose exec db pg_restore /backups/latest.dmp | docker exec -i $(COMPOSE_PROJECT_NAME)-db su - postgres -c "psql gis"

db-fresh-restore:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Restore dump from backups/latest.dmp in production mode"
	@echo "------------------------------------------------------------------"
	-@docker-compose exec db su - postgres -c "dropdb gis"
	@docker-compose exec db su - postgres -c "createdb -O docker -T template_postgis gis"
	@docker-compose exec db su - postgres -c "psql gis -f /sql/bims-old.sql"
	@docker-compose exec db su - postgres -c "psql gis -f /sql/migration.sql"


dbbackup:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Create `date +%d-%B-%Y`.dmp in production mode"
	@echo "Warning: backups/latest.dmp will be replaced with a symlink to "
	@echo "the new backup."
	@echo "------------------------------------------------------------------"
	@# - prefix causes command to continue even if it fails
	@# Explicitly don't use -it so we can call this make target over a remote ssh session
	@docker exec $(COMPOSE_PROJECT_NAME)-db-backups /backups.sh
	@docker exec $(COMPOSE_PROJECT_NAME)-db-backups cat /var/log/cron.log | tail -2 | head -1 | awk '{print $4}'
	-@if [ -f "backups/latest.dmp" ]; then rm backups/latest.dmp; fi
	# backups is intentionally missing from front of first clause below otherwise symlink comes
	# out with wrong path...
	@ln -s `date +%Y`/`date +%B`/PG_$(COMPOSE_PROJECT_NAME)_gis.`date +%d-%B-%Y`.dmp backups/latest.dmp
	@echo "Backup should be at: backups/`date +%Y`/`date +%B`/PG_$(COMPOSE_PROJECT_NAME)_gis.`date +%d-%B-%Y`.dmp"

sentry:
	@echo
	@echo "--------------------------"
	@echo "Running sentry production mode"
	@echo "--------------------------"
	@docker-compose up -d sentry

maillogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing smtp logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose exec smtp tail -f /var/log/mail.log

mailerrorlogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing smtp error logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose exec smtp tail -f /var/log/mail.err

create-machine:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Creating a docker machine."
	@echo "------------------------------------------------------------------"
	@docker-machine create -d virtualbox $(COMPOSE_PROJECT_NAME)

enable-machine:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Enabling docker machine."
	@echo "------------------------------------------------------------------"
	@echo "eval \"$(docker-machine env freshwater)\""

sync-geonode:
	@docker-compose ${ARGS} exec uwsgi paver sync

sync-roles:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running update migrations in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose run --rm uwsgi python manage.py sync_roles

gruntserver:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Run grunt"
	@echo "------------------------------------------------------------------"
	@docker-compose run --rm uwsgi python manage.py gruntserver

generate-boundaries:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Generate boundaries"
	@echo "------------------------------------------------------------------"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) run uwsgi bash -c "python manage.py update_countries_boundary"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) run uwsgi bash -c "python manage.py update_provinces_boundary"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) run uwsgi bash -c "python manage.py update_districts_boundary"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) run uwsgi bash -c "python manage.py update_municipals_boundary"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) run uwsgi bash -c "python manage.py update_cluster"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) run uwsgi bash -c "python manage.py generate_boundary_geojson"

# ----------------------------------------------------------------------------
#    DEVELOPMENT C O M M A N D S
# --no-deps will attach to prod deps if running
# after running you will have ssh and web ports open (see dockerfile for no's)
# and you can set your pycharm to use the python in the container
# Note that pycharm will copy in resources to the /root/ user folder
# for pydevd etc. If they dont get copied, restart pycharm...
# ----------------------------------------------------------------------------

devweb: db
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in DEVELOPMENT mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) up --no-deps -d devweb

build-devweb: db
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building devweb"
	@echo "------------------------------------------------------------------"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) build devweb

devweb-test:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running karma tests in devweb"
	@echo "------------------------------------------------------------------"
	@docker exec bims-dev-web bash -c 'cd / ; karma start --single-run'

rebuildindex-devweb:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running rebuild_index in DEVELOPMENT mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -f deployment/docker-compose.yml -p $(PROJECT_ID) run devweb python manage.py rebuild_index

# Run pep8 style checking
#http://pypi.python.org/pypi/pep8
pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@pep8 --version
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128,E402  --exclude='../django_project/.pycharm_helpers','../django_project/*/migrations/','../django_project/*/urls.py','../django_project/core/settings/secret.py' ../django_project || true

status:
	@echo
	@echo "--------------------------"
	@echo "Show status of all containers"
	@echo "--------------------------"
	@docker-compose ps

django-test:
	@docker-compose exec uwsgi python manage.py test --noinput --verbosity 3 bims

coverage-django-test:
	@docker-compose exec uwsgi coverage run -p --branch --source='.' manage.py test --noinput ${CMD_ARGS} bims

update-taxa:
	@echo
	@echo "--------------------------"
	@echo "Updating tax"
	@echo "--------------------------"
	@docker-compose exec uwsgi python manage.py update_taxa

# --------------- help --------------------------------

help:
	@echo "* **build** - builds all required containers."
	@echo "* **build-devweb** - build the development container. See [development notes](README-dev.md)."
	@echo "* **collectstatic** - run the django collectstatic command."
	@echo "* **create-machine** ."
	@echo "* **db** - build and run the db container."
	@echo "* **dbbackup** - make a snapshot of the database, saving it to deployments/backups/YYYY/MM/project-DDMMYYYY.dmp. It also creates a symlink to backups/latest.dmp for the latest backup."
	@echo "* **dbbash** - open a bash shell inside the database container."
	@echo "* **dblogs** - view the database logs."
	@echo "* **dbrestore** - restore deployment/backups/latest.dmp over the active database. Will delete any existing data in your database and replace with the restore, so **use with caution**."
	@echo "* **dbschema** - dump the current db schema (without data) to stdio. Useful if you want to compare changes between instances."
	@echo "* **dbshell** - get a psql prompt into the db container. "
	@echo "* **dbsnapshot** - as above but makes the backup as deployment/snapshot.smp - replacing any pre-existing snapshot."
	@echo "* **dbsync** - use this from a development or offsite machine. It will rsync all database backups from deployment/backups to your offsite machine."
	@echo "* **default** ."
	@echo "* **deploy** ."
	@echo "* **devweb** - create an ssh container derived from uwsgi that can be used as a remote interpreter for PyCharm. See [development notes](README-dev.md)."
	@echo "* **enable-machine** - "
	@echo "* **kill** - kills all running containers. Does not remove them."
	@echo "* **logs** - view the logs of all running containers. Note that you can also view individual logs in the deployment/logs directory."
	@echo "* **mailerrorlogs** - View the error logs from the mail server."
	@echo "* **maillogs** - view the transaction logs from the mail server."
	@echo "* **mediasync** - use this from a development or offsite machine. It will rsync all media backups from deployment/media to your offsite machine."
	@echo "* **migrate** - run any pending migrations. "
	@echo "* **nginx** - builds and runs the nginx container."
	@echo "* **nginxlogs** - view just the nginx activity logs."
	@echo "* **permissions** - Update the permissions of shared volumes. Note this will destroy any existing permissions you have in place."
	@echo "* **reload** - reload the uwsgi process. Useful when you need django to pick up any changes you may have deployed."
	@echo "* **rm** - remove all containers."
	@echo "* **rm-only** - remove any containers without trying to kill them first. "
	@echo "* **run** - builds and runs the complete orchestrated set of containers."
	@echo "* **sentry** - **currently not working I think.** The idea is to spin up a sentry instance together with your app for fault reporting."
	@echo "* **shell** - open a bash shell in the uwsgi (where django runs) container."
	@echo "* **superuser** - create a django superuser account."
	@echo "* **update-migrations** - freshen all migration definitions to match the current code base."
	@echo "* **web** - same as **run** - runs the production site."
	@echo "* **pep8** - Run Python PEP8 check."
	@echo "* **status** - show status for all containers."

