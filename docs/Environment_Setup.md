# TS_ERP 环境配置说明

## 1. 项目形态

TS_ERP 是前后端分离 + 智能体独立服务的三项目体系：

```text
frontend       Vue 3 前端项目
java-backend   Spring Boot Java 应用后端
agent_service  Python Agent / RAG 服务
```

三个项目独立开发、独立启动、通过 HTTP 接口协作。

## 2. 本机基础环境

### 前端

- Node.js 18+
- npm
- Vue 3
- Vite

### Java 后端

- JDK 17 或 JDK 21
- Maven 3.8+
- Spring Boot 3.x
- MyBatis-Plus
- Spring Security
- Flyway 或 Liquibase

### Python Agent

Python 统一使用 Conda 环境：

```text
advanced_rag
```

已确认本机环境：

```text
Python 3.10.20
D:\xuweiqun\anaconda3\envs\advanced_rag\python.exe
stdout encoding: utf-8
```

### 基础设施

- MySQL 8.0
- Redis 7
- Elasticsearch 8.x
- Kibana，可选

## 3. 配置文件

项目根目录 `.env` 作为本机统一配置入口：

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

`java-backend/` 后续通过 `application-local.yml` 映射这些环境变量。`agent_service/` 继续读取 `.env`。

## 4. 启动顺序

推荐顺序：

1. 启动 MySQL / Redis / Elasticsearch。
2. 启动 `agent_service/`。
3. 启动 `java-backend/`。
4. 启动 `frontend/`。

## 5. 端口规划

| 项目 | 技术 | 端口 | 说明 |
|------|------|------|------|
| frontend | Vue 3 / Vite | 5173 | 浏览器访问入口 |
| java-backend | Spring Boot | 8080 | 主业务 API |
| agent_service | FastAPI / Python | 8001 | Agent / RAG 内部服务 |
| MySQL | MySQL | 3306 | 业务数据库 |
| Redis | Redis | 6379 | 缓存与会话 |
| Elasticsearch | ES | 9200 | 搜索与知识索引 |

## 6. 中文支持

项目内中文文档、中文注释、接口中文解释、Agent 中文回复都按 UTF-8 处理。

PowerShell 中如果中文显示异常，先执行：

```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"
```

读取中文文档时建议显式指定编码：

```powershell
Get-Content -Encoding UTF8 docs\Environment_Setup.md
Get-Content -Encoding UTF8 docs\AGENTS.md
```

## 7. 注意事项

- TS_ERP 是全新系统，不做旧数据迁移。
- `sql/` 当前用于开发初始化参考，后续以 `java-backend/` 的 Flyway 或 Liquibase 脚本为准。
- `agent_service/` 不承载 ERP 主业务写操作，只提供智能体、RAG 和自然语言查询辅助。
- 前端所有业务 API 应优先对接 `java-backend/`，由 Java 后端再调用 Python Agent。
