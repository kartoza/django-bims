#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Connect to BIMS PostgreSQL database
# Requires: POSTGRES_BIN_DIR to be set

: "${POSTGRES_BIN_DIR:?POSTGRES_BIN_DIR must be set}"

PGDATA="$PWD/.pgdata"
PGPORT="${PGPORT:-5432}"
"$POSTGRES_BIN_DIR/psql" -h "$PGDATA" -p "$PGPORT" -d "${1:-bims}" "${@:2}"
