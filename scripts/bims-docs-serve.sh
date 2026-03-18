#!/usr/bin/env bash
# Serve mkdocs documentation locally with live reload
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0

set -e

cd "$(dirname "$0")/.."

echo "Starting mkdocs development server..."
echo "Documentation will be available at: http://127.0.0.1:8001"
echo "Press Ctrl+C to stop"
mkdocs serve -a 127.0.0.1:8001
