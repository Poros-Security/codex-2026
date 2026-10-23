#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import zipfile

import numpy as np

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DIST_DIR = os.path.join(ROOT_DIR, "dist")

FLAG = "CODEX26{bkz_m3nd3ng4r_b1s1k_d4r1_k4but}"
SEED = 0xC0DEC0DE

N = 72
M = 108
Q = 3329
ETA = 5


def centered_mod(x: np.ndarray, q: int) -> np.ndarray:
    r = np.remainder(x, q).astype(np.int64)
    return np.where(r > q // 2, r - q, r)


def gf_solve(A: np.ndarray, b: np.ndarray, q: int) -> np.ndarray | None:
    n = A.shape[0]
    Mtx = np.concatenate([A % q, (b % q).reshape(-1, 1)], axis=1).astype(object)
    for col in range(n):
        piv = None
        for r in range(col, n):
            if int(Mtx[r, col]) % q != 0:
                piv = r
                break
        if piv is None:
            return None
        Mtx[[col, piv]] = Mtx[[piv, col]]
        inv = pow(int(Mtx[col, col]) % q, -1, q)
        for j in range(col, n + 1):
            Mtx[col, j] = (int(Mtx[col, j]) * inv) % q
        for r in range(n):
            if r == col:
                continue
            f = int(Mtx[r, col]) % q
            if f:
                for j in range(col, n + 1):
                    Mtx[r, j] = (int(Mtx[r, j]) - f * int(Mtx[col, j])) % q
    return np.array([int(Mtx[i, n]) % q for i in range(n)], dtype=np.int64)


def babai_nearest_plane(B_rows: np.ndarray, target: np.ndarray) -> np.ndarray:
    B = B_rows.astype(np.float64)
    d = B.shape[0]
    mu = np.zeros((d, d), dtype=np.float64)
    G = np.zeros_like(B)
    for i in range(d):
        G[i] = B[i]
        for j in range(i):
            denom = float(np.dot(G[j], G[j]))
            mu[i, j] = 0.0 if denom == 0.0 else float(np.dot(B[i], G[j]) / denom)
            G[i] = G[i] - mu[i, j] * G[j]
    w = target.astype(np.float64).copy()
    c = np.zeros(d, dtype=np.float64)
    for i in range(d - 1, -1, -1):
        gi2 = float(np.dot(G[i], G[i]))
        if gi2 == 0.0:
            c[i] = 0.0
            continue
        c[i] = round(float(np.dot(w, G[i]) / gi2))
        w = w - c[i] * B[i]
    return np.rint(c @ B).astype(np.int64)


def kannan_rows(A: np.ndarray, b: np.ndarray, q: int, t: int = 1) -> np.ndarray:
    m, n = A.shape
    d = n + m + 1
    B = np.zeros((d, d), dtype=np.int64)
    for j in range(n):
        B[j, j] = 1
        B[j, n : n + m] = A[:, j]
    for i in range(m):
        B[n + i, n + i] = q
    B[n + m, n : n + m] = b
    B[n + m, n + m] = t
    return B


def encrypt_flag_bits(s: np.ndarray, q: int, eta: int, flag: str, rng: np.random.Generator):
    n = s.shape[0]
    bits = []
    for byte in flag.encode("utf-8"):
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    rows = []
    for bit in bits:
        a = rng.integers(0, q, size=n, dtype=np.int64)
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


def decrypt_flag_bits(s: np.ndarray, rows, q: int) -> str:
    bits = []
    for a, u in rows:
        t = int(centered_mod(np.array([(int(u) - int(a @ s)) % q], dtype=np.int64), q)[0])
        bits.append(1 if abs(t) > q / 4 else 0)
    out = []
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i : i + 8]:
            byte = (byte << 1) | bit
        out.append(byte)
    return bytes(out).decode("utf-8")


def build_handout(params_path: str, cipher_path: str, zip_path: str) -> None:
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    handout_src = os.path.join(ROOT_DIR, "handout_src")
    os.makedirs(handout_src, exist_ok=True)
    hs_params = os.path.join(handout_src, "params.json")
    hs_cipher = os.path.join(handout_src, "Cipher.txt")
    with open(params_path, "rb") as src, open(hs_params, "wb") as dst:
        dst.write(src.read())
    with open(cipher_path, "rb") as src, open(hs_cipher, "wb") as dst:
        dst.write(src.read())
    redacted = os.path.join(handout_src, "generate_bisikan_dari_kabut_angka.py")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(hs_params, arcname="params.json")
        zf.write(hs_cipher, arcname="Cipher.txt")
        zf.write(redacted, arcname="generate_bisikan_dari_kabut_angka.py")


def main() -> int:
    os.makedirs(SRC_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
    rng = np.random.default_rng(SEED)

    A = rng.integers(0, Q, size=(M, N), dtype=np.int64)
    s = rng.integers(-1, 2, size=N, dtype=np.int64)
    e = rng.integers(-ETA, ETA + 1, size=M, dtype=np.int64)
    b = (A @ s + e) % Q
    rows = encrypt_flag_bits(s, Q, ETA, FLAG, rng)

    params_path = os.path.join(SRC_DIR, "params.json")
    cipher_path = os.path.join(SRC_DIR, "Cipher.txt")
    handout_path = os.path.join(DIST_DIR, "handout.zip")
    write_params(params_path, A, b)
    write_cipher(cipher_path, rows)
    build_handout(params_path, cipher_path, handout_path)

    recovered = decrypt_flag_bits(s, rows, Q)
    if recovered != FLAG:
        print("[-] Honest decryption failed:", recovered, file=sys.stderr)
        return 1

    s_gf = gf_solve(A[:N], b[:N], Q)
    gf_ok = False
    if s_gf is not None:
        s_c = centered_mod(s_gf, Q)
        gf_ok = bool(np.array_equal(s_c, s) or np.array_equal(s_c, -s))

    B = kannan_rows(A, b, Q, t=1)
    target = np.zeros(B.shape[0], dtype=np.int64)
    target[-1] = 1
    babai_vec = babai_nearest_plane(B, target)
    s_babai = centered_mod(babai_vec[:N], Q)
    babai_ok = bool(np.array_equal(s_babai, s) or np.array_equal(s_babai, -s))

    print("[+] Wrote", params_path)
    print("[+] Wrote", cipher_path)
    print("[+] Wrote", handout_path)
    print(f"[+] Parameters: n={N}, m={M}, q={Q}, eta={ETA}, ternary secret")
    print(f"[+] Honest Regev decryption: {recovered}")
    print(f"[+] Ignore-error linear algebra recovers s: {gf_ok}")
    print(f"[+] Unreduced Babai recovers s: {babai_ok}")
    if gf_ok or babai_ok:
        print("[-] Instance is too easy (naive attacks succeeded).", file=sys.stderr)
        return 1
    print("[+] Naive attacks fail; run solver/solver.py for lattice recovery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
