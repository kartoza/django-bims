#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Run linters on BIMS code

echo "🔍 flake8..."
flake8 --config .flake8 bims core || true
echo "🔍 pylint..."
pylint --rcfile=.pylintrc bims core --exit-zero || true
