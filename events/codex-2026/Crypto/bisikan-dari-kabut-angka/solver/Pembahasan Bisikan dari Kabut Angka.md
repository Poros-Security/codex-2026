# Bisikan dari Kabut Angka — Pembahasan

**Topik:** Search-LWE, Kannan embedding, Regev  
**Kesulitan:** Hard  
**Solver:** `solver/solver.py`

## Yang diberikan

`params.json`: `n = 72`, `m = 108`, `q = 3329`, `eta = 5`, matriks `A`, vektor `b`.  
`Cipher.txt`: satu bit per baris, `a_0,...,a_{n-1};u`.

## Inti

Sampel publik:

```text
b = A s + e (mod q)
s_i in {-1, 0, 1}
|e_i| <= 5
```

Menghilangkan error lalu menyelesaikan sistem modulo `q` menghasilkan secret yang salah. Babai pada basis yang belum direduksi juga gagal.

Ciphertext memakai secret yang sama. Tiap baris adalah enkripsi Regev satu bit, MSB-first per byte UTF-8:

```text
u = <a, s> + e + bit * (q // 2)  (mod q)
```

## Langkah

1. Susun embedding Kannan berdimensi `n + m + 1 = 181`:

```text
baris j < n     : 1 di kolom j, dan kolom A[:, j]
baris error     : q pada diagonal
baris terakhir  : b, lalu 1
```

Vektor pendek yang dicari berbentuk `(s, e, 1)` atau lawan tandanya.

2. LLL. Jika belum ketemu, BKZ dengan blok 15, 20, 25, 30, lalu 40.
3. Untuk tiap baris hasil, ambil `n` entri pertama, coba tanda plus dan minus, pusatkan modulo `q`.
4. Terima `s` hanya jika `max |centered(b - A s)| <= eta`.
5. Dekripsi tiap baris cipher:

```text
t = centered(u - <a, s> mod q)
bit = 1 jika |t| > q/4, selain itu 0
```

6. Gabungkan tiap delapan bit, bit kiri paling signifikan, lalu decode UTF-8.

## Flag

```text
CODEX26{bkz_m3nd3ng4r_b1s1k_d4r1_k4but}
```

```text
python solver/generate.py
python solver/solver.py
```
