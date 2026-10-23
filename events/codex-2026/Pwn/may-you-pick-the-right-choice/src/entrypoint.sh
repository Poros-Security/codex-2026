#!/bin/sh
set -e
. /apply_dynamic_flag.sh
apply_dynamic_flag /flag
chmod 444 /flag
chown root:root /flag

exec socat TCP-LISTEN:1337,bind=0.0.0.0,reuseaddr,fork,nodelay EXEC:/app/run_chall.sh,stderr,su=ctf
