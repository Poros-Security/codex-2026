#!/bin/sh
set -e
# shellcheck disable=SC1091
. /apply_dynamic_flag.sh
apply_dynamic_flag /flag
chown root:root /flag 2>/dev/null || true
chmod 400 /flag 2>/dev/null || true
exec gosu jail python3.12 -u /app/server.py
