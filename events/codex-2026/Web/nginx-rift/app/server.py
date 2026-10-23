#!/usr/bin/env python3
"""Simple HTTP backend with configurable delay via X-Delay header."""
import http.server
import time
import socketserver
import subprocess
import re
import os


class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Threaded so that concurrent /spray connections don't stall /debug. Without
    # this, a single slow request (X-Delay: 60) blocks every other request
    # (including the /debug leak the exploit depends on).
    daemon_threads = True
    allow_reuse_address = True


# Calibration constants: where sprayed fake cleanup structs land, relative to the
# worker heap base. Leaked via /debug so players compute target addresses directly
# instead of brute-forcing offsets. These remain part of the "answer key" only
# insofar as the LANDING (A / plus) stays hidden; the spray offset is a deliberate
# accessibility clue.
#
# recalibrate.py overwrites these (and exploit.py's list) with live-measured
# values on `verify_deploy.sh <ip> <port> calibrate`, keeping a single source of
# truth even if a rebuild drifts the layout.
SPRAY_TARGET_OFFSET = 0x85157
SPRAY_TARGET_OFFSET2 = 0xd3257


def get_worker_maps():
    """Read nginx worker process memory maps."""
    try:
        result = subprocess.run(['pgrep', '-n', 'nginx'], capture_output=True, text=True)
        pid = result.stdout.strip()
        if not pid:
            return None, None
        with open(f'/proc/{pid}/maps', 'r') as f:
            maps = f.read()
        heap_base = None
        libc_base = None
        for line in maps.splitlines():
            if '[heap]' in line and heap_base is None:
                heap_base = '0x' + line.split('-')[0]
            if 'libc.so' in line and libc_base is None and 'r--p' in line:
                libc_base = '0x' + line.split('-')[0]
        return heap_base, libc_base
    except Exception:
        return None, None


def get_system_offset(libc_base_str):
    """Calculate system() offset within libc."""
    try:
        import ctypes, ctypes.util
        libc = ctypes.CDLL(ctypes.util.find_library('c'))
        system_abs = ctypes.cast(libc.system, ctypes.c_void_p).value
        # system() offset is constant regardless of load address
        # get it by loading libc ourselves and computing from our own base
        our_base = None
        with open('/proc/self/maps') as f:
            for line in f:
                if 'libc.so' in line and 'r--p' in line:
                    our_base = int(line.split('-')[0], 16)
                    break
        if our_base is None:
            return None
        offset = system_abs - our_base
        target_base = int(libc_base_str, 16)
        system_addr = target_base + offset
        return hex(offset), hex(system_addr)
    except Exception:
        return None, None



class BackendHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Debug endpoint — intentionally left exposed (challenge hint)
        if self.path.rstrip('/') == '/debug':
            heap_base, libc_base = get_worker_maps()
            sys_offset, sys_addr = get_system_offset(libc_base) if libc_base else (None, None)
            body = (
                "=== NGINX Worker Debug Info ===\n"
                "[WARNING] Remove this endpoint before production deployment!\n\n"
                f"worker_heap_base : {heap_base}\n"
                f"worker_libc_base : {libc_base}\n"
                f"system_offset    : {sys_offset}\n"
                f"system_addr      : {sys_addr}\n"
                f"spray_offset     : {SPRAY_TARGET_OFFSET:#x}\n"
                f"spray_offset2    : {SPRAY_TARGET_OFFSET2:#x}\n"
                f"aslr_status      : {open('/proc/sys/kernel/randomize_va_space').read().strip()}\n"
                f"nginx_pid        : {subprocess.run(['pgrep','-n','nginx'],capture_output=True,text=True).stdout.strip()}\n"
            ).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        delay = float(self.headers.get('X-Delay', '5'))
        time.sleep(delay)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'backend ok\n')

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        self.rfile.read(length)
        delay = float(self.headers.get('X-Delay', '5'))
        time.sleep(delay)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'backend ok\n')

    def log_message(self, format, *args):
        pass


with ThreadingHTTPServer(("127.0.0.1", 19323), BackendHandler) as httpd:
    print("Backend on :19323")
    httpd.serve_forever()
