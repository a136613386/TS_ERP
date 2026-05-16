# TS_ERP 三项目结构说明

## 1. 最终项目形态

TS_ERP 采用前后端分离，并将智能体能力独立成 Python 服务。最终开发形态是 3 个项目：

```text
frontend       Vue 3 前端项目
java-backend   Spring Boot Java 应用后端
agent_service  Python Agent / RAG 服务
```

三个项目独立开发、独立启动、独立管理依赖，通过 HTTP 接口协作。

## 2. 调用关系

```text
浏览器
  -> frontend，Vue 3，5173
      -> java-backend，Spring Boot，8080
          -> MySQL / Redis / Elasticsearch
          -> agent_service，Python，8001
```

前端不直接调用 `agent_service`。所有涉及登录用户、权限、业务数据、审计日志的请求，都先进入 `java-backend`。

## 3. 项目职责

### frontend

负责：

- 页面展示和交互。
- 登录页、业务模块页面、智能助手面板。
- 调用 Java 后端 API。
- 保存前端登录态和菜单状态。
- 展示业务表格、表单、看板、审批状态。

不负责：

- 业务权限判断的最终裁决。
- 直接查询数据库。
- 直接调用 Python Agent。
- 生成 SQL。

### java-backend

负责：

- 用户、角色、权限、组织、数据权限。
- 客户、供应商、商品、销售、采购、库存、财务、报表。
- 主业务事务一致性。
- 操作日志、审计日志、聊天记录。
- MySQL、Redis、Elasticsearch 集成。
- 给 Agent Service 提供用户权限上下文。
- 调用 Agent Service 并把结果返回给前端。

### agent_service

负责：

- 意图识别。
- 参数提取。
- RAG 知识库检索。
- SQL 安全校验建议。
- 自然语言回答组织。
- 多轮会话上下文。

不负责：

- 用户登录。
- 主业务写操作。
- 绕过 Java 权限直接查全量业务数据。
- 直接给前端暴露公网业务接口。

## 4. 端口规划

| 项目 | 端口 | 访问对象 |
|------|------|----------|
| frontend | 5173 | 浏览器 |
| java-backend | 8080 | 前端、内部服务 |
| agent_service | 8001 | Java 后端 |
| MySQL | 3306 | Java 后端、Agent 只读场景 |
| Redis | 6379 | Java 后端、Agent 会话 |
| Elasticsearch | 9200 | Java 后端、Agent RAG |

## 5. API 边界

前端调用：

```text
GET  /api/customers
POST /api/sales/orders
POST /api/agent/chat
```

这些 API 都由 `java-backend` 提供。

Java 后端调用 Agent：

```text
POST http://127.0.0.1:8001/agent/query
POST http://127.0.0.1:8001/rag/search
```

## 6. 开发优先级

1. 创建 `java-backend/` Spring Boot 工程。
2. 调整 `frontend/` 的 API base URL 指向 `http://127.0.0.1:8080`。
3. 保留并完善 `agent_service/`。
4. Java 后端统一接管登录、权限和 ERP 主业务。
5. Java 后端封装智能助手接口，内部调用 Python Agent。
