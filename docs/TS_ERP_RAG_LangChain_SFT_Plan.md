# TS_ERP RAG、LangChain 与 SFT 落地方案

## 1. 方案定位

本方案基于 `TS_ERP 产品架构方案` 继续细化，重点回答三个问题：

1. RAG 在系统中具体怎么落地
2. LangChain / LangGraph 在一期如何使用
3. 后续 SFT 微调是否适合引入，以及何时引入

当前判断：

- 一期可以引入 LangChain，但应控制使用边界，优先用于 RAG 检索链、Prompt 编排、Retriever 组合
- 一期不建议上复杂多 Agent 框架，先用代码化单 Agent 流程把业务闭环跑稳
- SFT 不建议一开始做，应该在积累足够高质量业务问答、SQL 生成、权限拒答、RAG 引用样本后再进入

## 2. RAG 在 TS_ERP 中的定位

TS_ERP 中的智能客服有三类问题：

### 2.1 实时业务数据查询

例如：

- 查看张三的订单
- 查询库存不足商品
- 本月订单金额最高的客户是谁

处理方式：

- 固定 SQL
- 动态 SQL
- MySQL 实时查询

这类问题不应该走 RAG，因为答案依赖实时数据库。

### 2.2 业务知识问答

例如：

- 客户等级规则是什么
- 订单状态分别代表什么
- 库存不足时应该怎么处理
- 财务收款确认流程是什么

处理方式：

- RAG
- 知识库检索
- LLM 基于引用片段回答

### 2.3 混合问题

例如：

- 哪些商品库存不足，按公司制度应该怎么处理
- 这个订单待付款，根据流程下一步应该做什么

处理方式：

- SQL 查询实时数据
- RAG 查询制度流程
- LLM 合并回答

## 3. RAG 一期落地目标

一期 RAG 不追求复杂，而是要稳定、可审计、可权限控制。

一期目标：

- 支持 Markdown / TXT / PDF 文档导入
- 支持文档清洗、分块、向量化、索引
- 支持 ES BM25 + 向量混合检索
- 支持知识分类与权限过滤
- 支持回答带引用来源
- 支持检索日志和效果评估

一期不做：

- GraphRAG
- 多 Agent 自动协作
- 大规模模型微调
- 完全自动知识更新

## 4. RAG 技术路线

### 4.1 一期推荐技术栈

- 文档加载：LangChain Document Loaders
- 文本分块：RecursiveCharacterTextSplitter
- 检索编排：LangChain Retriever
- 关键词检索：Elasticsearch BM25
- 向量检索：Elasticsearch dense_vector
- 重排序：可选 BGE Reranker
- 问答链：LangChain Runnable / LCEL
- 服务封装：Python Agent Service 内部使用 FastAPI 暴露接口，由 Spring Boot 调用

### 4.2 为什么一期先用 Elasticsearch 向量检索

当前总架构已经引入 ES，用 ES 同时承载：

- 关键词检索
- 模糊搜索
- 日志检索
- RAG chunk 检索
- 向量检索

这样一期部署复杂度最低。

后续如果知识库规模变大，再引入 Milvus：

- 一期：Elasticsearch BM25 + dense_vector
- 二期：Elasticsearch BM25 + Milvus 向量检索
- 三期：多路召回 + Reranker + Query Rewrite + HyDE

## 5. RAG 数据模型

### 5.1 MySQL 元数据表

建议新增：

- `knowledge_base_t`
- `knowledge_document_t`
- `knowledge_chunk_t`
- `knowledge_permission_t`
- `rag_query_log_t`

### 5.2 表职责

`knowledge_base_t`

- 知识库基础信息
- 适用业务模块
- 是否启用

`knowledge_document_t`

- 原始文档信息
- 文件类型
- 上传人
- 解析状态
- 索引状态

`knowledge_chunk_t`

- chunk 元数据
- chunk 顺序
- 原文摘要
- ES 文档 ID

`knowledge_permission_t`

- 知识库或文档授权
- 角色授权
- 部门授权
- 用户授权

`rag_query_log_t`

- 用户问题
- 检索 query
- 命中的 chunk
- 最终引用
- 回答结果

## 6. Elasticsearch 索引设计

索引名：

`knowledge_chunk_index`

建议字段：

```json
{
  "chunk_id": "string",
  "document_id": "string",
  "base_id": "string",
  "title": "text",
  "content": "text",
  "content_vector": "dense_vector",
  "module": "keyword",
  "tags": "keyword",
  "permission_scope": "keyword",
  "created_by": "keyword",
  "created_at": "date",
  "updated_at": "date"
}
```

检索策略：

- BM25 检索 `title + content`
- 向量检索 `content_vector`
- 过滤 `module / permission_scope / base_id`
- TopK 合并后进入 rerank

## 7. RAG 处理流程

### 7.1 文档入库流程

```text
上传文档
  -> 校验文件类型和权限
  -> 文档解析
  -> 文本清洗
  -> 语义分块
  -> 生成 embedding
  -> 写入 MySQL 元数据
  -> 写入 Elasticsearch
  -> 更新索引状态
```

### 7.2 问答检索流程

```text
用户问题
  -> 意图识别为 rag_query
  -> 获取当前用户权限上下文
  -> Query Rewrite
  -> BM25 检索
  -> 向量检索
  -> 合并召回
  -> 权限过滤
  -> Rerank
  -> 构建上下文
  -> LLM 生成答案
  -> 返回答案和引用来源
```

### 7.3 混合 SQL + RAG 流程

```text
用户问题
  -> 识别为 mixed_query
  -> SQL 查询实时业务数据
  -> RAG 查询制度流程
  -> LLM 合并回答
  -> 返回业务数据 + 处理建议 + 引用来源
```

