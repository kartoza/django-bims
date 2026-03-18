#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Stop BIMS development environment

echo "🛑 Stopping..."
bims-nginx-stop 2>/dev/null || true
bims-pg-stop
echo "✅ Stopped"
