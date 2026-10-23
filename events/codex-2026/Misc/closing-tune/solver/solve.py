#!/usr/bin/env python3
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

STEP = 25

def data_chunk(wav: bytes) -> bytes:
    if wav[:4] != b"RIFF" or wav[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file")
    pos = 12
    while pos + 8 <= len(wav):
        length = struct.unpack_from("<I", wav, pos + 4)[0]
        start = pos + 8
        if wav[pos : pos + 4] == b"data":
            return wav[start : start + length]
        pos = start + length + (length & 1)
    raise ValueError("data chunk not found")

def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "PUSPA.wav")
    pcm = data_chunk(path.read_bytes())
    bits = "".join(str(byte & 1) for byte in pcm[::STEP])
    decoded = bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits) - 7, 8))
    found = re.search(rb"CODEX26\{[^}]*\}", decoded)
    if not found:
        raise SystemExit("flag not found")
    print(found.group().decode())

if __name__ == "__main__":
    main()
