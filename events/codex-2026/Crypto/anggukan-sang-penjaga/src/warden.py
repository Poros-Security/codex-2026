#!/usr/bin/env python3
"""Attendant layanan amplop (padding oracle).

Dijalankan di container: python warden.py
Kunci dibaca dari env VAULT_KEY (hex) atau berkas vault.key di samping skrip.
Menjawab hanya well-formed / tidak; tidak pernah mengembalikan isi.
"""

from __future__ import annotations

import json
import os
import socket
import struct
import sys
import threading
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

BASE_DIR = Path(__file__).resolve().parent
BLOCK = 16
MAX_BLOB = 4096


def load_vault() -> bytes:
    env = os.environ.get("VAULT_KEY", "").strip()
    if env:
        key = bytes.fromhex(env)
    else:
        path = BASE_DIR / "vault.key"
        if not path.is_file():
            raise FileNotFoundError("VAULT_KEY / vault.key missing")
        raw = path.read_text(encoding="utf-8").strip()
        key = bytes.fromhex(raw)
    if len(key) != BLOCK:
        raise ValueError("vault key must be 16 bytes")
    return key


def load_params() -> dict:
    path = BASE_DIR / "params.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def pkcs7_well_formed(plain: bytes, block: int = BLOCK) -> bool:
    if not plain or len(plain) % block != 0:
        return False
    pad = plain[-1]
    if pad < 1 or pad > block:
        return False
    return plain[-pad:] == bytes([pad]) * pad


def decrypt_raw(key: bytes, iv: bytes, ct: bytes) -> bytes:
    decryptor = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend(),
    ).decryptor()
    return decryptor.update(ct) + decryptor.finalize()


def envelope_ok(key: bytes, blob: bytes) -> bool:
    if len(blob) < 2 * BLOCK or len(blob) % BLOCK != 0 or len(blob) > MAX_BLOB:
        return False
    iv, ct = blob[:BLOCK], blob[BLOCK:]
    try:
        plain = decrypt_raw(key, iv, ct)
    except Exception:
        return False
    return pkcs7_well_formed(plain)


def recv_exact(conn: socket.socket, n: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < n:
        piece = conn.recv(n - len(chunks))
        if not piece:
            raise ConnectionError("peer closed")
        chunks.extend(piece)
    return bytes(chunks)


def handle_client(conn: socket.socket, key: bytes) -> None:
    conn.settimeout(8.0)
    try:
        while True:
            header = recv_exact(conn, 2)
            (length,) = struct.unpack(">H", header)
            if length == 0 or length > MAX_BLOB:
                conn.sendall(b"\x00")
                continue
            blob = recv_exact(conn, length)
            conn.sendall(b"\x01" if envelope_ok(key, blob) else b"\x00")
    except (ConnectionError, TimeoutError, OSError, struct.error):
        return
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()


def serve(host: str, port: int, key: bytes) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(32)
    print(f"[+] Warden listening on {host}:{port}", flush=True)
    try:
        while True:
            conn, _addr = sock.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            thread = threading.Thread(target=handle_client, args=(conn, key), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Warden stepping down", flush=True)
        return 0
    finally:
        sock.close()


def main() -> int:
    try:
        key = load_vault()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[-] {exc}", file=sys.stderr)
        return 1
    params = load_params()
    host = str(params.get("host", "0.0.0.0"))
    port = int(params.get("port", 18431))
    return serve(host, port, key)


if __name__ == "__main__":
    raise SystemExit(main())
