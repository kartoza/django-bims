#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Install npm packages for BIMS frontend
set -euo pipefail

cd bims
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.npm-installed" ]; then
    echo "📦 Installing npm packages..."
    npm install --legacy-peer-deps
    touch node_modules/.npm-installed
    echo "✅ Done"
else
    echo "✅ npm packages already installed"
fi
