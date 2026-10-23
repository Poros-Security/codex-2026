## PoC
1. Analisis clipping koran berbahasa Korea yang diberikan.
2. Temukan kota, isu lingkungan, vehicle emission grade, dan tanggal kebijakan.
3. Hubungkan ke service Netcat menggunakan `nc <HOST> <PORT>`.
4. Daftar pertanyaan:
    - Q1. Which city is relevant to the measure?
    - Q2. What environmental issue is discussed in the clipping?
    - Q3. Which vehicle emission grade was affected?
    - Q4. On what date did the measure take effect? Format: YYYY-MM-DD
5. Jawab seluruh pertanyaan dengan:
    - `SEOUL`
    - `PM2.5`
    - `GRADE 5`
    - `2019-02-15`
6. Jika seluruh jawaban benar, service memberikan flag.