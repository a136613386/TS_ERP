# TS_ERP 智能助手二期技术方案

## 1. 文档目标

本文档用于规划 TS_ERP 智能助手二期建设方案。

一期已经完成了前端、Java 后端、Python Agent、MySQL、Redis、Elasticsearch 的基础联动，实现了：

- 前端智能助手入口
- Java 后端代理调用 Python Agent
- 固定 SQL 模板查询
- 基础 RAG 知识库上传、切块、索引、检索
- BM25 知识库问答
- 基础意图识别与路由

二期目标是在一期基础上，将智能助手从“规则驱动的问答雏形”升级为“可落地企业工程应用的智能 Agent”。

重点能力包括：

- 语义意图识别
- 低置信度追问
- 动态 SQL 安全生成
- RAG 向量召回
- Mixed Query 组合回答
- 多轮上下文追问

## 2. 一期现状与不足

### 2.1 一期优势

一期已经打通了完整技术链路：

```text
Vue 前端
  -> Java Spring Boot 后端
  -> Python Agent
  -> MySQL / Elasticsearch / Redis
```

当前已经可以回答：

- “查询最近的 3 个客户”
- “哪些商品库存不足”
- “ERP 是什么”
- “库存不足应该怎么办”

同时已经具备最基本的安全边界：

- 前端不直接访问 Python Agent
- Java 后端统一代理
- Python Agent 只作为智能能力服务
- SQL 查询经过基础 SQLGuard 校验
- RAG 回答基于知识库来源

### 2.2 一期主要不足

一期仍然偏规则和模板驱动，存在以下问题：

| 问题 | 表现 | 影响 |
|---|---|---|
| 意图识别依赖关键词 | “库存不足怎么办”和“哪些商品库存不足”需要靠规则区分 | 用户表达稍有变化就可能路由错误 |
| 固定模板覆盖有限 | 只能处理少量高频问题 | 企业真实问题不可穷举 |
| 动态 SQL 能力弱 | 不能稳定生成复杂统计 SQL | 难以支持经营分析 |
| RAG 仅 BM25 | 主要依赖关键词匹配 | 同义表达、口语表达召回弱 |
| Mixed Query 不完整 | 数据查询和制度解释还未完整组合 | 无法完成复杂业务问答 |
| 多轮上下文弱 | 追问“具体是哪一个？”不能稳定理解上一轮 | 对话体验不连续 |
| 可观测性不足 | 缺少完整链路日志、评分、审计 | 企业环境难排查、难上线 |

## 3. 二期建设目标

二期建设目标不是简单增加更多关键词规则，而是建立企业级 Agent 能力架构。

目标能力如下：

```text
用户自然语言问题
  -> 输入归一化
  -> 语义意图识别
  -> 低置信度追问
  -> 多轮上下文改写
  -> 工具规划
  -> SQL / RAG / Mixed 执行
  -> 安全校验
  -> 结构化结果
  -> 面向用户的最终回答
```

二期应满足以下工程要求：

- 可控：不能让大模型直接无约束访问数据库
- 可审计：每次意图、SQL、RAG 来源、工具调用都可记录
- 可解释：对用户展示来源和结果，不展示模型思维过程
- 可扩展：后续可以增加更多 ERP 模块和外部工具
- 可回退：LLM 不可用时，核心查询仍有基础能力
- 可测试：关键意图、SQL、安全规则、RAG 召回应有测试用例

## 4. 二期整体架构

### 4.1 推荐架构

```text
Vue Frontend
  |
  | /api/agent/chat
  v
Java Backend
  |
  | /agent/query
  v
Python Agent Service
  |
  +-- InputNormalizer
  |
  +-- SemanticIntentRecognizer
  |
  +-- FollowUpResolver
  |
  +-- ClarificationAgent
  |
  +-- Planner
  |
  +-- Tool Executor
      |
      +-- SQL Tool
      |   +-- Schema Registry
      |   +-- SQL Generator
      |   +-- SQLGuard
      |   +-- Permission Injector
      |   +-- MySQL / Java API
      |
      +-- RAG Tool
      |   +-- Query Rewrite
      |   +-- BM25 Retriever
      |   +-- Vector Retriever
      |   +-- Python RRF
      |   +-- Optional Rerank
      |   +-- Elasticsearch
      |
      +-- Mixed Tool
          +-- SQL Result
          +-- RAG Result
          +-- Answer Composer
```

