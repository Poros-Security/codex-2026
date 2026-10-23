#!/usr/bin/env python3
"""
recalibrate.py — ADMIN-ONLY offset recalibration for NGINX Rift.

Discover the correct PREREAD_HEAP_OFFSETS on a live server build, rewrite them
back into exploit.py (the reference solver), then optionally verify.

Why: if the challenge is deployed on a host/network where the heap layout drifts
(ASLR got enabled, different bridge, changed config), the hardcoded offsets in
exploit.py stop working. This script re-measures where a 4000-byte sprayed body
actually lands, relative to the worker heap base, and patches the solver.

How it works (content-independent):
  - Landing position of a sprayed body depends only on its SIZE (4000) + request
    header size + pool config, NOT on the body's content.
  - So we spray bodies carrying a unique 8-byte marker at the start, scan the
    worker heap via /proc/<pid>/mem (docker exec) to find where they landed,
    and compute offset = body_addr - heap_base.

Requirements:
  export DOCKER_HOST=tcp://...    (docker daemon reachable)
  python3, docker client

Usage:
  python3 recalibrate.py --host <IP> --port 19321 [--verify] [--no-patch]

The spray + header MUST match exploit.py's spray() exactly, otherwise the
measured offsets won't match what exploit.py actually sends (header size shifts
the body offset by a few bytes).
"""
import argparse
import re
import socket
import struct
import subprocess
import sys
import time

# Mirror exploit.py spray() EXACTLY — Host: x, Content-Length 4000, X-Delay 60.
BODY_LEN = 4000
N_SPRAY = 20
MARKER = b"RIFTCAL1"  # 8 unique bytes


def http_get(host, port, path, timeout=5.0):
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(f"GET {path} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".encode())
        out = b""
        while True:
            d = s.recv(65536)
            if not d:
                break
            out += d
        return out


def leak(host, port):
    body = http_get(host, port, "/debug").split(b"\r\n\r\n", 1)[-1].decode("utf-8", "replace")
    heap = int(re.search(r"worker_heap_base\s*:\s*(0x[0-9a-fA-F]+)", body).group(1), 16)
    return heap


def spray_markers(host, port):
    socks = []
    for _ in range(N_SPRAY):
        body = MARKER + b"Z" * (BODY_LEN - len(MARKER))
        s = socket.create_connection((host, port), timeout=5)
        req = (b"POST /spray HTTP/1.1\r\n"
               b"Host: x\r\n"
               b"Content-Length: " + str(BODY_LEN).encode() + b"\r\n"
               # MUST match exploit.py's spray: X-Delay 60 (not 2). The delay value
               # changes how nginx pools/queues the request, shifting the body's
               # landing offset by a byte or two. Keep 60 so measured offsets
               # match what the solver actually sends.
               b"X-Delay: 60\r\n"
               b"Connection: close\r\n\r\n" + body)
        s.sendall(req)
        socks.append(s)
        time.sleep(0.01)
    time.sleep(0.5)
    return socks


