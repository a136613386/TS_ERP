# Java / Spring Boot 应用体系规划

## 定位

TS_ERP 主业务后端建议直接采用 Spring Boot。原因很明确：

- 你对 Java / Spring Boot 更熟悉，长期维护成本更低。
- ERP 的用户、权限、组织、业务事务、审计日志更适合放在强类型主业务服务中。
- Python 更适合保留在 Agent、RAG、模型调用、向量检索编排这一侧。

因此推荐体系是：

```text
Vue 3 Frontend
  -> Spring Boot Business API
      -> MySQL / Redis / Elasticsearch
      -> Python Agent Service
```

本系统按全新项目建设，不做旧系统数据迁移。数据模型按 TS_ERP 的目标业务闭环重新设计，初始化数据只用于开发、演示和测试。

## 建议目录

```text
TS_ERP/
├── java-backend/       # Spring Boot 主业务服务
├── agent_service/      # Python Agent / RAG 服务
├── frontend/           # Vue 3 前端
├── sql/                # 开发初始化 SQL，后续由 Flyway 管理版本
└── docs/
```

## Java 技术栈建议

- JDK：17 或 21
- Spring Boot：3.x
- Spring Security：登录认证、接口鉴权
- JWT：Access Token + Refresh Token
- MyBatis-Plus：更贴近国内 ERP / 管理系统开发习惯
- Flyway：数据库结构版本管理，不承担旧数据迁移
- MySQL：业务主库
- Redis：登录态、缓存、限流、会话
- Elasticsearch：知识库检索、日志检索、业务搜索
- springdoc-openapi：接口文档
- Maven：项目构建

## 模块划分建议

第一阶段可以先做单体模块化，不急着拆微服务：

```text
com.ts.erp
├── TsErpApplication.java
├── common/             # 通用响应、异常、工具、分页
├── config/             # Spring 配置
├── security/           # JWT、登录、鉴权
├── system/             # 用户、角色、权限、组织
├── customer/           # 客户管理
├── order/              # 订单管理
├── inventory/          # 库存管理
├── finance/            # 财务管理
├── knowledge/          # 知识库元数据管理
├── agent/              # 调用 Python Agent Service
└── audit/              # 操作日志、SQL 审计、聊天记录
```

## 服务边界

### Spring Boot 负责

- 登录、退出、Token 刷新
- 用户、角色、权限、组织架构
- 客户、订单、库存、财务 CRUD 和查询
- 业务事务和审计日志
- 给 Agent Service 提供当前用户权限上下文
- 调用 Agent Service 并保存聊天记录

### Python Agent Service 负责

- 意图识别
- 参数提取
- RAG 检索
- SQL 安全校验建议
- 自然语言回答组织
- 多轮对话上下文

### 不建议让 Agent Service 直接做

- 用户登录
- 核心业务写操作
- 绕过 Java 权限体系直接查全库
- 直接维护 ERP 主业务事务

## 配置入口

Java 后端也沿用当前 `.env` 的 host / port 思路，核心配置包括：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ts_erp

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=

ES_HOST=127.0.0.1
ES_PORT=9200

AGENT_SERVICE_URL=http://127.0.0.1:8001
```

Spring Boot 中可以通过 `application-local.yml` 读取这些环境变量。

## 落地顺序

1. 新建 `java-backend/` Spring Boot 工程骨架。
2. 接入 MySQL、Redis、统一异常、统一响应、OpenAPI。
3. 实现登录、JWT、用户表和角色权限。
4. 实现客户、供应商、商品、销售、采购、库存、财务基础接口。
5. 前端 API 直接对接 Spring Boot。
6. Spring Boot 调用 Python Agent Service。
7. 按产品需求继续扩展审批、报表、知识库和智能助手。
