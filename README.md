# CODEX 2026 — Challenge Repository

Monorepo challenge CODEX 2026 untuk [gzcli](https://github.com/dimasma0305/gzcli) / GZCTF,
hasil migrasi dari `CODEX-2026-CTF` yang sebelumnya berformat CTFd.

Struktur dibuat dengan `gzcli init` + `gzcli event create`, jadi sesuai layout
multi-event gzcli versi sekarang.

## Struktur

```
.gzctf/                     # config server GZCTF + schema + compose
.gzcli/current-event        # event aktif (gitignored)
Makefile
events/codex-2026/
├── .gzevent                # metadata event
├── .example/  .structure/
└── <Kategori>/<slug>/
    ├── challenge.yml       # definisi challenge (canonical)
    ├── src/                # source + Dockerfile (maintainer-only)
    ├── dist/               # artifact yang diunduh player
    └── solver/             # solusi / PoC author
```

## Pemetaan dari format CTFd

| CTFd | GZCTF / gzcli |
|---|---|
| folder `Cryptography` | `Crypto` |
| folder `Forensic` | `Forensics` |
| folder `PWN` | `Pwn` |
| folder `Web Exploitation` | `Web` |
| `type: dynamic` / `standard` | `StaticAttachment` |
| `type: dynamic_docker` | `DynamicContainer` |
| `tags: [Author]` | `author` |
| `category` | nama folder induk (tidak ada field-nya di gzcli) |
| `files: [dist/...]` | `provide: "./dist"` |
| `state: hidden` | `visible: false` |
| `extra.base_flag` | `container.flagTemplate` + `_[TEAM_HASH]` |
| `extra.docker_image` | `container.containerImage` (`{{.slug}}`) |
| `extra.redirect_port` | `container.exposePort` |
| `extra.memory_limit: "128m"` | `container.memoryLimit: 128` |
| `extra.cpu_limit: 0.5` | `container.cpuCount: 1` (gzcli hanya terima integer) |
| `extra.initial/decay/minimum` | **dibuang** — dynamic scoring diatur GZCTF, `value` tetap 1000 |

## Flag per-tim

GZCTF menyuntikkan flag per-tim **hanya** lewat env `GZCTF_FLAG`, dan tidak ada
variabel lain yang ikut. Challenge di repo ini sebelumnya membaca `FLAG` /
`CTF_FLAG`, jadi semuanya sudah diberi shim:

- 8 challenge memakai helper bersama `src/apply_dynamic_flag.sh`. Helper itu
  **menurunkan sendiri** suffix `_<8hex>` dari seed. Kalau dibiarkan, flag di
  container akan berbeda dari yang dicatat GZCTF dan challenge jadi tidak bisa
  disolve. Sekarang helper memakai `GZCTF_FLAG` apa adanya bila ada.
- 6 challenge lain membaca `FLAG` langsung di `entrypoint.sh`, sudah diubah
  menjadi `FLAG="${GZCTF_FLAG:-${FLAG:-...}}"`.

Jalur CTFd lama tetap berfungsi, karena shim hanya menambah prioritas.

## Menjalankan satu challenge secara lokal

```sh
cd events/codex-2026/<Kategori>/<slug>/src
GZCTF_FLAG='CODEX26{test}' docker compose up --build
```

## Sync ke server

```sh
gzcli event list     # pastikan event terbaca
gzcli script start   # build semua image challenge
gzcli sync           # butuh .gzctf/conf.yaml terisi
```

`gzcli sync` harus dijalankan di mesin yang sama dengan Docker host GZCTF:
GZCTF menjalankan container dari image lokal lewat `/var/run/docker.sock` dan
tidak ada registry yang dikonfigurasi.

Lihat `STATUS.md` untuk challenge yang masih butuh perhatian.
