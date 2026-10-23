# Silent Curriculum

**Category:** Forensic / Network Traffic Analysis  
**Difficulty:** Medium–Hard  
**Author:** ghoti  
**Artifact:** `dist/chall.zip` → `silent_curriculum.pcap` + `questions.md`

## PoC (step by step)

1. Unzip `dist/chall.zip` → dapat `silent_curriculum.pcap` dan `questions.md` (10 soal investigator).
2. Buka PCAP di Wireshark. **Jangan** langsung percaya semua HTTP: ada noise DNS/TLS/ICMP, decoy di TCP **8080**, prefatory HTTP/2 di port aneh, dan header `X-Forwarded-For: 203.0.113.77` palsu dari IP lain. Fokus traffic ke victim `10.13.37.20` port **80**.
3. Cari anomali intrusion (bukan volume traffic biasa). Filter berguna:
   - `http.request.uri contains "SLEEP"` atau `http.request.uri contains "EXTRACTVALUE"`
   - `http.user_agent contains "sqlmap"`
   - `http.request.uri contains "learnpress"`
   Dari situ langsung keliatan source IP penyerang utama: **`203.0.113.77`** → jawaban Q1.
4. Filter `ip.addr == 203.0.113.77 && tcp.port == 80`. Urutkan by time. Sebelum burst SQLi, ada `GET /wp-content/plugins/learnpress/readme.txt` → plugin yang diinvestigasi: **`learnpress`** → Q2.
5. Request SQLi berikutnya mengarah ke REST LearnPress:  
   `/wp-json/lp/v1/courses/archive-course?term_id=...`  
   Endpoint (tanpa query): **`/wp-json/lp/v1/courses/archive-course`** → Q3.  
   Parameter injeksi: **`term_id`** → Q4.
6. URI SQLi panjang sering **terfragmentasi di beberapa TCP segment**. Klik satu packet → **Follow → TCP Stream** biar request utuh. Di stream terlihat `SLEEP(...)`, `EXTRACTVALUE`, `SUBSTRING`/`MID` + `IF` — pola **time-based blind** SQLi (sqlmap) → Q5: **`time-based blind`**.
7. Di payload yang sama (setelah URL-decode / baca hex `0x77705f7573657273` = `wp_users`) penyerang enumerasi kolom `user_login` / `user_email` / `user_pass` dari tabel **`wp_users`** → Q6.
8. Setelah exfil selesai: `GET/POST /wp-login.php?login=courseadmin...` lalu `GET /wp-admin/` (status 302 pada POST login) → akun yang dipakai: **`courseadmin`** → Q7.
9. Upload plugin palsu: `update.php?action=upload-plugin&filename=cache-helper-1.4.2.zip`, lalu eksekusi  
   `/wp-content/plugins/cache-helper/cache-helper.php?cmd=whoami` (dan `id`/`pwd`/`uname`) → backdoor file: **`cache-helper.php`** → Q8.
10. `POST /wp-json/wp/v2/users?username=svc_audit&email=nightshift.audit%40proton.me&roles[0]=administrator`  
    Decode `%40` → email **`nightshift.audit@proton.me`** → Q9.  
    Timestamp request itu (packet time / header `X-Access-Time`) dalam format Apache: **`25/Sep/2024:00:50:43 +0000`** → Q10.
11. Submit 10 jawaban berurutan ke check service (`nc` / container QnA di `src/`). Semua benar → flag:  
    `CODEX26{s1l3nt_c0urs3_adm1n_t4k30v3r}`.

## Concept

Challenge ini core-nya **rekonstruksi kill-chain dari network evidence**, bukan reverse binary.

1. **Volume ≠ sinyal.** PCAP penuh traffic WordPress/LMS biasa + decoy. Investigasi dimulai dari *signature* serangan (sqlmap UA, `SLEEP`, plugin upload), baru pivot ke IP sumber.
2. **REST API WordPress/LearnPress sebagai attack surface.** Endpoint `archive-course` + parameter `term_id` yang tidak tersanitasi → SQLi. Plugin reconnaissance lewat `readme.txt` adalah pola tipikal sebelum eksploit.
3. **Time-based blind** dipakai karena response body tidak membocorkan data; delay/`SLEEP` yang jadi oracle. Enumerasi berlanjut ke `information_schema` lalu `wp_users`.
4. **Pasca-eksploit klasik WordPress:** login dengan kredensial curian → upload malicious plugin → webshell (`?cmd=`) → persistensi lewat user admin palsu via `/wp-json/wp/v2/users`.
5. **Pitfall analisis PCAP:** TCP reassembly wajib untuk URI panjang; jangan ikut `X-Forwarded-For` atau HTTP di `:8080` sebagai sumber kebenaran.

