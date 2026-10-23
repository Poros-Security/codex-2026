# Status Challenge — CODEX 2026

Dibuat saat migrasi dari `CODEX-2026-CTF` (format CTFd) ke monorepo gzcli.
33 challenge dipindahkan: 18 `StaticAttachment`, 15 `DynamicContainer`.

## Butuh perhatian author

| Challenge | Masalah |
|---|---|
| `Pwn/p-balap` | **Tidak ada flag sama sekali.** initramfs (`rootfs.cpio.gz`) tidak memuat file flag; `init` hanya memberi shell user `ctf` + memuat `chall.ko`. Setelah exploit ke root, tidak ada apa pun untuk dibaca. Juga tidak ada mekanisme yang membaca `GZCTF_FLAG`, jadi flag per-tim belum jalan |
| `Web/nginx-rift` | Butuh `cap_add: SYS_PTRACE` + `security_opt: seccomp=unconfined` (untuk mematikan ASLR via `setarch -R`). **`challenge.yml` gzcli tidak punya field untuk ini** — lihat catatan di bawah |
| `Forensics/iot-sem5-asik-mwehehe` | Hanya ada `challenge.yml` di sumber. Tidak ada handout, README, maupun material solver |
| `Forensics/bad-practice-dev` | Tidak ada file handout (`dist/` kosong) walau ini challenge forensic |
| `Reverse/encrypted-presensi` | Tidak ada file handout (`dist/` kosong) walau ini challenge reverse |
| 9 challenge | `solver/` kosong di sumber; sudah diberi `solver/NOTES.md` sebagai penanda. Yaitu: bad-practice-dev, iot-sem5-asik-mwehehe, pathtophilosophy, sanity-check, breathing-room, jendral, the-last-flight, where-did-he-go, first-of-all |

## Sudah dibetulkan saat migrasi

| Challenge | Temuan |
|---|---|
| `Web/flowforge` | Di CTFd ditandai `type: dynamic` (challenge file statis), padahal punya `src/Dockerfile`, `src/entrypoint.sh`, dan compose dengan `FLAG` + port 8080. Di CTFd berarti tidak pernah dideploy sebagai container. Sudah di-retype ke `DynamicContainer` |
| `Pwn/p-balap` | `extra.redirect_port: 1337`, tapi `run.sh` listen di `31337` dan `Dockerfile` `EXPOSE 31337`. Port yang dibuka tidak akan cocok dengan service. `exposePort` sudah diperbaiki ke 31337 |
| 8 challenge via `apply_dynamic_flag.sh` | Helper menurunkan sendiri suffix `_<8hex>` dari seed `FLAG`/`CTF_FLAG`. Dengan GZCTF yang sudah mengirim flag final, ini menghasilkan flag berbeda dari catatan server sehingga challenge tidak bisa disolve. Helper sekarang memakai `GZCTF_FLAG` apa adanya |
| 6 challenge lain | `entrypoint.sh` hanya membaca `FLAG`, yang tidak pernah diisi GZCTF. Sudah diberi fallback `GZCTF_FLAG` |
| `Web/gopher-hole` | Default-nya `FLAG="${FLAG:-CODEX26{...}}"`. Tanda `}` di dalam nilai default menutup parameter expansion lebih awal; di sini hasilnya kebetulan benar, tapi rapuh. Sudah dipisah ke variabel sendiri |
| `Web/nginx-rift` | `Dockerfile`/`entrypoint.sh` ada di root challenge, bukan `src/`, sehingga `scripts.start` perlu `docker build .` tanpa `cd src` |
| 4 challenge Crypto | Folder `handout_src/` (generator handout) dipindahkan ke `src/`, sesuai kontrak gzcli "build input di src/" |
| `Web/nginx-rift` | Skrip exploit/verify yang berserakan di root dipindahkan ke `solver/` |

## Catatan: nginx-rift dan capability container

`challenge.yml` gzcli hanya mengenal `containerImage`, `memoryLimit`, `cpuCount`,
`storageLimit`, `exposePort`, `networkMode`, dan `enableTrafficCapture`. Tidak ada
field untuk `cap_add` atau `security_opt`.

Artinya `SYS_PTRACE` dan `seccomp=unconfined` yang dibutuhkan challenge ini tidak
bisa diminta per-challenge lewat GZCTF. Pilihan yang ada:

1. Ubah challenge supaya tidak perlu mematikan ASLR dari dalam container
   (misalnya ASLR sudah dimatikan saat build image, atau exploit dibuat tahan ASLR).
2. Jalankan challenge ini di luar GZCTF (compose manual) dan daftarkan sebagai
   `StaticAttachment` dengan `connection_info` ke host tersebut.
3. Longgarkan konfigurasi di level platform GZCTF, bukan per-challenge.

Belum dipilih — perlu keputusan author.

## Sisa pekerjaan umum

- `events/codex-2026/.gzevent`: `start` / `end` masih placeholder `TODO`.
- `.gzctf/conf.yaml`: URL + kredensial server (file ini gitignored).
- `.gzctf/.env`: `PUBLIC_ENTRY` masih `localhost`, `DB_PASSWORD` masih default.
  File ini **tracked** oleh `.gitignore` bawaan gzcli — gitignore dulu sebelum
  diisi secret asli.
- `state: hidden` dari CTFd diterjemahkan ke `visible: false`. Ubah ke `true`
  saat kompetisi dimulai.
- File `desc_ctfd.md` (5 challenge Web) adalah sisa format CTFd; isinya sudah
  ada di `description` pada `challenge.yml` dan boleh dihapus.

## Catatan ukuran repo

Repo ~115 MB. Yang besar: `Misc/closing-tune/dist/chall.zip` (40 MB) dan
`Pwn/p-balap` yang menyimpan `bzImage` 13 MB **dua kali** (di `src/` dan `dist/`),
plus `rootfs/` hasil ekstrak berdampingan dengan `rootfs.cpio.gz`.

Masih di bawah batas 100 MB per file GitHub sehingga git-lfs belum diperlukan,
tapi duplikasi di `p-balap` bisa dihemat ~13 MB kalau `dist/bzImage` dibuat
symlink atau dihasilkan saat build.
