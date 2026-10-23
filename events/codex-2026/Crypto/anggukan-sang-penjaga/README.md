# Anggukan Sang Penjaga

**Kategori:** Cryptography  
**Kesulitan:** Hard  
**Tipe:** remote (padding oracle)  
**Pembuat:** zanzan  
**Flag:** `CODEX26{4ngguk4n_p3nj4g4_m3mbuk4_p3t1}`

## PoC (step by step)

1. Unzip `dist/handout.zip` → dapat `Cipher.txt`, `params.json`, dan skrip generate (redacted).  
   `Cipher.txt` = hex dari `IV (16 byte) || ciphertext` (4 blok AES).
2. Jalankan oracle: `cd src && docker compose up --build -d` (atau `python warden.py`). Default `nc 127.0.0.1 18431`.
3. Protokol oracle: kirim `uint16` big-endian panjang blob, lalu blob `prev || C_i`. Balasan 1 byte: `0x01` = PKCS#7 valid, `0x00` = invalid. **Tidak pernah** mengembalikan plaintext.
4. Inti CBC: `P_i = Dec_K(C_i) XOR prev`. `I = Dec_K(C_i)` tetap selama `C_i` tidak diubah. Mengutak-atik `prev` mengubah plaintext yang “terlihat” oleh cek padding — tanpa tahu kunci `K`.
5. Untuk **setiap blok** ciphertext, pulihkan intermediate `I` byte-per-byte dari kanan ke kiri (`padlen = 1..16`):
   - Salin `prev` → `crafted`.
   - Byte kanan yang sudah diketahui disetel ke `I[j] XOR padlen`.
   - Brute `crafted[idx]` 0..255; kirim `crafted || C_i`.
   - Untuk `padlen = 1`: jika oracle mengangguk, **flip 1 bit** di byte sebelah kiri lalu tanya lagi — bedakan padding asli panjang vs padding `0x01` sejati (hindari false positive Vaudenay).
   - `I[idx] = tebakan XOR padlen`, lalu `P[j] = I[j] XOR prev_asli[j]`.
6. Gabung 4 blok plaintext, buang PKCS#7. Isi penuh:

```text
catatan:v1
CODEX26{4ngguk4n_p3nj4g4_m3mbuk4_p3t1}
```

7. Reference: `python solver/solver.py` (~9k query). Kunci AES **tidak** ditebak.

## Concept

Core-nya satu kelas serangan klasik: **padding oracle pada AES-CBC + PKCS#7**.

1. CBC mengikat tiap blok ke ciphertext sebelumnya (atau IV). Oracle yang hanya bilang “padding OK / tidak” cukup untuk merekonstruksi plaintext penuh (Vaudenay 2002).
2. Challenge memisahkan peran: handout = amplop (`IV||C`); remote = penjaga yang hanya mengangguk/menggeleng.
3. Ambiguity padding `0x01` vs padding lebih panjang wajib di-resolve dengan flip-test; tanpa itu solver sering dapat plaintext sampah di byte terakhir.

## Exploit Overview

1. **Oracle API:** framing `>H` + blob; respons biner 1 byte — bukan HTTP.
2. **Per-block attack:** serang satu blok per koneksi/logika; `prev` = IV untuk blok 0, `C_{i-1}` untuk blok berikutnya.
3. **Bytewise recovery:** 256 tebakan × 16 posisi × 4 blok ≈ ribuan query; parallelisasi boleh, urutan padlen harus naik.
4. **False-positive filter:** setelah anggukan pada `padlen=1`, corrupt byte `idx-1` dan pastikan oracle berubah ke `0x00`.
5. **Unpad + extract flag:** strip PKCS#7, cari baris `CODEX26{...}`.

## References & Further Reading

### 1️⃣ [Vaudenay — Security Flaws Induced by CBC Padding (EUROCRYPT 2002)](https://www.iacr.org/archive/eurocrypt2002/23320530/cbc02_e02d.pdf)
Paper klasik padding oracle. Menjelaskan cara memulihkan plaintext dari oracle validitas padding saja.

> **TL;DR** — Anggukan/gelengan PKCS#7 = oracle cukup untuk decrypt penuh AES-CBC.

### 2️⃣ [RFC 5652 / PKCS#7 padding](https://datatracker.ietf.org/doc/html/rfc5652#section-6.3)
Definisi padding `0x01` … `0x10` yang jadi sinyal oracle.

### 3️⃣ [Cryptography.io — AES CBC](https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/)
Implementasi server (`warden.py`) memakai `cryptography` AES-CBC decrypt lalu cek padding manual.

## Author / verify

```text
python solver/generate.py
cd src && docker compose up --build -d
python solver/solver.py
```
