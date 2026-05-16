# TS_ERP 产品架构方案

## 1. 项目背景

TS_ERP 是面向中小型贸易、分销和轻制造企业的新一代 ERP 智能助手系统。企业在日常经营中普遍存在以下问题：

- 客户、订单、库存、采购、财务等数据分散在 Excel、聊天工具和个人文件中，数据口径不统一
- 销售、采购、仓库、财务之间依赖人工同步，订单履约和回款过程难以追踪
- 库存预警、逾期应收、采购延期、低毛利报价等经营风险缺少及时提醒
- 企业制度、操作流程和业务知识沉淀在文档中，员工查询成本高、执行不一致
- 管理层缺少实时经营看板，难以及时掌握销售、库存、回款和利润情况
- 传统 ERP 实施周期长、定制成本高，难以快速适配成长型企业的实际流程

因此，TS_ERP 的建设目标不是复刻某个既有系统，而是从企业真实经营闭环出发，构建一套可持续演进的 ERP 产品：

- 用 Spring Boot 承载企业核心业务和权限体系
- 用 Vue 3 提供稳定、清晰、高效的业务操作界面
- 用 Python Agent Service 承载 RAG、智能问答和自然语言业务查询
- 用 MySQL、Redis、Elasticsearch 支撑业务数据、缓存、搜索、日志和知识检索
- 让 ERP 从“录数据的系统”升级为“业务协同 + 经营分析 + 智能辅助”的企业工作台

## 2. 建设目标

项目仓库名：

`TS_ERP`

建设目标如下：

1. 建设企业可用的 ERP 核心业务闭环：客户、供应商、商品、销售、采购、库存、财务、报表
2. 建立统一的用户、组织、角色、权限和数据权限体系
3. 使用 Spring Boot 作为长期主业务后端，降低长期维护成本
4. 使用 Python Agent Service 实现智能助手、RAG 知识库和自然语言查询
5. 引入 Redis 与 Elasticsearch 提升缓存、搜索、日志检索和知识检索能力
6. 支持本机开发、测试环境和后续容器化部署
7. 具备清晰的模块边界，支持多人协作、版本管理、测试和持续交付
8. 保证智能助手遵循当前登录用户权限，不能绕过 ERP 权限体系访问数据

## 3. 技术架构

TS_ERP 采用前后端分离 + 智能体独立服务的三项目架构：

1. `frontend/`：Vue 3 前端项目，负责页面、交互和 API 调用。
2. `java-backend/`：Spring Boot Java 应用后端，负责主业务、权限、审计和事务。
3. `agent_service/`：Python Agent / RAG 服务，负责智能问答、知识检索和自然语言查询辅助。

### 3.1 技术选型

- 前端：Vue 3 + TypeScript + Vite + Element Plus
- 主业务后端：Spring Boot 3.x + Java
- 智能体服务：Python Agent Service
- 关系型数据库：MySQL
- 缓存：Redis
- 搜索与日志检索：Elasticsearch
- RAG 检索增强：Elasticsearch BM25 + 向量检索
- Java 持久层：MyBatis-Plus 或 Spring Data JPA
- Java 数据库版本管理：Flyway 或 Liquibase，不承担旧数据迁移
- 状态管理：Pinia
- 异步任务：Spring Scheduler / XXL-JOB / Python Worker，按任务类型选择
- 容器编排：Docker Compose
- 登录认证：JWT Access Token + Refresh Token
- 权限模型：RBAC + 数据权限策略

### 3.2 总体架构图

```text
┌────────────────────────────────────────────┐
│                 Vue Frontend               │
│  ERP页面 / 智能客服 / 查询结果 / 管理后台   │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│          Spring Boot Business API          │
│ 登录鉴权 / ERP API / 权限 / 审计 / 业务事务  │
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
│          Python Agent Service              │
│ Intent / Params / RAG / SQL Guard / Answer │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│                 Worker Layer               │
│ 索引同步 / 报表预计算 / 异常扫描 / 异步任务  │
└────────────────────────────────────────────┘
```

## 4. 系统边界与职责划分

### 4.1 前端职责

前端负责：

- 客户、订单、库存、财务四大业务模块展示
- 智能客服聊天面板
- 查询结果的表格化、卡片化展示
- 会话管理与重置
- 基础权限控制与用户交互
- 登录、退出、用户信息展示
- 根据后端权限控制菜单、按钮和页面入口

