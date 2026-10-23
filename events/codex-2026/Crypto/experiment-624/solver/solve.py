#!/usr/bin/env python3

import sys
import zipfile
from pathlib import Path

from mt19937predictor import MT19937Predictor


def load_bundle(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        warmup = z.read("warmup.log").decode()
        sealed = z.read("flag.enc")
    ints = [int(line) for line in warmup.splitlines() if line.strip()]
    if len(ints) < 624:
        raise SystemExit(f"[!] need >=624 warmup samples, got {len(ints)}")
    return ints[:624], sealed


def recover_flag(warmup_ints, sealed_bytes):
    predictor = MT19937Predictor()
    for x in warmup_ints:
        predictor.setrandbits(x, 32)
    return bytes(b ^ predictor.getrandbits(8) for b in sealed_bytes)


def main():
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        zip_path = Path(__file__).resolve().parent.parent / "dist" / "chall.zip"

    if not zip_path.is_file():
        raise SystemExit(f"[!] chall.zip not found at {zip_path}")

    print(f"[*] loading bundle: {zip_path}")
    warmup, sealed = load_bundle(zip_path)

    print(f"[*] fed {len(warmup)} calibration samples into MT19937Predictor")
    print(f"[*] sealed project: {len(sealed)} bytes")

    flag = recover_flag(warmup, sealed)
    print(f"[+] flag: {flag.decode(errors='replace')}")


if __name__ == "__main__":
    main()
