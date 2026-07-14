#!/usr/bin/env bash
# webapp/scripts/dev.sh — macOS / Linux 一键启动 WebApp
# 用法：
#   bash webapp/scripts/dev.sh
set -e
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "== Trader WebApp dev launcher (macOS / Linux) =="
echo "  root: $ROOT"

# ---------- 后端 ----------
PYTHONPATH="$ROOT" python -m uvicorn webapp.backend.server:app \
    --host 127.0.0.1 --port 8765 --log-level info &
BACKEND_PID=$!
echo "  backend PID: $BACKEND_PID"

# 等就绪
for i in $(seq 1 30); do
    sleep 1
    if curl -fs "http://127.0.0.1:8765/api/health" > /dev/null 2>&1; then
        echo "  [ok] backend up"
        break
    fi
done

# ---------- 前端 ----------
cd "$ROOT/webapp/frontend"
[ -d node_modules ] || npm install --no-audit --no-fund --silent
npm run dev &
FRONTEND_PID=$!
echo "  frontend PID: $FRONTEND_PID"

trap "echo 'stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
