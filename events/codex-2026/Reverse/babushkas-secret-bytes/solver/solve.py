import marshal

# Paste PAYLOAD dari build_simple_challenge.py di sini
PAYLOAD = b'\xb6UUUUUUUUUUUUTUUUUUUU\xa6_UUU\xc0U\x06UOU\'U2T|W6TUUUUUUUUUUURUUUVUUU\xa6\x89UUU\xc0U\x0eTUUUUUUUU\x00U`TUUUUUU\x06To"UU4TUU2WzU\x06V\x04T;T\x0eVUUUUUUUU\x00U`TUUUUUUFU\x03W\x03V&VzU&WFU\x1dCUU WUU%v\x0ePUUUUUUUU\x00V`TUUUUUU\x06QxYUU\x00WxUUU\x05W\x18MUU^UuU;Q;W;V\x00Q\x06U\x06U\x06PgVPUUU;Q\x00QFU\x03P&WzU&WFU\x1dRUU:\x00\x06SxUUU\x05W\x18\\UU^UuU;Q;P\r\x14o\x1dUUqU&WuU&V;V;W3U&WuU&W;P3U|R\x1b\xbchUUU\x13|h\xbc\x04UUU\xbc#UUU\xbc+UUU\xbc\x07UUU\xbc\x17UUU\xbc)UUU\xbc\xd1UUU\xbc\xd4UUU\xbc2UUU\xbc\x15UUU\xbc\rUUU\xbc*UUU\'PUUU\xbcbUUU\xbc UUU\xbc\x0eUUU\xbc\nUUU\xbc,UUU\xbc<UUU\xbc\'UUU\xbc=UUU\xbc\x0fUUU\']UUU\xbc4UUU\xbc\x1cUUU\xbc\x03UUU\xbc>UUU\xbc\x10UUU\'LUUU\'RUUU\'YUUU\'IUUU\xbc3UUU\'BUUU\xbc\x18UUU\xbccUUU\']UUU\'VUUU\xbc5UUU\xbcIUUU\xbc\x12UUU\xbc\x00UUU\'tUUU\xbczUUU\'VUUU\xbc\tUUU\xbc\x14UUU\'MUUU\xbc~UUU\xbc\x1aUUU\'[UUU\'}UUU\'uUUU\xbcCUUU\'RUUU\'JUUU\'uUUU\'XUUU\'XUUU\xbc\x11UUU\'EUUU\xbc&UUU\xbc\xaa\xaa\xaa\xaa\xbcRUUU|V\x8fV90;\x8f\\0; 80\'4!0\x8fV:\'1|S\x8f_ &0\'\n<;% !\x8fS!4\'20!\x8fT<\x8fT6\x8fV\'0&\x8fT#&SUUUuuuuuu\x8fYi&<8%90\n\'0#k\x8f_6=06>\n3942\'lUUUWUUU&,UUU\xd5U\x89R_\xddo\xd6*\xcdw\x86RI\x8dZA\xa7QU[\x01Q\xd5\x13\xa1SUy`\xe5\x0f\x81~\x15\x81_\x14\x87~\x15\xf4a\xf5d\xd9\x16\xc5T\xde\x13\xc5\x01\xdc\x18\xcd\x04\x81^K\x84~\x15\xd5\x16\x84_\x14\x8d_X\xdc1\xc5W\xdd1\xdc|\xd5\x16\x8cOH\x86_K\xcfv\xc5\x04\xdd$\xd9`\xccv\xd5\x16\x85_K\xb5^[\xdch\x85QM\xac\xa6\\U^\x17T\xac\xb7_K&^UUU\xf6H\x14vS\x94Z[\x14|Q\x1b|T\'lUUU\xfcU\xa6UUUU\'mUUU\x8f]i8:1 90k\'iUUUTUUU&_UUU\xa5VTTT\xa6Q^TL\'nUUU'

def solve():
    print("[*] Dekripsi Inner Payload...")
    # 1. Dekripsi outer layer (XOR 0x55)
    raw_bytes = bytes([b ^ 0x55 for b in PAYLOAD])
    inner_code_obj = marshal.loads(raw_bytes)
    
    # 2. Eksekusi inner code object untuk mendapatkan scope fungsi
    scope = {}
    exec(inner_code_obj, scope)
    
    check_flag_func = scope["check_flag"]
    consts = check_flag_func.__code__.co_consts
    
    print(f"[*] Daftar isi co_consts fungsi: {consts!r}")
    
    # 3. Cari elemen di co_consts yang berupa tuple/list (array angka target)
    target = None
    for c in consts:
        if isinstance(c, (tuple, list)) and len(c) > 0:
            target = c
            break
            
    if target is None:
        print("[-] Gagal menemukan array target di dalam co_consts!")
        return

    print(f"[+] Target Array Ditemukan: {target}")
    
    # --- REVERSING LOGIC ---
    # Algoritma Enkripsi : ((ord(c) ^ 0x73) + i) -> Reverse -> (+ 7) = Target
    # Algoritma Dekripsi : Target -> (- 7) -> Reverse -> (- i) -> (^ 0x73) = Char
    
    # Step 1: Kurangi 7 dari tiap elemen
    step1 = [v - 7 for v in target]
    
    # Step 2: Balikkan kembali urutan array (Un-reverse)
    step2 = step1[::-1]
    
    # Step 3: Kurangi indeks (i) lalu XOR dengan 0x73
    flag_chars = []
    for i, val in enumerate(step2):
        char_code = (val - i) ^ 0x73
        flag_chars.append(chr(char_code))
        
    flag = "".join(flag_chars)
    
    print("\n" + "=" * 40)
    print(f"[+] FLAG DITEMUKAN: {flag}")
    print("=" * 40)

if __name__ == "__main__":
    solve()