def find_marker_addrs(container, heap_base, marker_hex):
    code = f'''
import subprocess
pid = int(subprocess.run(['pgrep','-n','nginx'], capture_output=True, text=True).stdout.strip())
marker = bytes.fromhex({marker_hex!r})
heap_base = {heap_base}
with open(f'/proc/{{pid}}/maps') as f:
    ranges = []
    for line in f:
        if '[heap]' in line:
            a,b = [int(x,16) for x in line.split()[0].split('-')]
            ranges.append((a,b))
with open(f'/proc/{{pid}}/mem','rb') as mem:
    for a,b in ranges:
        mem.seek(a)
        data = mem.read(b-a)
        pos = 0
        while True:
            i = data.find(marker, pos)
            if i < 0: break
            print(hex(a+i), hex(a+i-heap_base))
            pos = i + 1
'''
    r = subprocess.run(["docker", "exec", container, "python3", "-c", code],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError("docker exec scan failed: " + r.stderr)
    addrs = []
    for line in r.stdout.splitlines():
        m = re.match(r"(0x[0-9a-f]+)\s+(0x[0-9a-f]+)", line)
        if m:
            addrs.append((int(m.group(1), 16), int(m.group(2), 16)))
    return addrs


def addr_is_safe(addr):
    return all(
        (0x41 <= b <= 0x5A) or (0x61 <= b <= 0x7A) or (0x30 <= b <= 0x39)
        or b in (0x2D, 0x2E, 0x5F, 0x7E)
        for b in ((addr >> (j * 8)) & 0xFF for j in range(6))
    )


def patch_exploit(offsets):
    """Rewrite PREREAD_HEAP_OFFSETS list in exploit.py in-place."""
    path = "exploit.py"
    with open(path) as f:
        src = f.read()

    lines = []
    per = 7
    for i in range(0, len(offsets), per):
        chunk = offsets[i:i + per]
        lines.append("    " + ", ".join(hex(o) for o in chunk) + ",")
    new_block = "PREREAD_HEAP_OFFSETS = [\n" + "\n".join(lines) + "\n]"

    patched, n = re.subn(
        r"PREREAD_HEAP_OFFSETS = \[[^\]]*\]",
        new_block,
        src,
        count=1,
    )
    if n != 1:
        raise RuntimeError("could not locate PREREAD_HEAP_OFFSETS in exploit.py")

    with open(path, "w") as f:
        f.write(patched)
    print(f"[*] patched exploit.py with {len(offsets)} offsets")


def patch_server(offsets):
    """Rewrite SPRAY_TARGET_OFFSET / SPRAY_TARGET_OFFSET2 in app/server.py."""
    path = "app/server.py"
    with open(path) as f:
        src = f.read()

    o1 = offsets[0]
    o2 = offsets[1] if len(offsets) > 1 else o1

    src, n1 = re.subn(
        r"SPRAY_TARGET_OFFSET\s*=\s*0x[0-9a-fA-F]+",
        f"SPRAY_TARGET_OFFSET = {hex(o1)}",
        src,
        count=1,
    )
    src, n2 = re.subn(
        r"SPRAY_TARGET_OFFSET2\s*=\s*0x[0-9a-fA-F]+",
        f"SPRAY_TARGET_OFFSET2 = {hex(o2)}",
        src,
        count=1,
    )
    if n1 != 1 or n2 != 1:
        raise RuntimeError("could not locate SPRAY_TARGET_OFFSET constants in server.py")

    with open(path, "w") as f:
        f.write(src)
    print(f"[*] patched app/server.py: spray_offset={hex(o1)} spray_offset2={hex(o2)}")


def main():
    ap = argparse.ArgumentParser(description="admin-only offset recalibration")
    ap.add_argument("--host", default="172.17.0.1")
    ap.add_argument("--port", type=int, default=19321)
    ap.add_argument("--container", default="ctf-nginx-rift")
    ap.add_argument("--verify", action="store_true", help="run exploit.py after patching")
    ap.add_argument("--no-patch", action="store_true", help="print offsets, don't write exploit.py")
    args = ap.parse_args()

    heap = leak(args.host, args.port)
    print(f"[+] heap_base = {hex(heap)}")

    socks = spray_markers(args.host, args.port)
    try:
        found = find_marker_addrs(args.container, heap, MARKER.hex())
    finally:
        for s in socks:
            try:
                s.close()
            except Exception:
                pass

    if not found:
        print("[!] no marker body found in heap — scan failed")
        return 1

    print(f"[+] found {len(found)} body landing positions:")
    offsets = []
    for abs_addr, off in sorted(found, key=lambda x: x[1]):
        safe = addr_is_safe(heap + off)
        print(f"    {hex(abs_addr)}  off={hex(off)}  safe={safe}")
        if safe:
            offsets.append(off)

    offsets = sorted(set(offsets))
    if not offsets:
        print("[!] no URL-safe offsets; try again after restart")
        return 1

    if args.no_patch:
        print("[*] (no patch) offsets =", [hex(o) for o in offsets])
        return 0

    patch_exploit(offsets)
    patch_server(offsets)

    if args.verify:
        print("[*] verifying with exploit.py ...")
        r = subprocess.run(["python3", "exploit.py", "--host", args.host,
                            "--port", str(args.port), "--tries", "6"])
        return r.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