前端不负责：

- 智能体逻辑判断
- SQL 生成
- 数据权限核心逻辑
- 多轮对话状态决策

### 4.2 Spring Boot 主业务服务职责

Spring Boot 主业务服务负责：

- ERP 业务接口暴露
- 用户认证、鉴权、审计
- 用户、角色、权限、数据范围管理
- 访问 MySQL、Redis、ES
- 编排对 Agent Service 的调用
- 记录聊天记录、SQL 审计日志、错误日志
- 处理核心业务事务，保证数据一致性
- 对外提供稳定 REST API

### 4.3 Agent Service 职责

智能体服务负责：

- 意图识别
- 参数提取
- 是否追问判断
- 固定查询路由
- 动态 SQL 生成
- SQL 安全校验
- 用户权限上下文校验
- 回答范围控制
- 结果整理
- 多轮上下文管理

### 4.4 Worker 职责

异步任务层负责：

- MySQL 到 Elasticsearch 的索引同步
- 定时任务与批量任务
- 智能体日志归档
- 热门查询统计
- 异常数据扫描
- 报表预聚合

## 5. 业务模块设计

### 5.1 核心业务模块

系统核心业务模块：

1. 客户管理
2. 供应商管理
3. 商品与价格管理
4. 销售管理
5. 采购管理
6. 库存管理
7. 财务管理
8. 报表与经营看板
9. 知识库与智能助手

### 5.2 智能客服模块

智能客服模块支持三类能力：

#### 固定模板查询

适合高频、稳定、可控的问题：

- 客户列表
- 客户详情
- 最近订单
- 某客户订单
- 订单详情
- 库存预警
- 商品库存
- 最近财务
- 客户财务往来

#### 动态查询

适合统计分析、排名、组合筛选问题：

- 本月订单金额最高的客户是谁
- 最近 30 天哪些客户下过 2 次以上订单
- 哪些客户有待付款订单
- 最近已发货订单有哪些
- 本月收款总金额是多少

#### RAG 知识问答

适合回答制度、流程、操作说明、FAQ、业务规则类问题：

- 客户等级规则是什么
- 订单状态分别代表什么
- 库存不足时应该怎么处理
- 财务收款确认流程是什么
- 如何录入新客户
- 发货前需要检查哪些信息

RAG 不用于直接查询实时业务数据，实时数据仍然通过固定 SQL 或动态 SQL 查询。RAG 用于补充“规则、流程、说明、帮助文档、知识库”类回答。

## 6. 用户登录与权限体系设计

### 6.1 建设目标

新系统必须将用户身份和权限作为基础能力，而不是后续补丁。智能客服在回答问题前，需要明确知道当前用户是谁、拥有哪些功能权限、能访问哪些业务数据。

权限体系需要覆盖：

- 用户登录与退出
- Token 签发与刷新
- 菜单权限
- API 权限
- 按钮与操作权限
- 数据权限
- 智能客服问答权限
- 智能体 SQL 执行权限

### 6.2 认证方案

建议采用：

- Access Token：短期有效，用于接口访问
- Refresh Token：长期有效，用于刷新登录态
- Redis：保存刷新令牌、登录状态、黑名单、会话状态
- 后端统一鉴权中间件：解析用户身份并注入请求上下文

登录流程：

```text
用户登录
  -> 校验账号密码
  -> 生成 access_token 与 refresh_token
  -> refresh_token 写入 Redis
  -> 前端保存 token
  -> 后续请求携带 Authorization Header
```

### 6.3 RBAC 权限模型

建议采用 RBAC 模型：

```text
User
  -> UserRole
  -> Role
  -> RolePermission
  -> Permission
```

基础角色建议：

- `admin`：系统管理员，可管理用户、角色、权限和全部业务数据
- `manager`：业务主管，可查看客户、订单、库存、财务汇总
- `sales`：销售人员，可查看客户与订单，按数据范围限制客户数据
- `warehouse`：仓库人员，可查看库存与出入库，不默认查看财务
- `finance`：财务人员，可查看财务、订单收款状态，不默认管理库存
- `viewer`：只读用户，仅能查看被授权模块

### 6.4 权限类型

权限建议拆成三层：

功能权限：

