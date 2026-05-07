# TS_ERP - ERP 智能助手系统

基于 FastAPI + Vue 3 + Agent Service 构建的可代码化管理 ERP 智能助手系统。

## 项目概述

TS_ERP 是一个全新的 ERP 智能助手系统，采用代码化管理替代低代码节点编排，具备以下能力：

- 客户、订单、库存、财务四大业务模块
- 智能客服聊天交互
- 意图识别与动态 SQL 生成
- RAG 知识库问答
- RBAC 权限控制与数据权限策略

## 技术栈

### 前端
- Vue 3 + TypeScript
- Vite
- Element Plus
- Pinia 状态管理
- Vue Router

### 后端
- FastAPI (Python)
- SQLAlchemy 2.x
- Alembic 数据迁移
- JWT 认证

### 智能体服务
- Python Agent Service
- LangChain 检索编排
- Elasticsearch BM25 + 向量检索

### 基础设施
- MySQL - 业务数据
- Redis - 缓存/会话/限流
- Elasticsearch - 搜索/日志/RAG 索引
- Docker Compose - 容器编排

## 目录结构

```
TS_ERP/
├── frontend/          # Vue 3 前端项目
├── backend/          # FastAPI 主服务
├── agent_service/    # 智能体服务
├── worker/           # 异步任务服务
├── sql/              # 数据库脚本
├── docker/           # Docker 配置
└── docs/             # 项目文档
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- MySQL 8.0
- Redis 7.0
- Elasticsearch 8.x

### 启动服务

```bash
# 1. 启动基础设施
docker-compose -f docker/docker-compose.yml up -d

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 初始化数据库
alembic upgrade head

# 4. 启动后端服务
uvicorn app.main:app --reload --port 8000

# 5. 安装前端依赖
cd ../frontend
npm install

# 6. 启动前端
npm run dev
```

## 系统架构

```
┌────────────────────────────────────────────┐
│                 Vue Frontend               │
│  ERP页面 / 智能客服 / 查询结果 / 管理后台   │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│              FastAPI API Gateway           │
│ 登录鉴权 / ERP API / Agent API / 日志 / 配置 │
└────────────────────────────────────────────┘
        │                  │                 │
        ▼                  ▼                 ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│    MySQL     │   │    Redis     │   │ Elasticsearch│
│ 业务真数据    │   │缓存/会话/限流│   │搜索/日志/索引 │
└──────────────┘   └──────────────┘   └──────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│               Agent Service                │
│ Intent / Params / Policy / SQL / Formatter │
└────────────────────────────────────────────┘
```

## 核心模块

### 1. 后端服务 (backend)

- `api/` - API 路由定义
- `auth/` - 认证鉴权
- `core/` - 核心配置
- `db/` - 数据库连接
- `models/` - SQLAlchemy 模型
- `permissions/` - 权限系统
- `repositories/` - 数据访问层
- `schemas/` - Pydantic schemas
- `services/` - 业务逻辑层

### 2. 智能体服务 (agent_service)

- `agents/` - Agent 核心逻辑
- `prompts/` - 提示词模板
- `guards/` - SQL 安全校验
- `formatters/` - 响应格式化
- `memory/` - 对话上下文管理
- `rag/` - RAG 检索增强
- `permissions/` - 权限上下文校验

### 3. 前端 (frontend)

- `views/` - 页面组件
- `components/` - 通用组件
- `api/` - API 调用封装
- `stores/` - Pinia 状态管理
- `router/` - 路由配置

## API 接口

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新 Token
- `POST /api/v1/auth/logout` - 退出登录

### ERP 业务接口
- `/api/v1/customers` - 客户管理
- `/api/v1/orders` - 订单管理
- `/api/v1/inventory` - 库存管理
- `/api/v1/finance` - 财务管理

### 智能客服接口
- `POST /api/v1/chat/query` - 自然语言查询
- `POST /api/v1/chat/reset` - 重置会话
- `GET /api/v1/chat/history` - 获取历史记录

### 知识库接口
- `GET /api/v1/knowledge/bases` - 知识库列表
- `POST /api/v1/knowledge/documents` - 上传文档
- `POST /api/v1/knowledge/search` - 知识检索

## 权限模型

系统采用 RBAC + 数据权限策略：

- **功能权限**：菜单、按钮、API 访问
- **数据权限**：组织范围、部门范围、自定义范围
- **知识权限**：知识库访问、文档可见性

## RAG 演进路线

- **一期**：工程化 RAG - ES BM25 + ES 向量检索
- **二期**：高级 RAG - Query Rewrite + Reranker
- **三期**：LangGraph Agent - 状态机化
- **四期**：多 Agent 协作
- **五期**：SFT / LoRA 微调

## 开发指南

详见 [docs/](docs/) 目录下的详细文档。

## License

MIT
