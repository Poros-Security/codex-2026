## PoC

1. Buka binary dengan Ghidra/IDA/Cutter, lalu cari fungsi yang memakai operasi XOR (^).
2. Akan ditemukan key XOR: m3m0ry_X0R_k3y!
3. Di fungsi main, input sepanjang 40 byte di-XOR dengan key berulang, hasilnya disimpan di heap
4. Dekripsi tiap byte dengan XOR key berulang