- `customer:view`
- `customer:create`
- `customer:update`
- `order:view`
- `inventory:view`
- `finance:view`
- `agent:chat`
- `agent:dynamic_sql`
- `agent:debug`

菜单权限：

- 客户管理
- 订单管理
- 库存管理
- 财务管理
- 智能客服
- 系统管理

数据权限：

- `all`：全部数据
- `department`：本部门数据
- `self`：本人负责数据
- `custom`：自定义客户、门店、区域、部门范围

### 6.5 数据权限策略

ERP 查询与智能客服查询都必须套用相同的数据权限策略。不能出现页面上看不到的数据，智能客服却能问出来的情况。

建议通过 `DataScopeResolver` 统一生成数据范围：

```text
当前用户
  -> 查询用户角色
  -> 查询角色数据范围
  -> 生成 DataScope
  -> 业务查询 / Agent SQL 查询统一追加权限条件
```

示例：

- 销售只能查询自己负责的客户
- 仓库只能查询库存与出入库，不可查询财务金额
- 财务可查询收付款记录，但不可默认修改库存
- 普通只读用户只能查询被授权模块

### 6.6 智能客服权限控制

智能客服需要在意图识别之后、SQL 生成或固定查询执行之前，增加权限判断。

建议流程：

```text
用户输入
  -> 读取当前用户权限上下文
  -> 意图识别
  -> 参数提取
  -> AgentPermissionGuard
  -> PolicyDecision
  -> SQL 生成或固定查询
  -> SQLGuard 追加数据权限条件
  -> DBExecutor
  -> ResponseFormatter
```

Agent 权限判断规则：

- 用户没有 `agent:chat` 时，不能使用智能客服
- 用户没有 `finance:view` 时，不能咨询财务相关问题
- 用户没有 `inventory:view` 时，不能咨询库存相关问题
- 用户没有 `agent:dynamic_sql` 时，不能使用动态 SQL 分析类问题
- 用户只能获取自己数据范围内的客户、订单、库存、财务记录
- 权限不足时，不生成 SQL，不调用数据库，直接返回权限提示

权限不足回复建议：

```text
当前账号暂无权限查看该类业务数据，请联系管理员开通相关权限。
```

### 6.7 动态 SQL 权限控制

动态 SQL 风险更高，需要比固定查询更严格。

动态 SQL 执行前必须做：

- SQL 只能是单条 SELECT
- SQL 表名必须在白名单内
- SQL 字段必须在白名单内
- 用户必须拥有对应模块权限
- 根据用户数据范围追加过滤条件
- 记录原始问题、生成 SQL、执行用户、执行结果状态

对于动态查询，建议不要让 LLM 自己处理权限条件，而是由后端 `SQLGuard` 或 `DataScopeInjector` 统一追加。

### 6.8 RAG 权限控制

RAG 知识库同样需要权限控制。不同角色可访问的制度、流程、FAQ、内部说明可能不同，不能把未授权知识片段拼入模型上下文。

RAG 权限判断规则：

- 用户没有 `agent:chat` 时，不能使用 RAG 问答
- 用户没有对应知识分类权限时，不检索该分类文档
- 检索前先根据用户角色、部门、数据范围生成知识过滤条件
- 检索结果必须经过权限过滤后才能进入 LLM 上下文
- Agent 回答需要记录引用的知识文档和片段 ID，便于审计

建议增加权限：

- `knowledge:view`
- `knowledge:manage`
- `agent:rag`

### 6.9 权限相关数据表

建议新增：

- `user_t`
- `role_t`
- `permission_t`
- `user_role_t`
- `role_permission_t`
- `department_t`
- `user_data_scope_t`
- `login_log_t`
- `operation_log_t`

### 6.10 权限与 Redis

Redis 建议缓存：

- `auth:refresh:{token_id}`
- `auth:blacklist:{token}`
- `user:permissions:{user_id}`
- `user:data_scope:{user_id}`
- `user:session:{user_id}`

权限缓存需要设置合理 TTL，并在角色或权限变更时主动失效。

## 7. 智能体流程设计

### 7.1 代码化流程

智能体流程采用代码化编排，所有权限、路由、审计和检索逻辑都应在工程代码中可测试、可追踪：

