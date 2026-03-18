#!/usr/bin/env bash
# Build mkdocs documentation
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0

set -e

cd "$(dirname "$0")/.."

echo "Building mkdocs documentation..."
mkdocs build

echo "Documentation built successfully!"
echo "Output: site/"