## Exploit Overview

Cara “bypass” tiap lapisan noise / ambiguitas:

1. **Filter decoy:** batasi `ip.src == 203.0.113.77 && tcp.dstport == 80` (atau ekivalen). Abaikan 443/DNS/ICMP/8080 untuk jawaban utama.
2. **Reassemble streams:** Follow TCP Stream pada request SQLi yang terpotong; baru URL-decode penuh.
3. **Decode artefak:** `%40` → `@`; `0x77705f7573657273` → `wp_users`; hex/`%2520` double-encoding sqlmap dibaca bertingkat.
4. **Timeline:** urutkan frame attacker → recon plugin → SQLi → login → upload → shell → create user → logout/cleanup. Q1–Q10 map 1:1 ke titik di timeline itu.
5. **QnA gate:** flag tidak ada di PCAP sebagai string hadiah; diperoleh setelah 10 jawaban benar di service check (sama pola `unfit-to-boot`).

## Answers (author only)

1. `203.0.113.77`
2. `learnpress`
3. `/wp-json/lp/v1/courses/archive-course`
4. `term_id`
5. `time-based blind`
6. `wp_users`
7. `courseadmin`
8. `cache-helper.php`
9. `nightshift.audit@proton.me`
10. `25/Sep/2024:00:50:43 +0000`

Flag: `CODEX26{s1l3nt_c0urs3_adm1n_t4k30v3r}`

## QnA check service

```text
cd Forensic/Silent-Curriculum/src
set CTF_FLAG=CODEX26{s1l3nt_c0urs3_adm1n_t4k30v3r}
python server.py
# atau:
# docker build -t codex-silent-curriculum .
# docker run --rm -e CTF_FLAG=CODEX26{s1l3nt_c0urs3_adm1n_t4k30v3r} -p 11033:11033 codex-silent-curriculum
```

## References & Further Reading

### 1️⃣ [OWASP — SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
*OWASP Foundation*

**Summary**  
Kelas serangan di mana input dipakai sebagai bagian query SQL. Challenge ini menampilkan varian **time-based blind** lewat `SLEEP`/`IF` di parameter REST.

> **TL;DR**  
> Kalau response tidak echo data, attacker tetap bisa exfil lewat delay. Itu yang terlihat di URI `term_id`.

---

### 2️⃣ [sqlmap — automatic SQL injection tool](https://sqlmap.org/)
*Open source | User-Agent tipikal `sqlmap/...`*

**Summary**  
Tool yang menghasilkan pola request di PCAP (probe boolean, `SLEEP`, `EXTRACTVALUE`, enumerasi `information_schema` / table columns).

> **TL;DR**  
> Filter `sqlmap` di User-Agent atau `SLEEP` di URI = pintas masuk ke kill-chain.

---

### 3️⃣ [WordPress REST API — Users](https://developer.wordpress.org/rest-api/reference/users/)
*WordPress.org Developer Resources*

**Summary**  
`POST /wp-json/wp/v2/users` dengan role `administrator` (jika authenticated + capability) dipakai attacker untuk bikin akun persistence `svc_audit`.

> **TL;DR**  
> Setelah jadi admin, create-user via REST lebih “bersih” daripada editing DB manual — dan tercatat jelas di HTTP.

---

### 4️⃣ [Wireshark — Following Protocol Streams](https://www.wireshark.org/docs/wsug_html_chunked/ChAdvFollowStreamSection.html)
*Wireshark User’s Guide*

**Summary**  
Dokumentasi Follow TCP Stream — wajib untuk request yang ter-segment di beberapa packet.

> **TL;DR**  
> Tanpa reassembly, sebagian payload SQLi / email terlihat “putus” dan jawaban Q5–Q9 bisa salah.

## Notes

- Alur jawaban sama dengan edisi access-log Silent Curriculum.
- PCAP sengaja campur protokol supaya analisis lebih sulit; evidence penyerang tetap cleartext HTTP ke `10.13.37.20:80`.