### 4.2 与一期相比的核心提升

| 能力 | 一期 | 二期 |
|---|---|---|
| 意图识别 | 关键词 + 少量规则 | LLM 结构化语义识别 + 规则兜底 |
| SQL 查询 | 固定模板为主 | 固定模板 + 安全动态 SQL |
| RAG 检索 | BM25 | BM25 + 向量召回 + Python RRF |
| 混合问题 | 初步识别 | SQL + RAG 编排组合回答 |
| 多轮对话 | 保存上下文但弱使用 | 追问识别 + 问题改写 + 结果复用 |
| 安全 | 基础 SQLGuard | SQL AST 校验、表字段白名单、权限注入 |
| 工程化 | 可联调 | 可审计、可测试、可灰度、可扩展 |

## 5. 语义意图识别方案

### 5.1 技术选型

推荐使用：

- LLM：DeepSeek / Qwen / OpenAI-compatible API
- 结构化输出：Pydantic
- 编排：当前阶段自研轻量流程，不强制引入 LangGraph
- 兜底：保留少量高置信规则

### 5.2 结构化意图模型

建议将意图识别结果从简单字符串升级为结构化对象：

```json
{
  "intent": "sql_query",
  "domain": "inventory",
  "query_type": "list",
  "needs_business_data": true,
  "needs_knowledge": false,
  "confidence": 0.92,
  "missing_slots": [],
  "rewrite_query": "查询当前库存不足商品列表"
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| intent | sql_query / rag_query / mixed_query / clarification |
| domain | customer / order / inventory / finance / purchase / knowledge |
| query_type | list / count / detail / process / policy / analysis |
| needs_business_data | 是否需要业务数据库 |
| needs_knowledge | 是否需要知识库 |
| confidence | 意图置信度 |
| missing_slots | 缺失的必要参数 |
| rewrite_query | 语义改写后的完整问题 |

### 5.3 示例

#### 示例 1：业务数据查询

用户：

```text
哪些商品库存不足？
```

输出：

```json
{
  "intent": "sql_query",
  "domain": "inventory",
  "query_type": "list",
  "needs_business_data": true,
  "needs_knowledge": false,
  "confidence": 0.95,
  "rewrite_query": "查询当前库存不足商品列表"
}
```

#### 示例 2：知识库问答

用户：

```text
库存不足应该怎么办？
```

输出：

```json
{
  "intent": "rag_query",
  "domain": "inventory",
  "query_type": "process",
  "needs_business_data": false,
  "needs_knowledge": true,
  "confidence": 0.94,
  "rewrite_query": "查询库存不足处理流程和制度"
}
```

#### 示例 3：混合查询

用户：

```text
哪些商品库存不足，按制度应该怎么处理？
```

输出：

```json
{
  "intent": "mixed_query",
  "domain": "inventory",
  "query_type": "list_and_process",
  "needs_business_data": true,
  "needs_knowledge": true,
  "confidence": 0.96,
  "rewrite_query": "查询当前库存不足商品，并检索库存不足处理制度"
}
```

## 6. 低置信度追问方案

### 6.1 触发条件

当满足以下条件时，不直接执行工具，而是先追问：

- 意图识别置信度低于阈值
- 缺少关键参数
- 候选意图冲突
- 执行 SQL 或 RAG 的风险较高

建议阈值：

```text
confidence >= 0.80：直接执行
0.60 <= confidence < 0.80：低风险可执行，高风险追问
confidence < 0.60：必须追问
```

### 6.2 追问示例

用户：

```text
查一下客户
```

系统：

```text
你想查询客户列表，还是查询某个客户的详情？
```

用户：

```text
最近订单
```

系统：

```text
你想查询最近订单列表，还是统计最近订单数量？
```

### 6.3 工程落地

新增模块：

```text
agent_service/app/agents/clarification.py
```

职责：

- 根据缺失参数生成追问
- 保存等待用户补充的上下文状态
- 用户补充后继续执行原计划

## 7. 动态 SQL 安全生成方案

### 7.1 技术选型

推荐使用：

- LLM 生成 SQL
- Pydantic 结构化输出
- SQLGlot 解析 SQL AST
- 表白名单与字段白名单
- SQLGuard 安全校验
- 权限条件注入
- LIMIT 强制注入
- EXPLAIN 预检查

### 7.2 动态 SQL 执行流程

```text
语义意图
  -> 读取 Schema Registry
  -> LLM 生成 SQL JSON
  -> SQLGlot 解析
  -> 只读校验
  -> 表白名单校验
  -> 字段白名单校验
  -> 权限条件注入
  -> LIMIT 注入
  -> EXPLAIN
  -> 执行 SQL
  -> 格式化结果
