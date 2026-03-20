#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Build both frontends (Backbone + React) with webpack
set -euo pipefail

cd bims
[ ! -d "node_modules" ] && bims-npm-install

MODE="${1:-development}"

echo "🔨 Building frontends ($MODE)..."
echo ""

echo "📦 Building Backbone frontend..."
npx webpack --mode="$MODE"

echo ""
echo "⚛️  Building React frontend..."
npx webpack --config webpack.v2.config.js --mode="$MODE"

echo ""
echo "✅ Both frontends built successfully"
