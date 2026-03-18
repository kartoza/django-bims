#!/usr/bin/env bash
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
# Start Nginx reverse proxy for BIMS
# Requires: NGINX_BIN, NGINX_MIME_TYPES to be set
set -euo pipefail

: "${NGINX_BIN:?NGINX_BIN must be set}"
: "${NGINX_MIME_TYPES:?NGINX_MIME_TYPES must be set}"

mkdir -p "$PWD/logs"

# Generate nginx config at runtime
cat > "$PWD/logs/nginx.conf" << EOF
worker_processes 1;
error_log $PWD/logs/nginx-error.log;
pid $PWD/logs/nginx.pid;
daemon off;
events { worker_connections 1024; }
http {
    include $NGINX_MIME_TYPES;
    default_type application/octet-stream;
    access_log $PWD/logs/nginx-access.log;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 100M;
    gzip on;
    upstream django { server 127.0.0.1:8000; }
    server {
        listen 8080;
        server_name localhost;
        location /static { alias $PWD/static; expires 1d; }
        location /media { alias $PWD/media; expires 1d; }
        location / {
            proxy_pass http://django;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 300;
        }
    }
}
EOF

echo "🌐 Starting Nginx on http://localhost:8080..."
"$NGINX_BIN" -c "$PWD/logs/nginx.conf"
