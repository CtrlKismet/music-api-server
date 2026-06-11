#!/bin/bash
# Wrapper that runs uvicorn and kills it when parent process exits.
# Usage: ./run.sh <parent-pid>
PARENT_PID=$1
PORT=${2:-5000}
DIR="$(cd "$(dirname "$0")" && pwd)"

# Start uvicorn in background
"$DIR/venv/bin/python" -u -m uvicorn main:app --host 127.0.0.1 --port "$PORT" --log-level warning &
UVICORN_PID=$!

# Wait for parent to exit, then kill uvicorn
while kill -0 "$PARENT_PID" 2>/dev/null; do
  sleep 0.5
done
kill "$UVICORN_PID" 2>/dev/null
wait "$UVICORN_PID" 2>/dev/null
