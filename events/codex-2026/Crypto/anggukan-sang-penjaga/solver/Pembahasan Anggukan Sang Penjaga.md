# Anggukan Sang Penjaga — Pembahasan

**Topik:** padding oracle AES-CBC PKCS#7  
**Kesulitan:** Hard  
**Solver:** `solver/solver.py` terhadap `src/warden.py`

## Yang diberikan

`Cipher.txt` adalah hex dari `IV || ciphertext` (IV 16 byte, lalu 4 blok). Layanan menjawab satu byte: `0x01` jika PKCS#7 valid, `0x00` jika tidak. Klien mengirim panjang `uint16` big-endian, lalu blob sepanjang itu.

## Inti

Dekripsi CBC:

```text
P_i = Dec_K(C_i) XOR prev
```

`prev` adalah IV pada blok pertama, dan ciphertext blok sebelumnya pada blok berikutnya. `I = Dec_K(C_i)` tetap selama `C_i` tidak diubah. Mengganti `prev` mengubah plaintext tanpa mengetahui `K`.

Cukup kirim `prev' || satu blok`. Tidak perlu mengirim seluruh amplop.

## Langkah

Untuk tiap blok, pulihkan dari byte kanan ke kiri (`padlen` = 1 sampai 16):

1. Salin `prev` menjadi `crafted`.
2. Byte yang sudah diketahui di kanan disetel `I[j] XOR padlen`.
3. Coba `crafted[idx]` dari 0 sampai 255. Kirim `crafted || C_i`.
4. Pada `padlen = 1`, jika layanan mengangguk, balik satu bit pada byte di depannya dan tanya lagi.
   - Masih `0x01`: padding benar-benar `0x01`.
   - Menjadi `0x00`: anggukan pertama berasal dari padding asli yang lebih panjang. Lanjut ke tebakan berikutnya.
5. `I[idx] = tebakan XOR padlen`.
6. Plaintext blok: `P[j] = I[j] XOR prev_asli[j]`.

Gabungkan keempat blok, buang PKCS#7, ambil `CODEX26{...}`. Isi penuh:

```text
catatan:v1
CODEX26{4ngguk4n_p3nj4g4_m3mbuk4_p3t1}
```

Sekitar sembilan ribu pertanyaan. Kunci AES tidak ditebak.

## Flag

```text
CODEX26{4ngguk4n_p3nj4g4_m3mbuk4_p3t1}
```

```text
python solver/generate.py
python src/warden.py
python solver/solver.py
```
