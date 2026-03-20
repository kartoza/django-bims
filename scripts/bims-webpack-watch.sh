#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Watch both frontends (Backbone + React) with webpack for development
set -euo pipefail

cd bims
[ ! -d "node_modules" ] && bims-npm-install

echo "👀 Watching frontends (Backbone + React)..."
echo "   Backbone: webpack.config.js"
echo "   React:    webpack.v2.config.js"
echo ""

# Run both webpack configs in parallel
npx webpack --mode=development --watch &
BACKBONE_PID=$!

npx webpack --config webpack.v2.config.js --mode=development --watch &
REACT_PID=$!

# Handle cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping webpack watchers..."
    kill $BACKBONE_PID 2>/dev/null || true
    kill $REACT_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
