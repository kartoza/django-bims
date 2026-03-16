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
          # Core - Use Django 6 from our custom derivation
          django_6
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
          django-cryptography
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
          django-sentry
          django-uuid-upload-path
          djangorestframework-gis
          djangorestframework-guardian
          dj-pagination
          geonode-oauth-toolkit
          raven

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

        startPostgresScript = pkgs.writeShellScriptBin "bims-pg-start" ''
          #!/usr/bin/env bash
          set -euo pipefail
          PGDATA="$PWD/.pgdata"
          PGPORT=''${PGPORT:-5432}

          if [ ! -d "$PGDATA" ]; then
            echo "🗄️  Initializing PostgreSQL..."
            ${postgresWithPostGIS}/bin/initdb -D "$PGDATA" --auth=trust --no-locale --encoding=UTF8
            cat >> "$PGDATA/postgresql.conf" << EOF
          listen_addresses = 'localhost'
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
          python manage.py createsuperuser "$@"
        '';

        djangoTestScript = pkgs.writeShellScriptBin "bims-test" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.test}"
          python manage.py test "''${@:-bims}"
        '';

        celeryWorkerScript = pkgs.writeShellScriptBin "bims-celery-worker" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          celery -A bims worker -l INFO -Q "''${1:-celery,update,search,geocontext}"
        '';

        celeryBeatScript = pkgs.writeShellScriptBin "bims-celery-beat" ''
          #!/usr/bin/env bash
          set -euo pipefail
          export DJANGO_SETTINGS_MODULE="''${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
          celery -A bims beat -l INFO
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
          echo "🚀 Starting BIMS development environment..."

          mkdir -p "$PWD/media" "$PWD/static" "$PWD/logs"

          bims-pg-start

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

          echo ""
          echo "✅ Ready! Commands:"
          echo "   bims-runserver     - Django (port 8000)"
          echo "   bims-webpack-watch - Frontend"
          echo "   bims-nginx-start   - Nginx (port 8080)"
        '';

        devStopScript = pkgs.writeShellScriptBin "bims-dev-stop" ''
          #!/usr/bin/env bash
          echo "🛑 Stopping..."
          bims-nginx-stop 2>/dev/null || true
          bims-pg-stop
          echo "✅ Stopped"
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
            startPostgresScript
            stopPostgresScript
            pgStatusScript
            psqlScript
            djangoRunserverScript
            djangoMigrateScript
            djangoMakemigrationsScript
            djangoShellScript
            djangoCollectstaticScript
            djangoCreateSuperuserScript
            djangoTestScript
            celeryWorkerScript
            celeryBeatScript
            nginxStartScript
            nginxStopScript
            devStartScript
            devStopScript
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
            echo "  bims-dev-start      Full setup"
            echo "  bims-runserver      Django (8000)"
            echo "  bims-pg-start/stop  PostgreSQL"
            echo "  bims-test           Run tests"
            echo "  bims-lint           Linting"
            echo "  bims-clean-venv     Remove old venv"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Made with 💗 by Kartoza"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          '';
        };

        apps = {
          dev-start = { type = "app"; program = "${devStartScript}/bin/bims-dev-start"; };
          dev-stop = { type = "app"; program = "${devStopScript}/bin/bims-dev-stop"; };
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
