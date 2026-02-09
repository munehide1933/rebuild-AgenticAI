# Meta-Agent Development System

基于 **Python 3.12 + FastAPI + LangChain + LangGraph** 的后端服务，与 **Next.js** 前端实现的本地智能体开发系统。前端使用 **Azure GPT-5.1** 做意图识别；后端使用 **DeepSeek-R1** 生成代码补丁，支持 MCP 上下文协议与多轮会话长期记忆。

## ✨ 主要功能

- **意图识别**：Next.js 服务端 API 使用 Azure GPT-5.1 进行意图识别。
- **LangGraph 编排**：`intent → repo → architecture → patch` 形成补丁生成链路。
- **流式对话**：前端通过 SSE 渲染流式响应。
- **会话管理**：会话列表、详情、删除（前端删除，数据库软删除保留审计）。
- **仓库分析**：支持本地路径或 GitHub URL 分析。

## 🧱 技术栈

### 后端
- **FastAPI** + **SQLAlchemy (Async)**
- **LangChain + LangGraph**
- **Azure OpenAI**（意图分析等）
- **DeepSeek-R1**（代码补丁生成）
- **SQLite**（数据持久化）

### 前端
- **Next.js (App Router)**
- **React 18 + TypeScript**
- **Zustand + TailwindCSS**

## 📁 项目结构

```
.
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # Agent 与推理策略
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── services/        # LLM/会话/补丁服务
│   │   └── utils/           # 启动检查、异常等
├── frontend/                # Next.js 前端
│   ├── src/
│   │   ├── app/             # App Router
│   │   ├── components/      # UI 组件
│   │   ├── services/        # API 调用
│   │   └── stores/          # 状态管理
├── data/                    # 运行时数据（SQLite、上传）
├── run_linux.sh             # Linux 一键启动
├── run_mac.sh               # macOS 一键启动
├── run_windows.bat          # Windows 一键启动
└── setup.py                 # 一键安装脚本
```

## ⚙️ 环境配置

在项目根目录创建 `.env` 文件（可参考 `.env.example`）：

```bash
# Backend - Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.1-chat
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# Backend - DeepSeek (非 Azure)
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=your-deepseek-key
DEEPSEEK_MODEL=deepseek-r1

DEFAULT_MODEL=gpt-5.1-chat
CS_SPECIALIST_MODEL=DeepSeek-R1-0528

SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## 🚀 快速开始

### 方式一：一键安装 + 启动（推荐）

```bash
python setup.py
```

随后执行对应系统的启动脚本：

```bash
# Linux
./run_linux.sh

# macOS
./run_mac.sh

# Windows
run_windows.bat
```

### 方式二：手动启动

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd ../frontend
npm install
npm run dev
```

前端地址：<http://localhost:3000>
后端地址：<http://localhost:8000>
API 文档：<http://localhost:8000/docs>

## 🔌 主要 API

- `POST /api/chat/message`：普通对话
- `POST /api/chat/stream`：流式对话（SSE）
- `GET /api/chat/conversations`：会话列表
- `GET /api/chat/conversations/{id}`：会话详情
- `DELETE /api/chat/conversations/{id}`：删除会话（软删除）
- `POST /api/analyze`：仓库分析
- `POST /api/generate_patch`：生成代码补丁（DeepSeek-R1）

## 🧩 说明

- **意图识别**：Next.js API 使用 Azure GPT-5.1，仅在服务端使用密钥。
- **补丁生成**：LangGraph 编排 intent → repo → architecture → patch，最终由 DeepSeek-R1 输出 diff。
- **长期记忆**：会话内容写入 SQLite，MCP 上下文自动带入历史与偏好。

## 📄 License

MIT License
