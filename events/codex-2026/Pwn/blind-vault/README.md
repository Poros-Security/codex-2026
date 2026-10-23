# blind-vault

Challenge PWN x86_64/Linux bertema **blind OOB read/write + ELF parsing**.

## Konsep

Peserta hanya diberi service TCP dan binary ELF stripped. Menu memiliki bug
indeks tanpa bounds check. OOB read pada cell `9` membocorkan function pointer
PIE; peserta melakukan ELF parsing untuk mendapatkan offset `quiet()` dan
`win()`, menghitung PIE base, lalu memakai OOB write pada cell `9` untuk
menimpa hook dengan alamat `win()`. Perintah `invoke` menjadi ret2win.

## Jalankan lokal

```sh
docker compose up --build
nc 127.0.0.1 5001
```

## Catatan untuk penyelenggara

Ganti isi `flag.txt` sebelum deployment.

## Solver pengelola

Pasang `pwntools`, simpan binary debug sebagai `vault.debug`, lalu jalankan:

```sh
python3 solver/solve.py HOST=127.0.0.1 PORT=5001 REMOTE=1
```

Tanpa `vault.debug`, berikan offset hasil ELF parsing melalui `QUIET_OFF=...`
dan `WIN_OFF=...`.
