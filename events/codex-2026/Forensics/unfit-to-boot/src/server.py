#!/usr/bin/env python3

import json
import os
import socket
import socketserver
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

HOST = os.getenv("CTF_HOST", "0.0.0.0")
PORT = int(os.getenv("CTF_PORT", "11032"))

_timeout_env = os.getenv("CTF_TIMEOUT", "180").strip()
TIMEOUT = float(_timeout_env) if _timeout_env else None

RATE_LIMIT  = int(os.getenv("CTF_RATE_LIMIT", "10"))
RATE_WINDOW = int(os.getenv("CTF_RATE_WINDOW", "60"))

BANNER = r"""
                         ___
              ___======____=---=)
            /T            \_--===)
            [ \ (0)   \~    \_-==)
             \      / )J~~    \-=)
              \\___/  )JJ~~~   \)
               \_____/JJJ~~~~   \
               / \  , \J~~~~~    \
              (-\)\=|\\\~~~~      L__
              (\\)  (\\\)_          \==__
               \V    \\\) ===_____   \\\\\\
                      \V)     \_) \\\\JJ\J\)
                                  /J\JT\JJJJ)
                                  (JJJ| \UUU)
                                   (UU)

 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
 ██                                                   ██
 ██           U N F I T   T O   B O O T               ██
 ██ ------------------------------------------------- ██
 ██  [!] Answer 25 investigator Qs to catch the flag  ██
 ██  [x] Type `exit` to close                         ██
 ██                                                   ██
 ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

> """

QNA_PATH = Path(os.getenv("CTF_QNA_FILE", "qna.json"))


def _load_questions(path: Path):
    try:
        with path.open() as f:
            data = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"[!] QnA file not found: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"[!] Invalid JSON in {path}: {e}")

    if not isinstance(data, list) or not data:
        raise SystemExit(f"[!] {path} must be a non-empty JSON array")

    required = {"num": int, "question": str, "format": str, "answer": str}
    seen_nums = set()
    for i, q in enumerate(data):
        if not isinstance(q, dict):
            raise SystemExit(f"[!] {path}[{i}] must be an object")
        for key, typ in required.items():
            if key not in q:
                raise SystemExit(f"[!] {path}[{i}] missing key '{key}'")
            if not isinstance(q[key], typ):
                raise SystemExit(
                    f"[!] {path}[{i}].{key} must be {typ.__name__}, "
                    f"got {type(q[key]).__name__}"
                )
        if q["num"] in seen_nums:
            raise SystemExit(f"[!] {path}[{i}] duplicate num={q['num']}")
        seen_nums.add(q["num"])
    return sorted(data, key=lambda q: q["num"])


QUESTIONS = _load_questions(QNA_PATH)


def _load_flag():
    for name in ("CTF_FLAG", "GZCTF_FLAG"):
        flag = os.getenv(name)
        if flag:
            if "[TEAM_HASH]" in flag:
                raise SystemExit(
                    f"[!] {name} still contains unresolved [TEAM_HASH]; "
                    "expected a resolved per-team flag"
                )
            return flag
    raise SystemExit(
        "[!] CTF_FLAG (or GZCTF_FLAG) env var is required"
    )


FLAG = _load_flag()

_state_lock = Lock()
_conn_window = {}
_wrong_total = {}
_rl_hits = {}


def _log(ip, event, **kwargs):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    extras = "".join(f" {k}={v}" for k, v in kwargs.items())
    print(f"[{ts}] [{ip}] {event}{extras}", flush=True)


def _allow_connection(ip):
    now = time.monotonic()
    with _state_lock:
        dq = _conn_window.setdefault(ip, deque())
        while dq and now - dq[0] > RATE_WINDOW:
            dq.popleft()
        if len(dq) >= RATE_LIMIT:
            _rl_hits[ip] = _rl_hits.get(ip, 0) + 1
            return False, len(dq)
        dq.append(now)
        return True, len(dq)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        ip = self.client_address[0]

        allowed, in_window = _allow_connection(ip)
        if not allowed:
            with _state_lock:
                hits = _rl_hits.get(ip, 0)
            _log(ip, "RATE_LIMITED", in_window=in_window, hits=hits)
            try:
                self.request.sendall(
                    f"\n[!] Too many connections. Try again in {RATE_WINDOW}s.\n".encode()
                )
            except Exception:
                pass
            return

        if TIMEOUT is not None:
            self.request.settimeout(TIMEOUT)

        rfile = self.request.makefile("rb", buffering=4096)

        _log(ip, "CONNECT", in_window=in_window + 1)

        try:
            self.request.sendall(BANNER.encode())
        except Exception:
            _log(ip, "DISCONNECT", stage="banner")
            return

        total = len(QUESTIONS)
        for q in QUESTIONS:
            try:
                self.request.sendall(
                    f"---------------------------------------------------------\n"
                    f"  Question {q['num']}/{total}\n"
                    f"  {q['question']}\n"
                    f"  Format: {q['format']}\n"
                    f"---------------------------------------------------------\n"
                    f">>> Answer: ".encode()
                )
                data = rfile.readline(4096)
            except socket.timeout:
                _log(ip, "TIMEOUT", q=q["num"])
                try:
                    self.request.sendall(b"\n[!] Connection timed out.\n")
                except Exception:
                    pass
                return
            except Exception:
                _log(ip, "DISCONNECT", q=q["num"])
                return

            if not data:
                _log(ip, "DISCONNECT", q=q["num"], reason="eof")
                return

            try:
                answer = data.decode(errors="replace").strip()
            except Exception:
                _log(ip, "DISCONNECT", q=q["num"], reason="decode")
                return

            if answer.lower() == "exit":
                _log(ip, "EXIT", q=q["num"])
                try:
                    self.request.sendall(b"\n[!] Line cut. Swim well, investigator.\n")
                except Exception:
                    pass
                return

            if answer.lower() != q["answer"].lower():
                with _state_lock:
                    wrong = _wrong_total.get(ip, 0) + 1
                    _wrong_total[ip] = wrong
                _log(ip, "WRONG", q=q["num"], total_wrong=wrong)
                try:
                    self.request.sendall(
                        b"[-] Wrong answer!\n"
                    )
                except Exception:
                    pass
                return

            try:
                self.request.sendall(b"[+] Correct!\n\n")
            except Exception:
                _log(ip, "DISCONNECT", q=q["num"], reason="send_fail")
                return

        _log(ip, "SOLVED")
        try:
            self.request.sendall(f"\n  FLAG: {FLAG}\n\n".encode())
        except Exception:
            pass


class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server((HOST, PORT), Handler) as s:
        print(f"[*] Running on {HOST}:{PORT}", flush=True)
        print(f"[*] Questions loaded: {len(QUESTIONS)}", flush=True)
        print(f"[*] Rate limit: {RATE_LIMIT} conn / {RATE_WINDOW}s per IP", flush=True)
        if TIMEOUT is not None:
            print(f"[*] Connection idle timeout: {TIMEOUT}s", flush=True)
        else:
            print("[*] Connection idle timeout: disabled", flush=True)
        s.serve_forever()
