# Sepuluh Kulit Bawang

**Kategori:** Cryptography  
**Kesulitan:** Easy  
**Tipe:** static  
**Pembuat:** zanzan  
**Flag:** `CODEX26{10_l4y3r5_0f_0ni0n_p33l}`

## PoC (step by step)

1. Unzip `dist/handout.zip` → hanya `cipher.txt` (satu baris). **Tidak** ada daftar lapisan di handout — harus dikenali dari bentuk data saat dikupas.
2. Flag diolah **10 kali dari dalam ke luar**. Kupas **dari luar ke dalam** (lapisan 10 → 1):

| Urutan kupas | Operasi | Ciri setelah sukses |
|---|---|---|
| 1 (luar) | Base64 decode | teks angka dipisah spasi |
| 2 | `chr(int(x))` per token | string Base64 lagi |
| 3 | Base64 decode | sumber **Brainfuck** (`+ - < > . [ ]`) |
| 4 | Jalankan interpreter Brainfuck | string ter-URL-encode |
| 5 | `urllib.parse.unquote` | string masih “aneh” |
| 6 | Reverse string (`[::-1]`) | Base32 alphabet |
| 7 | Base32 decode | hex digits |
| 8 | `bytes.fromhex` | teks ROT13 |
| 9 | ROT13 | Base64 terakhir |
| 10 (dalam) | Base64 decode UTF-8 | `CODEX26{...}` |

3. Checkpoint: setelah langkah 3 **harus** kelihatan kode Brainfuck; setelah langkah 10 **harus** kelihatan flag.
4. Reference: `python solver/solver.py` (baca `src/cipher.txt` atau extract dari zip dulu).

Urutan encode asli (dalam → luar), kebalikan tabel di atas:

1. Base64 (UTF-8 flag)  
2. ROT13  
3. Hex  
4. Base32  
5. Reverse  
6. URL percent-encoding  
7. Bungkus jadi program Brainfuck yang `print` string itu  
8. Base64  
9. Kode ASCII desimal dipisah spasi  
10. Base64  

## Concept

Challenge **encoding onion** (bukan kriptografi modern):

1. Tiap lapisan mengubah *representasi*, bukan menyembunyikan lewat kunci. Skill = kenali alphabet/format (Base64 vs Base32 vs hex vs Brainfuck).
2. Brainfuck di tengah memaksa pemain menulis/menjalankan interpreter kecil — filter “hanya decode online” yang tidak support BF.
3. Urutan salah satu langkah (mis. ROT13 sebelum hex) langsung rusak; PoC harus disiplin berurutan.
4. Cocok sebagai warm-up kategori crypto/encoding sebelum soal lattice/RSA/oracle.

## Exploit Overview

1. **Detect layer** dari charset: `A–Za–z0–9+/=` → Base64; `A–Z2–7=` → Base32; `0-9a-f` → hex; `+-<>.,[]` → BF.
2. **Brainfuck:** tape 30k, handle loop `[` `]` dengan jump table; output dari `.`.
3. **URL then reverse then Base32 then hex then ROT13 then Base64** — jangan ditukar.
4. Automasi: tulis pipeline 10 fungsi seperti `solver/solver.py`; print tiap layer untuk debug.

## References & Further Reading

### 1️⃣ [RFC 4648 — Base16/32/64](https://datatracker.ietf.org/doc/html/rfc4648)
Spesifikasi alphabet Base64/Base32 yang dipakai bergantian di onion.

### 2️⃣ [Brainfuck language](https://esolangs.org/wiki/Brainfuck)
Delapan perintah; challenge hanya butuh subset yang mencetak string konstan.

### 3️⃣ [ROT13](https://en.wikipedia.org/wiki/ROT13)
Substitusi Caesar +13; self-inverse (aplikasi dua kali kembali).

### 4️⃣ [URL encoding (percent-encoding)](https://developer.mozilla.org/en-US/docs/Glossary/Percent-encoding)
Lapisan `unquote` sebelum reverse/Base32.

## Author / verify

```text
python solver/generate.py
python solver/solver.py
```
