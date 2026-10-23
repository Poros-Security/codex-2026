#!/usr/bin/env python3

import argparse
import hashlib
import io
import re
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path


PAGE_DATA  = 2048
PAGE_OOB   = 64
PAGE_TOTAL = PAGE_DATA + PAGE_OOB

def strip_oob(raw: bytes) -> bytes:
    assert len(raw) % PAGE_TOTAL == 0, "raw dump not a multiple of 2112"
    out = io.BytesIO()
    for i in range(len(raw) // PAGE_TOTAL):
        page = raw[i * PAGE_TOTAL:(i + 1) * PAGE_TOTAL]
        out.write(page[:PAGE_DATA])
    return out.getvalue()


ENV_SIZE = 0x20000
ENV0_OFF = 0x00100000
ENV1_OFF = 0x00120000

def parse_env(sector: bytes):
    stored_crc = int.from_bytes(sector[:4], "little")
    computed   = zlib.crc32(sector[4:]) & 0xFFFFFFFF
    valid      = stored_crc == computed
    body       = sector[5:]
    entries = {}
    for chunk in body.split(b"\x00"):
        if not chunk or chunk == b"\xff" * len(chunk):
            continue
        try:
            s = chunk.decode()
        except UnicodeDecodeError:
            continue
        if "=" in s:
            k, _, v = s.partition("=")
            entries[k] = v
    return stored_crc, valid, entries


def extract_ubi_with_ubireader(ubi_bytes: bytes):
    """Shell out to ubireader (from the ubi_reader pip package).
    Returns (fit_bytes, leb_size, user_volume_count)."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "ubi.bin").write_bytes(ubi_bytes)

        subprocess.run(
            ["ubireader_extract_files", "-o", str(td / "out"), str(td / "ubi.bin")],
            check=True, capture_output=True,
        )

        fit_paths = list((td / "out").rglob("image.fit"))
        if not fit_paths:
            raise RuntimeError("image.fit not found in extracted UBI")
        fit_bytes = fit_paths[0].read_bytes()

        info = subprocess.run(
            ["ubireader_display_info", str(td / "ubi.bin")],
            check=True, capture_output=True, text=True,
        ).stdout

        leb_size = None
        for line in info.splitlines():
            line = line.strip()
            if line.startswith("LEB size:"):
                leb_size = int(line.split(":", 1)[1].strip())
                break
        if leb_size is None:
            leb_size = 128 * 1024 - 2 * PAGE_DATA

        user_volume_count = 1
        return fit_bytes, leb_size, user_volume_count


def parse_fit_with_mkimage(fit_bytes: bytes):
    """Use mkimage -l (u-boot-tools) to enumerate images and configurations.
    Returns:
      configs: {"conf@1": {"kernel":..., "fdt":..., "ramdisk":..., "signed":bool}, ...}
      image_index: {"ramdisk@2": <int>, ...}   # index for `dumpimage -p N`
      fit_path: Path to the fit file (kept alive until caller done via tmpdir)
      tmpdir: TemporaryDirectory object (caller holds ref so it isn't cleaned)
    """
    tmp = tempfile.TemporaryDirectory()
    td = Path(tmp.name)
    fit_path = td / "image.fit"
    fit_path.write_bytes(fit_bytes)

    out = subprocess.run(
        ["mkimage", "-l", str(fit_path)],
        capture_output=True, text=True, check=True,
    ).stdout

    configs = {}
    image_index = {}
    cur_config = None

    for raw in out.splitlines():
        line = raw.strip()

        m = re.match(r"Image (\d+) \(([^)]+)\)", line)
        if m:
            idx, name = int(m.group(1)), m.group(2)
            image_index[name] = idx
            cur_config = None
            continue

        m = re.match(r"Configuration (\d+) \(([^)]+)\)", line)
        if m:
            cur_config = m.group(2)
            configs[cur_config] = {"signed": False}
            continue

        if cur_config is None:
            continue

        if line.startswith("Kernel:"):
            configs[cur_config]["kernel"] = line.split(":", 1)[1].strip()
        elif line.startswith("Init Ramdisk:"):
            configs[cur_config]["ramdisk"] = line.split(":", 1)[1].strip()
        elif line.startswith("FDT:"):
            configs[cur_config]["fdt"] = line.split(":", 1)[1].strip()
        elif line.startswith("Sign algo:"):
            configs[cur_config]["signed"] = True

    return configs, image_index, fit_path, tmp


def dumpimage_extract(fit_path: Path, index: int, out_path: Path) -> bytes:
    """Extract subimage at flat_dt index using dumpimage (u-boot-tools)."""
    subprocess.run(
        ["dumpimage", "-T", "flat_dt", "-p", str(index),
         "-o", str(out_path), str(fit_path)],
        check=True, capture_output=True,
    )
    return out_path.read_bytes()


def hkdf_derive(ikm: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    return HKDF(algorithm=hashes.SHA256(), length=length,
                salt=salt, info=info).derive(ikm)

def decrypt_audit(ct_blob: bytes, key: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce, ct = ct_blob[:12], ct_blob[12:]
    return AESGCM(key).decrypt(nonce, ct, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dist_dir", type=Path)
    ap.add_argument("--nc", metavar="HOST:PORT",
                    help="Also pipe answers to the challenge server")
    args = ap.parse_args()

    dist = args.dist_dir
    raw = (dist / "flash.bin").read_bytes()
    console = (dist / "console.log").read_text()

    print("[phase 1] Stripping OOB from raw SPI-NAND dump...")
    clean = strip_oob(raw)
    q05 = hashlib.sha256(clean).hexdigest()
    print(f"  clean image: {len(clean)} bytes,  sha256={q05}")

    q01 = "2048"
    q02 = "64"
    m = re.search(r"scheme (BCH\d+)", console)
    q03 = m.group(1) if m else "BCH8"
    q04 = str(len(clean) // (128 * 1024))
    print(f"  answers Q1-Q5: {q01}, {q02}, {q03}, {q04}, {q05[:16]}...")

    print("[phase 2] Parsing redundant U-Boot env sectors...")
    env0_sec = clean[ENV0_OFF:ENV0_OFF + ENV_SIZE]
    env1_sec = clean[ENV1_OFF:ENV1_OFF + ENV_SIZE]
    e0_crc, e0_ok, e0_vars = parse_env(env0_sec)
    e1_crc, e1_ok, e1_vars = parse_env(env1_sec)
    print(f"  env0 crc=0x{e0_crc:08x} valid={e0_ok}")
    print(f"  env1 crc=0x{e1_crc:08x} valid={e1_ok}")
    intact_vars = e0_vars if e0_ok else e1_vars
    torn = "env1" if not e1_ok else "env0"
    q06 = "0x00100000"
    q07 = f"0x{(e0_crc if e0_ok else e1_crc):08x}"
    q08 = torn
    q09 = intact_vars["bootcmd"]
    print(f"  bootcmd = {q09!r}")

    print("[phase 3] Extracting UBI + UBIFS (ubireader)...")
    UBI_OFF = 0x00200000
    UBI_SIZE = 0x00300000
    ubi = clean[UBI_OFF:UBI_OFF + UBI_SIZE]
    fit, leb_size, vol_count = extract_ubi_with_ubireader(ubi)
    print(f"  UBI: {vol_count} user volume(s), LEB size = {leb_size}")
    q10 = str(leb_size)
    q11 = str(vol_count)
    q12 = "rootfs"

    print("[phase 4] Parsing FIT with mkimage -l ...")
    q13 = hashlib.sha256(fit).hexdigest()
    print(f"  fit: {len(fit)} bytes  sha256={q13[:16]}...")
    configs, image_index, fit_path, _tmp = parse_fit_with_mkimage(fit)

    conf_nodes = [k for k in configs.keys() if k.startswith("conf")]
    q14 = str(len(conf_nodes))
    print(f"  configs found: {sorted(configs.keys())}")
    print(f"  images  found: {sorted(image_index.keys())}")

    m = re.search(r"#(conf@\d+)", q09)
    q15 = m.group(1)

    if q15 not in configs:
        raise RuntimeError(
            f"bootcmd selects {q15!r} but FIT only has {sorted(configs.keys())}"
        )

    sel_conf = configs[q15]
    q16 = sel_conf["ramdisk"]

    print("[phase 5] Extracting the unsigned ramdisk with dumpimage ...")
    idx = image_index[q16]
    rd_path = fit_path.parent / f"{q16.replace('@','_')}.bin"
    rd_bytes = dumpimage_extract(fit_path, idx, rd_path)
    q17 = hashlib.sha256(rd_bytes).hexdigest()
    print(f"  configs={q14}  selected={q15}  ramdisk={q16}  sha={q17[:16]}...")

    q18 = "CVE-2020-10648"
    q19 = "hashed-nodes"

    signed = [k for k, v in configs.items() if v.get("signed")]
    q20 = signed[0] if signed else "conf@1"

    print("[phase 6] Reading OTP-mirror + deriving key + decrypting audit log...")
    OTP_OFF = 0x00FF0000
    OTP_SIZE = 32
    otp_bytes = clean[OTP_OFF:OTP_OFF + OTP_SIZE]
    q21 = "0x00FF0000"
    q22 = "32"
    q23 = hashlib.sha256(otp_bytes).hexdigest()

    diag_cpio = rd_bytes

    def cpio_entries(buf: bytes):
        i = 0
        while i < len(buf) - 6:
            if buf[i:i+6] != b"070701":
                break
            hdr = buf[i:i+110]
            fields = [int(hdr[6+j*8:6+(j+1)*8], 16) for j in range(13)]
            (ino, mode, uid, gid, nlink, mtime, filesize,
             devmaj, devmin, rdevmaj, rdevmin, namesize, chk) = fields
            name = buf[i+110:i+110+namesize-1].decode(errors="replace")
            hdr_and_name_padded = ((110 + namesize + 3) & ~3)
            data_off = i + hdr_and_name_padded
            data = buf[data_off:data_off + filesize]
            yield name, data
            i = data_off + ((filesize + 3) & ~3)
            if name == "TRAILER!!!":
                break

    entries = dict(cpio_entries(diag_cpio))
    audit_enc = entries["opt/diag/audit.log.enc"]
    derive_sh = entries["opt/diag/derive.sh"].decode()

    m = re.search(r'salt=b"([^"]+)"', derive_sh)
    q24 = m.group(1)
    key = hkdf_derive(otp_bytes, salt=q24.encode(),
                      info=b"audit-key", length=32)
    pt = decrypt_audit(audit_enc, key)
    q25 = hashlib.sha256(pt).hexdigest()
    print(f"  audit plaintext: {len(pt)} bytes  sha={q25[:16]}...")

    flag_match = re.search(rb"CODEX26\{[^}]+\}", pt)
    print()
    print("=" * 60)
    print("Recovered flag (from audit plaintext):")
    print(f"  {flag_match.group().decode() if flag_match else '(not found)'}")
    print("=" * 60)

    answers = [q01, q02, q03, q04, q05, q06, q07, q08, q09, q10,
               q11, q12, q13, q14, q15, q16, q17, q18, q19, q20,
               q21, q22, q23, q24, q25]

    print("\nAll 25 answers:")
    for i, a in enumerate(answers, 1):
        print(f"  Q{i:02d}: {a}")

    if args.nc:
        host, _, port = args.nc.partition(":")
        port = int(port)
        pipe_to_nc(host, port, answers)


def pipe_to_nc(host: str, port: int, answers: list):
    import socket
    print(f"\nConnecting to {host}:{port}...")
    s = socket.create_connection((host, port))
    s.settimeout(10)
    buf = b""

    def read_until(marker: bytes) -> bytes:
        nonlocal buf
        while marker not in buf:
            data = s.recv(4096)
            if not data:
                return buf
            buf += data
        idx = buf.index(marker) + len(marker)
        chunk, buf = buf[:idx], buf[idx:]
        return chunk

    read_until(b">>> Answer: ")
    for i, a in enumerate(answers, 1):
        s.sendall(a.encode() + b"\n")
        if i < len(answers):
            read_until(b">>> Answer: ")

    s.settimeout(3.0)
    try:
        while True:
            data = s.recv(4096)
            if not data:
                break
            buf += data
    except socket.timeout:
        pass

    tail = buf.decode(errors="replace")
    for line in tail.splitlines():
        if "FLAG:" in line:
            print(line.strip())
            return
    print("(flag not found; last 400 chars of session:)")
    print(tail[-400:])


if __name__ == "__main__":
    main()
