# Jarum yang Selalu Condong

**Kategori:** Cryptography  
**Kesulitan:** Insane  
**Tipe:** static  
**Pembuat:** zanzan  
**Flag:** `CODEX26{j4rum_s3lalu_c0nd0ng_ke_ut4r4}`

## PoC (step by step)

1. Unzip `dist/handout.zip` → `challenge.json` (+ generate redacted).
2. Isi penting: public key **secp256k1**, **42** segel `(pesan, pitch, r, s)`, ciphertext “peti”.  
   `pitch` = **8 bit atas** nonce `k` yang dipublikasikan. `s` sudah dinormalisasi `s ≤ n/2`.
3. Model ECDSA:

```text
z = int(SHA-256(pesan))                 # big-endian
k = pitch · 2^248 + k_low                 # 0 ≤ k_low < 2^248
s · k ≡ z + r · d  (mod n)
```

4. Substitusi bagian nonce yang diketahui → bentuk **Hidden Number Problem**:

```text
a = r · s⁻¹ mod n
b = s⁻¹ · (z − s · pitch · 2^248) mod n
k_low ≡ b + a · d  (mod n)
```

   Empat puluh dua persamaan; `k_low` **248-bit** — tidak di-brute. Nonce **tidak** diulang.  
   Menganggap `pitch = 0` selalu → `b` salah → lattice gagal.

5. Susun lattice bilangan bulat **44×44** dengan `B = 2^248`:

```text
baris i < 42 : n² pada diagonal
baris 42     : a_i · n , dan B pada kolom 42
baris 43     : b_i · n , dan n·B pada kolom terakhir
```

6. **LLL** (`δ = 0.99`, mis. sympy). Vektor target ~ `(n·k_low_i…, B·d, n·B)`.
7. Baca `d`: jika entri terakhir `n·B` → `d = entri_sebelumnya / B`; jika `-n·B` balik tanda dulu; lalu `d mod n`.
8. **Verifikasi:** `d·G` harus sama dengan public key. Beberapa vektor LLL “bagus secara angka” tapi titiknya salah — buang.
9. Buka peti:

```text
key = SHA-256(d.to_bytes(32, "big"))[:16]
AES-128-ECB decrypt ciphertext, buang PKCS#7 → flag
```

10. Runtime LLL sympy ≈ **1 menit**. Reference: `pip install -r solver/requirements.txt && python solver/solver.py`.

## Concept

Challenge menggabungkan **ECDSA nonce bias** dengan **lattice HNP** (Boneh–Venkatesan style):

1. Nonce `k` harus full-entropy 256-bit. Di sini 8 MSB dipublikasikan sebagai `pitch` → sisa 248-bit masih besar untuk brute, tapi cukup bias untuk lattice dengan banyak sampel.
2. HNP: diketahui banyak pasangan affine `k_i ≈ b_i + a_i·d` dengan `k_i` “kecil” relatif terhadap modulus → pulihkan secret `d`.
3. Tanpa memakai `pitch` di rumus `b`, instance HNP salah dan LLL tidak mengarah ke `d` benar.
4. Flag tidak ada di signature; signature hanya jalan pulihkan `d`, lalu `d` jadi kunci AES peti.

## Exploit Overview

1. **Parse 42 signatures** → hitung `(a_i, b_i)` dengan invers `s` (jangan flip `s` sembarangan; sudah low-S).
2. **Build integer lattice 44×44** skala `n` / `B` persis spesifikasi di atas (salah skala = LLL noise).
3. **LLL + extract `d` + verify against pubkey**.
4. **KDF:** SHA-256(`d`||32be)[:16] → AES-ECB unpad.
5. Jebakan: nonce reuse hunt (tidak ada); ignore `pitch`; terima `d` tanpa cek `d·G`.

## References & Further Reading

### 1️⃣ [Boneh & Venkatesan — Hardness of Computing the Most Significant Bits of Secret Keys in Diffie-Hellman and Related Schemes](https://crypto.stanford.edu/~dabo/pubs/papers/MSBits.pdf)
Fondasi Hidden Number Problem.

> **TL;DR** — Bit atas yang bocor + banyak sample → lattice recover secret.

### 2️⃣ [Howgrave-Graham & Smart / Nguyen–Shparlinski — lattice attacks on DSA/ECDSA with biased nonces](https://link.springer.com/chapter/10.1007/3-540-44598-6_10)
Serangan praktis nonce bias pada (EC)DSA — pola yang ditiru challenge ini.

### 3️⃣ [SEC 2 — secp256k1 parameters](https://www.secg.org/sec2-v2.pdf)
Kurva yang dipakai; order `n` masuk ke modulus HNP.

### 4️⃣ [Bitcoin / low-S normalization](https://github.com/bitcoin/bips/blob/master/bip-0062.mediawiki)
Kenapa `s ≤ n/2` sudah di-set di handout — hindari ambigu signature malleability saat parse.

## Author / verify

```text
python solver/generate.py
python solver/solver.py
```
