#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Start all BIMS development services (Django + Webpack + PostgreSQL)
set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

WEBPACK_BACKBONE_PID=""
WEBPACK_REACT_PID=""

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"

    # Kill background processes
    if [ -n "${WEBPACK_BACKBONE_PID:-}" ]; then
        kill "$WEBPACK_BACKBONE_PID" 2>/dev/null || true
    fi
    if [ -n "${WEBPACK_REACT_PID:-}" ]; then
        kill "$WEBPACK_REACT_PID" 2>/dev/null || true
    fi

    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🚀 Starting BIMS Development Environment${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ensure directories exist
mkdir -p "$PWD/media" "$PWD/static" "$PWD/logs"

# Start PostgreSQL if not running
if ! bims-pg-status > /dev/null 2>&1; then
    echo -e "${BLUE}🗄️  Starting PostgreSQL...${NC}"
    bims-pg-start
fi

# Install npm dependencies if needed
if [ ! -d "bims/node_modules" ] || [ ! -f "bims/node_modules/.npm-installed" ]; then
    echo -e "${BLUE}📦 Installing npm dependencies...${NC}"
    bims-npm-install
fi

# Create secret.py if needed
if [ ! -f "core/settings/secret.py" ]; then
    echo -e "${BLUE}🔑 Creating secret.py...${NC}"
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
    cat > core/settings/secret.py << EOF
SECRET_KEY = '$SECRET_KEY'
IUCN_API_KEY = ""
EOF
fi

# Start webpack watch for Backbone frontend in background
echo -e "${BLUE}📦 Starting Backbone webpack...${NC}"
cd bims
npx webpack --mode=development --watch >> "$PWD/../logs/webpack-backbone.log" 2>&1 &
WEBPACK_BACKBONE_PID=$!
cd ..
echo -e "${GREEN}   ✓ Backbone webpack running (PID: $WEBPACK_BACKBONE_PID)${NC}"

# Start webpack watch for React frontend in background
echo -e "${BLUE}⚛️  Starting React webpack...${NC}"
cd bims
npx webpack --config webpack.v2.config.js --mode=development --watch >> "$PWD/../logs/webpack-react.log" 2>&1 &
WEBPACK_REACT_PID=$!
cd ..
echo -e "${GREEN}   ✓ React webpack running (PID: $WEBPACK_REACT_PID)${NC}"

# Give webpack a moment to build
echo -e "${BLUE}⏳ Waiting for initial webpack builds...${NC}"
sleep 5

# Start Django in foreground
echo -e "${BLUE}🐍 Starting Django...${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ BIMS is running!${NC}"
echo ""
echo "   Old Interface:  http://localhost:8000/"
echo "   New React UI:   http://localhost:8000/new/"
echo ""
echo "   Webpack logs:"
echo "     tail -f logs/webpack-backbone.log"
echo "     tail -f logs/webpack-react.log"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run Django in foreground (this blocks)
python manage.py runserver 0.0.0.0:8000
