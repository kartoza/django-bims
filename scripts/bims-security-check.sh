#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Run security checks on BIMS code
# Requires: BEARER_BIN to be set

: "${BEARER_BIN:?BEARER_BIN must be set}"

echo "🔒 bandit..."
bandit -r bims core -ll -x ".venv,venv,migrations" || true
echo "🔒 bearer..."
"$BEARER_BIN" scan . --quiet || true
