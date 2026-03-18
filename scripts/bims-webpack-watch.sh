#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Watch frontend with webpack for development
set -euo pipefail

cd bims
[ ! -d "node_modules" ] && bims-npm-install
echo "👀 Watching frontend..."
npx webpack --mode=development --watch
