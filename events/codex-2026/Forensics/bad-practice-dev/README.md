## PoC
1. Peserta mendapatkan file .img
2. Kemudian setelah di analisis ternyata korban terkena malware dari python3 encryptor.py
 
3. Peserta harus menemukan enc.py tersebut untuk mendapatkan kunci dari AES-256.
4. berada di /var/tmp/.malware_backup.py dengan KEY = b"isThisArEalKey??", dan IV = hashlib.md5(KEY) yaitu (36c40a97a2adfa4ca967311995a57eb2).
5. kemudian dekripsi file di home dan cari flagnya yang berada di /home/faz/Downloads/TugasDicoding/LocalStorage/index.html.secret
6. Setelah mendekripsi file tersebut maka didapat file index.html yang perlu melakukan game tebak angka sebanyak 5 kali percobaan benar untuk mendapatkan flagnya.
