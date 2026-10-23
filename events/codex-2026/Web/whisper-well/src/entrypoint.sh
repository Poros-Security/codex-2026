#!/bin/bash
set -e

# GZCTF hanya menyuntikkan GZCTF_FLAG; pakai itu lebih dulu.
FLAG="${GZCTF_FLAG:-${FLAG:-CODEX26_dummy_flag_for_local_testing}}"
echo "$FLAG" > /flag.txt
chmod 444 /flag.txt

exec gosu ctf /usr/local/bin/gunicorn -w 1 -b 0.0.0.0:8080 app:app
