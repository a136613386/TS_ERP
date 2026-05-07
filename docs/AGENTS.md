# AGENTS.md - TS_ERP 开发指南

## 项目概述

TS_ERP 是一个基于 FastAPI + Vue 3 + Agent Service 构建的 ERP 智能助手系统，采用代码化管理替代低代码节点编排。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus |
| 后端 | FastAPI + Python + SQLAlchemy |
| 智能体 | Python Agent Service + LangChain |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis 7.0 |
| 搜索引擎 | Elasticsearch 8.x |

## 项目结构

```
TS_ERP/
├── frontend/           # Vue 3 前端
│   ├── src/
│   │   ├── api/       # API 调用
│   │   ├── views/     # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── stores/    # Pinia 状态
│   │   ├── router/    # 路由配置
│   │   └── assets/    # 静态资源
│   └── package.json
│
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── auth/      # 认证模块
│   │   ├── core/      # 核心配置
│   │   ├── db/        # 数据库
│   │   ├── models/    # 数据模型
│   │   ├── schemas/   # Pydantic
│   │   └── services/  # 业务逻辑
│   └── requirements.txt
│
├── agent_service/      # 智能体服务
│   ├── app/
│   │   ├── agents/    # Agent 核心
│   │   ├── guards/    # 安全校验
│   │   ├── rag/       # RAG 检索
│   │   └── memory/    # 会话记忆
│   └── requirements.txt
│
├── worker/             # 异步任务
├── sql/                # 数据库脚本
└── docker/             # Docker 配置
```

## 启动服务

### 开发环境

```bash
# 1. 启动基础设施
docker-compose -f docker/docker-compose.yml up -d mysql redis elasticsearch

# 2. 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Agent Service
cd agent_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# 4. 前端
cd frontend
npm install
npm run dev
```

### 生产环境

```bash
docker-compose -f docker/docker-compose.yml up -d
```

## API 文档

启动后访问：
- 后端 API: http://localhost:8000/docs
- Agent Service: http://localhost:8001/docs
- Kibana: http://localhost:5601 (可选)

## 数据库

```bash
# 初始化数据库
mysql -h localhost -u root -p < sql/schema.sql
mysql -h localhost -u root -p < sql/seed.sql
```

## Agent 流程

```
用户查询
  ↓
意图识别 (IntentRecognizer)
  ↓
参数提取 (ParameterExtractor)
  ↓
权限校验 (PermissionGuard)
  ↓
路由分发
  ├─ fixed_query → SQL 模板
  ├─ dynamic_query → LLM SQL 生成
  ├─ rag_query → 知识库检索
  └─ mixed_query → SQL + RAG 混合
  ↓
SQL 安全校验 (SQLGuard)
  ↓
响应格式化 (ResponseFormatter)
  ↓
返回结果
```

## RAG 索引

Elasticsearch 索引 `knowledge_chunk_index` 包含：
- `chunk_id`: 块 ID
- `content`: 文本内容
- `content_vector`: 向量表示
- `permission_scope`: 权限范围

## 测试账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 超级管理员 |
| sales_manager | admin123 | 销售经理 |
| warehouse_manager | admin123 | 仓库管理员 |
| finance | admin123 | 财务人员 |
| staff | admin123 | 普通员工 |

## 开发规范

### 后端
- 使用 Pydantic 进行数据验证
- 使用 SQLAlchemy 进行数据库操作
- 遵循 RESTful API 设计
- 所有业务接口需要认证

### 前端
- 使用 TypeScript
- 使用 Composition API
- 遵循 Vue 3 最佳实践
- 组件使用 PascalCase

### Git
- 使用 Conventional Commits
- feature/xxx - 新功能
- fix/xxx - Bug 修复
- refactor/xxx - 重构

## 常见问题

Q: Agent Service 返回 500？
A: 检查 OpenAI API Key 配置

Q: 知识检索无结果？
A: 检查 Elasticsearch 索引是否创建

Q: 登录失败？
A: 检查数据库是否正确初始化
