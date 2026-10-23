#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import secrets

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

FLAG = "CODEX26{REDACTED}"
SEED = None
BLOCK = 16
HOST = "127.0.0.1"
PORT = 18431


def pkcs7_pad(data: bytes, block: int = BLOCK) -> bytes:
    n = block - (len(data) % block)
    return data + bytes([n]) * n


def aes_cbc_encrypt(key: bytes, iv: bytes, padded: bytes) -> bytes:
    encryptor = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend(),
    ).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def main() -> None:
    key = secrets.token_bytes(16)
    iv = secrets.token_bytes(16)
    plaintext = f"catatan:v1\n{FLAG}\n".encode("utf-8")
    ct = aes_cbc_encrypt(key, iv, pkcs7_pad(plaintext))
    blob = iv + ct

    os.makedirs("out", exist_ok=True)
    with open(os.path.join("out", "Cipher.txt"), "w", encoding="utf-8") as handle:
        handle.write(blob.hex() + "\n")
    params = {
        "cipher": "AES-128-CBC",
        "block_len": BLOCK,
        "host": HOST,
        "port": PORT,
        "note": (
            "Cipher.txt = hex(IV||C). Send uint16-be length then the blob. "
            "0x01 = AES-CBC PKCS#7 valid, else 0x00."
        ),
    }
    with open(os.path.join("out", "params.json"), "w", encoding="utf-8") as handle:
        json.dump(params, handle, indent=2)
        handle.write("\n")

    print("[*] Wrote sample out/Cipher.txt and out/params.json")
    print("[*] Key/IV/FLAG redacted — CTF handout Cipher.txt is a different instance")
    print("[*] Connect to the remote warden for the real oracle (see challenge.yml)")


if __name__ == "__main__":
    main()
