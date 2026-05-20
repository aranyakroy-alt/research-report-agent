#!/bin/bash
# Research & Report Agent — start backend + frontend
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "▶ Starting FastAPI backend on :8000 …"
cd "$ROOT"
.venv/bin/uvicorn poc2_research_agent.api.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "▶ Starting React frontend on :3000 …"
cd "$ROOT/frontend"
npm start &
FRONTEND_PID=$!

echo ""
echo "  Backend : http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Press Ctrl+C to stop both."

cleanup() {
  echo ""
  echo "Stopping processes…"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup INT TERM

wait
