#!/usr/bin/env bash
# ============================================================================
# start-dev.sh — 一键启动所有开发服务（Ctrl+C 统一退出）
# ============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_DIR="$PROJECT_DIR/server"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

PID_BACKEND=""
PID_SIMULATOR=""
PID_FRONTEND=""

trap 'echo ""; echo "正在停止所有服务..."; kill $PID_BACKEND $PID_SIMULATOR $PID_FRONTEND 2>/dev/null; wait; echo "已退出"; exit 0' SIGINT SIGTERM

# ── 后端 ──────────────────────────────────────────────────────────────────
echo "启动后端 (FastAPI + TCP Consumer)..."
cd "$SERVER_DIR"
"$VENV_PYTHON" -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
PID_BACKEND=$!
sleep 2

# ── 仿真器 ────────────────────────────────────────────────────────────────
echo "启动 IEC 61850 网关仿真器..."
"$VENV_PYTHON" tests/test_iec61850_gateway.py --interval 3 --port 9000 &
PID_SIMULATOR=$!
sleep 1

# ── 前端 ──────────────────────────────────────────────────────────────────
echo "启动前端 Vite 开发服务器..."
cd "$PROJECT_DIR"
pnpm dev &
PID_FRONTEND=$!

# ── 等待 —─────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo "  所有服务已启动，按 Ctrl+C 统一停止"
echo "  WebSocket: ws://0.0.0.0:8000/ws"
echo "  TCP:       0.0.0.0:9000"
echo "  前端:      http://localhost:5173/sc-datav/"
echo "  API:       http://0.0.0.0:8000/api/charts/4"
echo "═══════════════════════════════════════════════"
echo ""

wait