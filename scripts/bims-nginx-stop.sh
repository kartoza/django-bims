#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Stop Nginx

if [ -f "$PWD/logs/nginx.pid" ]; then
    kill "$(cat "$PWD/logs/nginx.pid")" 2>/dev/null || true
    rm -f "$PWD/logs/nginx.pid"
    echo "✅ Nginx stopped"
else
    echo "ℹ️  Nginx not running"
fi
