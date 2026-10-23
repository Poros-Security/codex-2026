# Jarum yang Selalu Condong — Pembahasan

**Topik:** ECDSA secp256k1, nonce bias, Hidden Number Problem  
**Kesulitan:** Insane  
**Solver:** `solver/solver.py`

## Yang diberikan

`challenge.json`: kunci publik secp256k1, 42 segel `(pesan, pitch, r, s)`, dan ciphertext peti. Delapan bit atas nonce dipublikasikan sebagai `pitch`. `s` sudah `<= n/2`.

## Inti

```text
z = int(SHA-256(pesan))                 # big-endian
k = pitch * 2^248 + k_low
0 <= k_low < 2^248
s * k ≡ z + r * d  (mod n)
```

Substitusi bagian nonce yang diketahui:

```text
a = r * s^(-1) mod n
b = s^(-1) * (z - s * pitch * 2^248) mod n
k_low ≡ b + a * d  (mod n)
```

Empat puluh dua persamaan ini cukup untuk memulihkan skalar 256-bit lewat lattice. `k_low` masih 248 bit, jadi tidak ditebak. Nonce tidak pernah diulang. Menganggap `pitch` selalu nol merusak `b`.

## Langkah

1. Hitung `a` dan `b` untuk ke-42 segel. Jangan membalik `s`.
2. Susun matriks bilangan bulat berukuran `44 x 44`, dengan `B = 2^248`:

```text
baris i < 42 : n^2 pada diagonal
baris 42     : a_i * n, dan B pada kolom 42
baris 43     : b_i * n, dan n*B pada kolom terakhir
```

3. LLL dengan `delta = 0.99`. Vektor target berbentuk

```text
(n*k_low_0, ..., n*k_low_41, B*d, n*B)
```

4. Jika entri terakhir `n*B`, maka `d = entri_sebelumnya / B`. Jika `-n*B`, balik tandanya dulu. Lalu `d mod n`.
5. Terima `d` hanya jika `d*G` sama dengan kunci publik. Beberapa baris lolos saringan angka tetapi titiknya salah.
6. Buka peti:

```text
key = SHA-256(d.to_bytes(32, "big"))[:16]
AES-128-ECB, lalu buang PKCS#7
```

LLL di sympy kira-kira satu menit.

## Flag

```text
CODEX26{j4rum_s3lalu_c0nd0ng_ke_ut4r4}
```

```text
python solver/generate.py
python solver/solver.py
```