```

### 7.3 Schema Registry

不允许模型猜表结构。Agent 应维护一份业务 schema 描述。

建议新增：

```text
agent_service/app/sql/schema_registry.py
```

示例：

```python
SCHEMA_REGISTRY = {
    "erp_customer": {
        "description": "客户主数据",
        "fields": {
            "customer_code": "客户编码",
            "customer_name": "客户名称",
            "status": "客户状态",
            "credit_limit": "信用额度",
            "created_at": "创建时间"
        },
        "allowed": True
    },
    "inventory_ledger": {
        "description": "库存台账",
        "fields": {
            "sku": "商品编码",
            "product_name": "商品名称",
            "warehouse_name": "仓库名称",
            "available_qty": "可用库存",
            "status": "库存状态"
        },
        "allowed": True
    }
}
```

### 7.4 SQL 安全边界

必须禁止：

- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- CREATE
- TRUNCATE
- UNION 注入
- 多语句执行
- information_schema 越权探查

必须强制：

- SELECT only
- LIMIT 最大行数
- 表白名单
- 字段白名单
- 数据权限条件
- SQL 审计日志

### 7.5 与固定模板的关系

二期不是完全废弃固定模板。

建议策略：

```text
高频、稳定、强业务定义的问题：固定模板优先
统计、排行、组合筛选、临时分析：动态 SQL
固定模板未覆盖：动态 SQL 兜底
```

这样既保证稳定，又提升覆盖面。

## 8. RAG 向量召回方案

### 8.1 一期现状

一期已改为：

```text
Elasticsearch BM25 multi_match
```

优点：

- 快
- 稳
- 不依赖 embedding
- 适合关键词明确的问题

不足：

- 同义表达召回弱
- 口语表达召回弱
- 短问题召回不稳定
- 不能很好理解语义相似

### 8.2 二期目标

二期 RAG 检索升级为：

```text
Query Rewrite
  -> BM25 召回
  -> Vector 召回
  -> Python RRF 融合
  -> 可选 Rerank
  -> Top K chunks
