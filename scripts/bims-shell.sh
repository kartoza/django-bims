#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Start Django shell (with shell_plus if available)
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings.dev_local}"
python manage.py shell_plus "$@" 2>/dev/null || python manage.py shell "$@"
