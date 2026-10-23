#!/usr/bin/env python3
"""
CTF Challenge Solver Script
Challenge: Encrypted Presensi (Hard RE)
Format: CODEX26{...}
"""

import os
import sys
import zipfile

def solve(apk_path):
    print(f"[*] Analyzing target APK: {apk_path}")
    if not os.path.exists(apk_path):
        print(f"[-] Error: File '{apk_path}' not found!")
        sys.exit(1)

    KEY = 0x7E
    found_flag = None

    with zipfile.ZipFile(apk_path, 'r') as z:
        # --- Technique 1: Asset Payload Extraction ---
        if 'assets/flutter_assets/data.bin' in z.namelist():
            data_bin = z.read('assets/flutter_assets/data.bin')
            print(f"[+] Found asset payload 'assets/flutter_assets/data.bin' ({len(data_bin)} bytes)")
            
            # Check magic bytes 'CODE' (0x434F4445)
            if data_bin.startswith(b'CODE'):
                flag_len = data_bin[4]
                enc_key = data_bin[5]
                enc_bytes = data_bin[6:6 + flag_len]
                
                print(f"[+] Magic Header Verified: 'CODE'")
                print(f"[+] Flag Length: {flag_len} bytes")
                print(f"[+] XOR Mask Key: {hex(enc_key)}")
                print(f"[+] Encrypted Hex: {enc_bytes.hex()}")

                # Decrypt flag using XOR mask
                decrypted = bytes([b ^ enc_key for b in enc_bytes])
                try:
                    found_flag = decrypted.decode('utf-8')
                    print(f"\n==========================================")
                    print(f"[SUCCESS] Extracted Flag: {found_flag}")
                    print(f"==========================================\n")
                except UnicodeDecodeError:
                    print(f"[-] Failed to decode decrypted bytes: {decrypted}")

        # --- Technique 2: Native Binary Header Inspection ---
        if 'lib/arm64-v8a/libapp.so' in z.namelist():
            libapp_bytes = z.read('lib/arm64-v8a/libapp.so')
            header = b'CODEX_HASH_CHECK:'
            pos = libapp_bytes.find(header)
            
            if pos != -1:
                print(f"[+] Found Native Header '{header.decode()}' at libapp.so offset: {hex(pos)}")
                enc_prefix = libapp_bytes[pos + len(header) : pos + len(header) + 15]
                dec_prefix = bytes([b ^ KEY for b in enc_prefix])
                print(f"[+] Verified Native Prefix Offset: {dec_prefix.decode('latin-1', errors='ignore')}")

    if not found_flag:
        print("[-] Flag extraction failed.")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'app-release.apk'
    solve(os.path.abspath(target))
