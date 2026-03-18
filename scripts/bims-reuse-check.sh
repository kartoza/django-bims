#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Check license compliance with REUSE
# Requires: REUSE_BIN to be set

: "${REUSE_BIN:?REUSE_BIN must be set}"

"$REUSE_BIN" lint
