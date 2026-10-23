#!/bin/sh
set -e
# Whale injects FLAG; keep /flag.txt as the reward target.
# GZCTF hanya menyuntikkan GZCTF_FLAG; pakai itu lebih dulu.
FLAG="${GZCTF_FLAG:-${FLAG:-}}"
if [ -n "${FLAG:-}" ]; then
  printf '%s\n' "$FLAG" > /flag.txt
  chmod 444 /flag.txt
  unset FLAG
fi
exec python app.py
