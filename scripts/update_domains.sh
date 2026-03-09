#!/usr/bin/env bash
set -euo pipefail

# --- Config -------------------------------------------------------------------
DB_CONTAINER="${DB_CONTAINER:-bims_staging_db}"
DJANGO_CONTAINER="${DJANGO_CONTAINER:-bims_staging_uwsgi}"

# Load credentials from .env file
ENV_FILE="$(dirname "$0")/../deployment/.env"

if [[ -f "$ENV_FILE" ]]; then
  # Source the .env file to get credentials
  set -a
  source "$ENV_FILE"
  set +a
fi

DB_NAME="${POSTGRES_DBNAME:-app}"
DB_USER="${POSTGRES_USER:-docker}"
DB_PASS="${POSTGRES_PASS:-docker}"
PGHOST_IN_CONTAINER="${PGHOST_IN_CONTAINER:-localhost}"
PGPORT_IN_CONTAINER="${PGPORT_IN_CONTAINER:-5432}"

SQL_FILE="update-staging-domains.sql"

# --- Helpers ------------------------------------------------------------------
die(){ echo "Error: $*" >&2; exit 1; }

# --- Check if SQL file exists -------------------------------------------------
[[ -f "$SQL_FILE" ]] || die "SQL file not found: $SQL_FILE"

# --- Copy SQL file into container ---------------------------------------------
echo "Copying SQL file to container..."
docker cp "$SQL_FILE" "${DB_CONTAINER}:/tmp/${SQL_FILE}"

# --- Execute SQL file ---------------------------------------------------------
echo "Updating domains in database ${DB_NAME}..."
docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
  psql -h "$PGHOST_IN_CONTAINER" -p "$PGPORT_IN_CONTAINER" \
       -U "$DB_USER" -d "$DB_NAME" \
       -f "/tmp/${SQL_FILE}"

# --- Cleanup ------------------------------------------------------------------
echo "Cleaning up..."
docker exec "$DB_CONTAINER" rm -f "/tmp/${SQL_FILE}"

# --- Fix duplicate content types ----------------------------------------------
echo "Fixing duplicate content types..."
docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
  psql -h "$PGHOST_IN_CONTAINER" -p "$PGPORT_IN_CONTAINER" \
       -U "$DB_USER" -d "$DB_NAME" \
       -c "DELETE FROM django_content_type
           WHERE id NOT IN (
             SELECT MIN(id)
             FROM django_content_type
             GROUP BY app_label, model
           );"

# --- Remove all harvest schedules for all tenants ----------------------------
echo "Removing all harvest schedules for all tenants..."
docker exec "$DJANGO_CONTAINER" python manage.py shell -c "
from django_tenants.utils import get_tenant_model, schema_context
from bims.models.harvest_schedule import HarvestSchedule

TenantModel = get_tenant_model()
for tenant in TenantModel.objects.exclude(schema_name='public'):
    with schema_context(tenant.schema_name):
        count = HarvestSchedule.objects.count()
        if count:
            HarvestSchedule.objects.all().delete()
            print(f'Deleted {count} harvest schedule(s) from {tenant.schema_name}')
        else:
            print(f'No harvest schedules in {tenant.schema_name}')
"

# --- Run migrations -----------------------------------------------------------
echo "Running migrations in ${DJANGO_CONTAINER}..."
docker exec "$DJANGO_CONTAINER" python manage.py migrate

echo "✅ Domain updates completed successfully!"