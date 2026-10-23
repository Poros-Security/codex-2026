#!/bin/bash
set -e

FLAG="${FLAG:-CODEX26_dummy_flag_for_local_testing}"
echo "$FLAG" > /flag.txt
chmod 444 /flag.txt

cp -f /app/index.html /var/www/html/index.html 2>/dev/null || true
chmod 777 /var/www/html

exec "$@"
