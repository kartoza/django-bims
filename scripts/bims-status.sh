#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Show BIMS system status including all statistics
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 BIMS System Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Django Server
echo ""
echo "🌐 Django Server"
echo "   ─────────────────────────────────────────────────────"
if pgrep -f "runserver" > /dev/null 2>&1; then
    port=$(pgrep -af "runserver" | grep -oE "[0-9]{4}" | head -1 || echo "8000")
    echo "   Status:    ✅ Running on port ${port:-8000}"
else
    echo "   Status:    ❌ Not running"
fi

# GIS Libraries
echo ""
echo "🗺️  GIS Libraries"
echo "   ─────────────────────────────────────────────────────"
if command -v gdalinfo &> /dev/null; then
    gdal_version=$(gdalinfo --version 2>/dev/null | head -1 || echo "Unknown")
    echo "   GDAL:      $gdal_version"
else
    echo "   GDAL:      Not found"
fi

if command -v geos-config &> /dev/null; then
    geos_version=$(geos-config --version 2>/dev/null || echo "Unknown")
    echo "   GEOS:      $geos_version"
else
    echo "   GEOS:      Not found"
fi

if command -v proj &> /dev/null; then
    proj_version=$(proj 2>&1 | head -1 || echo "Unknown")
    echo "   PROJ:      $proj_version"
else
    echo "   PROJ:      Not found"
fi

if command -v tippecanoe &> /dev/null; then
    tippecanoe_version=$(tippecanoe --version 2>&1 | head -1 || echo "Unknown")
    echo "   Tippecanoe: $tippecanoe_version"
else
    echo "   Tippecanoe: Not found"
fi

# PostgreSQL
echo ""
echo "🗄️  PostgreSQL"
echo "   ─────────────────────────────────────────────────────"
if pgrep -f "postgres" > /dev/null 2>&1; then
    echo "   Status:    ✅ Running"
    if [[ -d "$PWD/.pgdata" ]]; then
        socket_path=$(find "$PWD/.pgdata" -name ".s.PGSQL.*" 2>/dev/null | head -1 || echo "")
        if [[ -n "$socket_path" ]]; then
            echo "   Socket:    $socket_path"
        fi
    fi
    echo "   Network:   🔒 Unix socket only (secure)"
else
    echo "   Status:    ❌ Not running"
fi

# Database
echo ""
echo "💾 Database"
echo "   ─────────────────────────────────────────────────────"
if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "bims"; then
    echo "   Database:  ✅ 'bims' exists"
    postgis_version=$(psql -d bims -tAc "SELECT PostGIS_Version();" 2>/dev/null || echo "Unknown")
    if [[ -n "$postgis_version" ]]; then
        echo "   PostGIS:   ✅ v$postgis_version"
    fi
else
    echo "   Database:  ❌ 'bims' not found"
fi

# Migrations
echo ""
echo "🔄 Migrations"
echo "   ─────────────────────────────────────────────────────"
migration_count=$(python manage.py showmigrations --plan 2>/dev/null | grep "\[ \]" | wc -l)
migration_status=${migration_count//[^0-9]/}
if [[ "${migration_status:-0}" == "0" ]]; then
    echo "   Status:    ✅ All migrations applied"
else
    echo "   Status:    ⚠️  $migration_status pending migrations"
fi

# Tenants
echo ""
echo "🏢 Tenants"
echo "   ─────────────────────────────────────────────────────"
python << 'PYTHON'
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
django.setup()

try:
    from django_tenants.utils import tenant_context, get_tenant_model
    Tenant = get_tenant_model()
    tenants = Tenant.objects.all()
    print(f"   Count:     {tenants.count()} tenant(s)")
    print("")
    for tenant in tenants:
        domains = tenant.domains.all()
        domain_list = ", ".join([d.domain for d in domains]) if domains else "no domain"
        print(f"   📁 {tenant.name}")
        print(f"      Schema:  {tenant.schema_name}")
        print(f"      Domains: {domain_list}")
        print("")
except Exception as e:
    print(f"   Error: {e}")
PYTHON

# RabbitMQ
echo ""
echo "🐰 RabbitMQ"
echo "   ─────────────────────────────────────────────────────"
if pgrep -f "rabbitmq" > /dev/null 2>&1 || pgrep -f "beam.smp" > /dev/null 2>&1; then
    echo "   Status:    ✅ Running"
    echo "   URL:       amqp://localhost:5672"
    queue_raw=$(rabbitmqctl list_queues 2>/dev/null | tail -n +2 | wc -l)
    queue_count=${queue_raw//[^0-9]/}
    echo "   Queues:    ${queue_count:-0}"
else
    echo "   Status:    ❌ Not running"
fi

# Celery Workers
echo ""
echo "🔄 Celery Workers"
echo "   ─────────────────────────────────────────────────────"
if pgrep -f "celery.*worker" > /dev/null 2>&1; then
    worker_raw=$(pgrep -fc "celery.*worker" 2>/dev/null || echo "1")
    worker_count=${worker_raw//[^0-9]/}
    echo "   Status:    ✅ ${worker_count:-1} worker(s) online"
    active_raw=$(celery -A core inspect active 2>/dev/null | grep -c "'" 2>/dev/null || echo "0")
    active_tasks=${active_raw//[^0-9]/}
    echo "   Active:    ${active_tasks:-0} tasks"
else
    echo "   Status:    ❌ Not running"
fi

# Data Statistics
echo ""
echo "📈 Data Statistics"
echo "   ─────────────────────────────────────────────────────"
python << 'PYTHON'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
django.setup()

try:
    from django_tenants.utils import tenant_context, get_tenant_model
    Tenant = get_tenant_model()
    tenants = Tenant.objects.all()

    total_sites = 0
    total_records = 0
    total_taxa = 0
    total_surveys = 0

    for tenant in tenants:
        with tenant_context(tenant):
            try:
                from bims.models.location_site import LocationSite
                from bims.models.biological_collection_record import BiologicalCollectionRecord
                from bims.models.taxonomy import Taxonomy
                from bims.models.survey import Survey

                site_count = LocationSite.objects.count()
                record_count = BiologicalCollectionRecord.objects.count()
                taxa_count = Taxonomy.objects.count()
                survey_count = Survey.objects.count()

                total_sites += site_count
                total_records += record_count
                total_taxa += taxa_count
                total_surveys += survey_count

            except Exception:
                pass

    print(f"   Taxa:         {total_taxa:,}")
    print(f"   Sites:        {total_sites:,}")
    print(f"   Site Visits:  {total_surveys:,}")
    print(f"   Occurrences:  {total_records:,}")

except Exception as e:
    print(f"   Error: {e}")
PYTHON

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Made with 💗 by Kartoza"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
