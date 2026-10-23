## Soal
Peserta diberikan user ctf yang tidak boleh membaca flag. Mereka harus menemukan bahwa /dev/locker memiliki state machine yang tidak dilindungi lock, memenangkan race antara OPEN dan SYNC, mencapai STATE_GRANTED, lalu memanggil COMMIT yang menjalankan commit_creds() sehingga proses menjadi root.

## Menambahkan Solver Manual
1. Masukkan ke /bin/Nama_binary_solver
2. Kembali ke src
3. rm -f rootfs.cpio.gz
4. rebuild rootfs.cpio.gz dengan "find . -print0 | cpio --null -ov --format=newc | gzip -9 > ../rootfs.cpio.gz"

## Cara Masukkan Solver Ke Remote
1. Masuk ke path solver (Ex.  ~/probset/draft/P-Balap/solver/)
2. python3 -m http.server 8000 --bind 0.0.0.0
3. Ganti terminal
4. Akses nc
5. wget file dari socker solver
6. chmod +x /solver
7. /solver

## Proof Of Concept
1. Peserta menjalankan solver yang membuka /dev/locker, lalu membuat dua thread yang menjalankan LOCKER_OPEN dan LOCKER_SYNC
secara bersamaan.
2. LOCKER_OPEN mengubah state menjadi READY, mengaktifkan pending, lalu tidur selama 100 ms sehingga muncul race window.
3. Thread kedua memanfaatkan window tersebut dengan LOCKER_SYNC, mengubah sequence menjadi 1, sehingga ketika thread pertama bangun state berubah menjadi GRANTED.
4. Solver kemudian menjalankan LOCKER_COMMIT, yang menggunakan prepare_kernel_cred(&init_task) dan commit_creds() untuk memberikan credential root kepada proses.
5. Setelah UID menjadi 0, solver membuka /flag.txt dan mencetak flag.


