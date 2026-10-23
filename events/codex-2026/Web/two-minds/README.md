# POC - Two Minds (HTTP Request Smuggling CL.TE)

## POC

1. Peserta membuka website portal.

2. Peserta mengamati endpoint /status?ref=DBMC-XXXX-XXXX yang menampilkan status permohonan dari records office.

3. Peserta mencoba GET /admin langsung dan mendapat 403 forbidden dari edge gate.

4. Peserta mengamati bahwa ada dua server yang mengukur panjang request berbeda: gate memakai Content-Length, server memakai Transfer-Encoding chunked.

5. Peserta membuat request POST yang membawa KEDUA header Content-Length dan Transfer-Encoding.

6. Peserta menghitung nilai Content-Length sama dengan panjang seluruh body, termasuk request GET /admin yang diselipkan.

7. Peserta mengirim request tersebut, lalu mengirim satu request biasa kedua pada koneksi yang sama.

8. Karena server memproses sisa byte sebagai request berikutnya, GET /admin dieksekusi dan flag muncul pada respons kedua.

## Burp Suite

1. Menggunakan Burp Suite dan buka halamannya.

2. Akan terdapat record GET / dan GET /admin (403).

3. Untuk request POST akan digunakan di repeater dengan dua header Content-Length dan Transfer-Encoding.

4. Sebelum send, matikan fitur Update Content-Length dan tulis Content-Length manual sama dengan panjang body penuh, yaitu 45.

5. Setelah send, respons pertama adalah halaman Home (respons ke POST).

6. Ganti isi request di tab repeater yang SAMA menjadi GET / biasa, lalu send lagi pada koneksi yang sama.

7. Respons kedua berisi flag. request kedua WAJIB diakhiri satu baris kosong/satu enter ekstra di akhir. Tanpa baris kosong penutup, smuggled request tidak terbaca dan respons kedua tetap halaman Home.

## Payload

Request pertama (POST smuggling):

```
POST / HTTP/1.1
Host: two-minds
Content-Length: 45
Transfer-Encoding: chunked

0

GET /admin HTTP/1.1
Host: two-minds

```

Request kedua (di koneksi yang sama):

```
GET / HTTP/1.1
Host: two-minds

```

## Flag

```
CODEX26{tw0_m1nds_0n3_r3qu3st_5muggl3d}
```
