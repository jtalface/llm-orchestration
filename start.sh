#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Starting LLM Orchestration Platform..."

# Start backend
PYTHONPATH=. .venv/bin/uvicorn backend.main:app \
  --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
cd frontend && npm run dev -- --port 5173 &
FRONTEND_PID=$!

echo ""
echo "✓ Backend:  http://localhost:8000"
echo "✓ Frontend: http://localhost:5173"
echo "✓ API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