```

### 8.3 技术选型

推荐：

- Elasticsearch dense_vector
- Embedding：bge-small-zh-v1.5 / BGE-M3
- 融合：Python 侧 RRF
- 可选重排：bge-reranker-base / bge-reranker-v2-m3

### 8.4 为什么不用 ES 原生 RRF

当前本地 ES 是 Basic license，不支持：

```json
"rank": {
  "rrf": {}
}
```

因此二期继续采用 Python 侧 RRF，避免许可证依赖。

### 8.5 BM25 + 向量召回优势

| 能力 | BM25 | 向量召回 |
|---|---|---|
| 精确关键词 | 强 | 中 |
| 业务术语 | 强 | 中 |
| 同义表达 | 弱 | 强 |
| 口语问题 | 弱 | 强 |
| 速度 | 快 | 中 |
| 可解释性 | 强 | 中 |

组合后可以覆盖：

```text
库存不足怎么办
缺货了咋处理
仓库不够货怎么走流程
低库存要不要补货
```

这些问题都应该召回“库存不足处理规范”。

## 9. Mixed Query 组合回答方案

### 9.1 典型场景

用户：

```text
哪些商品库存不足，按制度应该怎么处理？
```

这不是单纯 SQL，也不是单纯 RAG。

它需要：

```text
SQL：查当前库存不足商品
RAG：查库存不足处理规范
Composer：组合成最终回答
```

### 9.2 执行流程

```text
Mixed Intent
  -> 生成业务数据子任务
  -> 生成知识库子任务
  -> SQL Tool 执行业务查询
  -> RAG Tool 执行制度检索
  -> Answer Composer 组合回答
```

### 9.3 回答格式

推荐格式：

```text
当前有 2 个库存不足商品：
1. 商用笔记本电脑，北京备货仓，可用库存 12
2. 工业传感器 S2，上海周转仓，可用库存 42

按制度建议：
1. 仓库先确认安全库存阈值
2. 通知采购部门补货
3. 若涉及客户订单，同步销售预计到货时间

来源：
- 库存不足处理规范
```

### 9.4 工程模块

建议新增：

```text
agent_service/app/agents/planner.py
agent_service/app/agents/answer_composer.py
agent_service/app/tools/sql_tool.py
agent_service/app/tools/rag_tool.py
```

## 10. 多轮上下文方案

### 10.1 一期问题

当前系统有 `session_id`，但上下文使用较弱。

例如：

用户：

```text
在订单中，状态为合作中的客户有几个？
```

系统：

```text
1 个
```

用户追问：

```text
具体是哪一个？
```

系统需要理解：

```text
“哪一个” 指的是上一轮“状态为合作中的客户”
```

### 10.2 二期方案

新增：

```text
FollowUpResolver
ConversationState
LastResultCache
```

保存内容：

```json
{
  "last_query": "在订单中，状态为合作中的客户有几个？",
  "last_intent": "sql_query",
  "last_sql": "SELECT COUNT(...)",
  "last_data": {
    "rows": [...]
  },
  "slots": {
    "domain": "customer",
    "status": "合作中",
    "scope": "order"
  }
}
```

### 10.3 追问识别

以下问题应识别为追问：

```text
具体是哪一个？
明细呢？
展开看看
为什么？
怎么处理？
那按制度呢？
还有哪些？
```

### 10.4 追问改写

示例：

```text
当前问题：具体是哪一个？
上一轮问题：在订单中，状态为合作中的客户有几个？

改写为：
查询订单中状态为合作中的客户明细
```

改写后再进入正常 Agent 流程。

## 11. 企业工程落地要求

### 11.1 安全要求

必须具备：

- SQL 只读
- 表字段白名单
- 数据权限注入
- 用户权限透传
- 敏感字段脱敏
- 工具调用审计
- 禁止展示模型内部思维过程

### 11.2 审计日志

每次 Agent 请求记录：

```json
{
  "session_id": "web-xxx",
  "user_id": 1,
  "query": "库存不足怎么办？",
  "intent": "rag_query",
  "confidence": 0.94,
  "route": "rag",
  "tools": ["rag_search"],
  "sql": null,
  "rag_chunks": ["DOC-IK-CHECK-001_1"],
  "latency_ms": 620,
  "status": "success"
}
```

### 11.3 可观测性

需要在 Agent 日志中输出：

- intent result
- route result
- SQL 生成结果
- SQLGuard 校验结果
- RAG query rewrite
- BM25 hits
- vector hits
- rerank score
- final answer source

### 11.4 测试要求

至少建立以下测试集：

#### 意图识别测试

```text
哪些商品库存不足？ -> sql_query
库存不足怎么办？ -> rag_query
哪些商品库存不足，按制度怎么处理？ -> mixed_query
具体是哪一个？ -> follow_up
```

#### SQL 安全测试

```text
删除客户数据 -> reject
更新库存数量 -> reject
查询客户列表 -> allow
统计本月订单金额 -> allow
```

#### RAG 召回测试

```text
库存不足怎么办 -> 库存不足处理规范
缺货了咋处理 -> 库存不足处理规范
采购入库流程 -> ERP用户手册
```

#### 多轮追问测试

```text
Q1: 状态为合作中的客户有几个？
A1: 1 个
Q2: 具体是哪一个？
A2: 返回客户明细
```

## 12. 文档上传与知识入库优化

RAG 的效果很大程度取决于文档入库质量。一期已经实现了基础上传、文本提取、切块和索引；二期需要将其升级为企业知识入库流水线。

### 12.1 一期现状

一期文档上传链路主要是：

```text
前端上传文档
  -> Java 保存文件和文档记录
  -> Java 调用 Python Agent /rag/index-document
  -> Agent 切块
  -> Agent 写入 Elasticsearch
  -> Java 更新 chunk_count 和索引状态
