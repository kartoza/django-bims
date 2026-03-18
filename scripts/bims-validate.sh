#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Bulk validate pending BIMS data
#
# Usage:
#   bims-validate --sites          Validate all pending sites
#   bims-validate --site-visits    Validate all pending site visits
#   bims-validate --records        Validate all pending records
#   bims-validate --taxa           Validate all pending taxa
#   bims-validate --all            Validate everything
#   bims-validate --dry-run --all  Preview without changes
#
# Made with love by Kartoza | https://kartoza.com
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"

# Show help if no arguments
if [[ $# -eq 0 ]]; then
    echo ""
    echo "BIMS Bulk Validation"
    echo "===================="
    echo ""
    echo "Usage: bims-validate [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --sites          Validate all pending location sites"
    echo "  --site-visits    Validate all pending site visits (surveys)"
    echo "  --surveys        Alias for --site-visits"
    echo "  --records        Validate all pending biological records"
    echo "  --taxa           Validate all pending taxa"
    echo "  --all            Validate all pending items in all categories"
    echo "  --dry-run        Show what would be validated without making changes"
    echo "  --tenant NAME    Specify tenant schema name"
    echo ""
    echo "Examples:"
    echo "  bims-validate --all                    # Validate everything"
    echo "  bims-validate --sites --site-visits   # Validate sites and visits"
    echo "  bims-validate --dry-run --all          # Preview all changes"
    echo ""
    echo "Made with love by Kartoza | https://kartoza.com"
    exit 0
fi

python manage.py validate_all "$@"
