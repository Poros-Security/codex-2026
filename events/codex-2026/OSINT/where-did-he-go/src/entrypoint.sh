#!/bin/sh
set -e
. /apply_dynamic_flag.sh
apply_dynamic_flag /tmp/.instance_flag
FLAG="$(cat /tmp/.instance_flag)"
export FLAG
CTF_FLAG="$FLAG"
export CTF_FLAG
exec python -u /app/server.py
