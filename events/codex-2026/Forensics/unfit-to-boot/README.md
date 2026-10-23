## PoC (step by step)

1. Baca isi bundle di `dist/`: `flash.bin` (raw SPI-NAND dump 16.5 MB), `console.log` (fragmen UART), `SHA256SUMS.manifest` (integrity check dari pabrik cuma dua region stabil yang di-hash, sisanya `*`), sama `factory_ate_sheet.pdf` (dokumen ATE Ghoti Labs yang ngasih tau region map lengkap termasuk OTP-mirror).

2. lihat ukuran `flash.bin` kalo dibagi 2048 gak bulat, tapi dibagi **2112** bulat. Itu tanda kalo raw dump ini nyimpen OOB (out-of-band) 64 byte tiap page 2048 byte. Strip OOB-nya dulu (buang 64 byte terakhir tiap 2112-byte page) sampe dapet clean image 16 MiB, SHA-256-nya yang jadi jawaban Q5.

3. Buka `console.log`, di situ SPL bilang `ECC engine: on-die, scheme BCH8/512`, dan ada line `*** Warning - bad CRC on env1, using env0` yang langsung ngonfirmasi sektor `env` mana yang torn.

4. Parse dua sektor env yang redundan di clean image (offset `0x00100000` dan `0x00120000`, masing masing 128 KiB). Format U-Boot redundant env: `[crc32 LE][flag 1B][key=value\0 ... \0][pad 0xFF]`. Hitung ulang CRC32 atas `flag||body`, bandingin sama CRC yang tersimpan, sektor yang gak match itu yang torn. Ambil variabel `bootcmd` dari sektor intact ada string aneh: `bootm 0x40800000#conf@2`.

5. Extract UBI di offset `0x00200000` (size 3 MiB) pake `ubireader_extract_files` (dari pip package `ubi_reader`). Alat ini bakal ngeluarin `/boot/image.fit` beserta isi rootfs lain. LEB size sama nama volume-nya keliatan pake `ubireader_display_info`.

6. Parse `image.fit` pake `mkimage -l` (dari `u-boot-tools`) atau `fdtdump`. Bakal keliatan ada dua `configuration` node: `conf@1` yang punya `signature@1` (algo sha256+rsa2048, key-hint `ghoti-prod`), dan `conf@2` yang **gak punya signature node sama sekali**. Bootcmd tadi ternyata ngarahin ke `conf@2` — anu, ini shape-nya CVE-2020-10648.

7. Baca isi `signature@1` di `conf@1`. Property `hashed-nodes`-nya cuma daftar node punya `conf@1` doang (`/`, `/configurations/conf@1`, subimage `kernel@1`, `fdt@1`, `ramdisk@1`, hash mereka). `conf@2` sama `ramdisk@2` gak masuk di daftar itu, jadi walaupun ada signature yang "valid" di image, config yang ke-boot itu unsigned. Property `hashed-nodes` ini yang jadi jawaban Q19.

8. Extract `ramdisk@2` dari FIT pake `dumpimage -T flat_dt -p <index>`. Isinya cpio kecil dengan `/opt/diag/audit.log.enc` sama `/opt/diag/derive.sh`. Baca `derive.sh` dia baca 32 byte dari `/dev/mtdblock0` di offset yang diambil dari argument, terus derive key pake HKDF-SHA256 dengan `salt=b"ghoti"` dan `info=b"audit-key"`, terus AES-256-GCM decrypt.

9. Balik lagi ke `factory_ate_sheet.pdf` di section OTP-mirror, disebut offset `0x00FF0000` sama size 32 byte. Baca 32 byte itu dari clean image (SHA-256-nya jadi jawaban Q23).

10. Bikin solver buat HKDF derive key dari 32 byte OTP itu terus AES-GCM decrypt `audit.log.enc`, terus dapat flag

## Concept

Jadi buat forensics IoT firmware ini ada 4 lapis sistem yang harus ditembus urut:

1. dump-nya masih dalam format mentah SPI-NAND, tiap 2048 byte data page ditempel 64 byte OOB (ECC + bad-block marker). Setelah di-strip, storage-nya masih pake UBI di atasnya UBIFS bukan filesystem yang bisa langsung di-`mount` atau di-`binwalk -e`. Butuh alat khusus (`ubi_reader`) buat rekonstruksi.

2. Ada dua sektor env identik di `0x00100000` sama `0x00120000`. Salah satunya CRC32-nya rusak (simulasi torn write pas OTA), jadi perlu arbitrase manual dulu, pilih yang CRC-nya cocok baru bisa baca `bootcmd`-nya.

