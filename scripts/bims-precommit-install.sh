#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Install pre-commit hooks
# Requires: PRECOMMIT_BIN to be set

: "${PRECOMMIT_BIN:?PRECOMMIT_BIN must be set}"

"$PRECOMMIT_BIN" install
echo "✅ Pre-commit hooks installed"
