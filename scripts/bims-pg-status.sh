#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Check PostgreSQL status
# Requires: POSTGRES_BIN_DIR to be set

: "${POSTGRES_BIN_DIR:?POSTGRES_BIN_DIR must be set}"

PGDATA="$PWD/.pgdata"
PGPORT="${PGPORT:-5432}"
if "$POSTGRES_BIN_DIR/pg_isready" -h "$PGDATA" -p "$PGPORT" > /dev/null 2>&1; then
    echo "✅ PostgreSQL running on port $PGPORT"
else
    echo "❌ PostgreSQL not running"
fi
