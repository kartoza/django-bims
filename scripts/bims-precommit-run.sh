#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Run pre-commit checks
# Requires: PRECOMMIT_BIN to be set

: "${PRECOMMIT_BIN:?PRECOMMIT_BIN must be set}"

"$PRECOMMIT_BIN" run --all-files
