#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# verify_deploy.sh — rebuild challenge, exploit, verify flag (server lomba)
#
# Usage:
#   ./verify_deploy.sh [TARGET_IP_OR_HOST] [PORT] [CALIBRATE]
#
# Defaults: target = 127.0.0.1, port = 19321.
# Third arg: pass "calibrate" to auto-recalibrate solver offsets before verify.
#
# Needs: docker (daemon reachable), python3, curl.
#
# Flow:
#   1. docker compose up --build -d   (rebuild dari repo ini -> binary pin)
#   2. tunggu nginx + backend up
#   3. [optional] recalibrate PREREAD_HEAP_OFFSETS via recalibrate.py (admin-only)
#   4. bersihkan /tmp/rift_flag.txt (biar hasil bukan sisa run lama)
#   5. run exploit.py (leak /debug -> spray -> trigger -> system())
#   6. curl /loot/rift_flag.txt + bandingkan sama flag.txt lokal
#
# Exit 0 = exploit jalan + flag valid di server itu.
# Exit 1 = gagal (rebuild error, exploit gagal, atau flag nggak cocok).
# ---------------------------------------------------------------------------

TARGET="${1:-127.0.0.1}"
PORT="${2:-19321}"
MODE="${3:-}"

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKDIR"

echo "=============================================================="
echo "[1/6] Rebuild & start (pin build -> offset relatif tetap)"
echo "=============================================================="
docker compose up --build -d

CONTAINER="$(docker compose ps -q nginx-rift 2>/dev/null || docker compose ps -q 2>/dev/null | head -n1)"
if [ -z "$CONTAINER" ]; then
  CONTAINER="ctf-nginx-rift"
fi
echo "[*] container id: $CONTAINER"

echo "=============================================================="
echo "[2/6] Tunggu nginx + backend siap"
echo "=============================================================="
for i in $(seq 1 30); do
  if curl -sf -m 2 "http://${TARGET}:${PORT}/" >/dev/null 2>&1; then
    echo "[*] up setelah ${i}s"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "[!] target nggak up dalam 30s"
    exit 1
  fi
  sleep 1
done

if [ "$MODE" = "calibrate" ]; then
  echo "=============================================================="
  echo "[3/6] Rekalibrasi offset solver (admin-only, docker exec heap scan)"
  echo "=============================================================="
  python3 recalibrate.py --host "$TARGET" --port "$PORT" --container "$CONTAINER"
else
  echo "=============================================================="
  echo "[3/6] Skip rekalibrasi (offset pakai yang udah ada di exploit.py)"
  echo "=============================================================="
fi

echo "=============================================================="
echo "[4/6] Bersihkan loot sisa (biar hasil = run ini, bukan stale)"
echo "=============================================================="
docker exec "$CONTAINER" sh -lc 'rm -f /tmp/rift_flag.txt' 2>/dev/null || true
if curl -sf -m 2 "http://${TARGET}:${PORT}/loot/rift_flag.txt" >/dev/null 2>&1; then
  echo "[!] loot masih ke-serve setelah rm — kemungkinan alias/restart belum refresh, cek manual"
else
  echo "[*] loot bersih (404)"
fi

echo "=============================================================="
echo "[5/6] Run exploit.py"
echo "=============================================================="
python3 exploit.py --host "$TARGET" --port "$PORT"

echo "=============================================================="
echo "[6/6] Verifikasi flag"
echo "=============================================================="
GOT="$(curl -sf -m 3 "http://${TARGET}:${PORT}/loot/rift_flag.txt" || true)"
EXPECTED="$(cat flag.txt)"

echo "[*] loot : $GOT"
echo "[*] flag : $EXPECTED"

if [ -n "$GOT" ] && [ "$GOT" = "$EXPECTED" ]; then
  echo ""
  echo "=============================================================="
  echo "[OK] OFFSET VALID DI SERVER INI — chall siap dipakai"
  echo "=============================================================="
  exit 0
else
  echo ""
  echo "=============================================================="
  echo "[FAIL] flag nggak keluar / nggak cocok — kemungkinan drift offset"
  echo "       Step pas hari-H: jalankan ulang dengan mode calibrate"
  echo "         ./verify_deploy.sh $TARGET $PORT calibrate"
  echo "       Itu otomatis scan heap live + patch offset di exploit.py."
  echo "=============================================================="
  exit 1
fi
