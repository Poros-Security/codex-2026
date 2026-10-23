#!/usr/bin/env python3
import base64

FLAG = "CODEX26{7r45h_c4n5_4r3_m4d3_70_b3_534rch3d}"

def encode(flag: str) -> str:
    out = bytearray()
    for b in flag.encode():
        t = ((b << 3) | (b >> 5)) & 0xFF   # rotate-left-3 on 8 bits
        t ^= 0x5A
        out.append(t)
    return base64.b64encode(bytes(out)).decode()

print(f"FLAG_LEN = {len(FLAG.encode())}")
print(f'TARGET   = "{encode(FLAG)}"')