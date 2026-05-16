# TS_ERP - ERP 智能助手系统

基于 **Python Agent Service**（智能体/ RAG） + **Spring Boot Java 后端** 构建的 ERP 智能助手系统。

## 项目概述

TS_ERP 是一个 ERP 智能助手系统，本仓库专注于 **Agent 智能体开发**，业务 API 由独立的 Java 后端项目提供。

### 项目组成

| 项目 | 路径 | 职责 |
|------|------|------|
| **Agent Service** | `agent_service/`（本仓库） | 意图识别、动态 SQL 生成、RAG 知识问答、多 Agent 编排 |
| **API Gateway** | `backend/`（本仓库） | 认证、聊天接口、知识库管理、代理转发至 Java 后端 |
| **Java 后端** | `D:\xuweiqun\py_project\TS_ERP_JAVA` | 业务 CRUD API、权限管理、审批流（Spring Boot） |

### 系统架构

```
┌──────────────────────────────────────────────────┐
│                   Client                         │
│          （第三方客户端 / 前端 / CLI）              │
└────────────────────────┬─────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────┐
│            Python Backend (FastAPI)              │ 8000
│  Auth / Chat / Knowledge / Java Proxy            │
└───────┬──────────────────────────┬───────────────┘
        │                          │
        ▼                          ▼
┌───────────────┐    ┌─────────────────────────────┐
│ Agent Service │    │   Java Backend (Spring Boot)│ 8080
│  Intent / RAG │    │   Business CRUD / 审批 / 权限 │
│  SQL / Memory │    │   MySQL / Redis / ES         │
└───────────────┘    └─────────────────────────────┘
```

## 技术栈

### 智能体服务 (agent_service)
- Python FastAPI
- LangChain / LangGraph
- Elasticsearch BM25 + 向量检索（RAG）
- Redis 会话管理

### API 网关 (backend)
- Python FastAPI
- SQLAlchemy + PyMySQL
- JWT 认证
- httpx（代理转发至 Java 后端）

### 外部依赖
- **Java 后端**：Spring Boot 3.x + MyBatis-Plus（独立项目 `TS_ERP_JAVA`）
- MySQL - 业务数据
- Redis - 缓存 / 会话 / 限流
- Elasticsearch - RAG 索引

## 目录结构

```
TS_ERP/
├── agent_service/          # 智能体服务（核心）
│   └── app/
│       ├── agents/         # Agent 核心逻辑
│       ├── clients/        # 外部 API 客户端（Java 后端等）
│       ├── core/           # 配置
│       ├── formatters/     # 响应格式化
│       ├── guards/         # SQL 安全校验
│       ├── memory/         # 对话上下文管理
│       ├── permissions/    # 权限上下文
│       └── rag/            # RAG 检索增强
├── backend/                # Python API 网关
│   └── app/
│       ├── api/v1/         # API 路由（auth / chat / knowledge / java-proxy）
│       ├── core/           # 配置 & 安全
│       └── models/         # 数据模型
├── docker/                 # Docker 编排
├── sql/                    # 数据库脚本
└── docs/                   # 项目文档
```

## 快速开始

### 环境要求

- Python 3.10+（推荐 Conda 环境 `advanced_rag`）
- MySQL 8.0
- Redis 7.0
- Elasticsearch 8.x
- JDK 17+（Java 后端需要）
- Maven 3.8+（Java 后端需要）

本机 Python 解释器路径：
```
D:\xuweiqun\anaconda3\envs\advanced_rag\python.exe
```

### 启动服务

```bash
# 1. 启动基础设施（MySQL / Redis / ES）
docker-compose -f docker/docker-compose.yml up -d mysql redis elasticsearch

# 2. 启动 Python Agent Service
cd agent_service
conda activate advanced_rag
python -m uvicorn app.main:app --reload --port 8001

# 3. 启动 Python API 网关
cd backend
conda activate advanced_rag
python -m uvicorn app.main:app --reload --port 8000

# 4. 启动 Java 后端（独立项目）
cd D:\xuweiqun\py_project\TS_ERP_JAVA
mvn spring-boot:run -Dspring-boot.run.profiles=local
```

### 配置说明

复制 `.env.example` 为 `.env`，按需修改：

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ts_erp

REDIS_HOST=127.0.0.1
REDIS_PORT=6379

ES_HOST=127.0.0.1
ES_PORT=9200

JWT_SECRET_KEY=your_secret_key_here

LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1

# Java 后端地址
JAVA_BACKEND_URL=http://localhost:8080
```

## Agent Service API

| 接口 | 说明 |
|------|------|
| `POST /agent/query` | 自然语言查询（意图识别 → SQL/RAG → 响应） |
| `POST /rag/search` | RAG 知识库检索 |
| `GET /health` | 健康检查 |

## API 网关接口

| 接口 | 说明 |
|------|------|
| `POST /api/v1/auth/login` | 用户登录 |
| `POST /api/v1/chat/query` | 智能客服查询（转发至 Agent Service） |
| `POST /api/v1/knowledge/search` | 知识库检索 |
| `GET/POST/PUT/DELETE /api/v1/java/*` | 代理转发至 Java 后端业务 API |

## Agent 处理流程

```
用户查询 → Intent 识别 → 参数提取 → 路由决策
    ├── fixed_query   → 固定模板 SQL 查询
    ├── dynamic_query → LLM 生成 SQL → 安全校验 → 执行
    ├── rag_query     → ES 向量检索 → LLM 回答
    ├── mixed_query   → SQL + RAG 混合
    └── permission_denied / need_clarification
        ↓
    响应格式化 → 保存会话上下文 → 返回
```

## 核心模块

### 1. 智能体服务 (agent_service)

- `agents/` - Agent 协调器、意图识别、参数提取、路由
- `clients/` - Java 后端 API 客户端
- `guards/` - SQL 安全校验（防注入）
- `formatters/` - 响应格式化
- `memory/` - 对话上下文管理
- `rag/` - RAG 检索增强（ES BM25 + 向量检索）

### 2. API 网关 (backend)

- `auth` - JWT 认证
- `chat` - 智能客服接口（调用 Agent Service）
- `knowledge` - 知识库管理
- `java_proxy` - 通用代理转发至 Java 后端

## License

MIT
