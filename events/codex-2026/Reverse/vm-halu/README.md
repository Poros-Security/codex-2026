## PoC:

1. Extract encrypted bytecode dari .rodata binary (offset 0x2060, panjang 942 byte)
2. Decrypt pakai stream cipher xorshift32 (seed 0x9e3779b9, counter mulai 0xA7 step +0x5D)
3. Parse jadi 157 instruksi VM (6 byte tiap instr: opcode, reg, imm32), ketemu 17 blok cek 4-byte
4. Tiap blok invert mundur: Target -> (ROR r2) -> (* modinv(mul)) -> (^ xor2) -> (- add) -> (ROR r1) -> (^ xor1) = 4 byte input
5. Susun semua blok -> Dapet deh flagnya CODEX26{...}