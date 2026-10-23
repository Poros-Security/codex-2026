#!/usr/bin/env python3

import os
import random
import time

FLAG_PATH = "flag.txt"
WARMUP_LOG = "warmup.log"
SEALED = "flag.enc"

CALIBRATION_ROUNDS = 624

def main() -> None:
    if not os.path.exists(FLAG_PATH):
        raise SystemExit(
            f"[!] {FLAG_PATH} not found. This script is shown for reference; "
            "the flag is not distributed with the challenge bundle."
        )

    with open(FLAG_PATH, "rb") as f:
        flag = f.read().strip()

    seed = int(time.time())
    random.seed(seed)

    with open(WARMUP_LOG, "w") as w:
        for _ in range(CALIBRATION_ROUNDS):
            w.write(f"{random.getrandbits(32)}\n")

    sealed = bytearray()
    for b in flag:
        sealed.append(b ^ random.getrandbits(8))

    with open(SEALED, "wb") as f:
        f.write(bytes(sealed))

    print(f"[+] seeded @ {seed}")
    print(f"[+] wrote {CALIBRATION_ROUNDS} calibration samples -> {WARMUP_LOG}")
    print(f"[+] sealed {len(flag)}-byte project -> {SEALED}")

if __name__ == "__main__":
    main()