```

该链路已经能完成最基本的知识库入库，但仍存在不足：

- 文档格式支持有限
- 对 Word、PDF、Excel 等企业常见文档解析不足
- 切块策略偏基础，容易割裂语义
- 缺少分块预览和质量检查
- 缺少审核发布流程
- 缺少文档版本管理
- 删除、更新、重建索引能力不足
- 上传处理同步阻塞，耗时任务体验较差

### 12.2 二期目标

二期文档上传要从“能上传”升级为“可治理、可审核、可追踪、可重建”的知识入库能力。

目标链路：

```text
上传
  -> 保存原文件
  -> 文档解析
  -> 结构化抽取
  -> 语义切块
  -> 分块预览
  -> 质量检查
  -> 审核发布
  -> embedding 向量化
  -> 写入 ES
  -> 状态回写
  -> 可检索问答
```

### 12.3 文档格式支持

二期建议按优先级支持以下格式：

| 优先级 | 格式 | 说明 |
|---|---|---|
| P0 | txt / md | 纯文本和 Markdown，解析成本低 |
| P0 | docx | 企业制度、流程文档常见格式 |
| P0 | pdf | 操作手册、制度文件常见格式 |
| P1 | xlsx / csv | 规则表、审批矩阵、阈值表 |
| P1 | html | 导出的网页知识、帮助中心 |
| P2 | 图片 / 扫描 PDF | 需要 OCR 支持 |

推荐解析技术：

| 格式 | 推荐技术 |
|---|---|
| docx | python-docx / unstructured |
| pdf | PyMuPDF / pdfplumber |
| xlsx | openpyxl |
| csv | Python csv / pandas |
| html | BeautifulSoup |
| OCR | PaddleOCR / Tesseract |

### 12.4 结构化解析

文档解析不应只得到一整段纯文本，而应尽量保留文档结构：

- 标题
- 章节
- 段落
- 编号
- 表格
- 页码
- 层级
- 图片说明
- 来源位置

推荐解析结果结构：

```json
{
  "document_id": "DOC-xxx",
  "title": "库存不足处理规范",
  "sections": [
    {
      "heading": "处理流程",
      "level": 1,
      "page": 3,
      "content": "库存不足时，仓库需要先确认安全库存阈值..."
    }
  ],
  "tables": [
    {
      "title": "库存预警阈值表",
      "page": 5,
      "headers": ["商品类型", "安全库存", "补货周期"],
      "rows": []
    }
  ]
}
```

### 12.5 语义切块

二期应从固定长度切块升级为语义切块。

切块优先级：

```text
标题/章节
  -> 制度条款
  -> FAQ 问答对
  -> 流程步骤
  -> 表格块
  -> 段落
  -> token 长度兜底
