#!/usr/bin/env bash

# Get the latest backup from production
SOURCE_FOLDER=/source
SOURCE_SERVER=server

DEST_FOLDER=/destination

echo "copy latest backup file"
scp $SOURCE_SERVER:$SOURCE_FOLDER/$(ssh $SOURCE_SERVER "cd $SOURCE_FOLDER; find $1 -type f -exec stat --format '%Y :%y %n' "{}" \; | sort -nr | cut -d. -f3- | head -1") $DEST_FOLDER

# Restart docker db
DOCKER_DB=$(docker ps --format '{{.Names}}' | grep kbims-healthyrivers-db- | head -1)
echo "restart docker db"
docker restart $DOCKER_DB
echo "wait for 15 seconds"
sleep 15s
echo "restore the backup"
docker exec $DOCKER_DB su - postgres -c "dropdb gis"
docker exec $DOCKER_DB su - postgres -c "createdb -O docker -T template_postgis gis"
docker exec $DOCKER_DB bash -c 'pg_restore /backups/latest.dmp | su - postgres -c "psql gis"'

echo "fix duplicates"
docker exec $DOCKER_DB su - postgres -c "psql -d gis -c \"DELETE FROM django_content_type a WHERE a.ctid <> (SELECT min(b.ctid) FROM django_content_type b WHERE a.app_label = b.app_label and a.model = b.model);\""
docker exec $DOCKER_DB su - postgres -c "psql -d gis -c \"DELETE FROM bims_sitesetting a WHERE a.ctid <> (SELECT min(b.ctid) FROM bims_sitesetting b WHERE a.preferences_ptr_id = b.preferences_ptr_id);\""
docker exec $DOCKER_DB su - postgres -c "psql -d gis -c \"DELETE FROM preferences_preferences a WHERE a.ctid <> (SELECT min(b.ctid) FROM preferences_preferences b WHERE a.id = b.id);\""
docker exec $DOCKER_DB su - postgres -c "psql -d gis -c \"DELETE FROM preferences_preferences_sites a WHERE a.ctid <> (SELECT min(b.ctid) FROM preferences_preferences_sites b WHERE a.preferences_id = b.preferences_id);\""

echo "migrate and add default location site view"
DOCKER_UWSGI=$(docker ps --format '{{.Names}}' | grep kbims-healthyrivers-uwsgi | head -1)
docker exec $DOCKER_UWSGI python manage.py migrate
docker exec $DOCKER_UWSGI python manage.py add_default_location_site_view
