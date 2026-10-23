#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FLAG = "CODEX26{tw1n_y0u_gotta_h34r_m3_0u7_0n_7hi5_0n3}"

def main() -> None:
    here = Path(__file__).resolve().parent
    chall_dir = here.parent               
    src_chall = here / "chall.py"
    dist_dir = chall_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dist_dir / "chall.zip"

    if not src_chall.is_file():
        raise SystemExit(f"[!] missing {src_chall}")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "flag.txt").write_text(FLAG + "\n")
        shutil.copy2(src_chall, td / "chall.py")

        r = subprocess.run(
            [sys.executable, "chall.py"],
            cwd=td,
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            sys.stderr.write(r.stdout)
            sys.stderr.write(r.stderr)
            raise SystemExit(f"[!] chall.py failed (rc={r.returncode})")
        print(r.stdout.strip())

        for expected in ("chall.py", "warmup.log", "flag.enc"):
            if not (td / expected).is_file():
                raise SystemExit(f"[!] chall.py did not produce {expected}")

        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(td / "chall.py",   arcname="chall.py")
            z.write(td / "warmup.log", arcname="warmup.log")
            z.write(td / "flag.enc",   arcname="flag.enc")

    size = zip_path.stat().st_size
    print(f"[+] wrote {zip_path} ({size} bytes)")
    print(f"[+] flag baked into flag.enc: {FLAG}")

if __name__ == "__main__":
    main()
