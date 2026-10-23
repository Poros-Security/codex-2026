#!/usr/bin/env python3

from __future__ import annotations

import os

import numpy as np

FLAG = "CODEX26{REDACTED}"
SEED = None

N = 72
M = 108
Q = 3329
ETA = 5


def centered_mod(x: np.ndarray, q: int) -> np.ndarray:
    r = np.remainder(x, q).astype(np.int64)
    return np.where(r > q // 2, r - q, r)


def encrypt_flag_bits(s: np.ndarray, q: int, eta: int, flag: str, rng: np.random.Generator):
    bits = []
    for byte in flag.encode("utf-8"):
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    rows = []
    for bit in bits:
        a = rng.integers(0, q, size=s.shape[0], dtype=np.int64)
        e = int(rng.integers(-eta, eta + 1))
        u = int((int(a @ s) + e + bit * (q // 2)) % q)
        rows.append((a, u))
    return rows


def write_params(path: str, A: np.ndarray, b: np.ndarray) -> None:
    n = int(A.shape[1])
    m = int(A.shape[0])
    with open(path, "w", encoding="utf-8") as f:
        f.write("{\n")
        f.write(f'  "n": {n},\n')
        f.write(f'  "m": {m},\n')
        f.write(f'  "q": {Q},\n')
        f.write(f'  "eta": {ETA},\n')
        f.write('  "secret_distribution": "ternary {-1,0,1}",\n')
        f.write('  "error_distribution": "uniform integer in [-eta, eta]",\n')
        f.write("  \"A\": [\n")
        for i, row in enumerate(A):
            comma = "," if i + 1 < m else ""
            f.write("    [" + ", ".join(str(int(x)) for x in row) + "]" + comma + "\n")
        f.write("  ],\n")
        f.write("  \"b\": [" + ", ".join(str(int(x)) for x in b) + "],\n")
        f.write(
            '  "note": "Search-LWE: b = As + e (mod q), s in {-1,0,1}, |e| <= eta. '
            'Cipher lines: Regev bits, MSB-first UTF-8, a_0,...,a_{n-1};u."\n'
        )
        f.write("}\n")


def write_cipher(path: str, rows) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for a, u in rows:
            f.write(",".join(str(int(x)) for x in a) + f";{int(u)}\n")


def main() -> None:
    rng = np.random.default_rng()
    A = rng.integers(0, Q, size=(M, N), dtype=np.int64)
    s = rng.integers(-1, 2, size=N, dtype=np.int64)
    e = rng.integers(-ETA, ETA + 1, size=M, dtype=np.int64)
    b = (A @ s + e) % Q
    rows = encrypt_flag_bits(s, Q, ETA, FLAG, rng)

    os.makedirs("out", exist_ok=True)
    write_params(os.path.join("out", "params.json"), A, b)
    write_cipher(os.path.join("out", "Cipher.txt"), rows)
    print("[*] Wrote sample instance to out/ (FLAG/SEED redacted; not the CTF files)")
    print("[*] Public challenge files: params.json + Cipher.txt in this zip")


if __name__ == "__main__":
    main()
