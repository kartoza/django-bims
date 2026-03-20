#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Clean stale lock files after unexpected shutdown
set -euo pipefail

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧹 Cleaning Stale Lock Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CLEANED=0

# PostgreSQL postmaster.pid
PGDATA="$PWD/.pgdata"
if [ -f "$PGDATA/postmaster.pid" ]; then
    # Check if PostgreSQL is actually running
    PG_PID=$(head -1 "$PGDATA/postmaster.pid" 2>/dev/null || echo "")
    if [ -n "$PG_PID" ] && ! kill -0 "$PG_PID" 2>/dev/null; then
        echo "🗄️  PostgreSQL: Removing stale postmaster.pid (PID $PG_PID not running)"
        rm -f "$PGDATA/postmaster.pid"
        rm -f "$PGDATA/postmaster.opts"
        CLEANED=$((CLEANED + 1))
    else
        echo "🗄️  PostgreSQL: postmaster.pid is valid (PID $PG_PID running)"
    fi
else
    echo "🗄️  PostgreSQL: No postmaster.pid found"
fi

# PostgreSQL socket files
if [ -d "$PGDATA" ]; then
    STALE_SOCKETS=$(find "$PGDATA" -name ".s.PGSQL.*" -type s 2>/dev/null || true)
    if [ -n "$STALE_SOCKETS" ]; then
        # Check if PostgreSQL is running
        if ! pgrep -f "postgres.*$PGDATA" > /dev/null 2>&1; then
            echo "🔌 PostgreSQL: Removing stale socket files"
            find "$PGDATA" -name ".s.PGSQL.*" -type s -delete 2>/dev/null || true
            find "$PGDATA" -name ".s.PGSQL.*.lock" -delete 2>/dev/null || true
            CLEANED=$((CLEANED + 1))
        fi
    fi
fi

# RabbitMQ lock files
RABBITMQ_DIR="$PWD/.rabbitmq"
if [ -d "$RABBITMQ_DIR" ]; then
    # Check for stale Erlang/RabbitMQ pid files
    if [ -f "$RABBITMQ_DIR/mnesia/rabbit@localhost.pid" ]; then
        RMQ_PID=$(cat "$RABBITMQ_DIR/mnesia/rabbit@localhost.pid" 2>/dev/null || echo "")
        if [ -n "$RMQ_PID" ] && ! kill -0 "$RMQ_PID" 2>/dev/null; then
            echo "🐰 RabbitMQ: Removing stale pid file (PID $RMQ_PID not running)"
            rm -f "$RABBITMQ_DIR/mnesia/rabbit@localhost.pid"
            CLEANED=$((CLEANED + 1))
        fi
    fi

    # Clean Erlang crash dumps
    if ls "$RABBITMQ_DIR"/erl_crash.dump* 1>/dev/null 2>&1; then
        echo "🐰 RabbitMQ: Removing crash dump files"
        rm -f "$RABBITMQ_DIR"/erl_crash.dump*
        CLEANED=$((CLEANED + 1))
    fi
fi

# Celery pid files
CELERY_PIDS=$(find "$PWD" -maxdepth 2 -name "celery*.pid" -o -name "celeryd.pid" 2>/dev/null || true)
for pidfile in $CELERY_PIDS; do
    if [ -f "$pidfile" ]; then
        CELERY_PID=$(cat "$pidfile" 2>/dev/null || echo "")
        if [ -n "$CELERY_PID" ] && ! kill -0 "$CELERY_PID" 2>/dev/null; then
            echo "🔄 Celery: Removing stale $pidfile (PID $CELERY_PID not running)"
            rm -f "$pidfile"
            CLEANED=$((CLEANED + 1))
        fi
    fi
done

# Nginx pid file
NGINX_PID_FILE="$PWD/.nginx/nginx.pid"
if [ -f "$NGINX_PID_FILE" ]; then
    NGINX_PID=$(cat "$NGINX_PID_FILE" 2>/dev/null || echo "")
    if [ -n "$NGINX_PID" ] && ! kill -0 "$NGINX_PID" 2>/dev/null; then
        echo "🌐 Nginx: Removing stale nginx.pid (PID $NGINX_PID not running)"
        rm -f "$NGINX_PID_FILE"
        CLEANED=$((CLEANED + 1))
    fi
fi

# Django/Gunicorn pid files
GUNICORN_PIDS=$(find "$PWD" -maxdepth 2 -name "gunicorn*.pid" 2>/dev/null || true)
for pidfile in $GUNICORN_PIDS; do
    if [ -f "$pidfile" ]; then
        GUN_PID=$(cat "$pidfile" 2>/dev/null || echo "")
        if [ -n "$GUN_PID" ] && ! kill -0 "$GUN_PID" 2>/dev/null; then
            echo "🦄 Gunicorn: Removing stale $pidfile (PID $GUN_PID not running)"
            rm -f "$pidfile"
            CLEANED=$((CLEANED + 1))
        fi
    fi
done

# Webpack/Node lock files
if [ -f "$PWD/bims/node_modules/.package-lock.json.lock" ]; then
    echo "📦 NPM: Removing stale package-lock.json.lock"
    rm -f "$PWD/bims/node_modules/.package-lock.json.lock"
    CLEANED=$((CLEANED + 1))
fi

# Python compiled files that might cause issues
STALE_PYC=$(find "$PWD" -path "*/__pycache__/*.pyc" -mtime +7 2>/dev/null | head -20 || true)
if [ -n "$STALE_PYC" ]; then
    echo "🐍 Python: Found old .pyc files (run 'find . -name \"*.pyc\" -delete' to clean)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$CLEANED" -gt 0 ]; then
    echo "✅ Cleaned $CLEANED stale lock file(s)"
else
    echo "✅ No stale lock files found"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
