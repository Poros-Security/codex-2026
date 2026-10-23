# Gema dari Mahkota Retak — Pembahasan

**Topik:** fault RSA-CRT (Bellcore/Lenstra)  
**Kesulitan:** Medium-Hard  
**Solver:** `solver/solver.js`

## Yang diberikan

`challenge.json`: modulus `n`, eksponen `e = 0x10001`, 64 pasang pesan dan segel, serta satu ciphertext.

## Inti

Pesan ditandatangani sebagai RSA textbook:

```text
m = int(SHA-256(pesan))          # big-endian
s = m^d mod n
```

Implementasi mempercepat lewat CRT. Jika cabang modulo `p` rusak tetapi cabang modulo `q` tetap benar:

```text
s^e ≡ m (mod q)
s^e ≢ m (mod p)
gcd(s^e - m, n) = q
```

Ada dua segel yang gagal verifikasi. Satu adalah fault CRT dan membagi `n`. Satu lagi hanya rusak setelah ditandatangani; GCD-nya biasanya 1.

Ciphertext adalah bilangan UTF-8 flag, dipangkatkan `e` modulo `n`. Bukan PKCS#1.

## Langkah

1. `n` dan `e` dibaca sebagai bilangan heksadesimal.
2. Untuk setiap entri:
   - `m = int.from_bytes(SHA-256(pesan), "big")`
   - `s = int(signature, 16)`
   - `v = pow(s, e, n)`
   - jika `v == m`, lewati
   - `g = gcd(v - m, n)`
   - jika `1 < g < n`, itu faktornya
3. `q = n // g`. Pastikan `g * q == n`.
4. `phi = (g - 1) * (q - 1)`, lalu `d = inverse(e, phi)`.
5. `pt = pow(ciphertext, d, n)`.
6. Ubah `pt` ke byte big-endian dan decode UTF-8.

Jangan berhenti pada segel invalid pertama sebelum menguji GCD.

## Flag

```text
CODEX26{r3t4k4n_m3mb0c0rk4n_m4hk0t4}
```

```text
node solver/generate.js
node solver/solver.js
```
