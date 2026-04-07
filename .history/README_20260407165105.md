# 🤖 多Agent智能求职助手

基于 **LangGraph + Vue3** 的多Agent协作智能求职系统，支持JD解析、简历分析、匹配评分、简历优化、面试题生成和智能对话。

## 📐 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    交互层 (Vue3 + Element Plus)           │
│         上传简历 / 粘贴JD / 聊天对话 / 查看结果            │
├─────────────────────────────────────────────────────────┤
│                 Agent调度层 (LangGraph)                   │
│              PlannerAgent 中枢调度器                       │
├──────┬──────┬──────┬──────────┬──────────┤
│  JD   │ 简历  │ 匹配  │  简历优化  │  面试问答  │
│ 解析  │ 解析  │ 分析  │   Agent   │  Agent   │
├──────┴──────┴──────┴──────────┴──────────┤
│               工具/存储层                              │
│   PDF解析 | LLM客户端 | 记忆存储 | RAG向量库            │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 环境准备

- Python 3.10+
- Node.js 18+
- 大模型API密钥（支持Qwen/GLM/GPT-4o等OpenAI兼容接口）

### 2. 配置API密钥

编辑 `backend/.env` 文件：

```bash
LLM_MODEL=qwen-plus
LLM_API_KEY=你的API密钥
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 4. 启动服务

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Docker部署:**
```bash
docker-compose up --build
```

### 5. 访问

- 前端: http://localhost:5173
- 后端API文档: http://localhost:8000/docs

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📋 JD解析 | 结构化抽取岗位名称、技能要求、职责等 |
| 📄 简历解析 | 解析PDF/文本简历，STAR法则结构化项目经历 |
| 🔗 匹配分析 | 计算匹配度评分，分析优势/不足 |
| ✍️ 简历优化 | 关键词对齐，定向优化简历内容 |
| 🎯 面试题库 | 技术面+项目面+行为面，附参考答案 |
| 💬 智能对话 | 基于分析结果的多轮对话，支持追问 |
| 🔄 流式输出 | SSE实时流式展示分析进度和对话回复 |
| 💾 记忆功能 | 多会话管理，聊天历史和分析结果持久化 |

## 🛠 技术栈

| 模块 | 技术 |
|------|------|
| 前端 | Vue3 + Element Plus + Vite + Pinia |
| 后端 | FastAPI + LangGraph + LangChain |
| 大模型 | Qwen/GLM/GPT-4o（OpenAI兼容接口） |
| 流式输出 | SSE (Server-Sent Events) |
| 文档解析 | PyPDF2 |
| 部署 | Docker + Nginx |

## 📁 项目结构

```
智能体项目/
├── backend/                # 后端服务
│   ├── main.py            # FastAPI入口
│   ├── agents/            # Agent模块
│   │   ├── planner_agent.py       # 中枢调度
│   │   ├── job_parser_agent.py    # JD解析
│   │   ├── resume_analyzer_agent.py # 简历解析
│   │   ├── matcher_agent.py       # 匹配分析
│   │   ├── resume_writer_agent.py # 简历优化
│   │   └── interview_qa_agent.py  # 面试问答
│   ├── tools/             # 工具模块
│   │   ├── llm_client.py  # LLM客户端
│   │   ├── pdf_parser.py  # PDF解析
│   │   └── rag_tool.py    # 记忆存储
│   ├── config/            # 配置
│   │   ├── config.py      # 全局配置
│   │   └── prompts.py     # Agent Prompts
│   └── data/              # 数据目录
├── frontend/              # 前端服务
│   ├── src/
│   │   ├── views/Home.vue # 主页面
│   │   ├── stores/        # Pinia状态
│   │   └── utils/         # 工具函数
│   └── ...
├── docker-compose.yml     # Docker编排
├── start.bat / start.sh   # 启动脚本
└── README.md
```

## 📝 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/session/create` | POST | 创建会话 |
| `/api/session/list` | GET | 会话列表 |
| `/api/session/{id}/history` | GET | 获取历史 |
| `/api/analyze` | POST | 全流程分析(SSE) |
| `/api/chat` | POST | 聊天对话(SSE) |
| `/api/parse-jd` | POST | 单独解析JD |
| `/api/parse-resume` | POST | 单独解析简历 |
| `/api/results/{id}` | GET | 获取分析结果 |
