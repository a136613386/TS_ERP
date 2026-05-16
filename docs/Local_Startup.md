# 本机启动说明

## 1. 三项目结构

TS_ERP 按前后端分离和智能体独立服务设计，实际开发时是 3 个项目：

```text
TS_ERP/
├── frontend/       # Vue 3 前端，端口 5173
├── java-backend/   # Spring Boot 应用后端，端口 8080
└── agent_service/  # Python Agent / RAG 服务，端口 8001
```

基础设施由本机已有服务或 Docker 提供：

- MySQL：业务数据库
- Redis：缓存、会话、限流、权限缓存
- Elasticsearch：业务搜索、日志检索、RAG 索引

## 2. 配置入口

复制环境模板：

```powershell
cd D:\xuweiqun\py_project\TS_ERP
Copy-Item .env.example .env
```

只需要先改这些连接信息：

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

后续 `java-backend/` 使用 `application-local.yml` 读取这些环境变量；`agent_service/` 读取项目根目录 `.env` 或服务目录 `.env`。

## 3. 数据库初始化

本系统全新建设，不做旧数据迁移。开发期可以创建空库并导入初始化结构和演示数据。

```sql
CREATE DATABASE IF NOT EXISTS ts_erp DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

当前 `sql/` 下的脚本可作为开发初始化参考。等 `java-backend/` 建成后，数据库结构版本由 Flyway 或 Liquibase 管理。

```powershell
cd D:\xuweiqun\py_project\TS_ERP
mysql -h 127.0.0.1 -P 3306 -u root -p ts_erp < sql\schema.sql
mysql -h 127.0.0.1 -P 3306 -u root -p ts_erp < sql\seed.sql
```

## 4. 启动 Java 后端

`java-backend/` 是 Spring Boot 主业务项目，规划端口为 `8080`。

```powershell
cd D:\xuweiqun\py_project\TS_ERP\java-backend
mvn spring-boot:run -Dspring-boot.run.profiles=local
```

访问：

```text
http://127.0.0.1:8080/doc.html
http://127.0.0.1:8080/swagger-ui/index.html
```

说明：当前仓库里的 `java-backend/` 还未生成，后续应优先创建该 Spring Boot 工程。

## 5. 启动 Python Agent Service

```powershell
conda activate advanced_rag
cd D:\xuweiqun\py_project\TS_ERP\agent_service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

访问：

```text
http://127.0.0.1:8001/docs
```

## 6. 启动 Vue 前端

```powershell
cd D:\xuweiqun\py_project\TS_ERP\frontend
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

前端本地开发时应把 API 代理到 Spring Boot：

```text
/api -> http://127.0.0.1:8080
```

## 7. 连接检查

Spring Boot 健康检查，后续实现：

```powershell
Invoke-RestMethod http://127.0.0.1:8080/actuator/health
```

Agent 健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```