```

切块原则：

- 一个 chunk 尽量表达一个完整业务含义
- 不切断流程步骤
- 不切断制度条款
- 不切断 FAQ 问答对
- 表格要保留标题、列名、行语义
- chunk 应保留章节路径

推荐 chunk 结构：

```json
{
  "chunk_id": "DOC-xxx_001",
  "document_id": "DOC-xxx",
  "title": "库存不足处理规范",
  "section_path": ["库存管理", "库存不足", "处理流程"],
  "content": "库存不足时，仓库需要先确认安全库存阈值，再通知采购部门补货。",
  "page": 3,
  "chunk_index": 1,
  "token_count": 86,
  "module": "库存管理",
  "permission_scope": "public"
}
```

### 12.6 表格处理

ERP 文档中表格价值很高，不能简单拍平成混乱文本。

典型表格：

- 审批矩阵
- 客户等级规则
- 信用额度规则
- 库存预警阈值
- 采购权限表
- 财务付款条件

表格应转换为可检索语义文本：

```text
客户信用等级规则：
等级 A，信用额度 500000，审批人 销售经理。
等级 B，信用额度 200000，审批人 部门主管。
```

同时保留结构化 metadata：

```json
{
  "type": "table",
  "table_title": "客户信用等级规则",
  "headers": ["等级", "信用额度", "审批人"],
  "row_index": 1
}
```

### 12.7 元数据设计

文档入库时必须补充完整 metadata：

```text
document_id
title
module
knowledge_type
permission_scope
department_id
version
effective_date
expire_date
status
tags
source_file
file_hash
content_hash
created_by
reviewed_by
published_at
```

示例：

```json
{
  "module": "库存管理",
  "knowledge_type": "制度",
  "permission_scope": "dept_inventory",
  "version": "v1.0",
  "effective_date": "2026-05-01",
  "status": "published",
  "tags": ["库存不足", "补货", "安全库存"]
}
```

### 12.8 审核发布流程

企业知识库不建议上传即生效。

推荐状态流转：

```text
uploaded
  -> parsing
  -> parsed
  -> chunking
  -> pending_review
  -> published
  -> indexing
  -> indexed
```

异常状态：

```text
parse_failed
chunk_failed
index_failed
rejected
archived
```

检索边界：

```text
只有 published/indexed 状态的文档允许进入智能助手检索。
```

### 12.9 去重与版本管理

二期需要支持：

- 文件 hash 去重
- 内容 hash 去重
- 文档版本号
- 历史版本归档
- 新版本发布后重建索引
- 检索时默认只查最新已发布版本

示例：

```text
库存不足处理规范 v1.0 archived
库存不足处理规范 v1.1 published
```

### 12.10 索引重建与删除同步

必须支持：

- 单文档重建索引
- 按知识库重建索引
- 全量重建索引
- 删除文档时同步删除 ES chunk
- 更新文档时删除旧 chunk，再写入新 chunk
- 索引失败后可重试

建议新增接口：

```text
POST /rag/reindex-document
POST /rag/reindex-base
DELETE /rag/index-document/{document_id}
```

### 12.11 异步任务化

文档解析、切块、embedding、索引都可能耗时，不应阻塞前端请求。

推荐链路：

```text
Java 接收上传
  -> 保存文件
  -> MySQL 创建 document 记录
  -> 投递索引任务
  -> 立即返回 document_id
  -> 前端轮询状态
