#!/usr/bin/env bash

# Get the latest backup from production
SOURCE_FOLDER=/source
SOURCE_SERVER=server

DEST_FOLDER=/destination

echo "copy latest backup file"
rm $DEST_FOLDER/latest.dmp
scp $SOURCE_SERVER:$SOURCE_FOLDER/$(ssh $SOURCE_SERVER "cd $SOURCE_FOLDER; find $1 -type f -exec stat --format '%Y :%y %n' "{}" \; | sort -nr | cut -d. -f3- | head -1") $DEST_FOLDER/latest.dmp

# Restart docker db
DOCKER_DB=$(docker ps --format '{{.Names}}' | grep kbims-healthyrivers-db- | head -1)
DOCKER_UWSGI=$(docker ps --format '{{.Names}}' | grep kbims-healthyrivers-uwsgi | head -1)
docker exec $DOCKER_UWSGI python manage.py dumpdata bims.SiteSetting --indent 2 > sitesetting.json
echo "restore the backup"
cp revoke.sql $DEST_FOLDER
cp restore.sql $DEST_FOLDER
docker exec $DOCKER_DB su - postgres -c "psql gis  -f /backups/revoke.sql"
docker exec $DOCKER_DB su - postgres -c "dropdb --if-exists gis"
docker exec $DOCKER_DB su - postgres -c "createdb -O docker gis"
docker exec $DOCKER_DB su - postgres -c 'pg_restore -d gis /backups/latest.dmp'
docker exec $DOCKER_DB su - postgres -c "psql gis -f /backups/restore.sql"

echo "fix duplicates"
docker exec $DOCKER_DB su - postgres -c "psql -d gis -c \"DELETE FROM django_content_type a WHERE a.ctid <> (SELECT min(b.ctid) FROM django_content_type b WHERE a.app_label = b.app_label and a.model = b.model);\""

echo "migrate and add default location site view"
docker exec $DOCKER_UWSGI python manage.py migrate
docker exec $DOCKER_UWSGI python manage.py add_default_location_site_view
docker exec $DOCKER_UWSGI python manage.py bims_loaddata sitesetting.json