```text
用户输入
  ↓
AuthContextLoader
  ↓
IntentRouter
  ↓
ParameterExtractor
  ↓
AgentPermissionGuard
  ↓
PolicyDecision
  ├─ unsupported
  ├─ need_clarification
  ├─ permission_denied
  ├─ fixed_query
  ├─ rag_query
  └─ dynamic_query
         ↓
  FixedSQLFactory / SQLGenerator / RAGRetriever
         ↓
      SQLGuard / DataScopeInjector / KnowledgePermissionFilter
         ↓
      DBExecutor / KnowledgeContextBuilder
         ↓
  ResponseFormatter
         ↓
       返回前端
```

### 7.3 智能体模块建议

建议拆分为以下 Python 模块：

- `intent_router.py`
- `parameter_extractor.py`
- `policy_decision.py`
- `agent_permission_guard.py`
- `data_scope_resolver.py`
- `fixed_sql_factory.py`
- `sql_generator.py`
- `sql_guard.py`
- `db_executor.py`
- `rag_retriever.py`
- `knowledge_permission_filter.py`
- `knowledge_context_builder.py`
- `response_formatter.py`
- `conversation_manager.py`
- `prompt_manager.py`

## 8. 数据存储设计

### 8.1 MySQL

MySQL 负责保存 ERP 主业务真数据与系统审计数据。

建议保留业务表：

- `customer_t`
- `order_t`
- `order_item_t`
- `inventory_t`
- `stock_record_t`
- `finance_t`

建议新增系统表：

- `user_t`
- `role_t`
- `permission_t`
- `user_role_t`
- `role_permission_t`
- `department_t`
- `user_data_scope_t`
- `login_log_t`
- `operation_log_t`
- `knowledge_base_t`
- `knowledge_document_t`
- `knowledge_chunk_t`
- `knowledge_permission_t`
- `chat_session_t`
- `chat_message_t`
- `agent_sql_log_t`
- `agent_trace_t`
- `query_cache_log_t`

### 8.2 Redis

Redis 负责缓存、上下文和限流。

建议用途：

- 聊天会话上下文缓存
- 高频查询缓存
- SQL 结果短期缓存
- 用户追问状态缓存
- 用户权限缓存
- 用户数据范围缓存
- 限流计数
- 异步任务状态

建议 Key 设计：

- `chat:session:{session_id}`
- `chat:history:{session_id}`
- `agent:context:{session_id}`
- `user:permissions:{user_id}`
- `user:data_scope:{user_id}`
- `query:cache:{hash}`
- `sql:cache:{hash}`
- `rate:user:{user_id}`
- `task:status:{task_id}`

### 8.3 Elasticsearch

ES 负责全文检索、模糊搜索、日志分析和 RAG 知识检索。

建议建立索引：

- `customer_index`
- `order_index`
- `inventory_index`
- `finance_index`
- `chat_message_index`
- `agent_trace_index`
- `operation_log_index`
- `knowledge_chunk_index`

ES 典型用途：

- 客户模糊搜索
- 订单全文搜索
- 商品快速搜索
- 财务记录筛选
- 聊天记录检索
- 智能体日志排障
- 登录与操作日志检索
- 知识库文档检索
- RAG 检索增强上下文召回

### 8.4 RAG 知识库设计

RAG 知识库用于保存和检索非实时业务数据类知识，例如制度、流程、FAQ、操作手册、业务规则。

建议知识来源：

- ERP 操作手册
- 客户管理规范
- 订单处理流程
- 库存管理规则
- 财务收付款流程
- 常见问题 FAQ
- 内部培训文档

知识处理流程：

```text
文档上传
  -> 文档解析
  -> 文本清洗
  -> 切分 Chunk
  -> 生成向量
  -> 写入 MySQL 元数据
  -> 写入 Elasticsearch 索引
```

检索流程：

```text
用户问题
  -> 判断为 rag_query
  -> 生成查询向量
  -> ES BM25 + 向量混合检索
  -> 权限过滤
  -> TopK Chunk 召回
  -> 构建上下文
  -> LLM 生成答案
  -> 返回答案与引用来源
```

RAG 与 SQL 的边界：

- 查实时业务数据走固定 SQL 或动态 SQL
- 查制度、流程、说明、FAQ 走 RAG
- 同一个问题既需要实时数据又需要规则说明时，可采用 SQL + RAG 混合回答

## 9. API 设计建议

