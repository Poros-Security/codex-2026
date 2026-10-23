#!/usr/bin/env python3
"""Author PoC: recover the sealed record by querying the local warden.

Byte-at-a-time well-formedness attack against AES-CBC + PKCS#7.
Expects public files at ../src/Cipher.txt and ../src/params.json.
Starts src/warden.py if nothing is already listening.
"""

from __future__ import annotations

import json
import os
import re
import socket
import struct
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "src"))
BLOCK = 16


def load_params(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_blob(path: str) -> bytes:
    with open(path, "r", encoding="utf-8") as handle:
        hex_str = "".join(line.strip() for line in handle if line.strip())
    blob = bytes.fromhex(hex_str)
    if len(blob) < 2 * BLOCK or len(blob) % BLOCK != 0:
        raise ValueError("Cipher.txt is not a whole number of AES blocks")
    return blob


def wait_for_port(host: str, port: int, timeout: float = 8.0) -> None:
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            probe = socket.create_connection((host, port), timeout=0.4)
            probe.close()
            return
        except OSError as exc:
            last_err = exc
            time.sleep(0.05)
    raise RuntimeError(f"warden did not bind {host}:{port}: {last_err}")


def ensure_warden(host: str, port: int):
    try:
        probe = socket.create_connection((host, port), timeout=0.4)
        probe.close()
        return None
    except OSError:
        pass
    warden = os.path.join(SRC_DIR, "warden.py")
    print(f"[*] No listener on {host}:{port}; starting {warden}")
    proc = subprocess.Popen(
        [sys.executable, warden],
        cwd=SRC_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_port(host, port)
    except Exception:
        proc.terminate()
        raise
    return proc


class Warden:
    """Persistent TCP client for the length-prefixed well-formedness service."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.sock = None
        self.queries = 0
        self._connect()

    def _connect(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def well_formed(self, iv: bytes, block: bytes) -> bool:
        blob = iv + block
        packet = struct.pack(">H", len(blob)) + blob
        for _attempt in range(3):
            try:
                self.sock.sendall(packet)
                reply = self.sock.recv(1)
                if not reply:
                    raise ConnectionError("empty reply")
                self.queries += 1
                return reply == b"\x01"
            except OSError:
                self._connect()
        raise RuntimeError("warden stopped answering")

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None


def decrypt_block(warden: Warden, prev: bytes, block: bytes) -> bytes:
    """Recover 16 plaintext bytes of `block` using `prev` as the CBC IV."""
    if len(prev) != BLOCK or len(block) != BLOCK:
        raise ValueError("block size")
    intermediate = [0] * BLOCK
    for padlen in range(1, BLOCK + 1):
        idx = BLOCK - padlen
        crafted = bytearray(prev)
        for i in range(idx + 1, BLOCK):
            crafted[i] = intermediate[i] ^ padlen
        found = None
        # Prefer values that already produce this pad on the real last block.
        order = list(range(256))
        for guess in order:
            crafted[idx] = guess
            if not warden.well_formed(bytes(crafted), block):
                continue
            if padlen < BLOCK:
                probe = bytearray(crafted)
                probe[idx - 1] ^= 0x01
                if not warden.well_formed(bytes(probe), block):
                    # Validity depended on an earlier byte: longer padding, skip.
                    continue
            found = guess
            break
        if found is None:
            raise RuntimeError(f"no well-formed guess at padlen={padlen}")
        intermediate[idx] = found ^ padlen
    return bytes(intermediate[i] ^ prev[i] for i in range(BLOCK))


def pkcs7_unpad(data: bytes) -> bytes:
    if not data or len(data) % BLOCK != 0:
        raise ValueError("length")
    pad = data[-1]
    if pad < 1 or pad > BLOCK or data[-pad:] != bytes([pad]) * pad:
        raise ValueError("padding")
    return data[:-pad]


def extract_flag(text: str) -> str | None:
    match = re.search(r"CODEX26\{[A-Za-z0-9_]+\}", text)
    return match.group(0) if match else None


def main() -> int:
    params_path = os.path.join(SRC_DIR, "params.json")
    cipher_path = os.path.join(SRC_DIR, "Cipher.txt")
    if not os.path.isfile(params_path) or not os.path.isfile(cipher_path):
        print("[-] Missing public files in src/", file=sys.stderr)
        return 1

    params = load_params(params_path)
    # Container binds 0.0.0.0; author solver connects locally.
    host = str(params.get("host", "127.0.0.1"))
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    port = int(params.get("port", 18431))
    blob = load_blob(cipher_path)
    iv, ct = blob[:BLOCK], blob[BLOCK:]
    nblocks = len(ct) // BLOCK
    print(f"[*] Envelope: IV + {nblocks} ciphertext blocks ({len(ct)} bytes)")

    spawned = ensure_warden(host, port)
    warden = Warden(host, port)
    t0 = time.time()
    try:
        prev = iv
        plain = bytearray()
        for i in range(nblocks):
            block = ct[i * BLOCK : (i + 1) * BLOCK]
            print(f"[*] Recovering block {i + 1}/{nblocks}")
            piece = decrypt_block(warden, prev, block)
            plain.extend(piece)
            prev = block
        elapsed = time.time() - t0
        padded = bytes(plain)
        body = pkcs7_unpad(padded)
        text = body.decode("utf-8")
        print(f"[*] Queries: {warden.queries} in {elapsed:.2f}s")
        print("[+] Recovered body:")
        print(text)
        flag = extract_flag(text)
        if flag is None:
            print("[-] Tidak menemukan CODEX26{...} dalam plaintext", file=sys.stderr)
            return 1
        print("[+] Recovered flag:", flag)
        return 0
    finally:
        warden.close()
        if spawned is not None:
            spawned.terminate()
            try:
                spawned.wait(timeout=2)
            except subprocess.TimeoutExpired:
                spawned.kill()


if __name__ == "__main__":
    raise SystemExit(main())
