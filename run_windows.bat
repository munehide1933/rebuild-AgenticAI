@echo off
echo ========================================
echo Meta-Agent Development System
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/6] Checking environment...
if not exist ".env" (
    echo [WARNING] .env file not found, copying from .env.example
    copy backend\.env.example .env
    echo.
    echo [IMPORTANT] Please edit .env file and add your Azure OpenAI credentials!
    echo Press any key after you've configured .env...
    pause >nul
)

echo [2/6] Setting up backend...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

cd ..

echo [3/6] Setting up frontend...
cd frontend
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
)
cd ..

echo [4/6] Creating data directories...
mkdir backend\data\qdrant 2>nul
mkdir backend\data\sqlite 2>nul
mkdir backend\data\uploads 2>nul

echo [5/6] Starting Qdrant (local mode)...
echo Qdrant will run in embedded mode (no separate process needed)

echo [6/6] Starting services...
echo.
echo Starting backend on http://localhost:8000
echo Starting frontend on http://localhost:5173
echo.

REM 启动后端（新窗口）
start "Meta-Agent Backend" cmd /k "cd backend && venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM 等待2秒确保后端启动
timeout /t 2 /nobreak >nul

REM 启动前端（新窗口）
start "Meta-Agent Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to stop all services...
pause >nul

REM 停止服务
taskkill /FI "WINDOWTITLE eq Meta-Agent Backend*" /F
taskkill /FI "WINDOWTITLE eq Meta-Agent Frontend*" /F

echo Services stopped.
pause