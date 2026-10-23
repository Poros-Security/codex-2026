#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DIST_DIR = os.path.join(ROOT_DIR, "dist")

FLAG = "CODEX26{4ngguk4n_p3nj4g4_m3mbuk4_p3t1}"
PLAINTEXT = "catatan:v1\n" + FLAG + "\n"
SEED = 0xA5CBC7E7
BLOCK = 16
HOST = "0.0.0.0"
PORT = 18431


def derive(label: bytes, n: int) -> bytes:
    material = hashlib.sha256(SEED.to_bytes(8, "big") + label).digest()
    return material[:n]


def pkcs7_pad(data: bytes, block: int = BLOCK) -> bytes:
    n = block - (len(data) % block)
    return data + bytes([n]) * n


def pkcs7_unpad(data: bytes, block: int = BLOCK) -> bytes:
    if not data or len(data) % block != 0:
        raise ValueError("length")
    pad = data[-1]
    if pad < 1 or pad > block or data[-pad:] != bytes([pad]) * pad:
        raise ValueError("padding")
    return data[:-pad]


def aes_cbc_encrypt(key: bytes, iv: bytes, padded: bytes) -> bytes:
    encryptor = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend(),
    ).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def aes_cbc_decrypt(key: bytes, iv: bytes, ct: bytes) -> bytes:
    decryptor = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend(),
    ).decryptor()
    return decryptor.update(ct) + decryptor.finalize()


def write_params(path: str) -> None:
    doc = {
        "cipher": "AES-128-CBC",
        "block_len": BLOCK,
        "host": HOST,
        "port": PORT,
        "note": (
            "Cipher.txt = hex(IV||C). Send uint16-be length then the blob. "
            "0x01 = AES-CBC PKCS#7 valid, else 0x00."
        ),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=2)
        handle.write("\n")


def build_handout(cipher_path: str, params_path: str, zip_path: str) -> None:
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    handout_src = os.path.join(ROOT_DIR, "handout_src")
    os.makedirs(handout_src, exist_ok=True)
    hs_cipher = os.path.join(handout_src, "Cipher.txt")
    hs_params = os.path.join(handout_src, "params.json")
    with open(cipher_path, "rb") as src, open(hs_cipher, "wb") as dst:
        dst.write(src.read())
    with open(params_path, "rb") as src, open(hs_params, "wb") as dst:
        dst.write(src.read())
    redacted = os.path.join(handout_src, "generate_anggukan_sang_penjaga.py")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(hs_cipher, arcname="Cipher.txt")
        zf.write(hs_params, arcname="params.json")
        zf.write(redacted, arcname="generate_anggukan_sang_penjaga.py")


def main() -> int:
    os.makedirs(SRC_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)

    key = derive(b"vault-key", 16)
    iv = derive(b"iv", 16)
    pt = PLAINTEXT.encode("utf-8")
    padded = pkcs7_pad(pt)
    ct = aes_cbc_encrypt(key, iv, padded)
    blob = iv + ct

    cipher_path = os.path.join(SRC_DIR, "Cipher.txt")
    params_path = os.path.join(SRC_DIR, "params.json")
    flag_path = os.path.join(SRC_DIR, "flag.txt")
    vault_path = os.path.join(SRC_DIR, "vault.key")
    handout_path = os.path.join(DIST_DIR, "handout.zip")

    with open(cipher_path, "w", encoding="utf-8") as handle:
        handle.write(blob.hex() + "\n")
    write_params(params_path)
    with open(flag_path, "w", encoding="utf-8") as handle:
        handle.write(FLAG + "\n")
    with open(vault_path, "w", encoding="utf-8") as handle:
        handle.write(key.hex() + "\n")
    build_handout(cipher_path, params_path, handout_path)

    recovered = pkcs7_unpad(aes_cbc_decrypt(key, iv, ct)).decode("utf-8")
    if recovered != PLAINTEXT or FLAG not in recovered:
        print("[-] Honest decryption failed:", repr(recovered), file=sys.stderr)
        return 1

    naive_ok = FLAG in blob.decode("latin-1", errors="replace")
    tweaked = bytearray(ct)
    tweaked[-1] ^= 0x01
    tweaked_plain = aes_cbc_decrypt(key, iv, bytes(tweaked))
    pad = tweaked_plain[-1]
    still_formed = 1 <= pad <= BLOCK and tweaked_plain[-pad:] == bytes([pad]) * pad
    if naive_ok or still_formed:
        print("[-] Instance is too easy (naive checks succeeded).", file=sys.stderr)
        return 1

    print("[+] Wrote", cipher_path)
    print("[+] Wrote", params_path)
    print("[+] Wrote", flag_path)
    print("[+] Wrote", vault_path)
    print("[+] Wrote", handout_path)
    print("[+] Naive reads fail; build src/ then run solver/solver.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
