#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Stop PostgreSQL
# Requires: POSTGRES_BIN_DIR to be set

: "${POSTGRES_BIN_DIR:?POSTGRES_BIN_DIR must be set}"

PGDATA="$PWD/.pgdata"
if [ -f "$PGDATA/postmaster.pid" ]; then
    echo "🛑 Stopping PostgreSQL..."
    "$POSTGRES_BIN_DIR/pg_ctl" -D "$PGDATA" stop -m fast
    echo "✅ Stopped"
else
    echo "ℹ️  Not running"
fi
