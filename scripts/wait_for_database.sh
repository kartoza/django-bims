#!/usr/bin/env bash
set -eu

echo "Waiting for databases..."

until PGPASSWORD=$DATABASE_PASSWORD psql -d $DATABASE_NAME -U $DATABASE_USERNAME -h $DATABASE_HOST -l;
do
    sleep 1m
done

echo "Database is ready..."