#!/bin/sh
set -eu

exec socat \
    TCP-LISTEN:31337,reuseaddr,fork \
    EXEC:/challenge/qemu.sh,pty,setsid,ctty,rawer,echo=0,stderr
