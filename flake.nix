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
          inflection
          uritemplate

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
          drf-spectacular
          drf-spectacular-sidecar

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
        # Script wrappers - thin wrappers that set env vars and call scripts
        # =======================================================================
        scriptsDir = ./scripts;

        # Simple scripts (no Nix paths needed)
        wrapSimpleScript = name: pkgs.writeShellScriptBin name ''
          exec ${scriptsDir}/${name}.sh "$@"
        '';

        # Scripts needing PostgreSQL paths
        wrapPostgresScript = name: pkgs.writeShellScriptBin name ''
          export POSTGRES_BIN_DIR="${postgresWithPostGIS}/bin"
          exec ${scriptsDir}/${name}.sh "$@"
        '';

        # Scripts needing Nginx paths
        wrapNginxScript = name: pkgs.writeShellScriptBin name ''
          export NGINX_BIN="${pkgs.nginx}/bin/nginx"
          export NGINX_MIME_TYPES="${pkgs.nginx}/conf/mime.types"
          exec ${scriptsDir}/${name}.sh "$@"
        '';

        # Scripts needing tool paths
        wrapToolScript = name: toolPath: varName: pkgs.writeShellScriptBin name ''
          export ${varName}="${toolPath}"
          exec ${scriptsDir}/${name}.sh "$@"
        '';

        # Define all scripts
        npmInstallScript = wrapSimpleScript "bims-npm-install";
        webpackBuildScript = wrapSimpleScript "bims-webpack-build";
        webpackWatchScript = wrapSimpleScript "bims-webpack-watch";
        startPostgresScript = wrapPostgresScript "bims-pg-start";
        stopPostgresScript = wrapPostgresScript "bims-pg-stop";
        pgStatusScript = wrapPostgresScript "bims-pg-status";
        psqlScript = wrapPostgresScript "bims-psql";
        djangoRunserverScript = wrapSimpleScript "bims-runserver";
        djangoMigrateScript = wrapSimpleScript "bims-migrate";
        djangoMakemigrationsScript = wrapSimpleScript "bims-makemigrations";
        djangoShellScript = wrapSimpleScript "bims-shell";
        djangoCollectstaticScript = wrapSimpleScript "bims-collectstatic";
        djangoCreateSuperuserScript = wrapSimpleScript "bims-createsuperuser";
        djangoTestScript = wrapSimpleScript "bims-test";
        celeryWorkerScript = wrapSimpleScript "bims-celery-worker";
        celeryBeatScript = wrapSimpleScript "bims-celery-beat";
        nginxStartScript = wrapNginxScript "bims-nginx-start";
        nginxStopScript = wrapSimpleScript "bims-nginx-stop";
        devStartScript = wrapSimpleScript "bims-dev-start";
        devStopScript = wrapSimpleScript "bims-dev-stop";
        lintScript = wrapSimpleScript "bims-lint";
        formatScript = wrapSimpleScript "bims-format";
        securityCheckScript = wrapToolScript "bims-security-check" "${pkgs.bearer}/bin/bearer" "BEARER_BIN";
        debugScript = wrapSimpleScript "bims-debug";
        precommitInstallScript = wrapToolScript "bims-precommit-install" "${pkgs.pre-commit}/bin/pre-commit" "PRECOMMIT_BIN";
        precommitRunScript = wrapToolScript "bims-precommit-run" "${pkgs.pre-commit}/bin/pre-commit" "PRECOMMIT_BIN";
        reuseCheckScript = wrapToolScript "bims-reuse-check" "${pkgs.reuse}/bin/reuse" "REUSE_BIN";
        packageStatusScript = wrapSimpleScript "bims-package-status";
        cleanVenvScript = wrapSimpleScript "bims-clean-venv";
        loadDummyDataScript = wrapSimpleScript "bims-load-dummy-data";
        loadDummyOccurrencesScript = wrapSimpleScript "bims-load-dummy-occurrences";
        statusScript = wrapSimpleScript "bims-status";

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
            loadDummyDataScript
            loadDummyOccurrencesScript
            statusScript
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
            echo "  bims-status           📊 System status overview"
            echo "  bims-run              🚀 Start everything"
            echo "  bims-dev-start        Start services (no Django)"
            echo "  bims-stop-all         Stop all services"
            echo "  bims-runserver        Django only (8000)"
            echo "  bims-test             Run tests"
            echo "  bims-lint             Linting"
            echo "  bims-load-dummy-data  Load test data"
            echo "  bims-clean-venv       Remove old venv"
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
          load-dummy-data = { type = "app"; program = "${loadDummyDataScript}/bin/bims-load-dummy-data"; };
          load-dummy-occurrences = { type = "app"; program = "${loadDummyOccurrencesScript}/bin/bims-load-dummy-occurrences"; };
          status = { type = "app"; program = "${statusScript}/bin/bims-status"; };
        };

        packages = {
          postgres = postgresWithPostGIS;
          python = pythonPkgs;
        };
      }
    );
}
