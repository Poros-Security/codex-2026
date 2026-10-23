# Sepuluh Kulit Bawang — Pembahasan

**Topik:** encoding bertingkat  
**Kesulitan:** Easy  
**Solver:** `solver/solver.py`

## Yang diberikan

Satu baris di `cipher.txt`. Tidak ada daftar lapisan untuk peserta.

## Inti

Flag diolah sepuluh kali, dari dalam ke luar:

1. Base64 atas byte UTF-8
2. ROT13
3. Hex
4. Base32
5. Balik string
6. URL percent-encoding
7. Program Brainfuck yang mencetak string itu
8. Base64
9. Kode ASCII dipisah spasi
10. Base64

Kupas dari lapisan 10 ke lapisan 1.

## Langkah

1. `base64.b64decode` pada `cipher.txt`.
2. Pisah dengan spasi, ubah tiap bilangan menjadi karakter (`chr(int)`).
3. `base64.b64decode` lagi. Hasilnya sumber Brainfuck (`+`, `-`, `.`).
4. Jalankan interpreter Brainfuck. Outputnya sebuah string.
5. `urllib.parse.unquote`.
6. Balik string.
7. `base64.b32decode`.
8. `bytes.fromhex`.
9. ROT13.
10. `base64.b64decode` sebagai UTF-8.

Setelah langkah 3 harus terlihat perintah Brainfuck. Setelah langkah 10 harus terlihat `CODEX26{...}`.

## Flag

```text
CODEX26{10_l4y3r5_0f_0ni0n_p33l}
```

```text
python solver/generate.py
python solver/solver.py
```