## 8. LangChain 一期使用方式

### 8.1 推荐使用边界

LangChain 一期用于：

- 文档加载
- 文本分块
- Retriever 封装
- PromptTemplate
- Runnable 链式编排
- 多路召回组合
- 输出解析

LangChain 一期不建议用于：

- 直接接管整个业务流程
- 自动执行 SQL
- 自动决定权限
- 复杂多 Agent 自治

权限、SQL Guard、业务策略必须留在自研代码中，不能交给 LangChain 或 LLM 自由发挥。

### 8.2 推荐模块结构

```text
agent_service/app/rag/
├─ loaders.py
├─ splitters.py
├─ embeddings.py
├─ indexer.py
├─ retrievers.py
├─ reranker.py
├─ chains.py
├─ evaluators.py
└─ schemas.py
```

### 8.3 LangChain RAG Chain 示例结构

```text
Question
  -> QueryRewriteChain
  -> EnsembleRetriever
  -> PermissionFilter
  -> Reranker
  -> ContextBuilder
  -> AnswerChain
  -> CitationParser
```

## 9. LangGraph 使用建议

LangGraph 适合后续把 Agent 流程状态机化。

建议二期再引入，用于：

- `fixed_query`
- `dynamic_query`
- `rag_query`
- `mixed_query`
- `permission_denied`
- `need_clarification`

示例状态：

```text
AuthContext
Intent
ExtractedParams
PermissionResult
QueryMode
SQLResult
RAGContext
FinalAnswer
Trace
```

一期可以先用普通 Python service 编排，等流程稳定后再迁移到 LangGraph。

## 10. RAG 权限策略

RAG 权限必须在检索阶段处理，而不是只在回答阶段处理。

规则：

- 无 `agent:rag` 权限，不能进入 RAG 链
- 无 `knowledge:view` 权限，不能访问知识库
- 无对应模块权限，不能检索对应模块文档
- 权限过滤发生在 Rerank 之前
- 最终回答只能引用授权后的 chunk

这点很重要：不能把未授权 chunk 放进 prompt，再要求模型不要说。

## 11. RAG 效果评估

一期需要建立简单评估集。

评估维度：

- 检索命中率
- TopK 命中率
- 答案准确性
- 引用一致性
- 无依据回答率
- 权限越权率
- 平均响应时间

建议维护测试集：

```text
docs/eval/rag_questions.yaml
```

样例：

```yaml
- question: "库存不足时应该怎么处理"
  expected_doc: "库存管理制度"
  expected_keywords: ["安全库存", "补货", "预警"]
  role: "warehouse"
```

## 12. SFT 微调综合评估

### 12.1 当前是否应该立即 SFT

不建议立即做。

原因：

- 当前系统核心问题是工程链路稳定性，不是模型能力上限
- RAG、SQL Guard、权限体系、日志评估还未稳定
- 训练数据还不够规范
- 过早 SFT 容易把系统问题误当成模型问题

### 12.2 什么时候适合做 SFT

建议满足以下条件后再做：

- 固定查询和动态查询稳定运行
- RAG 有真实问答日志
- 权限拒答样本足够
- SQL 生成错误样本足够
- 已有人工标注的高质量答案
- 已建立离线评测集

### 12.3 SFT 适合优化什么

适合：

- 意图识别
- 参数抽取
- SQL 生成格式稳定性
- 权限拒答话术
- ERP 领域回答风格
- RAG 答案组织方式

不适合：

- 替代权限系统
- 替代 SQL Guard
- 替代 RAG 检索
- 记忆实时业务数据

### 12.4 SFT 数据来源

建议从系统运行日志中沉淀：

- 用户问题
- 标准 intent
- 标准参数
- 生成 SQL
- 修正后 SQL
- SQL 执行结果摘要
- 标准回答
- 权限拒答样本
- RAG 引用样本

### 12.5 SFT 技术路线

第一阶段：

- 不训练模型，只做 prompt + RAG + Guard 优化

第二阶段：

- LoRA / QLoRA 微调小模型
- 用于意图识别和参数抽取

第三阶段：

- 微调 SQL 生成模型
- 使用严格 SQL 输出评测集

第四阶段：

- 微调领域客服回答模型
- 统一回答风格和拒答策略

## 13. 推荐演进路线

### 一期：工程化 RAG

- Python Agent Service，内部使用 FastAPI
- Spring Boot 统一封装前端可访问的智能助手 API
- LangChain RAG Chain
- ES BM25 + ES 向量检索
- 权限过滤
- 引用来源
- RAG 日志

### 二期：高级 RAG

- Query Rewrite
- Multi Query Retriever
- HyDE
- Reranker
- Context Compression
- 检索评测集

### 三期：LangGraph Agent

- 将 fixed_query / dynamic_query / rag_query / mixed_query 图化
- 增加状态机、Trace、可观测性
- 增加工具调用治理

### 四期：多 Agent 协作

- Query Agent
- SQL Agent
- RAG Agent
- Permission Agent
- Review Agent

这一阶段要谨慎，多 Agent 应该服务于复杂任务拆分，而不是让系统失控。

### 五期：SFT / LoRA 微调

- 意图识别微调
- 参数抽取微调
- SQL 生成微调
- 领域回答风格微调

## 14. 结论

TS_ERP 的智能体技术路线建议是：

```text
代码化 Agent
  -> 工程化 RAG
  -> LangChain 检索编排
  -> LangGraph 状态机
  -> 高级 RAG
  -> 数据沉淀
  -> SFT 微调
```

这条路线更稳。先把系统的权限、检索、SQL、日志、评估做好，再用微调提升模型表现。SFT 应该是工程体系成熟后的加速器，而不是第一天就上的核心依赖。
