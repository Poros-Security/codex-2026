#!/bin/sh
set -e
. /apply_dynamic_flag.sh
apply_dynamic_flag /flag.txt
chmod 444 /flag.txt
chown root:root /flag.txt

exec socat TCP-LISTEN:11030,reuseaddr,fork EXEC:"./notesvc",su=ctfuser
