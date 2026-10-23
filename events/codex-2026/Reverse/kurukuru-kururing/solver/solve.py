#!/usr/bin/env python3
"""
CTF Challenge Solver
Challenge: Kurukuru Kururing (Reverse)
Format: CODEX26{...}
"""
import base64

TARGET = "QCB4cJjL64HjyfvzGaBB+ynzoPvJw6Ax+3nDoOPboEnDoPPD+8lBGcN5sQ=="

def solve():
    print("[*] Decoding base64 target...")
    encoded_bytes = base64.b64decode(TARGET)
    print(f"[+] Target length: {len(encoded_bytes)} bytes")

    print("[*] Inverting: XOR 0x5A, then rotate-right-3...")
    flag_bytes = bytearray()
    for t in encoded_bytes:
        b = t ^ 0x5A                       
        b = ((b >> 3) | (b << 5)) & 0xFF 
        flag_bytes.append(b)

    flag = flag_bytes.decode("utf-8")
    print("\n" + "=" * 50)
    print(f"[+] FLAG: {flag}")
    print("=" * 50)

if __name__ == "__main__":
    solve()