### 9.1 认证与权限 API

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET /api/auth/menus`
- `GET /api/auth/permissions`

### 9.2 ERP 业务 API

- `GET /api/customers`
- `GET /api/customers/{id}`
- `GET /api/orders`
- `GET /api/orders/{id}`
- `GET /api/inventory`
- `GET /api/finance`

### 9.3 系统管理 API

- `GET /api/users`
- `POST /api/users`
- `PATCH /api/users/{id}`
- `GET /api/roles`
- `POST /api/roles`
- `PATCH /api/roles/{id}`
- `GET /api/permissions`

### 9.4 智能体 API

- `POST /api/agent/chat`
- `POST /api/agent/reset-session`
- `GET /api/agent/session/{session_id}`
- `POST /api/agent/debug/intent`
- `POST /api/agent/debug/sql`
- `POST /api/agent/debug/rag`

### 9.5 知识库 API

- `GET /api/knowledge/bases`
- `POST /api/knowledge/bases`
- `GET /api/knowledge/documents`
- `POST /api/knowledge/documents`
- `DELETE /api/knowledge/documents/{id}`
- `POST /api/knowledge/documents/{id}/reindex`
- `POST /api/knowledge/search`

### 9.6 内部服务接口

主服务与 Agent Service 之间建议采用内部 HTTP 或 gRPC 接口：

- `/internal/intent/recognize`
- `/internal/agent/permission-check`
- `/internal/sql/generate`
- `/internal/sql/guard`
- `/internal/rag/retrieve`
- `/internal/rag/context-build`
- `/internal/response/format`

## 10. TS_ERP 三项目目录建议

```text
TS_ERP/
├─ frontend/                 # Vue 3 前端项目
│  ├─ src/
│  │  ├─ api/
│  │  ├─ views/
│  │  ├─ components/
│  │  ├─ stores/
│  │  ├─ router/
│  │  └─ utils/
│  └─ package.json
├─ java-backend/             # Spring Boot Java 应用后端
│  ├─ src/main/java/com/ts/erp/
│  │  ├─ common/
│  │  ├─ config/
│  │  ├─ security/
│  │  ├─ system/
│  │  ├─ customer/
│  │  ├─ supplier/
│  │  ├─ product/
│  │  ├─ sales/
│  │  ├─ purchase/
│  │  ├─ inventory/
│  │  ├─ finance/
│  │  ├─ knowledge/
│  │  ├─ agent/
│  │  └─ audit/
│  ├─ src/main/resources/
│  │  ├─ application.yml
│  │  ├─ application-local.yml
│  │  └─ db/migration/
│  └─ pom.xml
├─ agent_service/            # Python Agent / RAG 服务
│  ├─ app/
│  │  ├─ agents/
│  │  ├─ prompts/
│  │  ├─ guards/
│  │  ├─ formatters/
│  │  ├─ memory/
│  │  ├─ permissions/
│  │  ├─ rag/
│  │  └─ main.py
│  └─ requirements.txt
├─ worker/
│  ├─ jobs/
│  ├─ sync/
│  └─ main.py
├─ sql/
│  ├─ schema.sql
│  ├─ seed.sql
│  └─ migration/
├─ docs/
├─ scripts/
├─ docker/
├─ .env.example
└─ README.md
```

## 11. 非功能性要求

### 11.1 安全要求

- 所有业务接口默认需要登录
- API 层必须做功能权限校验
- 业务查询和智能客服查询必须做数据权限校验
- 动态 SQL 仅允许单条 SELECT
- SQL 必须通过白名单与关键字校验
- RAG 检索结果必须经过知识权限过滤
- RAG 回答需要保留引用来源，避免无依据回答
- 记录智能体生成 SQL 的审计日志
- 对高风险调试能力做权限隔离

### 11.2 性能要求

- 高频查询走 Redis 缓存
- 用户权限和数据范围走 Redis 缓存
- 搜索类问题优先走 ES
- RAG 知识检索走 ES 混合检索
- 复杂统计类查询可异步化或预计算
- 聊天历史只保留必要上下文

### 11.3 可维护性要求

- 智能体逻辑全部代码化
- 提示词外置管理
- 模块边界清晰
- 核心流程具备单元测试与集成测试
- 权限策略集中维护，不分散在页面或提示词中

### 11.4 可观测性要求

- 接口日志
- 登录日志
- 权限拒绝日志
- SQL 审计日志
- Agent Trace 日志
- RAG 检索日志
- 错误告警
- ES 中保留可检索运行日志

## 12. 分阶段实施计划

### 第一阶段：项目底座建设

目标：

- 初始化 Spring Boot、Vue 3、Python Agent Service 目录
- 建立 MySQL、Redis、ES、Docker Compose
- 跑通基础开发环境

交付：

- 前端可启动
- Spring Boot 主业务服务可启动
- Python Agent Service 可启动
- MySQL 可连接
- Redis 可连接
- ES 可连接

### 第二阶段：登录与权限体系建设

目标：

- 实现用户登录、退出、Token 刷新
- 实现用户、角色、权限、菜单、数据范围基础模型
- 实现 API 鉴权中间件
- 实现前端菜单与页面权限控制

交付：

- 登录页可用
- `GET /api/auth/me` 可用
- RBAC 权限模型可用
- 用户权限与数据范围可缓存到 Redis

### 第三阶段：ERP 基础功能建设

目标：

- 实现客户、供应商、商品、销售、采购、库存、财务基础查询和展示
- 建立企业真实业务闭环的数据结构
- 所有业务查询接入数据权限过滤

交付：

- ERP 列表页和详情页
- 基础 CRUD API
- 数据初始化脚本

### 第四阶段：固定查询智能体建设

目标：

- 代码化实现第一版智能助手流程
- 支持意图识别、追问、固定 SQL 查询、结果整理
- 智能客服接入当前用户权限上下文
- 权限不足的问题不进入 SQL 查询

交付：

- 固定查询可用
- 智能客服闭环可用
- SQL 审计日志可追踪
- Agent 权限拒绝日志可追踪

### 第五阶段：动态查询能力建设

目标：

- 增加 dynamic_query 路由
- 实现 SQL 生成与 SQL Guard
- 支持复杂统计分析问题
- 动态 SQL 接入功能权限与数据权限

交付：

- 动态 SQL 可控执行
- 典型统计问题可回答
- 风险查询可被拦截

### 第六阶段：Redis 与 ES 深化接入

目标：

- 增强会话记忆
- 增强高频查询缓存
- 建立客户/订单/库存/财务索引
- 建立智能体日志检索能力

交付：

- 会话缓存
- 检索增强
- 日志可搜索

### 第七阶段：RAG 知识库能力建设

目标：

- 建立知识库、文档、Chunk、权限模型
- 支持文档上传、解析、切分、索引
- 支持 RAG 检索增强问答
- 智能客服可回答制度、流程、FAQ、操作说明类问题

交付：

- 知识库管理 API
- 文档索引任务
- RAG 检索链路
- 带引用来源的知识问答
- 知识权限过滤可用

### 第八阶段：运营与智能化增强

目标：

- 增加异常提醒
- 增加经营分析
- 增加多轮对话上下文能力

交付：

- 异常看板
- 简单经营分析
- 多轮会话能力

## 13. TS_ERP 系统定位

TS_ERP 是正式开发主线，定位为企业级 ERP 智能助手系统：

- Spring Boot 承载主业务、权限、审计和事务一致性
- Vue 3 承载前端业务操作和管理看板
- Python Agent Service 承载智能助手、RAG 和自然语言查询
- MySQL 保存企业主业务数据
- Redis 提供缓存、会话、限流和权限缓存
- Elasticsearch 提供业务搜索、日志检索和知识库检索

## 14. 结论

TS_ERP 采用“**企业 ERP 主业务系统 + 智能助手能力**”的产品架构，形成如下能力闭环：

- Vue 负责前端产品体验
- Spring Boot 负责业务服务编排、权限、审计和事务
- 登录、RBAC 与数据权限负责系统安全边界
- Python Agent Service 负责智能体能力代码化
- MySQL 保存主业务真数据
- Redis 提供上下文和缓存能力
- Elasticsearch 提供搜索和日志检索能力
- RAG 提供制度、流程、FAQ、操作手册类知识问答能力

RAG、LangChain、LangGraph 与后续 SFT 微调的详细落地路线，见：

- `docs/TS_ERP_RAG_LangChain_SFT_Plan.md`

该方案能够支撑 TS_ERP 从企业核心业务管理逐步扩展到智能问答、经营分析、流程协同和行业化能力，为后续代码化、权限化、测试化、审计化和团队协作打下长期可维护的技术基础。
