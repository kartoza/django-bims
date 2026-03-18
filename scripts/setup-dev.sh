#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
#
# Development environment setup script for Django BIMS
# Run this after entering the nix develop shell
#
# Made with love by Kartoza | https://kartoza.com

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=============================================="
echo "  Django BIMS Development Setup"
echo "=============================================="
echo ""

# Check if we're in a nix shell
if [ -z "${IN_NIX_SHELL:-}" ]; then
  echo "Warning: Not running in a Nix shell."
  echo "Consider running: nix develop"
  echo ""
fi

# Create required directories
echo "Creating required directories..."
mkdir -p logs media static

# Setup virtual environment
if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python -m venv .venv
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

# Install Python requirements
echo "Installing Python requirements..."
pip install --upgrade pip > /dev/null
if [ -f "deployment/docker/REQUIREMENTS.txt" ]; then
  pip install -r deployment/docker/REQUIREMENTS.txt 2>/dev/null || echo "Some packages may require additional system libraries"
fi
if [ -f "deployment/docker/REQUIREMENTS-dev.txt" ]; then
  pip install -r deployment/docker/REQUIREMENTS-dev.txt 2>/dev/null || true
fi

# Create secret.py if it doesn't exist
if [ ! -f "core/settings/secret.py" ]; then
  echo "Creating secret.py..."
  SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
  cat > core/settings/secret.py << EOF
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
#
# Auto-generated secret key - DO NOT COMMIT
# Made with love by Kartoza

SECRET_KEY = '$SECRET_KEY'
IUCN_API_KEY = ''
EOF
  echo "Secret key generated."
fi

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
  echo "Installing pre-commit hooks..."
  pre-commit install
fi

# Start PostgreSQL
echo ""
echo "Starting PostgreSQL..."
bims-pg-start

# Run migrations
echo ""
echo "Running database migrations..."
export DJANGO_SETTINGS_MODULE="core.settings.dev_local"
python manage.py migrate --run-syncdb || echo "Migrations may require manual intervention"

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Quick start commands:"
echo "  bims-runserver      - Start Django dev server"
echo "  bims-shell          - Django shell"
echo "  bims-test           - Run tests"
echo "  bims-lint           - Run linters"
echo ""
echo "Use <leader>ph in Neovim for project menu."
echo ""
echo "Made with love by Kartoza | https://kartoza.com"
echo ""
