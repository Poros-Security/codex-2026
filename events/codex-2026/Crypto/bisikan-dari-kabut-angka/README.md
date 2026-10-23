# Bisikan dari Kabut Angka

**Kategori:** Cryptography  
**Kesulitan:** Hard  
**Tipe:** static  
**Pembuat:** zanzan  
**Flag:** `CODEX26{bkz_m3nd3ng4r_b1s1k_d4r1_k4but}`

## PoC (step by step)

1. Unzip `dist/handout.zip` → `params.json` + `Cipher.txt` (+ generate redacted).
2. Baca parameter LWE: `n = 72`, `m = 108`, `q = 3329`, `eta = 5`, matriks `A` (`m×n`), vektor `b` (`m`).
3. Model publik (Search-LWE / Regev-style):

```text
b ≡ A s + e  (mod q)
s_i ∈ {-1, 0, 1}
|e_i| ≤ eta (= 5)
```

   **Jangan** buang `e` lalu solve linear di `Z/qZ` — secret yang keluar salah. Babai tanpa reduksi lattice yang memadai juga gagal.

4. Pulihkan `s` lewat **Kannan embedding** berdimensi `n + m + 1 = 181`:
   - Baris `j < n`: basis secret (1 di kolom `j` + kolom `A[:, j]`).
   - Baris error: `q` di diagonal.
   - Baris terakhir: `b` lalu `1`.
   - Target short vector berbentuk `(s, e, 1)` (atau lawan tanda).
5. Reduksi: mulai **LLL**; jika belum ketemu, **BKZ** block size 15 → 20 → 25 → 30 → 40.
6. Untuk tiap baris hasil reduksi: ambil `n` entri pertama, coba `±`, center modulo `q`. Terima `s` hanya jika `max |center(b − A s)| ≤ eta`.
7. `Cipher.txt`: tiap baris `a_0,...,a_{n-1};u` = enkripsi Regev **satu bit** (MSB-first per byte UTF-8):

```text
u ≡ ⟨a, s⟩ + e + bit·(q//2)  (mod q)
```

8. Dekripsi tiap bit:

```text
t = center(u − ⟨a, s⟩ mod q)
bit = 1 jika |t| > q/4, else 0
```

9. Pack 8 bit → byte → UTF-8 → flag.

10. Reference: `pip install -r solver/requirements.txt && python solver/solver.py`.

## Concept

Ini challenge **lattice / Learning With Errors**, bukan RSA/AES klasik.

1. Error `e` kecil sengaja ada: tanpa itu LWE trivial; dengan itu perlu short-vector recovery.
2. Kannan embedding mengubah “cari `s` konsisten dengan `b≈As`” menjadi SVP/CVP-ish pada lattice yang lebih tinggi dimensinya.
3. Setelah `s` ketemu, ciphertext bit-wise Regev langsung dibuka — flag tersembunyi di “bisikan” bit, bukan di `params.json` sendiri.
4. Dimensi (`n=72`, embedding 181) dipilih agar LLL kadang cukup, BKZ perlu untuk instance yang lebih “kabut”.

## Exploit Overview

1. **Parse JSON** → matriks integer `A`, `b`, `q`, `eta`.
2. **Build Kannan lattice** persis dimensi `181` (salah dimensi = gagal total).
3. **LLL → BKZ escalate** sampai short vector lolos uji `eta`.
4. **Sign flip / center** kandidat `s` sebelum verifikasi.
5. **Bit decrypt + UTF-8 assemble** dari `Cipher.txt`.

Jebakan umum: mengira cukup least-squares / solve `As=b` tanpa lattice; atau salah threshold `q/4` saat decoding bit.

## References & Further Reading

### 1️⃣ [Regev — On Lattices, Learning with Errors…](https://cims.nyu.edu/~regev/papers/qcrypto.pdf)
Fondasi LWE dan enkripsi berbasis LWE.

> **TL;DR** — `b = As + e` dengan `e` kecil; recovery `s` = inti challenge.

### 2️⃣ [Kannan embedding / CVP → SVP](https://en.wikipedia.org/wiki/Lattice_problem)
Teknik menanam instance CVP ke SVP dengan satu dimensi ekstra — dipakai di langkah 4 PoC.

### 3️⃣ [fpylll / BKZ](https://github.com/fplll/fpylll) · [Sage Math lattice](https://doc.sagemath.org/html/en/reference/matrices/sage/matrix/matrix_integer_dense.html)
Tool praktis LLL/BKZ; solver author memakai stack Python + lattice reduction setara.

## Author / verify

```text
python solver/generate.py
python solver/solver.py
```
