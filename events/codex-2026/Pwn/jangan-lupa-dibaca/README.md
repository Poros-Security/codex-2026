## PoC
1. Konek ke service (`nc 10.34.9.91 11030`) atau reverse langsung binary dari `dist/chall.zip` -> ketauan protokolnya: `[1 byte opcode][2 byte length little-endian][length byte data]`, opcode `0x01` = SET_NOTE, `0x02` = DELETE_NOTE
2. Cek proteksi binary pakai `checksec` -> No canary, NX enabled, No PIE. Tambahan cek `readelf -n ./notesvc | grep -i "x86 feature"` buat mastiin CET/shadow stack nggak nyala
3. Reverse handler `SET_NOTE` -> ketemu nih kalo panjang payload divalidasi maksimal 256, tapi buffer tujuannya cuma 64 byte. Validasinya ngecek angka yang salah, nah itu dia
4. Cari offset ke saved return address pakai cyclic pattern + gdb. Pas testing, jangan lupa `set follow-fork-mode parent`, soalnya `system()` di dalem kode manggil `vfork` dan gdb defaultnya malah ngikutin child process-nya, bukan `notesvc` yang mau di-debug. Offset ketemu = 72
5. Ada fungsi `internal_admin` yang nggak kepanggil di alur normal, dan minta argumen `token == 0x1337C0DE` di rdi sebelum mau baca `/flag.txt`
6. Susun payload: padding 72 byte + alamat `note_flags_helper` + token `0x1337C0DE` + alamat `internal_admin`, kirim lewat frame SET_NOTE (opcode `0x01`)
7. Verifikasi pake solver yang difolder 