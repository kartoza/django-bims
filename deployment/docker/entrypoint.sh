#!/usr/bin/env bash

mkdir -p /home/web/media
mkdir -p /home/web/static

# Check dependent service is ready
pushd /home/web/django_project
sleep 15 # Waits 15 second.
python scripts/wait_for_broker.py
popd

pushd /home/web/django_project
python manage.py migrate --noinput
python manage.py gruntserver
python manage.py collectstatic --noinput
python manage.py update_site_domain
python manage.py add_default_location_site_view
python manage.py add_location_site_view_geoserver
popd

exec "$@"