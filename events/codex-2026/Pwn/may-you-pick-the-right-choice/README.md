# May The Right Path You Choose

# PoC
1. Struktur chall ada main yang berisi kerentanan fmtstr dan buffer overflow
2. Yang dikasi hanya stripped binary
3. Sebenernya tinggal ret2func, tapi ada 5 func yang belum dipanggil jadi guessy tipis tipis.

Struktur project:

- `dist/` — hanya binary `chall` yang dibagikan kepada peserta.
- `solver/` — solver, exploit script, dan catatan pengujian internal.
- `src/` — source binary, entrypoint, service web, dan private unlock service.
- `Dockerfile` dan `docker-compose.yaml` — konfigurasi build/deployment internal.
- `challenge.yml` — metadata challenge untuk CTFd.

## Menjalankan secara lokal

Buat `.env` di root project dan isi `RESULT_KEY` dengan secret acak yang sama untuk service pwn dan unlock-api. Kemudian jalankan:

```bash
docker compose up -d --build
```

Challenge TCP tersedia di port `1337`, dan result page di port `8080`.