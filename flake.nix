# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
#
# Nix Flake for Django BIMS Development Environment
# All Python dependencies are sourced from nixpkgs + custom derivations
# No pip/venv required - pure Nix environment
#
# Made with love by Kartoza | https://kartoza.com
{
  description = "NixOS developer environment for Django BIMS.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # Import the custom Python packages overlay
        customPythonOverlay = import ./nix/overlay.nix;

        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
          };
          overlays = [ customPythonOverlay ];
        };

        # PostgreSQL with PostGIS
        postgresWithPostGIS = pkgs.postgresql_16.withPackages (ps: [
          ps.postgis
          ps.pgrouting
        ]);

        # =======================================================================
        # Python packages - ALL from nixpkgs + custom derivations (no pip)
        # =======================================================================
        pythonPkgs = pkgs.python312.withPackages (ps: with ps; [
          # Core - Django 6 from overlay (overrides nixpkgs django)
          django
          djangorestframework
          django-allauth
          django-extensions
          django-filter
          django-guardian
          django-cors-headers
          django-crispy-forms
          django-taggit

          # Django packages from nixpkgs
          django-model-utils
          django-prometheus
          django-json-widget
          django-webpack-loader
          django-autocomplete-light
          dj-database-url
          django-tenants
          django-celery-results
          django-celery-beat
          django-polymorphic
          django-modeltranslation
          django-mptt
          django-treebeard
          django-debug-toolbar
          tenant-schemas-celery
          django-cryptography-5  # Django 5/6 compatible fork
          django-js-asset

          # Django packages from custom derivations
          cloudnativegis
          django-admin-inline-paginator
          django-admin-rangefilter
          django-braces
          django-ckeditor
          django-colorfield
          django-contact-us
          django-easy-audit
          django-forms-bootstrap
          django-grappelli
          django-imagekit
          django-invitations
          django-modelsdoc
          django-ordered-model
          django-pipeline
          django-preferences
          django-role-permissions
          django-uuid-upload-path
          djangorestframework-gis
          djangorestframework-guardian
          dj-pagination
          geonode-oauth-toolkit

          # Database
          psycopg2

          # Caching & Queue
          python-memcached
          pymemcache
          redis
          celery
          pika

          # Scientific
          pandas
          numpy
          openpyxl
          geopandas
          scipy
          bibtexparser
          habanero
          eutils
          pygbif
          python-dwca-reader

          # GIS
          gdal
          pyproj
          shapely
          fiona
          geoalchemy2
          geopy
          pyshp

          # Image
          pillow
          pilkit
          django-appconf
          reportlab
          sorl-thumbnail
          svglib

          # HTTP
          requests
          requests-cache
          httpx
          urllib3
          service-identity

          # Serialization
          simplejson
          pyyaml
          toml

          # Auth
          pyjwt
          oauthlib

          # Parsing
          lxml
          beautifulsoup4
          markdown
          markupsafe

          # Utils
          pytz
          python-dateutil
          click
          mock
          importlib-metadata
          packaging
          typing-extensions
          pycurl
          appdirs
          geojson
          matplotlib

          # API
          drf-nested-routers
          drf-yasg

          # Monitoring
          sentry-sdk
          prometheus-client

          # Dev tools
          pip
          setuptools
          wheel
          pytest
          pytest-django
          pytest-cov
          pytest-xdist
          factory-boy
          faker
          black
          isort
          flake8
          pylint
          pylint-django
          mypy
          bandit
          debugpy
          watchdog
          ipython
          ipdb

          # Testing
          selenium

          # GitHub
          pygithub
        ]);

        # Node.js CLI tools from nixpkgs
        nodePkgs = with pkgs.nodePackages; [ eslint prettier typescript ];

        # =======================================================================
        # Scripts - All use $PWD for runtime paths, no venv needed
        # =======================================================================

        npmInstallScript = pkgs.writeShellScriptBin "bims-npm-install" ''
          #!/usr/bin/env bash
          set -euo pipefail
          cd bims
          if [ ! -d "node_modules" ] || [ ! -f "node_modules/.npm-installed" ]; then
            echo "📦 Installing npm packages..."
            npm install --legacy-peer-deps
            touch node_modules/.npm-installed
            echo "✅ Done"
          else
            echo "✅ npm packages already installed"
          fi
        '';

        webpackBuildScript = pkgs.writeShellScriptBin "bims-webpack-build" ''
          #!/usr/bin/env bash
          set -euo pipefail
          cd bims
          [ ! -d "node_modules" ] && bims-npm-install
          echo "🔨 Building frontend..."
          npx webpack --mode=development
          echo "✅ Done"
        '';

        webpackWatchScript = pkgs.writeShellScriptBin "bims-webpack-watch" ''
          #!/usr/bin/env bash
          set -euo pipefail
          cd bims
          [ ! -d "node_modules" ] && bims-npm-install
          echo "👀 Watching frontend..."
          npx webpack --mode=development --watch
        '';

        webpackProdScript = pkgs.writeShellScriptBin "bims-webpack-prod" ''
          #!/usr/bin/env bash
          set -euo pipefail
          cd bims
          [ ! -d "node_modules" ] && bims-npm-install
          echo "📦 Building frontend for production..."
          npx webpack --mode=production
          echo "✅ Done"
        '';

        startPostgresScript = pkgs.writeShellScriptBin "bims-pg-start" ''
          #!/usr/bin/env bash
          set -euo pipefail
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}

          if [ ! -d "$PGDATA" ]; then
            echo "🗄️  Initializing PostgreSQL..."
            ${postgresWithPostGIS}/bin/initdb -D "$PGDATA" --auth=trust --no-locale --encoding=UTF8
            cat >> "$PGDATA/postgresql.conf" << EOF
          # Only listen on Unix socket, no TCP (security)
          listen_addresses = ''''
          port = $PGPORT
          unix_socket_directories = '$PGDATA'
          EOF
          fi

          if [ -f "$PGDATA/postmaster.pid" ]; then
            echo "✅ PostgreSQL already running"
            exit 0
          fi

          echo "🚀 Starting PostgreSQL..."
          ${postgresWithPostGIS}/bin/pg_ctl -D "$PGDATA" -l "$PGDATA/postgresql.log" -o "-k $PGDATA" start

          for i in {1..30}; do
            ${postgresWithPostGIS}/bin/pg_isready -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1 && break
            sleep 0.5
          done

          if ! ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -lqt | cut -d \| -f 1 | grep -qw "bims"; then
            echo "📦 Creating database..."
            ${postgresWithPostGIS}/bin/createdb -h "$PGDATA" -p "$PGPORT" "bims"
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "bims" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "bims" -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "bims" -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"
          fi
          echo "✅ PostgreSQL running (socket: $PGDATA)"
        '';

        stopPostgresScript = pkgs.writeShellScriptBin "bims-pg-stop" ''
          #!/usr/bin/env bash
          PGDATA="$PWD/.pgdata"
          if [ -f "$PGDATA/postmaster.pid" ]; then
            echo "🛑 Stopping PostgreSQL..."
            ${postgresWithPostGIS}/bin/pg_ctl -D "$PGDATA" stop -m fast
            echo "✅ Stopped"
          else
            echo "ℹ️  Not running"
          fi
        '';

        pgStatusScript = pkgs.writeShellScriptBin "bims-pg-status" ''
          #!/usr/bin/env bash
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}
          if ${postgresWithPostGIS}/bin/pg_isready -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1; then
            echo "✅ PostgreSQL running on port $PGPORT"
          else
            echo "❌ PostgreSQL not running"
          fi
        '';

        psqlScript = pkgs.writeShellScriptBin "bims-psql" ''
          #!/usr/bin/env bash
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}
          ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "''${1:-bims}" "''${@:2}"
        '';

        djangoRunserverScript = pkgs.writeShellScriptBin "bims-runserver" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py runserver "''${1:-0.0.0.0:8000}"
        '';

        djangoMigrateScript = pkgs.writeShellScriptBin "bims-migrate" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py migrate "$@"
        '';

        djangoMakemigrationsScript = pkgs.writeShellScriptBin "bims-makemigrations" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py makemigrations "$@"
        '';

        djangoShellScript = pkgs.writeShellScriptBin "bims-shell" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py shell_plus "$@" 2>/dev/null || python manage.py shell "$@"
        '';

        djangoCollectstaticScript = pkgs.writeShellScriptBin "bims-collectstatic" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py collectstatic --noinput "$@"
        '';

        djangoCreateSuperuserScript = pkgs.writeShellScriptBin "bims-createsuperuser" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          SCHEMA="''${1:-}"
          USERNAME="''${2:-}"
          EMAIL="''${3:-}"
          PASSWORD="''${4:-}"

          # Non-interactive mode if all args provided
          if [ -n "$SCHEMA" ] && [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
            EMAIL="''${EMAIL:-$USERNAME@localhost}"
            python << EOF
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
import django
django.setup()

from django.db import connection
from tenants.models import Client
from django.contrib.auth import get_user_model

tenant = Client.objects.get(schema_name='$SCHEMA')
connection.set_tenant(tenant)

User = get_user_model()
if User.objects.filter(username='$USERNAME').exists():
    print(f"ℹ️  User '$USERNAME' already exists in tenant '$SCHEMA'")
else:
    User.objects.create_superuser('$USERNAME', '$EMAIL', '$PASSWORD')
    print(f"✅ Created superuser '$USERNAME' in tenant '$SCHEMA'")
EOF
            exit 0
          fi

          # Interactive mode
          echo ""
          echo "Usage: bims-createsuperuser [schema] [username] [email] [password]"
          echo ""
          echo "Interactive mode - select a tenant:"
          echo "─────────────────────────────────────────────────────"

          TENANTS=$(python << 'EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
import django
django.setup()
from tenants.models import Client
for i, t in enumerate(Client.objects.all(), 1):
    print(f"{i}) {t.name} (schema: {t.schema_name})")
EOF
)
          echo "$TENANTS"
          echo ""

          read -p "Select tenant number: " TENANT_NUM

          SCHEMA=$(python << EOF
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
import django
django.setup()
from tenants.models import Client
tenants = list(Client.objects.all())
idx = int('$TENANT_NUM') - 1
if 0 <= idx < len(tenants):
    print(tenants[idx].schema_name)
else:
    print("")
EOF
)

          if [ -z "$SCHEMA" ]; then
            echo "❌ Invalid tenant selection"
            exit 1
          fi

          echo ""
          echo "Creating superuser in tenant: $SCHEMA"
          echo "─────────────────────────────────────────────────────"
          python manage.py tenant_command createsuperuser --schema="$SCHEMA"
        '';

        djangoResetPasswordScript = pkgs.writeShellScriptBin "bims-resetpwd" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          USERNAME="''${1:-}"

          if [ -z "$USERNAME" ]; then
            echo "Usage: bims-resetpwd <username> [new_password]"
            echo ""
            echo "If no password provided, you'll be prompted to enter one."
            echo ""
            echo "Examples:"
            echo "  bims-resetpwd admin"
            echo "  bims-resetpwd admin newpassword123"
            exit 1
          fi

          # Get tenant selection
          echo ""
          echo "Available tenants:"
          echo "─────────────────────────────────────────────────────"

          TENANTS=$(python << 'EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
import django
django.setup()
from tenants.models import Client
for i, t in enumerate(Client.objects.all(), 1):
    print(f"{i}) {t.name} (schema: {t.schema_name})")
EOF
)
          echo "$TENANTS"
          echo ""

          read -p "Select tenant number: " TENANT_NUM

          SCHEMA=$(python << EOF
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
import django
django.setup()
from tenants.models import Client
tenants = list(Client.objects.all())
idx = int('$TENANT_NUM') - 1
if 0 <= idx < len(tenants):
    print(tenants[idx].schema_name)
else:
    print("")
EOF
)

          if [ -z "$SCHEMA" ]; then
            echo "❌ Invalid tenant selection"
            exit 1
          fi

          PASSWORD="''${2:-}"

          if [ -z "$PASSWORD" ]; then
            # Interactive mode - use Django's changepassword with tenant
            echo ""
            echo "Resetting password in tenant: $SCHEMA"
            echo "─────────────────────────────────────────────────────"
            python manage.py tenant_command changepassword --schema="$SCHEMA" "$USERNAME"
          else
            # Non-interactive mode
            python << EOF
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
import django
django.setup()

from django.db import connection
from tenants.models import Client
from django.contrib.auth import get_user_model

# Switch to tenant schema
tenant = Client.objects.get(schema_name='$SCHEMA')
connection.set_tenant(tenant)

User = get_user_model()

try:
    user = User.objects.get(username='$USERNAME')
    user.set_password('$PASSWORD')
    user.save()
    print(f"✅ Password reset for user '$USERNAME' in tenant '$SCHEMA'")
except User.DoesNotExist:
    print(f"❌ User '$USERNAME' not found in tenant '$SCHEMA'")
    exit(1)
EOF
          fi
        '';

        djangoTestScript = pkgs.writeShellScriptBin "bims-test" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.test}"
          python manage.py test "''${@:-bims}"
        '';

        # RabbitMQ management scripts
        rabbitmqStartScript = pkgs.writeShellScriptBin "bims-rabbitmq-start" ''
          #!/usr/bin/env bash
          set -euo pipefail
          RABBITMQ_DATA="$PWD/.rabbitmq"
          mkdir -p "$RABBITMQ_DATA"

          export RABBITMQ_MNESIA_BASE="$RABBITMQ_DATA/mnesia"
          export RABBITMQ_LOG_BASE="$RABBITMQ_DATA/log"
          export RABBITMQ_NODENAME="rabbit@localhost"

          if ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" status > /dev/null 2>&1; then
            echo "✅ RabbitMQ already running"
          else
            echo "🐰 Starting RabbitMQ..."
            mkdir -p "$RABBITMQ_MNESIA_BASE" "$RABBITMQ_LOG_BASE"
            ${pkgs.rabbitmq-server}/bin/rabbitmq-server -detached

            # Wait for startup
            for i in {1..30}; do
              ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" status > /dev/null 2>&1 && break
              sleep 1
            done

            if ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" status > /dev/null 2>&1; then
              echo "✅ RabbitMQ running on amqp://localhost:5672"
            else
              echo "❌ Failed to start RabbitMQ"
              exit 1
            fi
          fi
        '';

        rabbitmqStopScript = pkgs.writeShellScriptBin "bims-rabbitmq-stop" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export RABBITMQ_NODENAME="rabbit@localhost"

          if ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" status > /dev/null 2>&1; then
            echo "🛑 Stopping RabbitMQ..."
            ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" stop
            echo "✅ Stopped"
          else
            echo "ℹ️  RabbitMQ not running"
          fi
        '';

        rabbitmqStatusScript = pkgs.writeShellScriptBin "bims-rabbitmq-status" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export RABBITMQ_NODENAME="rabbit@localhost"

          if ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" status > /dev/null 2>&1; then
            echo "✅ RabbitMQ running"
            ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" list_queues 2>/dev/null || true
          else
            echo "❌ RabbitMQ not running"
            echo "   Start with: bims-rabbitmq-start"
          fi
        '';

        celeryWorkerScript = pkgs.writeShellScriptBin "bims-celery-worker" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          LOG_LEVEL="''${2:-DEBUG}"
          echo "🔄 Starting Celery worker..."
          echo "   Queues: ''${1:-celery,update,search,geocontext}"
          echo "   Log level: $LOG_LEVEL"
          celery -A bims worker \
            -l "$LOG_LEVEL" \
            -Q "''${1:-celery,update,search,geocontext}" \
            -E
        '';

        celeryBeatScript = pkgs.writeShellScriptBin "bims-celery-beat" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          LOG_LEVEL="''${1:-DEBUG}"
          echo "⏰ Starting Celery beat scheduler..."
          echo "   Log level: $LOG_LEVEL"
          celery -A bims beat -l "$LOG_LEVEL"
        '';

        celeryStatusScript = pkgs.writeShellScriptBin "bims-celery-status" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          echo "Celery Status:"
          echo "─────────────────────────────────────────────────────"
          celery -A bims inspect active 2>/dev/null || echo "❌ No workers responding"
        '';

        # Migration helper scripts
        showMigrationsScript = pkgs.writeShellScriptBin "bims-showmigrations" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py showmigrations "$@"
        '';

        migrateCheckScript = pkgs.writeShellScriptBin "bims-migrate-check" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py migrate --check "$@"
        '';

        migratePlanScript = pkgs.writeShellScriptBin "bims-migrate-plan" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          python manage.py migrate --plan "$@"
        '';

        sqlMigrateScript = pkgs.writeShellScriptBin "bims-sqlmigrate" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          if [ $# -lt 2 ]; then
            echo "Usage: bims-sqlmigrate <app_label> <migration_name>"
            echo "Example: bims-sqlmigrate bims 0001"
            exit 1
          fi
          python manage.py sqlmigrate "$@"
        '';

        squashMigrationsScript = pkgs.writeShellScriptBin "bims-squashmigrations" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          if [ $# -lt 2 ]; then
            echo "Usage: bims-squashmigrations <app_label> <start_migration> [end_migration]"
            echo "Example: bims-squashmigrations bims 0001 0010"
            exit 1
          fi
          python manage.py squashmigrations "$@"
        '';

        migrateFakeScript = pkgs.writeShellScriptBin "bims-migrate-fake" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          echo "⚠️  Warning: This will mark migrations as run without executing them!"
          read -p "Continue? [y/N] " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
            python manage.py migrate --fake "$@"
          fi
        '';

        migrateZeroScript = pkgs.writeShellScriptBin "bims-migrate-zero" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          if [ $# -lt 1 ]; then
            echo "Usage: bims-migrate-zero <app_label>"
            echo "Example: bims-migrate-zero bims"
            exit 1
          fi
          echo "⚠️  Warning: This will unapply ALL migrations for $1!"
          read -p "Continue? [y/N] " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
            python manage.py migrate "$1" zero
          fi
        '';

        # Database management scripts
        dbCreateScript = pkgs.writeShellScriptBin "bims-db-create" ''
          #!/usr/bin/env bash
          set -euo pipefail
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}
          DB_NAME="''${1:-bims}"

          echo "📦 Creating database $DB_NAME..."
          ${postgresWithPostGIS}/bin/createdb -h "$PGDATA" -p "$PGPORT" "$DB_NAME" || true
          ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
          ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
          ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;"
          ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;"
          echo "✅ Database $DB_NAME created with PostGIS extensions"
        '';

        dbDropScript = pkgs.writeShellScriptBin "bims-db-drop" ''
          #!/usr/bin/env bash
          set -euo pipefail
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}
          DB_NAME="''${1:-bims}"

          echo "⚠️  Warning: This will permanently delete the database '$DB_NAME'!"
          read -p "Continue? [y/N] " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${postgresWithPostGIS}/bin/dropdb -h "$PGDATA" -p "$PGPORT" --if-exists "$DB_NAME"
            echo "🗑️  Database $DB_NAME dropped"
          else
            echo "Cancelled"
          fi
        '';

        dbResetScript = pkgs.writeShellScriptBin "bims-db-reset" ''
          #!/usr/bin/env bash
          set -euo pipefail
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}
          DB_NAME="''${DATABASE_NAME:-bims}"
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          echo "⚠️  Warning: This will permanently delete and recreate the database '$DB_NAME'!"
          echo "   All data will be lost!"
          read -p "Continue? [y/N] " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Dropping database..."
            ${postgresWithPostGIS}/bin/dropdb -h "$PGDATA" -p "$PGPORT" --if-exists "$DB_NAME"

            echo "📦 Creating database..."
            ${postgresWithPostGIS}/bin/createdb -h "$PGDATA" -p "$PGPORT" "$DB_NAME"
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;"
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;"

            echo "🔄 Running migrations..."
            python manage.py migrate

            echo "✅ Database reset complete!"
          else
            echo "Cancelled"
          fi
        '';

        dbDumpScript = pkgs.writeShellScriptBin "bims-db-dump" ''
          #!/usr/bin/env bash
          set -euo pipefail
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}
          DB_NAME="''${DATABASE_NAME:-bims}"
          DUMP_FILE="''${1:-bims_dump_$(date +%Y%m%d_%H%M%S).sql}"

          echo "📤 Dumping database $DB_NAME to $DUMP_FILE..."
          ${postgresWithPostGIS}/bin/pg_dump -h "$PGDATA" -p "$PGPORT" "$DB_NAME" > "$DUMP_FILE"
          echo "✅ Database dumped to $DUMP_FILE"
        '';

        dbRestoreScript = pkgs.writeShellScriptBin "bims-db-restore" ''
          #!/usr/bin/env bash
          set -euo pipefail
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}
          DB_NAME="''${DATABASE_NAME:-bims}"

          if [ $# -lt 1 ]; then
            echo "Usage: bims-db-restore <dump_file>"
            echo "Example: bims-db-restore bims_dump_20260317.sql"
            exit 1
          fi
          DUMP_FILE="$1"

          if [ ! -f "$DUMP_FILE" ]; then
            echo "❌ File not found: $DUMP_FILE"
            exit 1
          fi

          echo "⚠️  Warning: This will replace the database '$DB_NAME' with the contents of $DUMP_FILE!"
          read -p "Continue? [y/N] " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Dropping existing database..."
            ${postgresWithPostGIS}/bin/dropdb -h "$PGDATA" -p "$PGPORT" --if-exists "$DB_NAME"

            echo "📦 Creating database..."
            ${postgresWithPostGIS}/bin/createdb -h "$PGDATA" -p "$PGPORT" "$DB_NAME"

            echo "📥 Restoring from $DUMP_FILE..."
            ${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -d "$DB_NAME" < "$DUMP_FILE"
            echo "✅ Database restored!"
          else
            echo "Cancelled"
          fi
        '';

        # Tenant management scripts
        tenantCreateScript = pkgs.writeShellScriptBin "bims-tenant-create" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          SCHEMA_NAME="''${1:-}"
          TENANT_NAME="''${2:-}"
          DOMAINS="''${3:-localhost,127.0.0.1}"

          if [ -z "$SCHEMA_NAME" ]; then
            echo "Usage: bims-tenant-create <schema_name> [tenant_name] [domains]"
            echo ""
            echo "Arguments:"
            echo "  schema_name  PostgreSQL schema name (required, e.g., 'dev' or 'staging')"
            echo "  tenant_name  Display name (optional, defaults to schema_name)"
            echo "  domains      Comma-separated domains (optional, defaults to 'localhost,127.0.0.1')"
            echo ""
            echo "Examples:"
            echo "  bims-tenant-create dev"
            echo "  bims-tenant-create dev 'Development Tenant'"
            echo "  bims-tenant-create prod 'Production' 'bims.example.com,www.bims.example.com'"
            exit 1
          fi

          if [ -z "$TENANT_NAME" ]; then
            TENANT_NAME="$SCHEMA_NAME"
          fi

          echo "🏢 Creating tenant '$TENANT_NAME' with schema '$SCHEMA_NAME'..."
          echo "   Domains: $DOMAINS"

          python manage.py shell << EOF
from tenants.models import Client, Domain

# Create or get the tenant
tenant, created = Client.objects.get_or_create(
    schema_name='$SCHEMA_NAME',
    defaults={'name': '$TENANT_NAME'}
)

if created:
    print(f"✅ Created tenant: {tenant.name} (schema: {tenant.schema_name})")
else:
    print(f"ℹ️  Tenant already exists: {tenant.name} (schema: {tenant.schema_name})")

# Create domains
domains = '$DOMAINS'.split(',')
for domain_name in domains:
    domain_name = domain_name.strip()
    if domain_name:
        domain, domain_created = Domain.objects.get_or_create(
            domain=domain_name,
            tenant=tenant,
            defaults={'is_primary': domains.index(domain_name.strip()) == 0}
        )
        if domain_created:
            print(f"✅ Created domain: {domain_name}")
        else:
            print(f"ℹ️  Domain already exists: {domain_name}")

print("")
print("🎉 Tenant setup complete!")
print(f"   Access at: http://{domains[0].strip()}:8000/")
EOF
        '';

        tenantListScript = pkgs.writeShellScriptBin "bims-tenant-list" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          python manage.py shell << 'EOF'
from tenants.models import Client, Domain

print("=" * 60)
print("TENANTS")
print("=" * 60)

for tenant in Client.objects.all():
    domains = Domain.objects.filter(tenant=tenant)
    domain_list = ', '.join([d.domain for d in domains])
    print(f"\n📁 {tenant.name}")
    print(f"   Schema: {tenant.schema_name}")
    print(f"   Domains: {domain_list or '(none)'}")
    print(f"   Created: {tenant.created_on}")
    print(f"   On trial: {tenant.on_trial}")

print("\n" + "=" * 60)
EOF
        '';

        tenantDeleteScript = pkgs.writeShellScriptBin "bims-tenant-delete" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          SCHEMA_NAME="''${1:-}"

          if [ -z "$SCHEMA_NAME" ]; then
            echo "Usage: bims-tenant-delete <schema_name>"
            echo "Example: bims-tenant-delete dev"
            exit 1
          fi

          if [ "$SCHEMA_NAME" = "public" ]; then
            echo "❌ Cannot delete the public schema!"
            exit 1
          fi

          echo "⚠️  Warning: This will permanently delete tenant '$SCHEMA_NAME' and ALL its data!"
          read -p "Continue? [y/N] " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
            python manage.py shell << EOF
from tenants.models import Client, Domain

try:
    tenant = Client.objects.get(schema_name='$SCHEMA_NAME')
    tenant_name = tenant.name

    # Delete domains first
    Domain.objects.filter(tenant=tenant).delete()

    # Delete tenant (this also drops the schema)
    tenant.delete()

    print(f"🗑️  Deleted tenant: {tenant_name} (schema: $SCHEMA_NAME)")
except Client.DoesNotExist:
    print(f"❌ Tenant with schema '$SCHEMA_NAME' not found")
EOF
          else
            echo "Cancelled"
          fi
        '';

        # System status script
        statusScript = pkgs.writeShellScriptBin "bims-status" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}

          echo ""
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo "📊 BIMS System Status"
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo ""

          # Django Server Status
          echo "🌐 Django Server"
          echo "   ─────────────────────────────────────────────────────"
          if ss -tlnp 2>/dev/null | grep -q ":8000 "; then
            echo "   Status:    ✅ Running on port 8000"
          else
            echo "   Status:    🔴 NOT RUNNING"
            echo "   Start:     bims-runserver"
          fi
          echo ""

          # GIS Libraries
          echo "🗺️  GIS Libraries"
          echo "   ─────────────────────────────────────────────────────"
          GDAL_VER=$(gdalinfo --version 2>/dev/null | head -1 || echo "Not found")
          echo "   GDAL:      $GDAL_VER"
          GEOS_VER=$(python -c "from django.contrib.gis.geos import geos_version; print(geos_version().decode())" 2>/dev/null || echo "Not found")
          echo "   GEOS:      $GEOS_VER"
          PROJ_VER=$(proj 2>&1 | head -1 | grep -oP 'Rel\. \K[0-9.]+' || echo "Not found")
          echo "   PROJ:      $PROJ_VER"
          TIPP_VER=$(tippecanoe --version 2>&1 | head -1 || echo "Not found")
          echo "   Tippecanoe: $TIPP_VER"
          echo ""

          # PostgreSQL Status
          echo "🗄️  PostgreSQL"
          echo "   ─────────────────────────────────────────────────────"
          if [ -f "$PGDATA/postmaster.pid" ]; then
            if ${postgresWithPostGIS}/bin/pg_isready -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1; then
              echo "   Status:    ✅ Running"
              echo "   Socket:    $PGDATA/.s.PGSQL.$PGPORT"
              # Check if TCP is disabled
              if ss -tlnp 2>/dev/null | grep -q ":$PGPORT "; then
                echo "   Network:   ⚠️  TCP enabled (less secure)"
              else
                echo "   Network:   🔒 Unix socket only (secure)"
              fi
            else
              echo "   Status:    ⚠️  PID file exists but not responding"
            fi
          else
            echo "   Status:    ❌ Not running"
            echo "   Start with: bims-pg-start"
          fi
          echo ""

          # Database Status
          echo "💾 Database"
          echo "   ─────────────────────────────────────────────────────"
          if ${postgresWithPostGIS}/bin/pg_isready -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1; then
            DB_EXISTS=$(${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -tAc "SELECT 1 FROM pg_database WHERE datname='bims'" postgres 2>/dev/null || echo "")
            if [ "$DB_EXISTS" = "1" ]; then
              echo "   Database:  ✅ 'bims' exists"
              POSTGIS=$(${postgresWithPostGIS}/bin/psql -h "$PGDATA" -p "$PGPORT" -tAc "SELECT extversion FROM pg_extension WHERE extname='postgis'" bims 2>/dev/null || echo "")
              if [ -n "$POSTGIS" ]; then
                echo "   PostGIS:   ✅ v$POSTGIS"
              else
                echo "   PostGIS:   ❌ Not installed"
              fi
            else
              echo "   Database:  ❌ 'bims' does not exist"
              echo "   Create with: bims-db-create"
            fi
          else
            echo "   Database:  ⏸️  Cannot check (PostgreSQL not running)"
          fi
          echo ""

          # Migrations Status
          echo "🔄 Migrations"
          echo "   ─────────────────────────────────────────────────────"
          if ${postgresWithPostGIS}/bin/pg_isready -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1; then
            MIGRATION_CHECK=$(python manage.py migrate --check 2>&1) || true
            if echo "$MIGRATION_CHECK" | grep -q "Starting migration"; then
              echo "   Status:    ✅ All migrations applied"
            else
              UNAPPLIED=$(python manage.py showmigrations --plan 2>/dev/null | grep -c "\[ \]" || echo "0")
              if [ "$UNAPPLIED" -gt 0 ]; then
                echo "   Status:    ⚠️  $UNAPPLIED unapplied migration(s)"
                echo "   Run:       bims-migrate"
              else
                echo "   Status:    ✅ All migrations applied"
              fi
            fi
          else
            echo "   Status:    ⏸️  Cannot check (PostgreSQL not running)"
          fi
          echo ""

          # Tenants Status
          echo "🏢 Tenants"
          echo "   ─────────────────────────────────────────────────────"
          if ${postgresWithPostGIS}/bin/pg_isready -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1; then
            python << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev_local')
import django
django.setup()

from tenants.models import Client, Domain

tenants = Client.objects.all()
if tenants.exists():
    print(f"   Count:     {tenants.count()} tenant(s)")
    print("")
    for tenant in tenants:
        domains = Domain.objects.filter(tenant=tenant)
        domain_list = ', '.join([d.domain for d in domains]) or '(no domains)'
        print(f"   📁 {tenant.name}")
        print(f"      Schema:  {tenant.schema_name}")
        print(f"      Domains: {domain_list}")
        print("")
else:
    print("   Status:    ⚠️  No tenants configured")
    print("   Create:    bims-tenant-create dev 'Development'")
PYEOF
          else
            echo "   Status:    ⏸️  Cannot check (PostgreSQL not running)"
          fi
          echo ""

          # RabbitMQ Status
          echo "🐰 RabbitMQ"
          echo "   ─────────────────────────────────────────────────────"
          export RABBITMQ_NODENAME="rabbit@localhost"
          if ${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" status > /dev/null 2>&1; then
            echo "   Status:    ✅ Running"
            echo "   URL:       amqp://localhost:5672"
            QUEUES=$(${pkgs.rabbitmq-server}/bin/rabbitmqctl -n "$RABBITMQ_NODENAME" list_queues name messages consumers 2>/dev/null | tail -n +2 || echo "")
            if [ -n "$QUEUES" ]; then
              QUEUE_COUNT=$(echo "$QUEUES" | wc -l)
              echo "   Queues:    $QUEUE_COUNT"
            fi
          else
            echo "   Status:    ❌ Not running"
            echo "   Start:     bims-rabbitmq-start"
          fi
          echo ""

          # Celery Status
          echo "🔄 Celery Workers"
          echo "   ─────────────────────────────────────────────────────"
          CELERY_STATUS=$(celery -A bims inspect ping 2>/dev/null || echo "")
          if echo "$CELERY_STATUS" | grep -q "pong"; then
            WORKER_COUNT=$(echo "$CELERY_STATUS" | grep -c "pong" || echo "0")
            echo "   Status:    ✅ $WORKER_COUNT worker(s) online"

            # Get active tasks
            ACTIVE=$(celery -A bims inspect active 2>/dev/null || echo "")
            if echo "$ACTIVE" | grep -q "empty"; then
              echo "   Active:    0 tasks"
            else
              TASK_COUNT=$(echo "$ACTIVE" | grep -E "^\s+\*" | wc -l || echo "0")
              echo "   Active:    $TASK_COUNT task(s)"
            fi

            # Get reserved tasks
            RESERVED=$(celery -A bims inspect reserved 2>/dev/null || echo "")
            if ! echo "$RESERVED" | grep -q "empty"; then
              RESERVED_COUNT=$(echo "$RESERVED" | grep -E "^\s+\*" | wc -l || echo "0")
              if [ "$RESERVED_COUNT" -gt 0 ]; then
                echo "   Reserved:  $RESERVED_COUNT task(s)"
              fi
            fi
          else
            echo "   Status:    ❌ No workers running"
            echo "   Start:     bims-celery-worker"
          fi

          echo ""
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo ""
        '';

        # PMTiles generation script
        pmtilesGenerateScript = pkgs.writeShellScriptBin "bims-pmtiles-generate" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          # Check tippecanoe is available
          if ! command -v tippecanoe &> /dev/null; then
            echo "❌ tippecanoe not found in PATH"
            exit 1
          fi

          echo "🗺️  PMTiles Generation"
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

          # Get available tenants
          TENANTS=$(python -c "
          import django
          django.setup()
          from django.db import connection
          connection.ensure_connection()
          from django_tenants.utils import get_tenant_model
          Tenant = get_tenant_model()
          for t in Tenant.objects.all():
              print(t.schema_name)
          " 2>/dev/null || echo "public")

          echo ""
          echo "Available tenants:"
          echo "$TENANTS" | nl -w2 -s') '
          echo ""
          read -p "Enter tenant schema name (or press Enter for 'public'): " SCHEMA
          SCHEMA=''${SCHEMA:-public}
          echo ""

          # List available layers
          echo "Fetching available layers in schema '$SCHEMA'..."
          python manage.py generate_pmtiles --tenant "$SCHEMA" 2>&1 || true
          echo ""
          read -p "Enter layer ID(s) to generate PMTiles for (space-separated): " LAYER_IDS

          if [ -z "$LAYER_IDS" ]; then
            echo "❌ No layer IDs provided."
            exit 1
          fi

          echo ""
          echo "Generating PMTiles for layer(s): $LAYER_IDS in schema: $SCHEMA"
          echo "─────────────────────────────────────────────────────────────"
          # shellcheck disable=SC2086
          python manage.py generate_pmtiles --tenant "$SCHEMA" --layer-id $LAYER_IDS
          echo ""
          echo "✅ PMTiles generation complete!"
        '';

        # Direct tippecanoe wrapper for custom GeoJSON to PMTiles conversion
        tippecanoeScript = pkgs.writeShellScriptBin "bims-tippecanoe" ''
          #!/usr/bin/env bash
          set -euo pipefail

          if [ $# -lt 2 ]; then
            echo "Usage: bims-tippecanoe <input.geojson> <output.pmtiles> [options]"
            echo ""
            echo "Convert GeoJSON to PMTiles using tippecanoe."
            echo ""
            echo "Examples:"
            echo "  bims-tippecanoe data.geojson tiles.pmtiles"
            echo "  bims-tippecanoe data.geojson tiles.pmtiles -z 14 -Z 8"
            echo ""
            echo "Common options:"
            echo "  -z/--maximum-zoom ZOOM   Maximum zoom level (default: 14)"
            echo "  -Z/--minimum-zoom ZOOM   Minimum zoom level (default: 0)"
            echo "  -l/--layer NAME          Name for the layer (default: from filename)"
            echo "  --drop-densest-as-needed Drop features to fit tile limits"
            echo "  --extend-zooms-if-still-dropping  Add detail if needed"
            echo ""
            tippecanoe --help | head -50
            exit 1
          fi

          INPUT="$1"
          OUTPUT="$2"
          shift 2

          echo "🗺️  Converting GeoJSON to PMTiles"
          echo "   Input:  $INPUT"
          echo "   Output: $OUTPUT"
          echo ""

          tippecanoe -o "$OUTPUT" "$INPUT" "$@"

          echo ""
          echo "✅ PMTiles generated: $OUTPUT"
          ls -lh "$OUTPUT"
        '';

        nginxStartScript = pkgs.writeShellScriptBin "bims-nginx-start" ''
          #!/usr/bin/env bash
          set -euo pipefail
          mkdir -p "$PWD/logs"

          # Generate nginx config at runtime
          cat > "$PWD/logs/nginx.conf" << EOF
          worker_processes 1;
          error_log $PWD/logs/nginx-error.log;
          pid $PWD/logs/nginx.pid;
          daemon off;
          events { worker_connections 1024; }
          http {
            include ${pkgs.nginx}/conf/mime.types;
            default_type application/octet-stream;
            access_log $PWD/logs/nginx-access.log;
            sendfile on;
            keepalive_timeout 65;
            client_max_body_size 100M;
            gzip on;
            upstream django { server 127.0.0.1:8000; }
            server {
              listen 8080;
              server_name localhost;
              location /static { alias $PWD/static; expires 1d; }
              location /media { alias $PWD/media; expires 1d; }
              location / {
                proxy_pass http://django;
                proxy_set_header Host \$host;
                proxy_set_header X-Real-IP \$remote_addr;
                proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto \$scheme;
                proxy_read_timeout 300;
              }
            }
          }
          EOF

          echo "🌐 Starting Nginx on http://localhost:8080..."
          ${pkgs.nginx}/bin/nginx -c "$PWD/logs/nginx.conf"
        '';

        nginxStopScript = pkgs.writeShellScriptBin "bims-nginx-stop" ''
          #!/usr/bin/env bash
          if [ -f "$PWD/logs/nginx.pid" ]; then
            kill $(cat "$PWD/logs/nginx.pid") 2>/dev/null || true
            rm -f "$PWD/logs/nginx.pid"
            echo "✅ Nginx stopped"
          else
            echo "ℹ️  Nginx not running"
          fi
        '';

        devStartScript = pkgs.writeShellScriptBin "bims-dev-start" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

          echo "🚀 Starting BIMS development environment..."

          mkdir -p "$PWD/media" "$PWD/static" "$PWD/logs"

          # Start PostgreSQL
          bims-pg-start

          # Start RabbitMQ
          bims-rabbitmq-start

          if [ ! -f "bims/node_modules/.npm-installed" ]; then
            bims-npm-install
          fi

          if [ ! -f "core/settings/secret.py" ]; then
            echo "🔑 Creating secret.py..."
            SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
            cat > core/settings/secret.py << EOF
          SECRET_KEY = '$SECRET_KEY'
          IUCN_API_KEY = ""
          EOF
          fi

          # Start Celery worker in background
          mkdir -p "$PWD/logs"
          if [ -f "$PWD/logs/celery-worker.pid" ] && kill -0 $(cat "$PWD/logs/celery-worker.pid") 2>/dev/null; then
            echo "✅ Celery worker already running"
          else
            rm -f "$PWD/logs/celery-worker.pid"
            echo "🔄 Starting Celery worker..."
            celery -A bims worker \
              -l DEBUG \
              -Q celery,update,search,geocontext \
              -E \
              --pidfile="$PWD/logs/celery-worker.pid" \
              --logfile="$PWD/logs/celery-worker.log" \
              --detach
          fi

          # Start Celery beat in background
          if [ -f "$PWD/logs/celery-beat.pid" ] && kill -0 $(cat "$PWD/logs/celery-beat.pid") 2>/dev/null; then
            echo "✅ Celery beat already running"
          else
            rm -f "$PWD/logs/celery-beat.pid"
            echo "⏰ Starting Celery beat..."
            celery -A bims beat \
              -l DEBUG \
              --pidfile="$PWD/logs/celery-beat.pid" \
              --logfile="$PWD/logs/celery-beat.log" \
              --detach
          fi

          echo ""
          echo "✅ All services started!"
          echo ""
          echo "   Services running:"
          echo "   • PostgreSQL (socket: .pgdata)"
          echo "   • RabbitMQ (amqp://localhost:5672)"
          echo "   • Celery worker (log: logs/celery-worker.log)"
          echo "   • Celery beat (log: logs/celery-beat.log)"
          echo ""
          echo "   Commands:"
          echo "   bims-runserver     - Django (port 8000)"
          echo "   bims-webpack-watch - Frontend watcher"
          echo "   bims-status        - Check all services"
          echo "   bims-dev-stop      - Stop all services"
        '';

        devStopScript = pkgs.writeShellScriptBin "bims-dev-stop" ''
          #!/usr/bin/env bash
          bims-stop-all
        '';

        # Single command to run everything
        startAllScript = pkgs.writeShellScriptBin "bims-start-all" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          export PGDATA="''${PGDATA:-$PWD/.pgdata}"
          export PGPORT="''${PGPORT:-5432}"
          export PGHOST="$PGDATA"

          echo "🚀 Starting BIMS (all services)..."
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

          mkdir -p "$PWD/media" "$PWD/static" "$PWD/logs"

          # Start PostgreSQL if not running
          if ! ${postgresWithPostGIS}/bin/pg_isready -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1; then
            echo "🗄️  Starting PostgreSQL..."
            bims-pg-start
          else
            echo "🗄️  PostgreSQL: already running"
          fi

          # Start RabbitMQ if not running
          if ! rabbitmqctl status &>/dev/null; then
            echo "🐰 Starting RabbitMQ..."
            bims-rabbitmq-start
          else
            echo "🐰 RabbitMQ: already running"
          fi

          # Create secret.py if missing
          if [ ! -f "core/settings/secret.py" ]; then
            echo "🔑 Creating secret.py..."
            SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
            cat > core/settings/secret.py << EOF
          SECRET_KEY = '$SECRET_KEY'
          IUCN_API_KEY = ""
          EOF
          fi

          # Start Celery worker in background
          if [ -f "$PWD/logs/celery-worker.pid" ] && kill -0 "$(cat "$PWD/logs/celery-worker.pid" 2>/dev/null)" 2>/dev/null; then
            echo "⚙️  Celery worker: already running"
          else
            rm -f "$PWD/logs/celery-worker.pid"
            echo "⚙️  Starting Celery worker..."
            celery -A bims worker \
              -l DEBUG \
              -Q celery,update,search,geocontext \
              -E \
              --pidfile="$PWD/logs/celery-worker.pid" \
              --logfile="$PWD/logs/celery-worker.log" \
              --detach
          fi

          # Start Celery beat in background
          if [ -f "$PWD/logs/celery-beat.pid" ] && kill -0 "$(cat "$PWD/logs/celery-beat.pid" 2>/dev/null)" 2>/dev/null; then
            echo "📅 Celery beat: already running"
          else
            rm -f "$PWD/logs/celery-beat.pid"
            echo "📅 Starting Celery beat..."
            celery -A bims beat \
              -l DEBUG \
              --pidfile="$PWD/logs/celery-beat.pid" \
              --logfile="$PWD/logs/celery-beat.log" \
              --detach
          fi

          echo ""
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo "🌐 Starting Django server on http://localhost:8000"
          echo "   Press Ctrl+C to stop Django (other services keep running)"
          echo "   Use bims-stop-all to stop everything"
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo ""

          python manage.py runserver 0.0.0.0:8000
        '';

        stopAllScript = pkgs.writeShellScriptBin "bims-stop-all" ''
          #!/usr/bin/env bash
          echo "🛑 Stopping all BIMS services..."
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

          # Stop Django runserver (if running)
          DJANGO_PID=$(pgrep -f "python manage.py runserver" 2>/dev/null || true)
          if [ -n "$DJANGO_PID" ]; then
            echo "   🌐 Stopping Django server (PID: $DJANGO_PID)..."
            kill $DJANGO_PID 2>/dev/null || true
          else
            echo "   🌐 Django server: not running"
          fi

          # Stop Nginx
          if [ -f "$PWD/logs/nginx.pid" ]; then
            echo "   🔀 Stopping Nginx..."
            kill $(cat "$PWD/logs/nginx.pid") 2>/dev/null || true
            rm -f "$PWD/logs/nginx.pid"
          else
            echo "   🔀 Nginx: not running"
          fi

          # Stop Celery workers (all)
          CELERY_PIDS=$(pgrep -f "celery.*worker" 2>/dev/null || true)
          if [ -n "$CELERY_PIDS" ]; then
            echo "   ⚙️  Stopping Celery workers..."
            echo "$CELERY_PIDS" | xargs kill 2>/dev/null || true
          fi
          if [ -f "$PWD/logs/celery-worker.pid" ]; then
            kill "$(cat "$PWD/logs/celery-worker.pid" 2>/dev/null)" 2>/dev/null || true
            rm -f "$PWD/logs/celery-worker.pid"
          fi
          if [ -z "$CELERY_PIDS" ] && [ ! -f "$PWD/logs/celery-worker.pid" ]; then
            echo "   ⚙️  Celery workers: not running"
          fi

          # Stop Celery beat
          BEAT_PID=$(pgrep -f "celery.*beat" 2>/dev/null || true)
          if [ -n "$BEAT_PID" ]; then
            echo "   📅 Stopping Celery beat..."
            kill $BEAT_PID 2>/dev/null || true
          fi
          if [ -f "$PWD/logs/celery-beat.pid" ]; then
            kill "$(cat "$PWD/logs/celery-beat.pid" 2>/dev/null)" 2>/dev/null || true
            rm -f "$PWD/logs/celery-beat.pid"
          fi
          if [ -z "$BEAT_PID" ] && [ ! -f "$PWD/logs/celery-beat.pid" ]; then
            echo "   📅 Celery beat: not running"
          fi

          # Stop RabbitMQ
          if rabbitmqctl status &>/dev/null; then
            echo "   🐰 Stopping RabbitMQ..."
            rabbitmqctl stop 2>/dev/null || true
          else
            echo "   🐰 RabbitMQ: not running"
          fi

          # Stop PostgreSQL
          if [ -f "$PGDATA/postmaster.pid" ]; then
            echo "   🗄️  Stopping PostgreSQL..."
            ${postgresWithPostGIS}/bin/pg_ctl -D "$PGDATA" stop -m fast 2>/dev/null || true
          else
            echo "   🗄️  PostgreSQL: not running"
          fi

          # Stop webpack watch (if running)
          WEBPACK_PID=$(pgrep -f "webpack.*watch" 2>/dev/null || true)
          if [ -n "$WEBPACK_PID" ]; then
            echo "   📦 Stopping Webpack watch..."
            kill $WEBPACK_PID 2>/dev/null || true
          else
            echo "   📦 Webpack watch: not running"
          fi

          echo ""
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo "✅ All services stopped"
        '';

        lintScript = pkgs.writeShellScriptBin "bims-lint" ''
          #!/usr/bin/env bash
          echo "🔍 flake8..."
          flake8 --config .flake8 bims core || true
          echo "🔍 pylint..."
          pylint --rcfile=.pylintrc bims core --exit-zero || true
        '';

        formatScript = pkgs.writeShellScriptBin "bims-format" ''
          #!/usr/bin/env bash
          echo "🎨 black..."
          black bims core
          echo "🎨 isort..."
          isort bims core
        '';

        securityCheckScript = pkgs.writeShellScriptBin "bims-security-check" ''
          #!/usr/bin/env bash
          echo "🔒 bandit..."
          bandit -r bims core -ll -x ".venv,venv,migrations" || true
          echo "🔒 bearer..."
          ${pkgs.bearer}/bin/bearer scan . --quiet || true
        '';

        debugScript = pkgs.writeShellScriptBin "bims-debug" ''
          #!/usr/bin/env bash
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          echo "🐛 debugpy on port 5678..."
          python -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000
        '';

        precommitInstallScript = pkgs.writeShellScriptBin "bims-precommit-install" ''
          #!/usr/bin/env bash
          ${pkgs.pre-commit}/bin/pre-commit install
          echo "✅ Pre-commit hooks installed"
        '';

        precommitRunScript = pkgs.writeShellScriptBin "bims-precommit-run" ''
          #!/usr/bin/env bash
          ${pkgs.pre-commit}/bin/pre-commit run --all-files
        '';

        reuseCheckScript = pkgs.writeShellScriptBin "bims-reuse-check" ''
          #!/usr/bin/env bash
          ${pkgs.reuse}/bin/reuse lint
        '';

        packageStatusScript = pkgs.writeShellScriptBin "bims-package-status" ''
          #!/usr/bin/env bash
          echo "📦 Package Status (Pure Nix - No venv)"
          echo "======================================="
          python -c "import django; print(f'Django: {django.__version__}')" 2>/dev/null || echo "Django: not available"
          python -c "import pandas; print(f'Pandas: {pandas.__version__}')" 2>/dev/null || echo "Pandas: not available"
          python -c "import osgeo.gdal as gdal; print(f'GDAL: {gdal.__version__}')" 2>/dev/null || echo "GDAL: not available"
          python -c "import rolepermissions; print('rolepermissions: ✅')" 2>/dev/null || echo "rolepermissions: ❌"
          echo ""
          [ -f "bims/node_modules/.npm-installed" ] && echo "npm packages: ✅" || echo "npm packages: ❌ (run bims-npm-install)"
        '';

        cleanVenvScript = pkgs.writeShellScriptBin "bims-clean-venv" ''
          #!/usr/bin/env bash
          echo "🧹 Removing old venv (no longer needed with pure Nix)..."
          rm -rf .venv
          echo "✅ Done"
        '';

      in
      {
        checks = { };

        devShells.default = pkgs.mkShell {
          packages = [
            pythonPkgs
            postgresWithPostGIS
            pkgs.nginx
            pkgs.rabbitmq-server
            pkgs.redis
            pkgs.nodejs_20
            pkgs.nodePackages.npm
          ] ++ nodePkgs ++ [
            pkgs.gdal
            pkgs.tippecanoe
            pkgs.gcc
            pkgs.gnumake
            pkgs.pkg-config
            pkgs.openssl
            pkgs.libffi
            pkgs.zlib
            pkgs.libjpeg
            pkgs.libpng
            pkgs.freetype
            pkgs.git
            pkgs.gh
            pkgs.jq
            pkgs.curl
            pkgs.wget
            pkgs.httpie
            pkgs.pre-commit
            pkgs.shellcheck
            pkgs.shfmt
            pkgs.nixfmt-classic
            pkgs.yamllint
            pkgs.markdownlint-cli
            pkgs.actionlint
            pkgs.codespell
            pkgs.bearer
            pkgs.trivy
            pkgs.reuse
            pkgs.glow
            pkgs.gum
            pkgs.fzf
            pkgs.ripgrep
            pkgs.fd
            # Scripts
            npmInstallScript
            webpackBuildScript
            webpackWatchScript
            webpackProdScript
            startPostgresScript
            stopPostgresScript
            pgStatusScript
            psqlScript
            dbCreateScript
            dbDropScript
            dbResetScript
            dbDumpScript
            dbRestoreScript
            tenantCreateScript
            tenantListScript
            tenantDeleteScript
            statusScript
            djangoRunserverScript
            djangoMigrateScript
            djangoMakemigrationsScript
            showMigrationsScript
            migrateCheckScript
            migratePlanScript
            sqlMigrateScript
            squashMigrationsScript
            migrateFakeScript
            migrateZeroScript
            djangoShellScript
            djangoCollectstaticScript
            djangoCreateSuperuserScript
            djangoResetPasswordScript
            djangoTestScript
            rabbitmqStartScript
            rabbitmqStopScript
            rabbitmqStatusScript
            celeryWorkerScript
            celeryBeatScript
            celeryStatusScript
            pmtilesGenerateScript
            tippecanoeScript
            nginxStartScript
            nginxStopScript
            devStartScript
            devStopScript
            stopAllScript
            startAllScript
            lintScript
            formatScript
            securityCheckScript
            debugScript
            precommitInstallScript
            precommitRunScript
            reuseCheckScript
            packageStatusScript
            cleanVenvScript
          ];

          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
            pkgs.libffi
            pkgs.openssl
            pkgs.gdal
            pkgs.geos
            pkgs.proj
          ];

          shellHook = ''
            export PGHOST="$PWD/.pgdata"
            export PGPORT=5432
            export PGDATABASE="bims"
            export DJANGO_SETTINGS_MODULE="core.settings.dev_local"
            export PYTHONPATH="$PWD:''${PYTHONPATH:-}"
            export DATABASE_NAME="bims"
            export DATABASE_USERNAME="$USER"
            export DATABASE_PASSWORD=""
            export DATABASE_HOST="$PWD/.pgdata"
            export DATABASE_PORT="5432"
            export GDAL_LIBRARY_PATH="${pkgs.gdal}/lib/libgdal.so"
            export GEOS_LIBRARY_PATH="${pkgs.geos}/lib/libgeos_c.so"

            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "🌿 Django BIMS Development Environment (Pure Nix)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "  bims-status         📊 System status overview"
            echo "  bims-start-all      🚀 Start everything (DB+Celery+Django)"
            echo "  bims-dev-start      Start services (no Django)"
            echo "  bims-stop-all       Stop all services"
            echo "  bims-runserver      Django only (8000)"
            echo "  bims-test           Run tests"
            echo "  bims-lint           Linting"
            echo "  bims-clean-venv     Remove old venv"
            echo ""
            echo "  Frontend:"
            echo "  bims-npm-install    Install npm packages"
            echo "  bims-webpack-build  Build frontend (dev)"
            echo "  bims-webpack-watch  Watch and rebuild"
            echo "  bims-webpack-prod   Build frontend (production)"
            echo ""
            echo "  Database:"
            echo "  bims-pg-start/stop  Start/stop PostgreSQL"
            echo "  bims-pg-status      Check PostgreSQL status"
            echo "  bims-psql           PostgreSQL shell"
            echo "  bims-db-create      Create database with PostGIS"
            echo "  bims-db-drop        Drop database"
            echo "  bims-db-reset       Drop, recreate, and migrate"
            echo "  bims-db-dump        Dump database to file"
            echo "  bims-db-restore     Restore database from file"
            echo ""
            echo "  Tenants:"
            echo "  bims-tenant-create  Create tenant with domains"
            echo "  bims-tenant-list    List all tenants"
            echo "  bims-tenant-delete  Delete a tenant"
            echo ""
            echo "  Celery/RabbitMQ:"
            echo "  bims-rabbitmq-start Start RabbitMQ broker"
            echo "  bims-rabbitmq-stop  Stop RabbitMQ"
            echo "  bims-celery-worker  Start Celery worker"
            echo "  bims-celery-beat    Start Celery scheduler"
            echo "  bims-celery-status  Check worker status"
            echo ""
            echo "  PMTiles:"
            echo "  bims-pmtiles-generate  Generate PMTiles for layers"
            echo "  bims-tippecanoe        Convert GeoJSON to PMTiles"
            echo ""
            echo "  Migrations:"
            echo "  bims-migrate        Run migrations"
            echo "  bims-makemigrations Create new migrations"
            echo "  bims-showmigrations List all migrations"
            echo "  bims-migrate-check  Check for unapplied"
            echo "  bims-migrate-plan   Show migration plan"
            echo "  bims-sqlmigrate     Show SQL for migration"
            echo "  bims-squashmigrations Squash migrations"
            echo "  bims-migrate-fake   Fake migrations (dangerous)"
            echo "  bims-migrate-zero   Unapply all (dangerous)"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Made with 💗 by Kartoza"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          '';
        };

        apps = {
          start-all = { type = "app"; program = "${startAllScript}/bin/bims-start-all"; };
          dev-start = { type = "app"; program = "${devStartScript}/bin/bims-dev-start"; };
          dev-stop = { type = "app"; program = "${devStopScript}/bin/bims-dev-stop"; };
          stop-all = { type = "app"; program = "${stopAllScript}/bin/bims-stop-all"; };
          pg-start = { type = "app"; program = "${startPostgresScript}/bin/bims-pg-start"; };
          pg-stop = { type = "app"; program = "${stopPostgresScript}/bin/bims-pg-stop"; };
          psql = { type = "app"; program = "${psqlScript}/bin/bims-psql"; };
          runserver = { type = "app"; program = "${djangoRunserverScript}/bin/bims-runserver"; };
          migrate = { type = "app"; program = "${djangoMigrateScript}/bin/bims-migrate"; };
          test = { type = "app"; program = "${djangoTestScript}/bin/bims-test"; };
          debug = { type = "app"; program = "${debugScript}/bin/bims-debug"; };
          nginx-start = { type = "app"; program = "${nginxStartScript}/bin/bims-nginx-start"; };
          nginx-stop = { type = "app"; program = "${nginxStopScript}/bin/bims-nginx-stop"; };
          celery-worker = { type = "app"; program = "${celeryWorkerScript}/bin/bims-celery-worker"; };
          celery-beat = { type = "app"; program = "${celeryBeatScript}/bin/bims-celery-beat"; };
          lint = { type = "app"; program = "${lintScript}/bin/bims-lint"; };
          format = { type = "app"; program = "${formatScript}/bin/bims-format"; };
          security = { type = "app"; program = "${securityCheckScript}/bin/bims-security-check"; };
          precommit = { type = "app"; program = "${precommitRunScript}/bin/bims-precommit-run"; };
          npm-install = { type = "app"; program = "${npmInstallScript}/bin/bims-npm-install"; };
          webpack-build = { type = "app"; program = "${webpackBuildScript}/bin/bims-webpack-build"; };
          webpack-watch = { type = "app"; program = "${webpackWatchScript}/bin/bims-webpack-watch"; };
          package-status = { type = "app"; program = "${packageStatusScript}/bin/bims-package-status"; };
          clean-venv = { type = "app"; program = "${cleanVenvScript}/bin/bims-clean-venv"; };
        };

        packages = {
          postgres = postgresWithPostGIS;
          python = pythonPkgs;
        };
      }
    );
}
