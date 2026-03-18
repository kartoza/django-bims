#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Start BIMS development environment
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
