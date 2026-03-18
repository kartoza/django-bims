#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Build frontend with webpack
set -euo pipefail

cd bims
[ ! -d "node_modules" ] && bims-npm-install
echo "🔨 Building frontend..."
npx webpack --mode=development
echo "✅ Done"
