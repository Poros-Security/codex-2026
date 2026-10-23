#!/bin/sh
set -e
. /apply_dynamic_flag.sh
apply_dynamic_flag /flag
chmod 0440 /flag
chown root:ctf /flag
exec socat TCP-LISTEN:5000,reuseaddr,fork EXEC:"/usr/bin/timeout 30s /home/ctf/vault",su=ctf
