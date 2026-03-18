#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Show package status for BIMS development environment

echo "📦 Package Status (Pure Nix - No venv)"
echo "======================================="
python -c "import django; print(f'Django: {django.__version__}')" 2>/dev/null || echo "Django: not available"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')" 2>/dev/null || echo "Pandas: not available"
python -c "import osgeo.gdal as gdal; print(f'GDAL: {gdal.__version__}')" 2>/dev/null || echo "GDAL: not available"
python -c "import rolepermissions; print('rolepermissions: ✅')" 2>/dev/null || echo "rolepermissions: ❌"
echo ""
[ -f "bims/node_modules/.npm-installed" ] && echo "npm packages: ✅" || echo "npm packages: ❌ (run bims-npm-install)"
