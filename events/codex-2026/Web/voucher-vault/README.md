# POC
1. Peserta membuka website dan melihat saldo awal sebesar 100 kredit, sementara satu voucher juga berharga 100 kredit.
2. Peserta mengamati endpoint `POST /api/claim` yang mengecek saldo sebelum proses pengurangan kredit dilakukan.
3. Peserta mengirim minimal lima request ke `/api/claim` secara paralel, misalnya memakai JavaScript `Promise.all()` atau tool pengirim request paralel.
4. Karena terdapat jeda sebelum saldo diperbarui, beberapa request dapat sama-sama lolos pengecekan saldo awal.
5. Jumlah voucher menjadi lima atau lebih meskipun kredit awal hanya cukup untuk satu voucher.
6. Peserta membuka endpoint `/reward` untuk mendapatkan flag.

# Untuk Jika Menggunakan Brupsuite
1. Menggunakan Brupsuite dan buka halamannya
2. Akan terdapat record /api/claim dan /reward
3. Untuk /api/clam akan digunakan di repeater dan melakukan claim sebanyak 9 kali
4. Setelah melakukan send 9 kali kita 
