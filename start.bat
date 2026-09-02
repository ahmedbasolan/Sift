@echo off
title Sift - AI Due Diligence Copilot
echo.
echo  ============================
echo   Sift - Starting Services
echo  ============================
echo.

REM Check if backend .venv exists
if not exist "backend\.venv" (
    echo [1/4] Setting up Python virtual environment...
    cd backend
    py -m venv .venv
    call .venv\Scripts\activate.bat
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    cd ..
) else (
    echo [1/4] Backend venv found.
)

REM Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo [2/4] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo [2/4] Frontend node_modules found.
)

echo [3/4] Starting backend on port 8000...
start "Sift Backend" cmd /k "cd backend && .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM Wait for backend to be ready
echo [4/4] Waiting for backend to start...
timeout /t 5 /nobreak >nul

:check_backend
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto check_backend
)
echo       Backend ready!

echo.
echo  ============================
echo   All services running!
echo  ============================
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.

REM Start frontend in current window
cd frontend && npx next dev
