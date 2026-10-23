#!/bin/sh

exec qemu-system-x86_64 \
    -kernel /challenge/bzImage \
    -initrd /challenge/rootfs.cpio.gz \
    -append "console=ttyS0 nokaslr nopti oops=panic panic=-1 quiet loglevel=1" \
    -display none \
    -monitor none \
    -serial stdio \
    -m 128M \
    -smp 1 \
    -no-reboot \
    -netdev user,id=net0 \
    -device e1000,netdev=net0
