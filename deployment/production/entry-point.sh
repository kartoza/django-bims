#!/usr/bin/env bash

# Run database migrations
echo "Run database migrations"
python manage.py makemigrations --noinput --merge
python manage.py migrate --noinput

# Run gruntserver
echo "Run gruntserver"
python manage.py gruntserver

# Run collectstatic
echo "Run collectstatic"
python manage.py collectstatic --noinput -i geoexplorer

# Run as bash entrypoint
exec "$@"
