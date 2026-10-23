#!/usr/bin/env python3
"""Author PoC: pulihkan skalar ECDSA dari nonce ber-pitch lewat HNP + LLL.

Setiap persamaan berbentuk k_low ≡ b + a*d (mod n), dengan k_low < 2^(256-bits).
Lattice Kannan/Boneh–Venkatesan yang diskalakan bilangan bulat kemudian
direduksi dengan LLL. Ekspektasi runtime: sekitar satu menit.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from ecdsa import SECP256k1, SigningKey
from sympy import Matrix

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CHALLENGE = os.path.normpath(os.path.join(BASE_DIR, "..", "src", "challenge.json"))


def load_challenge(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def digest_int(message: str) -> int:
    return int.from_bytes(hashlib.sha256(message.encode("utf-8")).digest(), "big")


def pkcs7_unpad(data: bytes) -> bytes:
    if not data or len(data) % 16 != 0:
        raise ValueError("length")
    pad = data[-1]
    if pad < 1 or pad > 16 or data[-pad:] != bytes([pad]) * pad:
        raise ValueError("padding")
    return data[:-pad]


def open_chest(secret: int, ciphertext_hex: str) -> str:
    key = hashlib.sha256(secret.to_bytes(32, "big")).digest()[:16]
    decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    raw = decryptor.update(bytes.fromhex(ciphertext_hex)) + decryptor.finalize()
    return pkcs7_unpad(raw).decode("utf-8")


def pubkey_of(secret: int):
    point = SigningKey.from_secret_exponent(secret, curve=SECP256k1).verifying_key.pubkey.point
    return point.x(), point.y()


def hnp_samples(challenge: dict, order: int):
    bits = int(challenge["nonce_bias"]["bits"])
    shift = 256 - bits
    samples = []
    for entry in challenge["signatures"]:
        r = int(entry["r"], 16)
        s = int(entry["s"], 16)
        pitch = int(entry["pitch"], 16)
        z = digest_int(entry["message"])
        s_inv = pow(s, -1, order)
        pitch_term = pitch << shift
        a = (r * s_inv) % order
        b = ((z - s * pitch_term) * s_inv) % order
        samples.append((a, b))
    return samples, 1 << shift


def build_lattice(samples, order: int, bound: int) -> Matrix:
    """Integer embedding of k_low = b + a*d - λ*n, |k_low| < bound.

    Baris target (k_low diskalakan n, lalu B*d, lalu n*B) seimbang bit-nya.
    """
    m = len(samples)
    dim = m + 2
    rows = [[0] * dim for _ in range(dim)]
    nn = order * order
    for i, (a, b) in enumerate(samples):
        rows[i][i] = nn
        rows[m][i] = a * order
        rows[m + 1][i] = b * order
    rows[m][m] = bound
    rows[m + 1][m + 1] = order * bound
    return Matrix(rows)


def candidates_from_reduced(reduced: Matrix, order: int, bound: int):
    target = order * bound
    for row in reduced.tolist():
        last = row[-1]
        secret_slot = row[-2]
        if last == target and secret_slot % bound == 0:
            yield int((secret_slot // bound) % order)
        elif last == -target and (-secret_slot) % bound == 0:
            yield int(((-secret_slot) // bound) % order)


def main() -> int:
    if not os.path.isfile(CHALLENGE):
        print("[-] Missing src/challenge.json", file=sys.stderr)
        return 1

    challenge = load_challenge(CHALLENGE)
    order = SECP256k1.order
    want_x = int(challenge["public_key"]["x"], 16)
    want_y = int(challenge["public_key"]["y"], 16)
    samples, bound = hnp_samples(challenge, order)
    print(f"[*] {len(samples)} signatures, k_low < 2^{bound.bit_length() - 1}")

    print(f"[*] Building {len(samples) + 2}-dimensional lattice")
    lattice = build_lattice(samples, order, bound)
    print("[*] LLL reduction")
    started = time.time()
    reduced = lattice.lll(delta=0.99)
    print(f"[*] LLL finished in {time.time() - started:.1f}s")

    for secret in candidates_from_reduced(reduced, order, bound):
        got_x, got_y = pubkey_of(secret)
        if (got_x, got_y) != (want_x, want_y):
            continue
        try:
            flag = open_chest(secret, challenge["ciphertext"])
        except (ValueError, UnicodeDecodeError):
            continue
        if not (flag.startswith("CODEX26{") and flag.endswith("}")):
            continue
        print("[+] Recovered flag:", flag)
        return 0

    print("[-] Lattice reduction did not yield the private scalar", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
