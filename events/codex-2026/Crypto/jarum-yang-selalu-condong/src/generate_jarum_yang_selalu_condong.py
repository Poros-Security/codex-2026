#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import random
import secrets

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from ecdsa import SECP256k1, SigningKey
from ecdsa.util import sigdecode_string

FLAG = "CODEX26{REDACTED}"
SEED = None
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


def main() -> None:
    order = SECP256k1.order
    rng = random.Random(secrets.randbits(64))
    secret = rng.randrange(1, order)
    signing_key = SigningKey.from_secret_exponent(secret, curve=SECP256k1)
    point = signing_key.verifying_key.pubkey.point

    signatures = []
    for index in range(SIGNATURE_COUNT):
        tag = f"{rng.randrange(1 << 64):016x}"
        message = f"titah:{index:02d}:{tag}"
        digest = message_digest(message)
        while True:
            pitch, _low, nonce = sample_nonce(rng, order)
            encoded = signing_key.sign_digest(digest, k=nonce)
            r, s = sigdecode_string(encoded, order)
            if r == 0 or s == 0 or s > order // 2:
                continue
            signatures.append(
                {
                    "id": index,
                    "message": message,
                    "pitch": hex_fixed(pitch, 1),
                    "r": hex_fixed(r, 32),
                    "s": hex_fixed(s, 32),
                }
            )
            break

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
            "sebagai 32 byte big-endian)."
        ),
        "ciphertext": seal_flag(secret, FLAG),
        "signatures": signatures,
    }

    os.makedirs("out", exist_ok=True)
    with open(os.path.join("out", "challenge.json"), "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")
    print("[*] Wrote sample out/challenge.json (FLAG/SEED redacted; not the CTF file)")
    print("[*] Public challenge file in this zip: challenge.json")


if __name__ == "__main__":
    main()
