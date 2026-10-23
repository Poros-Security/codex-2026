#!/usr/bin/env python3
from pathlib import Path
import sys

PROGRAM_SIZE = 942
MASK = 0xFFFFFFFF
OPS = (0xA7, 0x3D, 0xF1, 0x72, 0x3D, 0x19, 0xF1, 0xC4, 0x5B)


def next_key(x: int) -> int:
    x ^= (x << 13) & MASK
    x ^= x >> 17
    x ^= (x << 5) & MASK
    return x & MASK


def decrypt(blob: bytes) -> bytes:
    key = 0x9E3779B9
    plain = bytearray(PROGRAM_SIZE)
    for i, value in enumerate(blob):
        key = next_key(key)
        plain[i] = value ^ ((key ^ (i * 0x5D + 0xA7)) & 0xFF)
    return bytes(plain)


def u32(code: bytes, ip: int) -> int:
    return int.from_bytes(code[ip + 2:ip + 6], "little")


def valid_program(code: bytes) -> bool:
    if len(code) != PROGRAM_SIZE:
        return False
    for block in range(17):
        ip = block * 54
        if tuple(code[ip + 6 * n] for n in range(9)) != OPS:
            return False
        if u32(code, ip) != block * 4 or u32(code, ip + 48) != 930:
            return False
    return (code[918], code[919], u32(code, 918), code[924], code[930], code[931], u32(code, 930), code[936]) == (0x2E, 7, 1, 0x96, 0x2E, 7, 0, 0x96)


def locate_program(executable: bytes) -> bytes:
    # First cipher byte must decrypt to LDW (0xa7), so avoid decrypting every
    # possible offset in the ELF. The full grammar check prevents false hits.
    first_key = next_key(0x9E3779B9)
    wanted = 0xA7 ^ ((first_key ^ 0xA7) & 0xFF)
    hits = []
    for offset in range(0, len(executable) - PROGRAM_SIZE + 1):
        if executable[offset] != wanted:
            continue
        candidate = decrypt(executable[offset:offset + PROGRAM_SIZE])
        if valid_program(candidate):
            hits.append(candidate)
    if len(hits) != 1:
        raise RuntimeError(f"expected exactly one VM bytecode blob, found {len(hits)}")
    return hits[0]


def ror32(x: int, count: int) -> int:
    count &= 31
    return ((x >> count) | (x << (32 - count))) & MASK if count else x


def solve(code: bytes) -> bytes:
    answer = bytearray()
    for ip in range(0, 918, 54):
        offset = u32(code, ip)
        key, r1 = u32(code, ip + 6), u32(code, ip + 12)
        add, xor = u32(code, ip + 18), u32(code, ip + 24)
        mul, r2, expected = u32(code, ip + 30), u32(code, ip + 36), u32(code, ip + 42)

        # Inverse of: rol(((rol(word ^ key, r1) + add) ^ xor) * mul, r2)
        value = ror32(expected, r2)
        value = (value * pow(mul, -1, 1 << 32)) & MASK  # mul is odd
        value ^= xor
        value = (value - add) & MASK
        value = ror32(value, r1)
        word = value ^ key
        if offset != len(answer):
            raise RuntimeError(f"unexpected input offset {offset}")
        answer.extend(word.to_bytes(4, "little"))
    return bytes(answer[:67])


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).parents[1] / "dist" / "vm_mirage"
    if len(sys.argv) > 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} [path/to/vm_mirage]")
    try:
        result = solve(locate_program(target.read_bytes()))
        print(result.decode("ascii"))
    except (OSError, RuntimeError, UnicodeDecodeError, ValueError) as exc:
        raise SystemExit(f"solver error: {exc}") from exc


if __name__ == "__main__":
    main()
