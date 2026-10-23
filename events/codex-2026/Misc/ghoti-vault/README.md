## PoC (step by step)
1. Baca source code jail yang dibagikan di `dist/server.py`. Ada 4 lapisan proteksi: filter karakter (blokir `_ # @ $` backtick dan backslash), AST walker (blokir statement `Import`/`ClassDef`/`Lambda` serta nama `eval`/`exec`/`compile`/`open`/dst), `__builtins__` yang dipangkas, dan audit hook PEP 578 yang menolak event `import`, `open`, `subprocess.Popen`, `os.system`, `os.exec*`, `os.spawn*`, dll
2. Karena filter karakter langsung memblokir `_` di source, bangun string `"__"` saat runtime lewat `chr(95) * 2` supaya karakter underscore tidak pernah muncul di kode yang dikirim
3. Pakai `getattr()` berantai untuk menyusuri `().__class__.__base__.__subclasses__()` tanpa pernah menulis literal `_`  hasilnya daftar seluruh subclass `object` yang aktif di proses
4. Iterasi daftar subclass tersebut, cari salah satu yang `__init__.__globals__`-nya memuat modul `sys` (banyak class bawaan standard library memenuhi syarat ini).
5. Dari `sys.modules`, ambil `_posixsubprocess`. Modul ini otomatis ter-populate karena `server.py` sengaja melakukan `import subprocess` di awal, dan `_posixsubprocess.fork_exec` adalah primitive C-level yang TIDAK terdaftar sebagai audit event PEP 578
6. Panggil `_posixsubprocess.fork_exec(...)` langsung untuk menjalankan binary SUID `/usr/local/bin/readflag`, tangkap stdout-nya lewat `os.pipe()` (gak diaudit juga btw), lalu `print()` hasilnya supaya terkirim balik lewat socket
7. Bikin solver buat anu payloadnya terus dapat flag

## Concept
Jadi buat Pyjailnya ada beberapa sistem:
1. Pake AST (Abstract Syntax Tree) buat baca kode terus reject kalo ada pake `_` (underscore), terus kalo bikin function baru, class baru, import itu bakal direject semua
2. Python built-ins udah tak hapus hampir semua jadi gak bisa pake function bawaan python kecuali `range()`, `len()`, sama `print()`
3. Audit hook python buat ngelarang kalau ada command aneh aneh yang dieksekusi, contohnya `os.system` atau `subprocess.Popen`


## Exploit Overview
Terus buat exploitnya perlu bikin payload oneshot command soalnya cuman nerima one line command doang, cara bypass masing masing sistem:
1.  Commandnya dimasukin ke dalam string pake `.format()`, AST blokir spesifik karakter tapi kalo karakternya di dalam string bisa ke bypass
2. Perlu balikin built ins command nya dulu, nah basically python kan dbangun pake sistem `Object-Oriented`. Jadinya setiap elemen bakal terhubung satu sama lain dan punya "parent" utama, dari parent bakal bisa nyari `sys.modules` agar bisa pake command command lainnya
3. Python tuh base languagenya C dan audit hook ini cuman ngawasin level Python doang, jadi dari `sys.modules` bisa pake function mentah C which is `_posixsubprocess` yang berfungsi untuk jalanin program yang membaca flag



## References & Further Reading

### 1️⃣ [Be careful with Python's new-style string format](https://lucumr.pocoo.org/2016/12/29/careful-with-str-format/)
*by **Armin Ronacher** | Dec 29, 2016*

**Summary**  
`str.format`'s field spec syntax (`{0.attr.subattr}`) walks `__getattribute__` at format time. This provides attribute reflection that source-level filters completely miss.

> **TL;DR**  
> Di python ada fitur buat format teks pake `.format()` terus fitur ini punya celah yang bisa jalanin command tanpa kelihatan kayak command dengan jadiin command itu ke string

---

### 2️⃣ [PEP 578 — Python Runtime Audit Hooks](https://peps.python.org/pep-0578/)
*(Introduced in 2019, shipped with Python 3.8)*

**Summary**  
Defines `sys.addaudithook` and the standard event catalogue (`exec`, `open`, `compile`, `import`, `subprocess.Popen`, `os.system`, etc.). **Note:** Coverage is only at documented event sites; C-level helpers below those sites are not audited.

> **TL;DR**  
> Isinya update python, sekarang python ada audit hooks yang ngawas kalau ada command yang aneh (buka file misalnya), tapi yang diawasi cuman perintah tingkat tinggi python doang, jadi karena bahasa dasar python tuh C kan yak, makanya perintah tingkat rendahnya aka C gak diawasi

---

### 3️⃣ [hxp CTF 2021 "audited2" writeup](https://ctftime.org/writeup/31883)
*by **clubby789** | ([Alternate Gist link](https://gist.github.com/clubby789/fb4efeb86be2045f82ba7eeb3a5ea370))*

**Summary**  
Demonstrates the specific `_posixsubprocess.fork_exec` bypass we're re-using. This is the C primitive that `Popen` wraps, callable via a deeply nested payload like `().__class__.__base__.__subclasses__()[N].__init__.__globals__["sys"].modules["_posixsubprocess"].fork_exec(...)` with zero audit events firing.

> **TL;DR**  
> WU dari HXP CTF 2021, ada chall yang pernah bikin ginian juga. WU nya ngasih tunjuk cara bypass audit hooksnya pake fungsi C level which is (`_posixsubprocess.fork_exec`) yang of course perlu di obfuscate pake payload panjang

---

### 4️⃣ [DiceCTF 2024 "IRS" writeup](https://maplebacon.org/2024/02/dicectf2024-irs/)
*by **Maple Bacon** | (Support, 2024)*

**Summary**  
Confirms the `_posixsubprocess.fork_exec` bypass technique still works on Python 3.12.

> **TL;DR**  
> Konfirmasi tambahan aja sih kalo bypassnya masih bisa sampe python paling baru (3.12).

---