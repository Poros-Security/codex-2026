#!/usr/bin/env python3

import ast
import socket
import subprocess
import sys
import threading

BLOCKED_CHARS = frozenset("_#@$`\\\t")

DISALLOWED_STMT = (
    ast.Import, ast.ImportFrom,
    ast.Global, ast.Nonlocal,
    ast.Lambda,
    ast.FunctionDef, ast.AsyncFunctionDef,
    ast.ClassDef,
)
NAME_BLOCKLIST = frozenset({
    "eval", "exec", "compile",
    "open", "input", "breakpoint",
    "__import__", "__builtins__",
})


def _ast_ok(tree: ast.AST) -> tuple[bool, str]:
    for node in ast.walk(tree):
        if isinstance(node, DISALLOWED_STMT):
            return False, f"statement type {type(node).__name__}"
        if isinstance(node, ast.Name) and node.id in NAME_BLOCKLIST:
            return False, f"name '{node.id}'"
    return True, ""


import builtins as _builtins
SAFE_BUILTINS = {
    k: v for k, v in vars(_builtins).items() if k not in NAME_BLOCKLIST
}

_STARTUP_DONE = False

DENIED_EVENTS = (
    "import",
    "open",
    "subprocess.Popen",
    "os.system",
    "os.exec",
    "os.spawn",
    "pickle.find_class",
    "code.__new__",
    "marshal.loads",
    "builtins.input",
    "builtins.breakpoint",
    "cpython.run_command",
)


def _audit_hook(event, args):
    if not _STARTUP_DONE:
        return
    for prefix in DENIED_EVENTS:
        if event == prefix or event.startswith(prefix):
            raise RuntimeError(f"[audit] denied event: {event}")


sys.addaudithook(_audit_hook)


def boot(src: str, out) -> None:
    if any(ch in BLOCKED_CHARS for ch in src):
        out.write("source contains a forbidden character\n")
        return
    try:
        tree = ast.parse(src, mode="exec")
    except SyntaxError as e:
        out.write(f"[!] parse error: {e}\n")
        return
    ok, why = _ast_ok(tree)
    if not ok:
        out.write(f"[!] AST rejected: {why}\n")
        return
    ns = {"__builtins__": SAFE_BUILTINS}
    old_stdout = sys.stdout
    sys.stdout = out
    try:
        exec(compile(tree, "<jail>", "exec"), ns, ns)
    except Exception as e:
        out.write(f"[!] runtime: {type(e).__name__}: {e}\n")
    finally:
        sys.stdout = old_stdout


BANNER = (
    "\n"
    " ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
    "\n"
    "  ██████╗ ██╗  ██╗ ██████╗ ████████╗██╗\n"
    " ██╔════╝ ██║  ██║██╔═══██╗╚══██╔══╝██║\n"
    " ██║  ███╗███████║██║   ██║   ██║   ██║\n"
    " ██║   ██║██╔══██║██║   ██║   ██║   ██║\n"
    " ╚██████╔╝██║  ██║╚██████╔╝   ██║   ██║\n"
    "  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝\n"
    "\n"
    " ██╗   ██╗ █████╗ ██╗  ██╗██╗     ████████╗\n"
    " ██║   ██║██╔══██╗██║  ██║██║     ╚══██╔══╝\n"
    " ██║   ██║███████║██║  ██║██║        ██║   \n"
    " ╚██╗ ██╔╝██╔══██║██║  ██║██║        ██║   \n"
    "  ╚████╔╝ ██║  ██║╚██████╔╝███████╗  ██║   \n"
    "   ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝  ╚═╝   \n"
    "\n"
    " ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
    "\n> "
)


class SocketWriter:
    def __init__(self, conn: socket.socket):
        self.conn = conn

    def write(self, s):
        if not isinstance(s, (bytes, bytearray)):
            s = str(s).encode("utf-8", errors="replace")
        try:
            self.conn.sendall(s)
        except Exception:
            pass

    def flush(self):
        pass


def handle(conn: socket.socket) -> None:
    conn.settimeout(15)
    conn.sendall(BANNER.encode("utf-8"))
    buf = b""
    try:
        while len(buf) < 4096:
            chunk = conn.recv(4096 - len(buf))
            if not chunk:
                break
            buf += chunk
    except socket.timeout:
        pass
    src = buf.decode("utf-8", errors="replace")
    out = SocketWriter(conn)
    try:
        boot(src, out)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main():
    global _STARTUP_DONE
    host = "0.0.0.0"
    port = 11031
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(64)
    print(f"[+] dip-pen listening on {host}:{port}", flush=True)
    _STARTUP_DONE = True
    while True:
        conn, addr = s.accept()
        t = threading.Thread(target=handle, args=(conn,), daemon=True)
        t.start()


if __name__ == "__main__":
    main()