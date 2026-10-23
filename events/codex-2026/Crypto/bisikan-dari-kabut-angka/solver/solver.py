#!/usr/bin/env python3
"""Author PoC: recover the LWE secret by Kannan embedding + LLL/BKZ, then decrypt.

Expects the public files at ../src/params.json and ../src/Cipher.txt.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from fpylll import BKZ, IntegerMatrix, LLL

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "src"))


def centered_mod(x: np.ndarray, q: int) -> np.ndarray:
    r = np.remainder(x, q).astype(np.int64)
    return np.where(r > q // 2, r - q, r)


def load_params(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    A = np.array(data["A"], dtype=np.int64)
    b = np.array(data["b"], dtype=np.int64)
    return data, A, b


def load_cipher(path: str):
    pairs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            left, right = line.split(";")
            a = np.array([int(x) for x in left.split(",")], dtype=np.int64)
            u = int(right)
            pairs.append((a, u))
    return pairs


def kannan_rows(A: np.ndarray, b: np.ndarray, q: int, t: int = 1) -> np.ndarray:
    """Rows are basis vectors of the Kannan embedding of b = A s + e (mod q)."""
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


def to_fpylll(B: np.ndarray) -> IntegerMatrix:
    d = B.shape[0]
    M = IntegerMatrix(d, d)
    for i in range(d):
        for j in range(d):
            M[i, j] = int(B[i, j])
    return M


def residual_ok(s: np.ndarray, A: np.ndarray, b: np.ndarray, q: int, eta: int) -> bool:
    e = centered_mod((b - A @ s) % q, q)
    return bool(np.max(np.abs(e)) <= eta)


def extract_secret(M: IntegerMatrix, A: np.ndarray, b: np.ndarray, q: int, eta: int):
    n = A.shape[1]
    for i in range(M.nrows):
        row_s = np.array([int(M[i, j]) for j in range(n)], dtype=np.int64)
        for sign in (1, -1):
            s = centered_mod(sign * row_s, q)
            if residual_ok(s, A, b, q, eta):
                return s
    return None


def reduce_until_secret(M: IntegerMatrix, A: np.ndarray, b: np.ndarray, q: int, eta: int):
    print("[*] LLL-reducing Kannan embedding (dim = {})".format(M.nrows))
    t0 = time.time()
    LLL.reduction(M)
    print(f"[*] LLL finished in {time.time() - t0:.2f}s")
    s = extract_secret(M, A, b, q, eta)
    if s is not None:
        print("[+] Secret recovered after LLL")
        return s, "LLL"

    for block in (15, 20, 25, 30, 40):
        print(f"[*] BKZ-{block}")
        t0 = time.time()
        par = BKZ.Param(block_size=block, max_loops=8, flags=BKZ.AUTO_ABORT)
        BKZ.reduction(M, par)
        print(f"[*] BKZ-{block} finished in {time.time() - t0:.2f}s")
        s = extract_secret(M, A, b, q, eta)
        if s is not None:
            print(f"[+] Secret recovered after BKZ-{block}")
            return s, f"BKZ-{block}"
    return None, None


def decrypt_flag(s: np.ndarray, pairs, q: int) -> str:
    bits = []
    for a, u in pairs:
        t = int(centered_mod(np.array([(int(u) - int(a @ s)) % q], dtype=np.int64), q)[0])
        bits.append(1 if abs(t) > q / 4 else 0)
    out = []
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i : i + 8]:
            byte = (byte << 1) | bit
        out.append(byte)
    return bytes(out).decode("utf-8")


def main() -> int:
    params_path = os.path.join(SRC_DIR, "params.json")
    cipher_path = os.path.join(SRC_DIR, "Cipher.txt")
    if not os.path.isfile(params_path) or not os.path.isfile(cipher_path):
        print("[-] Missing public files in src/", file=sys.stderr)
        return 1

    params, A, b = load_params(params_path)
    pairs = load_cipher(cipher_path)
    q = int(params["q"])
    eta = int(params["eta"])
    n = int(params["n"])
    m = int(params["m"])
    print(f"[*] Loaded LWE instance n={n} m={m} q={q} eta={eta}, {len(pairs)} ciphertext bits")

    B = kannan_rows(A, b, q, t=1)
    M = to_fpylll(B)
    s, how = reduce_until_secret(M, A, b, q, eta)
    if s is None:
        print("[-] Lattice reduction did not recover a plausible secret", file=sys.stderr)
        return 1

    e = centered_mod((b - A @ s) % q, q)
    print(f"[+] Residual error max |e_i| = {int(np.max(np.abs(e)))} (via {how})")
    try:
        flag = decrypt_flag(s, pairs, q)
    except UnicodeDecodeError:
        print("[-] Decryption did not yield UTF-8", file=sys.stderr)
        return 1

    print("[+] Recovered flag:", flag)
    if not flag.startswith("CODEX26{") or not flag.endswith("}"):
        print("[-] Flag format mismatch", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
