"""
SQL 安全校验
"""
import re
from typing import Tuple


class SQLGuard:
    """SQL 安全校验器"""
    
    # 允许的 SQL 关键字
    ALLOWED_KEYWORDS = [
        "SELECT", "FROM", "WHERE", "AND", "OR", "IN", "NOT", "LIKE",
        "ORDER", "BY", "ASC", "DESC", "LIMIT", "OFFSET", "GROUP",
        "HAVING", "COUNT", "SUM", "AVG", "MAX", "MIN", "AS", "ON",
        "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "DISTINCT", "BETWEEN"
    ]
    
    # 禁止的 SQL 关键字
    FORBIDDEN_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
        "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE", "UNION"
    ]
    
    # 禁止的函数
    FORBIDDEN_FUNCTIONS = [
        "sleep", "benchmark", "load_file", "into outfile", "information_schema"
    ]

    ALLOWED_TABLES = {
        "erp_customer": {
            "id", "customer_code", "customer_name", "contact_name", "owner_name",
            "credit_limit", "status", "created_at"
        },
        "inventory_ledger": {
            "id", "sku", "product_name", "warehouse_name", "on_hand_qty",
            "available_qty", "locked_qty", "status"
        },
        "sales_orders": {
            "id", "order_no", "customer_name", "owner_name", "amount",
            "status", "biz_date", "created_at"
        },
        "purchase_orders": {
            "id", "order_no", "supplier_name", "owner_name", "amount",
            "status", "biz_date", "created_at"
        },
        "receivables": {
            "id", "bill_no", "customer_name", "amount", "paid_amount",
            "status", "due_date", "created_at"
        },
        "payables": {
            "id", "bill_no", "supplier_name", "amount", "paid_amount",
            "status", "due_date", "created_at"
        },
        "erp_supplier": {
            "id", "supplier_code", "supplier_name", "category", "settlement",
            "lead_time", "status", "created_at"
        },
    }
    
    def __init__(self):
        self.forbidden_pattern = re.compile(
            r"\b(" + "|".join(self.FORBIDDEN_KEYWORDS) + r")\b",
            re.IGNORECASE
        )
        self.function_pattern = re.compile(
            r"(" + "|".join(self.FORBIDDEN_FUNCTIONS) + ")",
            re.IGNORECASE
        )
    
    async def validate(self, sql: str) -> Tuple[bool, str]:
        """
        校验 SQL 安全性
        返回: (是否安全, 错误信息)
        """
        sql_upper = sql.upper()
        
        # 1. 必须以 SELECT 开头
        if not sql_upper.strip().startswith("SELECT"):
            return False, "只允许 SELECT 查询"
        
        # 2. 检查禁止关键字
        if self.forbidden_pattern.search(sql):
            return False, f"SQL 包含禁止关键字"
        
        # 3. 检查禁止函数
        if self.function_pattern.search(sql):
            return False, f"SQL 包含禁止函数"
        
        # 4. 检查是否有多个语句
        if ";" in sql.strip().rstrip(";"):
            return False, "不允许多个语句"
        
        # 5. 检查注释
        if "--" in sql or "/*" in sql:
            return False, "不允许 SQL 注释"

        # 6. 白名单表校验
        tables = self._extract_tables(sql)
        if not tables:
            return False, "无法识别查询表"
        illegal_tables = [table for table in tables if table not in self.ALLOWED_TABLES]
        if illegal_tables:
            return False, f"不允许访问表: {', '.join(illegal_tables)}"

        # 7. 基础字段白名单校验。允许聚合函数、别名和 * 以兼容现有模板。
        illegal_columns = self._find_illegal_columns(sql, tables)
        if illegal_columns:
            return False, f"不允许访问字段: {', '.join(sorted(illegal_columns))}"

        # 8. 动态查询必须有限制，避免误扫大表。
        if " LIMIT " not in f" {sql_upper} ":
            return False, "查询必须包含 LIMIT"
        
        return True, ""

    def _extract_tables(self, sql: str) -> set[str]:
        tables = set()
        for match in re.finditer(r"\b(?:FROM|JOIN)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?", sql, re.IGNORECASE):
            tables.add(match.group(1))
        return tables

    def _find_illegal_columns(self, sql: str, tables: set[str]) -> set[str]:
        allowed = {"*", "count", "sum", "avg", "min", "max"} | set().union(
            *(self.ALLOWED_TABLES.get(table, set()) for table in tables)
        )
        illegal = set()

        select_match = re.search(r"\bSELECT\b(.+?)\bFROM\b", sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            for raw_item in select_match.group(1).split(","):
                item = raw_item.strip()
                item = re.sub(r"\bAS\b\s+`?[A-Za-z_][A-Za-z0-9_]*`?$", "", item, flags=re.IGNORECASE).strip()
                item = re.sub(r"^(COUNT|SUM|AVG|MIN|MAX)\s*\((.*?)\)$", r"\2", item, flags=re.IGNORECASE).strip()
                item = item.split(".")[-1].strip("` ")
                if item and item not in allowed and not item.isdigit():
                    illegal.add(item)

        for _, column in re.findall(r"`?([A-Za-z_][A-Za-z0-9_]*)`?\.`?([A-Za-z_][A-Za-z0-9_]*)`?", sql):
            if column not in allowed:
                illegal.add(column)
        return illegal
