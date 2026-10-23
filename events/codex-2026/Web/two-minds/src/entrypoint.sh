#!/bin/bash
set -e

# GZCTF hanya menyuntikkan GZCTF_FLAG; pakai itu lebih dulu.
FLAG="${GZCTF_FLAG:-${FLAG:-CODEX26_dummy_flag_for_local_testing}}"
echo "$FLAG" > /flag.txt
chmod 444 /flag.txt

gosu ctf python3 /app/backend.py &
sleep 0.4

exec gosu ctf python3 /app/frontend.py
