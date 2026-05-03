<div align="center">

# 🤖 多Agent智能求职助手

**基于 LangGraph + MCP + Vue3 构建的多智能体协作求职系统**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue3](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-orange)](https://github.com/langchain-ai/langgraph)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple)](https://modelcontextprotocol.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*JD 解析 → 简历分析 → 匹配评分 → 简历优化 → 面试题生成 → 智能对话，全流程 AI 驱动*

</div>

---

## 💡 项目亮点

- 🧠 **Multi-Agent 架构**：基于 LangGraph 状态图实现 5 个专业子 Agent 的有向无环协作调度
- 🔌 **MCP 协议集成**：通过 Model Context Protocol 标准接入外部岗位搜索能力，解耦数据源与业务逻辑
- ⚡ **SSE 实时流式输出**：全链路 Server-Sent Events，前端逐字渲染，用户体验如同与 AI 实时对话
- 🧩 **OpenAI 兼容接口**：一份代码无缝适配 Qwen / GLM / DeepSeek / GPT-4o 等主流大模型
- 💾 **SQLite 持久化记忆**：支持多会话管理、聊天历史回溯、用户画像（弱项/技能标签）累积
- 🔍 **Langfuse 可观测性**：可选接入 Langfuse，追踪每次 LLM 调用的耗时、Token 消耗与链路关系
- 🐳 **Docker 一键部署**：`docker-compose up` 即可完成前后端 + Nginx 的生产环境部署

---

## 📐 系统架构

```
┌───────────────────────────────────────────────────────────────┐
│                   Frontend (Vue3 + Vite + Pinia)              │
│          上传简历 · 粘贴JD · 聊天对话 · 查看结果              │
├───────────────────────────────────────────────────────────────┤
│                   FastAPI (SSE Stream + REST)                 │
├───────────────────────────────────────────────────────────────┤
│              PlannerAgent — LangGraph 中枢调度                │
├─────────┬──────────┬──────────┬───────────┬──────────────────┤
│ JD解析   │ 简历解析  │ 匹配分析  │ 简历优化   │   面试问答       │
│ Agent   │ Agent    │ Agent   │ Agent     │   Agent          │
├─────────┴──────────┴──────────┴───────────┴──────────────────┤
│                       Tools & Storage                         │
│  LLM Client · PDF Parser · SQLite Memory · RAG · MCP Client │
├───────────────────────────────────────────────────────────────┤
│               MCP Server (岗位搜索 / 可扩展)                  │
│         stdio 协议通信 — 可替换为真实招聘平台 API              │
└───────────────────────────────────────────────────────────────┘
```

---

## ✨ 核心功能

| 功能 | 说明 |
|:-----|:-----|
| 📋 **JD 智能解析** | 结构化抽取岗位名称、技能要求、职责描述，输出标准化 JSON |
| 📄 **简历深度分析** | 解析 PDF/文本简历，STAR 法则结构化项目经历，提取技能图谱 |
| 🎯 **人岗匹配评分** | 多维度计算匹配率，精准定位优势项与待提升项 |
| ✍️ **简历定向优化** | 基于目标 JD 关键词对齐，生成优化建议与改写版本 |
| 🧠 **面试题生成** | 覆盖技术面 / 项目面 / 行为面三大场景，附参考答案与追问思路 |
| 🔍 **岗位智能搜索** | 通过 MCP 协议调用岗位搜索服务，支持关键词 / 城市 / 薪资过滤 |
| 💬 **多轮智能对话** | 基于分析上下文的持续对话，支持追问细节、深入讨论 |
| 🔄 **SSE 流式输出** | 全链路实时流式渲染，分析过程可视化 |
| 💾 **多会话记忆** | SQLite 持久化存储，支持历史回溯与会话切换 |

---

## 🛠 技术栈

| 层级 | 技术选型 |
|:-----|:---------|
| **前端** | Vue 3 + Vite + Pinia + Element Plus + SSE |
| **后端框架** | FastAPI (async) + Uvicorn |
| **Agent 编排** | LangGraph (StateGraph / DAG) + LangChain |
| **工具协议** | MCP (Model Context Protocol) — stdio 客户端 + 服务端 |
| **大模型** | Qwen / GLM / DeepSeek / GPT-4o（OpenAI 兼容接口） |
| **持久化** | SQLite（会话 + 记忆 + 用户画像） |
| **可观测性** | Langfuse（可选，LLM Tracing & Monitoring） |
| **文档解析** | PyPDF2 |
| **部署** | Docker Compose + Nginx 反向代理 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 大模型 API 密钥（任选：阿里 DashScope / 智谱 / OpenAI）

### 1️⃣ 克隆项目

```bash
git clone https://github.com/www41762/job-Multi-Agent
cd job-agent
```

### 2️⃣ 配置环境变量

复制示例配置并填入你的 API Key：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`：

```env
LLM_MODEL=qwen-plus
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# MCP 岗位搜索（已内置本地 MCP Server，开箱即用）
JOB_MCP_CMD=python
JOB_MCP_ARGS=D:/your-path/backend/job_mcp_server.py
JOB_MCP_TOOL_NAME=search_jobs
```

### 3️⃣ 安装依赖 & 启动

```bash
# 后端
cd backend
pip install -r requirements.txt
python main.py

# 前端（新终端）
cd frontend
npm install
npm run dev
```

### 4️⃣ Docker 一键部署（推荐生产环境）

```bash
docker-compose up --build
```

### 5️⃣ 访问应用

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173（开发）/ http://localhost（Docker） |
| 后端 API 文档 | http://localhost:8000/docs |

---

## 📁 项目结构

```
├── backend/                        # Python 后端
│   ├── main.py                     # FastAPI 入口 (SSE + REST)
│   ├── job_mcp_server.py           # 岗位搜索 MCP Server（独立进程）
│   ├── agents/                     # Multi-Agent 模块
│   │   ├── planner_agent.py        # LangGraph 中枢调度
│   │   ├── job_parser_agent.py     # JD 解析 Agent
│   │   ├── resume_analyzer_agent.py# 简历分析 Agent
│   │   ├── matcher_agent.py        # 匹配评分 Agent
│   │   ├── resume_writer_agent.py  # 简历优化 Agent
│   │   └── interview_qa_agent.py   # 面试问答 Agent
│   ├── tools/                      # 工具层
│   │   ├── llm_client.py           # LLM 统一客户端（OpenAI 兼容）
│   │   ├── job_search.py           # 岗位搜索（MCP Client + Fallback）
│   │   ├── pdf_parser.py           # PDF 解析
│   │   ├── db_memory.py            # SQLite 持久化记忆
│   │   ├── rag_tool.py             # RAG 向量存储
│   │   └── langfuse_tracer.py      # Langfuse 可观测性
│   ├── config/                     # 配置 & Prompt
│   │   ├── config.py               # 全局配置
│   │   └── prompts.py              # Agent System Prompts
│   └── data/                       # 运行时数据
│       ├── resumes/                # 上传的简历
│       ├── vector_db/              # 向量存储 + SQLite
│       └── chat_history/           # 历史记录
├── frontend/                       # Vue3 前端
│   ├── src/
│   │   ├── views/Home.vue          # 主交互页面
│   │   ├── stores/session.js       # Pinia 会话状态
│   │   ├── utils/api.js            # 后端通信 (SSE + Fetch)
│   │   └── utils/markdown.js       # Markdown 渲染
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml              # Docker 编排
└── README.md
```

---

## 📝 API 接口

| 接口 | 方法 | 说明 |
|:-----|:-----|:-----|
| `/api/session/create` | POST | 创建新会话 |
| `/api/session/list` | GET | 获取会话列表（含标题/时间/消息数） |
| `/api/session/{id}/history` | GET | 获取会话历史 & 分析结果 |
| `/api/session/{id}` | DELETE | 删除会话 |
| `/api/analyze` | POST | 全流程分析（SSE 流式） |
| `/api/chat` | POST | 智能对话（SSE 流式） |
| `/api/parse-jd` | POST | 单独解析 JD |
| `/api/parse-resume` | POST | 单独解析简历（支持 PDF 上传） |
| `/api/job/search` | POST | 岗位搜索（MCP 驱动） |
| `/api/results/{id}` | GET | 获取分析结果 |

---

## 🔌 MCP 架构说明

本项目通过 [Model Context Protocol](https://modelcontextprotocol.io) 将**岗位搜索**能力解耦为独立的 MCP Server：

```
JobSearchTool (MCP Client)  ──stdio──▶  job_mcp_server.py (MCP Server)
        │                                        │
        │  如果 MCP 未配置或调用失败                │  声明 search_jobs 工具
        ▼                                        ▼
   LLM Fallback (Mock 生成)              可替换为真实招聘 API
```

- **开箱即用**：项目内置 `job_mcp_server.py`，无需额外安装即可体验完整链路
- **可热插拔**：未来接入 Boss 直聘 / 猎聘等真实 API 时，只需替换 MCP Server 实现，主工程零改动
- **容错降级**：当 MCP 服务不可用时，自动降级为 LLM 智能生成岗位数据

---

## 🔍 可观测性（Langfuse）

项目已集成 [Langfuse](https://langfuse.com) 用于 LLM 全链路追踪：

```env
LANGFUSE_ENABLED=true
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

启用后可追踪：每个 Agent 的 Prompt / Completion / Token 消耗 / 延迟，以及完整的调用链路。

---

## 📄 License

[MIT](LICENSE) © 2025
