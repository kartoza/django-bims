#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Clean old virtualenv (no longer needed with pure Nix)

echo "🧹 Removing old venv (no longer needed with pure Nix)..."
rm -rf .venv
echo "✅ Done"
