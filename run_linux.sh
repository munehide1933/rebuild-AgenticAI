#!/bin/bash

echo "========================================"
echo "Meta-Agent Development System"
echo "========================================"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo "Please install Python 3.10+ using: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Node.js is not installed"
    echo "Please install Node.js using: sudo apt install nodejs npm"
    exit 1
fi

echo -e "${GREEN}[1/6]${NC} Checking environment..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env file not found, copying from .env.example"
    cp .env.example .env
    echo
    echo -e "${YELLOW}[IMPORTANT]${NC} Please edit .env file and add your Azure OpenAI credentials!"
    read -p "Press Enter after you've configured .env..."
fi

echo -e "${GREEN}[2/6]${NC} Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

cd ..

echo -e "${GREEN}[3/6]${NC} Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

cd ..

echo -e "${GREEN}[4/6]${NC} Creating data directories..."
mkdir -p data/qdrant
mkdir -p data/sqlite
mkdir -p data/uploads

echo -e "${GREEN}[5/6]${NC} Starting Qdrant (local mode)..."
echo "Qdrant will run in embedded mode (no separate process needed)"

echo -e "${GREEN}[6/6]${NC} Starting services..."
echo
echo "Starting backend on http://localhost:8000"
echo "Starting frontend on http://localhost:3000"
echo

# 启动后端
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo
echo "========================================"
echo -e "${GREEN}Services are running!${NC}"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo "========================================"
echo
echo "Press Ctrl+C to stop all services..."

# 捕获Ctrl+C信号
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT

# 等待
wait