3. FIT image kelihatannya "signed" (ada `signature@1` yang lengkap: algo, key-hint, sign-images list), tapi property `hashed-nodes` yang seharusnya nge-list SEMUA node yang masuk hash cuma nyebut `conf@1` doang. `conf@2` yang isinya `ramdisk@2` gak masuk hash — dan `bootcmd` di env justru ngarahin boot ke `conf@2` itu. Ini shape yang sama persis kayak CVE-2020-10648 dan cluster BRLY-2026-037…042 dari Binarly.

4. Flag disimpan di dalam audit log yang di-AES-256-GCM. Key-nya diturunin lewat HKDF-SHA256 dari 32 byte "OTP-mirror" yang ditulis pabrik di lokasi hardcoded (`0x00FF_0000`). Lokasi ini gak ada di flash header manapun, cuma dokumen ATE (PDF) yang nyebutin, jadi player harus baca dokumen manufacturing beneran buat tau offset-nya.

## Exploit Overview

Terus buat exploit-nya perlu urut peel semua lapisan dari luar ke dalam, cara bypass masing masing sistem:

1. strip 64 byte tiap 2112-byte page dulu buat dapet clean NAND image, terus feed hasilnya ke `ubireader_extract_files` yang beneran ngerti UBI vtbl + UBIFS node index. Baru bisa keluar file `image.fit`-nya.

2. hitung ulang `zlib.crc32(sector[4:])` (yaitu CRC atas flag byte + body) sama bandingin sama 4 byte LE di awal sektor. Yang match aja yang dipake `console.log` juga ngonfirmasi via line `bad CRC on env1`.

3. bypass verified boot lewat gap di property `hashed-nodes`. Signature verifier U-Boot cuma hash node yang di-list di `hashed-nodes`; node di luar daftar itu ikut ke-load tapi gak pernah masuk hash. Attacker taruh payload di `ramdisk@2` yang direferensiin `conf@2`, dua-duanya diluar `hashed-nodes` scope-nya `conf@1`. Terus modif `bootcmd` di env ke `bootm ...#conf@2` U-Boot ngeliat "eh ini config yang diminta, load", gak crosscheck sama config yang di-sign. Persis pola yang dijelasin di advisory F-Secure 2020 sama re-disclosure Binarly 2026.

4. buat decrypt audit log-nya, KEY-nya bukan hardcode di script dia diturunin runtime dari 32 byte OTP-mirror. Player perlu baca offset region dari `factory_ate_sheet.pdf` (bukan dari flash structure, karena OTP-mirror gak punya header), extract 32 byte dari clean image, terus HKDF-SHA256(ikm=OTP, salt=b"ghoti", info=b"audit-key", length=32). Salt-nya `ghoti` disebut di dalam `derive.sh` yang di-extract dari `ramdisk@2` — jadi player perlu SEMUA lapisan sebelumnya berhasil dulu buat tau salt-nya. Key jadi → AES-GCM decrypt → flag muncul di plaintext audit log.

## References & Further Reading

