#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import zipfile

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from ecdsa import SECP256k1, SigningKey
from ecdsa.util import sigdecode_string

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DIST_DIR = os.path.join(ROOT_DIR, "dist")

FLAG = "CODEX26{j4rum_s3lalu_c0nd0ng_ke_ut4r4}"
SEED = 0xEC05A001
SIGNATURE_COUNT = 42
LEAK_BITS = 8
SHIFT = 256 - LEAK_BITS
BOUND = 1 << SHIFT


def hex_fixed(value: int, nbytes: int) -> str:
    return f"{value:0{nbytes * 2}x}"


def message_digest(message: str) -> bytes:
    return hashlib.sha256(message.encode("utf-8")).digest()


def derive_aes_key(secret: int) -> bytes:
    return hashlib.sha256(secret.to_bytes(32, "big")).digest()[:16]


def seal_flag(secret: int, flag: str) -> str:
    padder = padding.PKCS7(128).padder()
    raw = padder.update(flag.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.AES(derive_aes_key(secret)), modes.ECB()).encryptor()
    return (encryptor.update(raw) + encryptor.finalize()).hex()


def sample_nonce(rng: random.Random, order: int) -> tuple[int, int, int]:
    while True:
        low = rng.randrange(0, BOUND)
        pitch = rng.randrange(0, 1 << LEAK_BITS)
        nonce = (pitch << SHIFT) + low
        if 1 <= nonce < order:
            return pitch, low, nonce


def main() -> int:
    os.makedirs(SRC_DIR, exist_ok=True)
    order = SECP256k1.order
    rng = random.Random(SEED)
    secret = rng.randrange(1, order)
    signing_key = SigningKey.from_secret_exponent(secret, curve=SECP256k1)
    point = signing_key.verifying_key.pubkey.point

    signatures = []
    seen_nonces = set()
    pitches = []
    for index in range(SIGNATURE_COUNT):
        tag = f"{rng.randrange(1 << 64):016x}"
        message = f"titah:{index:02d}:{tag}"
        digest = message_digest(message)
        placed = False
        for _attempt in range(64):
            pitch, low, nonce = sample_nonce(rng, order)
            if nonce in seen_nonces:
                continue
            try:
                encoded = signing_key.sign_digest(digest, k=nonce)
            except Exception:
                continue
            r, s = sigdecode_string(encoded, order)
            if r == 0 or s == 0 or s > order // 2:
                continue
            z = int.from_bytes(digest, "big")
            if (s * nonce - z - r * secret) % order != 0:
                print("[-] Persamaan ECDSA gagal", file=sys.stderr)
                return 1
            if (nonce >> SHIFT) != pitch or (nonce & (BOUND - 1)) != low:
                print("[-] Pitch tidak sesuai nonce", file=sys.stderr)
                return 1
            signing_key.verifying_key.verify_digest(encoded, digest)
            seen_nonces.add(nonce)
            pitches.append(pitch)
            signatures.append(
                {
                    "id": index,
                    "message": message,
                    "pitch": hex_fixed(pitch, 1),
                    "r": hex_fixed(r, 32),
                    "s": hex_fixed(s, 32),
                }
            )
            placed = True
            break
        if not placed:
            print(f"[-] Gagal menempatkan segel {index}", file=sys.stderr)
            return 1

    if all(pitch == 0 for pitch in pitches):
        print("[-] Semua pitch nol; serangan MSB-nol terlalu langsung.", file=sys.stderr)
        return 1
    if len(seen_nonces) != SIGNATURE_COUNT:
        print("[-] Nonce tidak unik", file=sys.stderr)
        return 1
    if min(nonce.bit_length() for nonce in seen_nonces) < 200:
        print("[-] Ada nonce yang cukup kecil untuk ditebak.", file=sys.stderr)
        return 1

    ciphertext = seal_flag(secret, FLAG)
    if FLAG.encode("utf-8") in bytes.fromhex(ciphertext):
        print("[-] Flag terlihat di ciphertext", file=sys.stderr)
        return 1

    document = {
        "title": "Jarum yang Selalu Condong",
        "curve": "secp256k1",
        "hash": "SHA-256",
        "public_key": {
            "x": hex_fixed(point.x(), 32),
            "y": hex_fixed(point.y(), 32),
        },
        "nonce_bias": {
            "model": "msb_pitch",
            "bits": LEAK_BITS,
            "note": (
                "k = pitch*2^(256-bits) + k_low, k_low < 2^(256-bits). "
                "z = int(SHA-256(msg)). s <= n/2; do not flip s."
            ),
        },
        "ciphertext_scheme": (
            "AES-128-ECB PKCS#7. Kunci = 16 byte pertama SHA-256(skalar privat "
            "sebagai 32 byte big-endian, termasuk nol di depan)."
        ),
        "ciphertext": ciphertext,
        "signatures": signatures,
    }

    os.makedirs(DIST_DIR, exist_ok=True)
    output = os.path.join(SRC_DIR, "challenge.json")
    handout = os.path.join(DIST_DIR, "handout.zip")
    handout_src = os.path.join(ROOT_DIR, "handout_src")
    os.makedirs(handout_src, exist_ok=True)
    hs_challenge = os.path.join(handout_src, "challenge.json")
    redacted = os.path.join(handout_src, "generate_jarum_yang_selalu_condong.py")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")
    with open(output, "rb") as src, open(hs_challenge, "wb") as dst:
        dst.write(src.read())
    with zipfile.ZipFile(handout, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(hs_challenge, arcname="challenge.json")
        zf.write(redacted, arcname="generate_jarum_yang_selalu_condong.py")

    print("[+] Wrote", output)
    print("[+] Wrote", handout)
    print(f"[+] Signatures: {SIGNATURE_COUNT}, MSB pitch: {LEAK_BITS} bits")
    print(f"[+] Nonzero pitches: {sum(pitch != 0 for pitch in pitches)}")
    print("[+] Naive reuse/brute checks passed; run solver/solver.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
