#!/bin/bash

echo "=== Sift ==="
echo "Starting backend and frontend..."

# Install backend deps if needed
if [ ! -d "backend/.venv" ]; then
  echo "Setting up Python venv..."
  cd backend
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
  cd ..
fi

# Install frontend deps if needed
if [ ! -d "frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  cd frontend
  npm install
  cd ..
fi

# Start backend in background
echo "Starting backend on port 8000..."
cd backend
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 30); do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  sleep 1
done

# Start frontend
echo "Starting frontend on port 3000..."
cd frontend
PORT=3000 npx next start &
FRONTEND_PID=$!
cd ..

echo "=== Services running ==="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
