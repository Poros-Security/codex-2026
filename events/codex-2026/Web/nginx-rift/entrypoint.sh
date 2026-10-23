#!/bin/bash
set -e
cd /app

# Whale injects FLAG env; keep /flag.txt as the vault target for the PoC.
# GZCTF hanya menyuntikkan GZCTF_FLAG; pakai itu lebih dulu.
FLAG="${GZCTF_FLAG:-${FLAG:-}}"
if [ -n "${FLAG:-}" ]; then
  printf '%s\n' "$FLAG" > /flag.txt
  chmod 444 /flag.txt
  unset FLAG
fi

python3 server.py &>/dev/null &
# setarch -R disables ASLR for the launched process (deterministic addresses)
exec setarch x86_64 -R /nginx-src/build/nginx -p /app -c /app/nginx.conf
