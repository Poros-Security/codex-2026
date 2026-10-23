#!/bin/bash
set -e

# GZCTF hanya menyuntikkan GZCTF_FLAG; pakai itu lebih dulu.
DEFAULT_FLAG='CODEX26{ssrf_t0_r3d1s_t0_r3m0t3_c0d3}'
FLAG="${GZCTF_FLAG:-${FLAG:-$DEFAULT_FLAG}}"
printf '%s\n' "$FLAG" > /flag.txt
chmod 444 /flag.txt

# Ensure redis hostname resolves inside the container even if /etc/hosts was reset
grep -q '[[:space:]]redis$' /etc/hosts || echo '127.0.0.1 redis' >> /etc/hosts

# Redis must be able to rewrite /var/www/html
chmod 777 /var/www/html

exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
