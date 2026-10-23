#!/usr/bin/env python3
"""Author solver — peel 10 encoding layers."""

from __future__ import annotations

import base64
import os
import urllib.parse

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CIPHER = os.path.normpath(os.path.join(BASE_DIR, "..", "src", "cipher.txt"))


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


def main() -> int:
    blob = open(CIPHER, encoding="utf-8").read().strip()
    text = base64.b64decode(blob).decode("ascii")
    print("[*] peeled 10 Base64")
    text = "".join(chr(int(part)) for part in text.split())
    print("[*] peeled 9 ASCII decimals")
    text = base64.b64decode(text).decode("ascii")
    print("[*] peeled 8 Base64 -> Brainfuck source")
    text = run_brainfuck(text)
    print("[*] peeled 7 Brainfuck")
    text = urllib.parse.unquote(text)
    print("[*] peeled 6 URL")
    text = text[::-1]
    print("[*] peeled 5 reverse")
    text = base64.b32decode(text).decode("ascii")
    print("[*] peeled 4 Base32")
    text = bytes.fromhex(text).decode("ascii")
    print("[*] peeled 3 Hex")
    text = rot13(text)
    print("[*] peeled 2 ROT13")
    text = base64.b64decode(text).decode("utf-8")
    print("[*] peeled 1 Base64")
    print("[+] Flag:", text)
    return 0 if text.startswith("CODEX26{") else 1


if __name__ == "__main__":
    raise SystemExit(main())
