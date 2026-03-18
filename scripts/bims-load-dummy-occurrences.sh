#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Load dummy occurrences for BIMS development
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
echo "🌿 Loading dummy occurrences for BIMS..."
python manage.py load_dummy_occurrences "$@"
