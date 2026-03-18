#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Format BIMS code with black and isort

echo "🎨 black..."
black bims core
echo "🎨 isort..."
isort bims core
