#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Populate African freshwater taxa from GBIF
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
echo "🌍 Populating African freshwater taxa from GBIF..."
python manage.py populate_african_taxa "$@"