### 1️⃣ [U-Boot Verified Boot Vulnerability: CVE-2020-10648](https://firmwaresecurity.com/2020/03/18/u-boot-verified-boot-vulnerability-cve-2020-10648/)
*by **Dmitry Janushkevich & Andrea Barisani (F-Secure Labs)** | March 18, 2020 --- ([Original oss-sec announcement, archived at seclists.org](https://seclists.org/oss-sec/2020/q1/117))*

**Summary**
The original disclosure of the FIT verified-boot bypass class. Janushkevich and Barisani demonstrated that U-Boot's FIT signature verification hashes only the nodes enumerated in the `hashed-nodes` property of the signature subnode. Configuration nodes not present in `hashed-nodes` (including alternate configurations added post-signing, or subimages referenced by them) are loaded by the boot code without contributing to the signed hash enabling a valid signature on `conf@1` to coexist with a fully unsigned `conf@2` in the same image. This is the direct anchor for the challenge's FIT structure. The original F-Secure Labs advisory URL was retired when F-Secure rebranded to WithSecure; the firmwaresecurity.com writeup preserves the original technical description verbatim, and the seclists.org archive holds Janushkevich's original oss-sec mailing list announcement.

> **TL;DR**
> kalau `hashed-nodes` di FIT gak nyebut suatu config atau subimage, U-Boot tetep mau boot node itu walaupun dia diluar hash. Jadi "signed" di image gak berarti "semua yang di-boot udah di-sign" cuma yang masuk daftar `hashed-nodes` yang beneran diverif. Challenge ini bikin ulang bug itu dengan `conf@2` sengaja diluar daftar. btw advisory F-Secure aslinya udah hilang gara-gara mereka rebrand jadi WithSecure, jadi link-nya sekarang ke mirror firmwaresecurity dan archive seclists.org.

---

### 2️⃣ [Unfit to Boot: Breaking U-Boot's FIT Signature Verification](https://www.binarly.io/blog/unfit-to-boot-breaking-u-boots-fit-signature-verification)
*by **Anton Ivanov (Binarly Research)** | July 9, 2026*

**Summary**
Modern re-disclosure showing that the FIT signature verification bypass class remained exploitable in shipping U-Boot even after CVE-2020-10648 was patched. Binarly documented six new bypass variants affecting stable releases dating back to v2013.07, all rooted in the same `hashed-nodes` scoping gap plus adjacent parser quirks (duplicate node names, unit-address handling, node reordering) ranging from denial-of-service to potential arbitrary code execution during processing of untrusted FIT images. The blog post's title is the direct namesake of this challenge.

> **TL;DR**
> Enam tahun setelah CVE aslinya, Binarly nemu bug yang polanya sama masih exist di U-Boot versi baru. Bukan cuma satu bypass mereka temuin enam varian sekaligus, semuanya main di gap yang sama antara "apa yang di-hash" versus "apa yang di-load". btw judul challenge-nya diambil dari judul post ini.

---

### 3️⃣ [U-Boot FIT Signature Verification Documentation](https://docs.u-boot.org/en/latest/usage/fit/signature.html)
*U-Boot upstream docs, `doc/uImage.FIT/signature.txt` in tree*

**Summary**
The upstream specification for how U-Boot FIT signatures work where `hashed-nodes`, `hashed-strings`, `sign-images`, and `key-name-hint` are defined and what the verifier does with each. Reading this spec side-by-side with the challenge's FIT source (`fit.its`) is how the player confirms which property name is supposed to enumerate hashed nodes (Q19) and which configurations carry valid signatures (Q20). The "Signed Configurations" section documents the exact mix-and-match attack CVE-2020-10648 exploits; the "Details" section describes how U-Boot rebuilds the hashed-node list from the configuration's own image references at verification time.

> **TL;DR**
> Dokumentasi resmi U-Boot buat FIT signature kalo bingung `hashed-nodes` itu apaan dan gimana verifier-nya baca, ini source of truth-nya. Section "Signed Configurations"-nya bahkan langsung ngejelasin skenario mix-and-match yang jadi dasar CVE-2020-10648. Bacanya bareng file `fit.its` challenge biar ketauan property mana yang bocor.

---

### 4️⃣ [UBI: Unsorted Block Images — Design & Volume Table Layout](http://www.linux-mtd.infradead.org/doc/ubi.html)
*Linux MTD project documentation (linux-mtd.infradead.org)*

**Summary**
Reference for the UBI on-flash format that sits between MTD and UBIFS: erase counter headers, VID headers, volume table (`layout` volume), and the LEB size derivation on NAND with sub-pages. For a 128 KiB PEB with 2048-byte pages and sub-page support (which W25N01GV has), UBI packs both the EC and VID headers into the first NAND page using sub-page writes, so LEB size = PEB size − one NAND page = 128 KiB − 2 KiB = 126976 bytes. Also explains why `ubireader_display_info` shows *two* volumes even when only one user volume was created — the second is the internal `layout` volume that holds two copies of the volume table. Directly informs Q10 (LEB size = 126976) and Q11 (user volume count = 1).

> **TL;DR**
> Docs UBI dari linux-mtd buat ngerti kenapa `ubireader` nunjukin dua volume padahal kita cuma bikin satu (yang satunya volume internal `layout` yang nyimpen vtbl), dan buat ngerti kenapa LEB size = 126976. Chip W25N01GV support sub-pages, jadi UBI naruh EC header sama VID header di sub-page yang beda tapi dalam page yang sama satu NAND page ke-consume, bukan dua. Q10 dan Q11 jawabannya lahir dari docs ini.

---

### 5️⃣ [Winbond W25N01GV 1 Gbit SPI-NAND Datasheet (Rev Q)](https://www.winbond.com/resource-files/W25N01GV%20Rev%20Q%20051721.pdf)
*by **Winbond Electronics Corporation** | Publication Release Date: May 17, 2021*

**Summary**
Datasheet for the SPI-NAND part used in the challenge's fictional Ghoti-One board. Documents the memory-array organisation ("1G-bit memory array organized into 65,536 programmable pages of 2,048-bytes each … erased in groups of 64 (128KB block erase)"), on-die ECC engine, and the OOB byte layout (bad-block marker at byte 0 of first-page OOB, ECC parity bytes in the remainder). Every page-size and erase-block value the player sees in `console.log` and `factory_ate_sheet.pdf` cross-references directly to this datasheet a good sanity check for Q1 through Q4.

> **TL;DR**
> Datasheet chip-nya beneran ada dan angkanya cocok semua sama yang ada di `console.log` + PDF ATE, cek datasheet Rev Q spec beneran, page 2048 byte, block 128 KiB, 1024 block, OOB 64 byte semua sesuai.

---
