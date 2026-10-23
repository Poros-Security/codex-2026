#!/usr/bin/env python3

from __future__ import annotations

import base64
import os
import urllib.parse
import zipfile

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DIST_DIR = os.path.join(ROOT_DIR, "dist")

FLAG = "CODEX26{10_l4y3r5_0f_0ni0n_p33l}"


def rot13(text: str) -> str:
    out = []
    for char in text:
        if "a" <= char <= "z":
            out.append(chr((ord(char) - 97 + 13) % 26 + 97))
        elif "A" <= char <= "Z":
            out.append(chr((ord(char) - 65 + 13) % 26 + 65))
        else:
            out.append(char)
    return "".join(out)


def to_brainfuck(text: str) -> str:
    parts: list[str] = []
    current = 0
    for char in text:
        target = ord(char)
        delta = target - current
        if delta > 0:
            parts.append("+" * delta)
        elif delta < 0:
            parts.append("-" * (-delta))
        parts.append(".")
        current = target
    return "".join(parts)


def run_brainfuck(code: str) -> str:
    tape = [0] * 30000
    pointer = 0
    output: list[str] = []
    stack: list[int] = []
    jumps: dict[int, int] = {}
    for index, command in enumerate(code):
        if command == "[":
            stack.append(index)
        elif command == "]":
            start = stack.pop()
            jumps[start] = index
            jumps[index] = start
    pc = 0
    while pc < len(code):
        command = code[pc]
        if command == ">":
            pointer += 1
        elif command == "<":
            pointer -= 1
        elif command == "+":
            tape[pointer] = (tape[pointer] + 1) % 256
        elif command == "-":
            tape[pointer] = (tape[pointer] - 1) % 256
        elif command == ".":
            output.append(chr(tape[pointer]))
        elif command == "[" and tape[pointer] == 0:
            pc = jumps[pc]
        elif command == "]" and tape[pointer] != 0:
            pc = jumps[pc]
        pc += 1
    return "".join(output)


def encode_layers(flag: str) -> str:
    text = flag
    text = base64.b64encode(text.encode("utf-8")).decode("ascii")
    text = rot13(text)
    text = text.encode("ascii").hex()
    text = base64.b32encode(text.encode("ascii")).decode("ascii")
    text = text[::-1]
    text = urllib.parse.quote(text, safe="")
    text = to_brainfuck(text)
    text = base64.b64encode(text.encode("ascii")).decode("ascii")
    text = " ".join(str(ord(char)) for char in text)
    text = base64.b64encode(text.encode("ascii")).decode("ascii")
    return text


def decode_layers(blob: str) -> str:
    text = base64.b64decode(blob).decode("ascii")
    text = "".join(chr(int(part)) for part in text.split())
    text = base64.b64decode(text).decode("ascii")
    text = run_brainfuck(text)
    text = urllib.parse.unquote(text)
    text = text[::-1]
    text = base64.b32decode(text).decode("ascii")
    text = bytes.fromhex(text).decode("ascii")
    text = rot13(text)
    text = base64.b64decode(text).decode("utf-8")
    return text


def main() -> int:
    os.makedirs(SRC_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)

    blob = encode_layers(FLAG)
    recovered = decode_layers(blob)
    if recovered != FLAG:
        raise SystemExit(f"round-trip failed: {recovered!r}")

    cipher_path = os.path.join(SRC_DIR, "cipher.txt")
    with open(cipher_path, "w", encoding="utf-8") as handle:
        handle.write(blob + "\n")

    handout = os.path.join(DIST_DIR, "handout.zip")
    with zipfile.ZipFile(handout, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(cipher_path, arcname="cipher.txt")

    print("[+] Wrote", cipher_path)
    print("[+] Wrote", handout)
    print("[+] Flag length", len(FLAG), "cipher length", len(blob))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
