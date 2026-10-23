## PoC
1. Ekstrak `chall.zip` → dapet `chall.jar`. Isinya cuma satu `Chall.class`
2. Decompile `Chall.class` pake jd-gui / CFR / JADX, logikanya kebaca langsung tanpa obfuscation apa-apa
3. Di method `check()`: tiap byte input di-rotate-left 3 bit, XOR sama `0x5A`, hasilnya di-base64 encode, terus di-`String.equals` ke konstanta `TARGET` yang udah hardcoded
4. Copy string base64 `TARGET` dari view decompiler, bikin solver terus base64 decode terus XOR `0x5A` lanjut rotate-right 3 bit entar decode UTF-8
5. Dapet deh flagnya