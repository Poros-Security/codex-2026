# POC — Whisper Well (Command Injection)

## POC

1. Peserta membuka website dan melihat sebuah web yang mengulang kembali apa pun yang diucapkan.

2. Peserta mengamati endpoint /whisper?msg=... yang memasukkan input langsung ke perintah echo di shell server.

3. Peserta mencoba karakter shell umum seperti ; & | > < dan mendapat balasan forbidden character.

4. Peserta mencoba command substitution $() dan backtick yang tidak diblokir filter.

5. Peserta mengirim msg=$(cat /flag.txt) dan sumur mengembalikan isi file flag.



## Payload

```
/whisper?msg=$(cat /flag.txt)
```

URL-encode:

```
/whisper?msg=%24%28cat%20%2Fflag.txt%29
```

## Flag

```
CODEX26{wh1sp3r_w3ll_3ch0_sh3ll_1nj3ct10n}
```
