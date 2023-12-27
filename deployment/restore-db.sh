#!/bin/bash
# Wait for the PostgreSQL server to start
echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h db-restore -p 5432 -U ${POSTGRES_USER}; do
    sleep 1
done
echo "PostgreSQL started."

# Revoke connections and terminate backends
su - postgres -c "psql gis -f /revoke.sql"

# Sleep for a short time to ensure that the sessions are terminated
sleep 2

# Drop the database
su - postgres -c "psql -c 'DROP DATABASE IF EXISTS gis;'"

su - postgres -c "createdb -O docker gis"
su - postgres -c 'pg_restore -d gis /backups/latest.dmp'
