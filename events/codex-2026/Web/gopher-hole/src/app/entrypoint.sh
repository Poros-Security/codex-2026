#!/bin/bash
set -e
exec gosu ctf /usr/local/bin/python3 /app/app.py
