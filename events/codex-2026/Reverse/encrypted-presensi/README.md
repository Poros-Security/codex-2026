## PoC 
1. Ekstrak file `chall.zip` untuk mendapatkan file APK `app-release.apk`.
2. Unzip file APK dan analisis binary asset `assets/flutter_assets/data.bin` untuk menemukan Magic Header `CODE` (`43 4F 44 45`), panjang payload (`0x2C`), dan XOR Key (`0x7E`).
3. Verifikasi native binary offset `CODEX_HASH_CHECK:` pada `lib/arm64-v8a/libapp.so` di offset `0x35f00`.
4. Jalankan script solver `python solver/solve.py app-release.apk` untuk dekripsi bitwise XOR `0x7E` dan dapatkan Flag.
