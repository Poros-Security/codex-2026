#!/bin/sh
set -e
. /apply_dynamic_flag.sh
apply_dynamic_flag /tmp/.instance_flag
# Export for python servers that read FLAG at startup
FLAG="$(cat /tmp/.instance_flag)"
export FLAG
CTF_FLAG="$FLAG"
export CTF_FLAG
exec python3 -u /app/server.py
