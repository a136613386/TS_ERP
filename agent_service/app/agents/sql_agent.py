"""
SQL Agent for deterministic ERP data queries.

Fixed templates are used for high-frequency ERP questions. They return both
machine-readable rows and a concise natural-language answer with key details.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List
import re

from app.core.config import settings
from app.guards.sql_guard import SQLGuard


class SQLAgent:
    """Execute fixed SQL templates and guarded dynamic SQL."""

    TEMPLATE_SQL = {
        "customer_list": """
            SELECT
                id,
                customer_code,
                customer_name,
                contact_name,
                owner_name,
                credit_limit,
                status,
                created_at
            FROM erp_customer
            ORDER BY created_at DESC
            LIMIT {limit}
        """,
        "customer_detail": """
            SELECT
                id,
                customer_code,
                customer_name,
                contact_name,
                owner_name,
                credit_limit,
                status,
                created_at
            FROM erp_customer
            WHERE customer_name LIKE '%{customer_name}%'
            ORDER BY created_at DESC
            LIMIT {limit}
        """,
        "customer_orders": """
            SELECT
                id,
                order_no,
                customer_name,
                owner_name,
                amount,
                status,
                biz_date,
                created_at
            FROM sales_orders
            WHERE customer_name LIKE '%{customer_name}%'
            {status_filter}
            {date_filter}
            ORDER BY created_at DESC
            LIMIT {limit}
        """,
        "inventory_alert": """
            SELECT
                id,
                sku,
                product_name,
                warehouse_name,
                on_hand_qty,
                available_qty,
                locked_qty,
                status
            FROM inventory_ledger
            WHERE status = '低库存'
            ORDER BY available_qty ASC
            LIMIT {limit}
        """,
        "finance_records": """
            SELECT
                id,
                bill_no,
                customer_name,
                amount,
                paid_amount,
                status,
                due_date,
                created_at
            FROM receivables
            WHERE 1=1
            {type_filter}
            {date_filter}
            ORDER BY created_at DESC
            LIMIT {limit}
        """,
    }

    def __init__(self):
        self.sql_guard = SQLGuard()

    async def execute_fixed_query(
        self,
        template_id: str,
        params: Dict[str, Any],
        permission: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a trusted fixed SQL template."""
        if not template_id or template_id not in self.TEMPLATE_SQL:
            return {
                "answer": "抱歉，暂不支持该查询类型。",
                "sql": None,
                "data": None,
            }

        sql = self._build_template_sql(self.TEMPLATE_SQL[template_id], params)
        is_safe, error_msg = await self.sql_guard.validate(sql)
        if not is_safe:
            return {
                "answer": f"查询被拒绝: {error_msg}",
                "sql": sql,
                "data": None,
            }

        data = await self._execute_sql(sql)
        return {
            "answer": self._format_data_answer(template_id, data),
            "sql": sql,
            "data": data,
            "intent": "fixed_query",
        }

    async def execute_dynamic_query(
        self,
        query: str,
        params: Dict[str, Any],
        permission: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate and execute dynamic SQL after guard validation."""
        local_sql = self._generate_local_dynamic_sql(query, params)
        if local_sql:
            return await self._execute_guarded_sql(local_sql, "dynamic_query")

        if not settings.LLM_API_KEY:
            return {
                "answer": "当前问题没有命中可控动态 SQL 规则。请换一种更明确的说法，例如：查询最近 3 个客户、统计合作中客户数量、查询逾期应收。",
                "sql": None,
                "data": None,
            }

        from langchain_core.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        import json
        import re

        prompt = PromptTemplate.from_template("""
你是一个 ERP SQL 生成专家。根据用户问题生成只读 SQL。

已知核心表:
- erp_customer: id, customer_code, customer_name, contact_name, owner_name, credit_limit, status, created_at
- inventory_ledger: sku, product_name, warehouse_name, on_hand_qty, available_qty, locked_qty, status
- sales_orders: id, order_no, customer_name, owner_name, amount, status, biz_date, created_at
- purchase_orders: id, order_no, supplier_name, owner_name, amount, status, biz_date, created_at
- receivables: id, bill_no, customer_name, amount, paid_amount, status, due_date, created_at
- payables: id, bill_no, supplier_name, amount, paid_amount, status, due_date, created_at

用户问题: {query}

要求:
1. 只允许 SELECT 查询
2. 不允许 DROP、DELETE、UPDATE、INSERT、ALTER、CREATE
3. 只允许访问上面列出的表和字段
4. 必须包含 LIMIT，最大 LIMIT 100
5. 输出 JSON: {{"sql": "SELECT ...", "reasoning": "..."}}
""")

        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0,
            api_key=settings.LLM_API_KEY or None,
            base_url=settings.LLM_BASE_URL,
        )

        try:
            response = await (prompt | llm).ainvoke({"query": query})
            json_match = re.search(r"\{[^{}]*\}", response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                sql = result.get("sql", "")
                return await self._execute_guarded_sql(sql, "dynamic_query")
        except Exception as exc:
            return {
                "answer": f"查询处理失败: {exc}",
                "sql": None,
                "data": None,
            }

        return {
            "answer": "抱歉，无法理解您的查询。",
            "sql": None,
            "data": None,
        }

    def _build_template_sql(self, template: str, params: Dict[str, Any]) -> str:
        """Fill placeholders used by fixed SQL templates."""
        sql = template
        sql = sql.replace("{customer_name}", self._escape_like(str(params.get("customer_name", ""))))
        sql = sql.replace("{limit}", str(self._safe_limit(params.get("limit", 20))))

        status = params.get("status")
        sql = sql.replace("{status_filter}", f"AND status = '{self._escape_literal(status)}'" if status else "")

        start_date = params.get("start_date")
        end_date = params.get("end_date")
        if start_date and end_date:
            sql = sql.replace("{date_filter}", f"AND created_at BETWEEN '{self._escape_literal(start_date)}' AND '{self._escape_literal(end_date)}'")
        else:
            sql = sql.replace("{date_filter}", "")

        record_type = params.get("type")
        sql = sql.replace("{type_filter}", f"AND status = '{self._escape_literal(record_type)}'" if record_type else "")
        return sql

    async def _execute_guarded_sql(self, sql: str, intent: str) -> Dict[str, Any]:
        normalized_sql = self._normalize_limit(sql)
        is_safe, error_msg = await self.sql_guard.validate(normalized_sql)
        if not is_safe:
            return {
                "answer": f"查询被拒绝: {error_msg}",
                "sql": normalized_sql,
                "data": None,
                "intent": intent,
            }

        data = await self._execute_sql(normalized_sql)
        return {
            "answer": self._format_data_answer(intent, data),
            "sql": normalized_sql,
            "data": data,
            "intent": intent,
        }

    def _generate_local_dynamic_sql(self, query: str, params: Dict[str, Any]) -> str | None:
        """Generate deterministic dynamic SQL for common ERP analysis questions."""
        normalized = self._normalize_question(query)
        limit = self._safe_limit(params.get("limit", 20))

        if "客户" in normalized:
            status = self._extract_status(normalized, ["合作中", "潜在", "停用"])
            if any(word in normalized for word in ["多少", "几个", "数量", "统计", "count"]):
                where = f"WHERE status = '{status}'" if status else ""
                return f"SELECT COUNT(*) AS customer_count FROM erp_customer {where} LIMIT 1"
            where = f"WHERE status = '{status}'" if status else "WHERE 1=1"
            return f"""
                SELECT id, customer_code, customer_name, contact_name, owner_name, credit_limit, status, created_at
                FROM erp_customer
                {where}
                ORDER BY created_at DESC
                LIMIT {limit}
            """

        if any(word in normalized for word in ["库存", "缺货", "低库存", "库存不足"]):
            return f"""
                SELECT id, sku, product_name, warehouse_name, on_hand_qty, available_qty, locked_qty, status
                FROM inventory_ledger
                WHERE status = '低库存' OR available_qty <= 0
                ORDER BY available_qty ASC
                LIMIT {limit}
            """

        if "订单" in normalized:
            status = self._extract_status(normalized, ["待发货", "已审核", "已完成", "待入库"])
            if "采购" in normalized:
                where = f"WHERE status = '{status}'" if status else "WHERE 1=1"
                return f"""
                    SELECT id, order_no, supplier_name, owner_name, amount, status, biz_date, created_at
                    FROM purchase_orders
                    {where}
                    ORDER BY created_at DESC
                    LIMIT {limit}
                """
            where = f"WHERE status = '{status}'" if status else "WHERE 1=1"
            customer = self._extract_named_value(normalized, "客户")
            if customer:
                where += f" AND customer_name LIKE '%{self._escape_like(customer)}%'"
            return f"""
                SELECT id, order_no, customer_name, owner_name, amount, status, biz_date, created_at
                FROM sales_orders
                {where}
                ORDER BY created_at DESC
                LIMIT {limit}
            """

        if "应收" in normalized or "欠款" in normalized:
            where = "WHERE 1=1"
            if "逾期" in normalized:
                where += " AND status = '逾期'"
            return f"""
                SELECT id, bill_no, customer_name, amount, paid_amount, status, due_date, created_at
                FROM receivables
                {where}
                ORDER BY due_date ASC
                LIMIT {limit}
            """

        if "应付" in normalized:
            where = "WHERE 1=1"
            if "逾期" in normalized:
                where += " AND status = '逾期'"
            return f"""
                SELECT id, bill_no, supplier_name, amount, paid_amount, status, due_date, created_at
                FROM payables
                {where}
                ORDER BY due_date ASC
                LIMIT {limit}
            """

        if "供应商" in normalized:
            return f"""
                SELECT id, supplier_code, supplier_name, category, settlement, lead_time, status, created_at
                FROM erp_supplier
                ORDER BY created_at DESC
                LIMIT {limit}
            """

        return None

    async def _execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL and normalize database values for JSON responses."""
        import pymysql

        connection = None
        try:
            connection = pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                charset="utf8mb4",
            )
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql)
                raw_rows = cursor.fetchall()
                rows = [self._normalize_row(row) for row in raw_rows]
                return {
                    "columns": list(rows[0].keys()) if rows else [],
                    "rows": rows,
                    "count": len(rows),
                }
        except Exception as exc:
            return {"columns": [], "rows": [], "count": 0, "error": str(exc)}
        finally:
            if connection:
                connection.close()

    def _format_data_answer(self, template_id: str, data: Dict[str, Any]) -> str:
        """Format a concise answer; tabular details are rendered by the frontend."""
        rows = data.get("rows", [])
        count = len(rows)
        if count == 0:
            error = data.get("error")
            return f"没有找到相关数据。{error}" if error else "没有找到相关数据。"

        if template_id in {"customer_list", "customer_detail"}:
            return f"共找到 {count} 个客户，明细如下。"
        if template_id == "inventory_alert":
            return f"共发现 {count} 个库存不足的商品，明细如下。"
        if template_id == "customer_orders":
            return f"共找到 {count} 条订单记录，明细如下。"
        if template_id == "finance_records":
            return f"共找到 {count} 条财务记录，明细如下。"

        return f"共找到 {count} 条记录，明细如下。"

    @staticmethod
    def _normalize_question(query: str) -> str:
        return (query or "").translate(str.maketrans({
            "詢": "询",
            "戶": "户",
            "庫": "库",
            "貨": "货",
            "訂": "订",
            "單": "单",
            "應": "应",
            "財": "财",
            "務": "务",
        }))

    @staticmethod
    def _extract_status(query: str, statuses: List[str]) -> str | None:
        for status in statuses:
            if status in query:
                return status
        return None

    @staticmethod
    def _extract_named_value(query: str, prefix: str) -> str | None:
        match = re.search(prefix + r"([\u4e00-\u9fa5A-Za-z0-9（）()有限公司集团科技制造贸易]{2,40})", query)
        if not match:
            return None
        value = match.group(1)
        value = re.split(r"(的|有|是|状态|订单|列表)", value)[0]
        return value.strip() or None

    @staticmethod
    def _escape_literal(value: Any) -> str:
        return str(value).replace("\\", "\\\\").replace("'", "''")

    @classmethod
    def _escape_like(cls, value: Any) -> str:
        return cls._escape_literal(value).replace("%", "\\%").replace("_", "\\_")

    @staticmethod
    def _safe_limit(value: Any) -> int:
        try:
            return max(1, min(int(value), 100))
        except (TypeError, ValueError):
            return 20

    @classmethod
    def _normalize_limit(cls, sql: str) -> str:
        stripped = sql.strip().rstrip(";")
        match = re.search(r"\bLIMIT\s+(\d+)\b", stripped, re.IGNORECASE)
        if not match:
            return f"{stripped} LIMIT 20"
        limit = cls._safe_limit(match.group(1))
        return re.sub(r"\bLIMIT\s+\d+\b", f"LIMIT {limit}", stripped, flags=re.IGNORECASE)

    def _format_customer_rows(self, rows: List[Dict[str, Any]], count: int) -> str:
        lines = [f"共找到 {count} 个客户："]
        for index, row in enumerate(rows[:10], start=1):
            name = row.get("customer_name", "-")
            code = row.get("customer_code", "-")
            contact = row.get("contact_name") or "-"
            owner = row.get("owner_name") or "-"
            status = row.get("status") or "-"
            lines.append(f"{index}. {name}（编码：{code}，联系人：{contact}，负责人：{owner}，状态：{status}）")
        return "\n".join(lines)

    def _format_inventory_rows(self, rows: List[Dict[str, Any]], count: int) -> str:
        lines = [f"共发现 {count} 个库存不足的商品："]
        for index, row in enumerate(rows[:10], start=1):
            lines.append(
                f"{index}. {row.get('product_name', '-')}（SKU：{row.get('sku', '-')}，"
                f"仓库：{row.get('warehouse_name', '-')}，可用：{row.get('available_qty', '-')}）"
            )
        return "\n".join(lines)

    def _format_generic_rows(self, rows: List[Dict[str, Any]]) -> str:
        lines = []
        for index, row in enumerate(rows[:10], start=1):
            values = [f"{key}={value}" for key, value in row.items()]
            lines.append(f"{index}. " + "，".join(values))
        return "\n".join(lines)

    @classmethod
    def _normalize_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        return {key: cls._normalize_value(value) for key, value in row.items()}

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return value
