#!/usr/bin/env bash

# Run database migrations
echo "Run database migrations"
python manage.py makemigrations --noinput --merge
python manage.py migrate --noinput

# Run collectstatic
echo "Run collectstatic"
python manage.py collectstatic --noinput -i geonode -i geoexplorer -i geonode_generic -i js -i lib

# Run as bash entrypoint
exec "$@"
