#!/usr/bin/env sh
set -eu

uvicorn main:app --app-dir /app/dashboard/app/backend --host 127.0.0.1 --port 8000 &
API_PID="$!"

envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;' &
NGINX_PID="$!"

trap 'kill "$API_PID" "$NGINX_PID" 2>/dev/null || true' INT TERM

while true; do
    if ! kill -0 "$API_PID" 2>/dev/null; then
        wait "$API_PID" || exit "$?"
    fi
    if ! kill -0 "$NGINX_PID" 2>/dev/null; then
        wait "$NGINX_PID" || exit "$?"
    fi
    sleep 1
done
