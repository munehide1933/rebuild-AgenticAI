# Meta-Agent Development System

基于 FastAPI + React 的本地智能体开发系统，提供多模型路由、对话管理与流式输出能力，支持可选的 Web 搜索与用户偏好上下文。

## ✨ 主要功能

- **智能体推理策略**：简单问题走 CoT 直答，复杂问题走 ReAct + 工具调用（可选 Tavily 搜索）。
- **多模型路由**：根据问题内容在默认模型与计算机科学专家模型之间自动切换。
- **流式对话**：前端通过 SSE 逐块渲染回复，体验更自然。
- **会话管理**：支持会话列表、详情、删除，数据持久化到 SQLite。
- **MCP 上下文**：基于近期对话与用户偏好构建上下文提示。

## 🧱 技术栈

### 后端
- **FastAPI** + **SQLAlchemy (Async)**
- **Azure OpenAI**（默认模型 + DeepSeek 模型部署）
- **SQLite**（数据持久化）
- **Tavily**（可选 Web 搜索）

### 前端
- **React 18 + TypeScript**
- **Vite** 构建
- **Zustand** 状态管理
- **TailwindCSS** 样式

## 📁 项目结构

```
.
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # Agent 与推理策略
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── services/        # LLM/会话/用户偏好服务
│   │   ├── tools/           # 外部工具（Tavily 搜索）
│   │   └── utils/           # 启动检查、异常等
│   └── requirements.txt
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── stores/
│   │   └── types/
│   └── package.json
├── data/                    # 运行时数据（SQLite、上传、Qdrant 目录占位）
├── run_linux.sh             # Linux 一键启动
├── run_mac.sh               # macOS 一键启动
├── run_windows.bat          # Windows 一键启动
└── setup.py                 # 一键安装脚本
```

## ✅ 环境要求

- Python 3.10+
- Node.js 18+
- Azure OpenAI 访问权限（可不配置，系统会返回占位响应）

## ⚙️ 环境配置

在项目根目录创建 `.env` 文件，填写以下变量：

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.1-chat
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_DEEPSEEK_DEPLOYMENT_NAME=DeepSeek-R1-0528

DEFAULT_MODEL=gpt-5.1-chat
CS_SPECIALIST_MODEL=DeepSeek-R1-0528

SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# 可选：Web 搜索
WEB_SEARCH_ENABLED=false
TAVILY_API_KEY=
TAVILY_MAX_RESULTS=5
```

> 未配置 Azure OpenAI 时，接口仍可启动，但会返回占位响应。

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

前端地址：<http://localhost:5173>
后端地址：<http://localhost:8000>
API 文档：<http://localhost:8000/docs>

## 🔌 主要 API

- `POST /api/chat/message`：普通对话
- `POST /api/chat/stream`：流式对话（SSE）
- `GET /api/chat/conversations`：会话列表
- `GET /api/chat/conversations/{id}`：会话详情
- `DELETE /api/chat/conversations/{id}`：删除会话
- `GET /health`：健康检查

## 🗄️ 数据持久化

SQLite 数据库默认位置：

```
./data/sqlite/meta_agent.db
```

会话与消息会自动写入数据库；启动时会自动创建 `data/qdrant`、`data/sqlite`、`data/uploads` 目录。

## 🧩 说明

- **模型路由**：当问题包含编程相关关键字，会优先使用计算机科学专家模型。
- **Web 搜索**：启用 `WEB_SEARCH_ENABLED` 且配置 `TAVILY_API_KEY` 后，复杂问题将使用搜索工具辅助推理。

## 📄 License

MIT License
