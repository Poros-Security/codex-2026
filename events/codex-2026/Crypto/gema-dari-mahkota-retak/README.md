# Gema dari Mahkota Retak

**Kategori:** Cryptography  
**Kesulitan:** Medium–Hard  
**Tipe:** static  
**Pembuat:** zanzan  
**Flag:** `CODEX26{r3t4k4n_m3mb0c0rk4n_m4hk0t4}`

## PoC (step by step)

1. Unzip `dist/handout.zip` → `challenge.json` (+ generate JS redacted).
2. Baca: modulus `n`, `e = 0x10001`, **64** pasangan `(pesan, signature)`, satu `ciphertext`.
3. Verifikasi tiap segel sebagai **RSA textbook** (bukan PKCS#1 v1.5 pad):

```text
m = int.from_bytes(SHA-256(pesan), "big")
s = int(signature, 16)
v = pow(s, e, n)
```

   - Jika `v == m` → segel valid, skip.
   - Jika tidak → kandidat “retak”.
4. Di antara segel invalid ada **dua** jenis:
   - **Fault CRT (Bellcore/Lenstra):** satu cabang CRT (`mod p` atau `mod q`) rusak →  
     `gcd(s^e − m, n)` menghasilkan faktor sejati (`p` atau `q`).
   - **Segel rusak biasa** (korupsi setelah tanda tangan) → `gcd` biasanya `1` — **bukan** faktor.
5. **Jangan** berhenti di invalid pertama tanpa cek GCD. Loop semua 64; ambil `g` dengan `1 < g < n`.
6. `q = n // g` (atau sebaliknya); pastikan `g * q == n`.
7. `φ = (g−1)(q−1)`, `d = inverse(e, φ)`.
8. Ciphertext = `flag_int^e mod n` (UTF-8 flag sebagai integer big-endian, **tanpa** PKCS).  
   `pt = pow(ciphertext, d, n)` → bytes → UTF-8 → flag.
9. Reference: `node solver/solver.js`.

## Concept

Ini demonstrasi **RSA-CRT fault attack** (Bellcore / Lenstra):

1. Implementasi CRT hitung `mp = m^d mod p`, `mq = m^d mod q`, gabung. Satu fault di salah satu cabang membuat signature salah secara keseluruhan tetapi masih “benar” modulo faktor yang utuh.
2. Akibatnya `s^e ≡ m (mod q)` tapi tidak modulo `p` (atau sebaliknya) → `gcd(s^e − m, n)` bocorkan faktor.
3. Challenge menyisipkan **decoy** signature invalid agar pemain yang `break` terlalu cepat gagal memfaktorkan.
4. Setelah `n` terbagi, RSA textbook sisanya trivial (phi + decrypt).

## Exploit Overview

1. **Hash pesan** SHA-256 → integer `m` (big-endian).
2. **Scan semua signature**; kumpulkan yang `pow(s,e,n) != m`.
3. **GCD filter:** hanya `g = gcd(pow(s,e,n) - m, n)` dengan `1 < g < n` yang dipakai.
4. **Reconstruct `d`**, decrypt ciphertext integer ke flag string.
5. Jebakan: menganggap semua invalid = fault; atau mengira ciphertext PKCS#1.

## References & Further Reading

### 1️⃣ [Boneh, DeMillo, Lipton — On the Importance of Checking Cryptographic Protocols for Faults (EUROCRYPT’97 / Bellcore)](https://www.cs.umd.edu/~jkatz/papers/faults.pdf)
Paper dasar fault attack pada RSA-CRT.

> **TL;DR** — Satu fault di cabang CRT + GCD → faktorisasi `n`.

### 2️⃣ [Lenstra — Memo on RSA signature faults](https://eprint.iacr.org/)
Varian GCD klasik yang dipakai di writeup (“Lenstra trick”).

### 3️⃣ [RSA CRT implementation notes](https://en.wikipedia.org/wiki/RSA_(cryptosystem)#Using_the_Chinese_remainder_algorithm)
Kenapa produksi RSA memakai CRT (cepat) dan mengapa fault berbahaya tanpa verification.

## Author / verify

```text
node solver/generate.js
node solver/solver.js
```
