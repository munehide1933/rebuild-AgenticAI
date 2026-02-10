#!/usr/bin/env bash
# Meta-Agent 开发环境启动脚本 - macOS (Apple Silicon / Intel)

set -e

echo "========================================"
echo "Meta-Agent Development System (macOS)"
echo "========================================"
echo

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 Python（Mac 上多为 python3）
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}[ERROR]${NC} Python not found. Install: brew install python@3.11"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Node.js not found. Install: brew install node"
    exit 1
fi

echo -e "${GREEN}[1/6]${NC} Checking environment..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env not found, copying from .env.example"
    cp .env.example .env
    echo
    echo -e "${YELLOW}[IMPORTANT]${NC} Edit .env and add your Azure OpenAI credentials!"
    read -p "Press Enter after you've configured .env..."
fi

echo -e "${GREEN}[2/6]${NC} Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi
echo "Activating virtual environment..."
source venv/bin/activate
echo "Installing Python dependencies..."
pip install -q -r requirements.txt
cd ..

echo -e "${GREEN}[3/6]${NC} Setting up frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi
cd ..

echo -e "${GREEN}[4/6]${NC} Creating data directories..."
mkdir -p data/qdrant data/sqlite data/uploads

echo -e "${GREEN}[5/6]${NC} Qdrant (embedded, no separate process)"

echo -e "${GREEN}[6/6]${NC} Starting services..."
echo
echo "Backend will run on http://localhost:8000"
echo "Frontend will run on http://localhost:3000"
echo

# 启动后端（当前目录要在项目根）
(
  cd backend
  source venv/bin/activate
  exec python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

# 等待后端就绪：轮询 /health，最多 60 秒
echo "Waiting for backend to be ready..."
MAX_WAIT=60
INTERVAL=2
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}Backend is ready.${NC}"
    break
  fi
  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
  printf "  ... %ds\r" $ELAPSED
done
if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo -e "${RED}[ERROR]${NC} Backend did not become ready in ${MAX_WAIT}s. Check backend window for errors."
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
fi

# 启动前端
(
  cd frontend
  exec npm run dev
) &
FRONTEND_PID=$!

echo
echo "========================================"
echo -e "${GREEN}Services are running.${NC}"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo "========================================"
echo
echo "Press Ctrl+C to stop all services."

trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
