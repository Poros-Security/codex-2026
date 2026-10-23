## PoC (step by step)

1. Unzip `dist/chall.zip` → dapet tiga file: `chall.py`, `warmup.log`, `flag.enc`.
2. Baca `chall.py`: dia `random.seed(int(time.time()))`, terus dump 624 output `random.getrandbits(32)` ke `warmup.log`, terus XOR tiap byte flag pake `random.getrandbits(8)` yang dipanggil setelah 624 sampel calibration itu.
3. 624 output 32-bit dari MT19937 = seluruh internal state PRNG-nya. Ini bukan celah — ini justru spec-nya (Matsumoto & Nishimura 1998), dan CPython docs terang-terangan bilang "`random` should not be used for security purposes".
4. `pip install mt19937predictor==0.0.3`. Feed 624 uint dari `warmup.log` ke `MT19937Predictor.setrandbits(x, 32)` satu-satu. State-nya balik utuh.
5. Panggil `predictor.getrandbits(8)` sebanyak `len(flag.enc)` kali (predictor otomatis lanjut dari state yang sama kayak `chall.py` waktu masuk phase encrypt), XOR sama tiap byte `flag.enc`, decode UTF-8 → flag muncul.
6. Bikin solver di `solver/solve.py` yang ngerjain langkah 4–5 dan cetak flag. Reference solver ada di `solver/solve.py`.

## Concept

Jadi buat challenge crypto easy ini core-nya cuma satu: **Python `random` bukan CSPRNG**.

1. `random` module CPython pake Mersenne Twister MT19937. Doc-nya explicit warn: [python.org — random](https://docs.python.org/3/library/random.html) → "The pseudo-random generators of this module should not be used for security purposes."
2. Sifat matematis MT19937: 624 output 32-bit berturut-turut = *seluruh* 19937-bit internal state. Sekali attacker punya state itu, dia bisa reproduce semua output masa depan bit-for-bit — termasuk `getrandbits(8)` yang di-XOR ke flag.
3. Challenge ini sengaja masang 624 output "calibration" persis sebelum masuk phase encrypt, jadi celah teoritis itu bener-bener tersedia buat player. Kalo `chall.py` cuma dump 100 output atau pake `os.urandom`, MT recovery gak jalan.

## Exploit Overview

Buat exploit-nya cara bypass tiap step:

1. **PRNG recovery**: pakai `mt19937predictor` (pip package by tna0y). Loop `predictor.setrandbits(x, 32)` 624 kali. Package internally rebuild MT state via inverse tempering — player gak perlu implement matematisnya sendiri.
2. **Alignment antara warmup ↔ ciphertext**: `chall.py` pake 624 kali `getrandbits(32)` (untuk log) DULU, baru `getrandbits(8) * len(flag)` (untuk XOR). Kalo player pake predictor yang di-fed 624 uint32 doang, `getrandbits(8)` berikutnya di predictor otomatis sinkron sama panggilan pertama `getrandbits(8)` di `chall.py`. Ini beat kecil yang bedain player yang beneran ngerti alignment MT state (state sudah maju 624 words, next call apapun bit-width-nya lanjut dari situ) vs player yang cuma nge-XOR 624 log ints ke flag.enc dan bingung dapet gibberish.
3. **XOR decrypt**: langsung `bytes(b ^ p.getrandbits(8) for b in ct)`.

## References & Further Reading

### 1️⃣ [Python `random` module — CPython documentation](https://docs.python.org/3/library/random.html)
*Python Software Foundation | stable across all Python 3.x*

**Summary**
Dokumen resmi `random` module yang menyatakan Mersenne Twister sebagai core generator dan secara eksplisit memperingatkan: "The pseudo-random generators of this module should not be used for security purposes. For security or cryptographic uses, see the `secrets` module." Baris ini adalah anchor real-world challenge — bug-nya bukan bug, ini spec yang di-abuse.

> **TL;DR**
> Docs Python literally warn di paragraf pertama: `random` bukan buat security. Challenge ini tinggal jadiin warning itu load-bearing. Kalau `secrets.token_bytes()` dipake ganti `getrandbits`, challenge gugur — makanya pake `random` doang yang jadi core-nya.

---

### 2️⃣ [Matsumoto & Nishimura, "Mersenne Twister: A 623-Dimensionally Equidistributed Uniform Pseudo-Random Number Generator" (ACM TOMACS 1998)](https://dl.acm.org/doi/10.1145/272991.272995)
*Makoto Matsumoto, Takuji Nishimura | ACM Transactions on Modeling and Computer Simulation, Vol. 8 No. 1*

**Summary**
Paper original yang define MT19937. Section 2 nge-define transisi state (twist operation) dan section 3 nge-define tempering. Fakta yang di-exploit di challenge: internal state = 624 kata 32-bit + index counter, tempering-nya bijective, jadi 624 output 32-bit consecutive = full state recovery (inverse tempering per-output). Bukan "cryptanalysis" dalam arti attack — ini konsekuensi langsung dari desain PRNG statistical (bukan cryptographic).

> **TL;DR**
> Paper tempat MT19937 pertama kali di-define. Property "624 output → state balik utuh" itu bukan bug, itu efek samping tempering yang bijective. Baca section 3 kalo mau ngerti kenapa recovery-nya deterministic bukan search-based.

---

### 3️⃣ [`mt19937predictor` on PyPI](https://pypi.org/project/mt19937predictor/)
*by **tna0y** | pip installable, MIT license*

**Summary**
Off-the-shelf tool buat inverse-temper + state-load MT19937 dari observed output. API: `MT19937Predictor().setrandbits(value, nbits)` untuk feed observed output, lalu `getrandbits(nbits)` untuk predict. Butuh persis 624 kali 32-bit input (atau equivalent width total) sebelum bisa predict. Solver reference challenge ini pake package ini langsung.

> **TL;DR**
> Ada pip package siap pakai (`pip install mt19937predictor`). Player gak perlu implement tempering manual — tinggal feed 624 uint32, lalu getrandbits(8) sebanyak yang perlu. Alternative: kmyk/mt19937-predictor (repo GitHub, functionally sama).

---

### 4️⃣ [Python `secrets` module — the correct alternative](https://docs.python.org/3/library/secrets.html)
*Python Software Foundation | PEP 506 by Steven D'Aprano, added in Python 3.6*

**Summary**
Modul yang seharusnya dipake untuk security-sensitive random. Sourced from `os.urandom` (which pulls from the OS CSPRNG — `getrandom(2)` on Linux, `BCryptGenRandom` on Windows). Player yang cek README ini setelah selesai challenge harus ngerti: kalau `chall.py` diganti pake `secrets.token_bytes(len(flag))` untuk keystream, challenge ini gak solvable — itulah defense terhadap kelas attack ini.

> **TL;DR**
> `secrets` = benerannya buat crypto, `random` = buat simulasi/game. Kalo dev nulis `random.getrandbits` di code produksi security-sensitive, itu bug (post-mortem-worthy). Challenge ini reproduce bug itu di laboratory setting.
