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
    
    def __init__(self):
        self.forbidden_pattern = re.compile(
            r"(" + "|".join(self.FORBIDDEN_KEYWORDS) + ")",
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
        
        return True, ""