```

任务状态：

```text
uploaded
parsing
chunking
embedding
indexing
indexed
failed
```

执行方式：

- 一期增强可使用 Java 异步线程池
- 二期正式建议使用 Redis Queue / Celery / APScheduler / 独立 worker

### 12.12 文档质量检查

上传后应自动检查：

- 文件是否为空
- 是否乱码
- 是否重复
- 是否缺少标题
- 是否缺少模块
- 是否缺少权限
- chunk 是否过大
- chunk 是否过小
- embedding 是否成功
- ES 写入是否成功

前端展示：

```text
解析状态
分块数量
索引状态
失败原因
可预览 chunk
重试按钮
```

### 12.13 向量化入库

二期建议使用本机已有：

```text
bge-small-zh-v1.5
```

向量维度：

```text
512
```

入库结构：

```text
title/content：用于 BM25
content_vector：用于向量召回
metadata：用于权限、模块、版本、状态过滤
```

最终支持：

```text
BM25 召回
+ 向量召回
+ Python RRF 融合
```

### 12.14 前端知识库体验优化

知识库页面建议增加：

- 上传进度
- 解析状态
- 审核状态
- 索引状态
- 失败原因
- chunk 预览
- 权限选择
- 模块选择
- 标签编辑
- 版本记录
- 重新索引按钮
- 删除文档按钮

文档列表建议展示：

```text
文档标题
业务模块
知识类型
版本
权限范围
分块数
索引状态
审核状态
更新时间
```

### 12.15 二期推荐入库链路

推荐最终链路：

```text
前端上传文件
  -> Java 保存原文件
  -> MySQL 创建 document 记录
  -> Java 调用 Agent /rag/parse-document
  -> Agent 解析文档
  -> Agent 返回结构化段落
  -> Java 保存解析结果
  -> 用户预览/提交审核
  -> 审核通过
  -> Java 调 Agent /rag/index-document
  -> Agent 语义切块
  -> Agent 生成 embedding
  -> Agent 写入 ES
  -> Java 更新索引状态
```

### 12.16 P0 落地范围

二期 P0 建议优先完成：

- 支持 docx / pdf 解析
- 语义切块替代固定长度切块
- 上传后 chunk 预览
- 文档状态流转：待审核 / 已发布 / 索引失败
- bge-small-zh-v1.5 向量化
- 删除/重建索引
- 文件 hash 去重

这些能力完成后，知识库质量、可维护性和企业落地程度会明显优于一期。

## 13. 推荐实施计划

### 阶段 1：语义路由与追问

目标：

- 新增 SemanticIntentRecognizer
- 新增结构化 intent schema
- 新增低置信度追问
- 新增 FollowUpResolver 初版

收益：

- 不再依赖大量关键词
- 用户表达变化更稳定
- 开始支持真正追问

### 阶段 2：动态 SQL 工程化

目标：

- 建立 Schema Registry
- 引入 SQLGlot
- 实现 SQLGenerator
- 实现 PermissionInjector
- 完善 SQLGuard

收益：

- 支持复杂经营分析
- 动态 SQL 可控、安全、可审计

### 阶段 3：RAG 语义召回

目标：

- 引入 embedding 模型
- 建立向量索引
- BM25 + vector 双路召回
- Python RRF 融合
- 可选 rerank

收益：

- 口语问题、同义表达召回更强
- 知识库问答准确度提升

### 阶段 4：Mixed Query

目标：

- Planner 拆解任务
- SQL Tool + RAG Tool 并行执行
- AnswerComposer 组合回答

收益：

- 支持企业真实复杂问题
- 例如“当前哪些异常，按制度怎么处理”

### 阶段 5：企业级上线能力

目标：

- 审计日志
- 管理端可观测
- 测试集
- 评测集
- 权限与脱敏

收益：

- 可进入企业工程应用
- 支持后续模块扩展与运维

## 14. 二期验收标准

二期完成后，应至少满足：

- 80% 常见问题可以通过语义意图正确路由
- 低置信度问题不乱执行，能主动追问
- 动态 SQL 只允许安全 SELECT
- RAG 能支持同义表达召回
- Mixed Query 能同时返回业务数据和制度建议
- 追问“具体是哪一个”能结合上一轮上下文回答
- 所有 Agent 请求可审计
- 前端不展示模型内部思维过程

## 15. 总结

一期解决的是“链路能跑通”。

二期要解决的是：

```text
用户怎么问都相对稳定
企业数据查询安全可控
知识库召回更接近语义
复杂问题能组合回答
多轮对话能承接上下文
上线后可审计、可观测、可维护
```

最终目标是将 TS_ERP 智能助手建设成企业 ERP 系统中的智能操作入口，而不是简单聊天机器人。
