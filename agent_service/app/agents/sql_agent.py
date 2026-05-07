"""
SQL Agent
负责固定查询和动态 SQL 生成
"""
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

from app.core.config import settings
from app.agents.guards.sql_guard import SQLGuard


class SQLAgent:
    """SQL Agent"""
    
    # 固定模板 SQL
    TEMPLATE_SQL = {
        "customer_list": """
            SELECT id, name, contact, phone, level, created_at 
            FROM customers 
            WHERE is_active = 1 
            ORDER BY created_at DESC 
            LIMIT {limit}
        """,
        "customer_detail": """
            SELECT * FROM customers WHERE name LIKE '%{customer_name}%' AND is_active = 1
        """,
        "customer_orders": """
            SELECT o.*, c.name as customer_name 
            FROM orders o 
            LEFT JOIN customers c ON o.customer_id = c.id 
            WHERE c.name LIKE '%{customer_name}%'
            {status_filter}
            {date_filter}
            ORDER BY o.created_at DESC
        """,
        "inventory_alert": """
            SELECT i.*, p.name as product_name 
            FROM inventory i 
            LEFT JOIN products p ON i.product_id = p.id 
            WHERE i.quantity <= i.min_stock_level
        """,
        "finance_records": """
            SELECT f.*, c.name as customer_name 
            FROM finance_records f 
            LEFT JOIN customers c ON f.customer_id = c.id 
            WHERE 1=1 
            {type_filter}
            {date_filter}
            ORDER BY f.record_date DESC
        """
    }
    
    def __init__(self):
        self.sql_guard = SQLGuard()
    
    async def execute_fixed_query(
        self,
        template_id: str,
        params: Dict[str, Any],
        permission: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行固定模板查询"""
        if not template_id or template_id not in self.TEMPLATE_SQL:
            return {
                "answer": "抱歉，暂不支持该查询类型。",
                "sql": None,
                "data": None
            }
        
        # 1. 获取 SQL 模板
        sql_template = self.TEMPLATE_SQL[template_id]
        
        # 2. 构建 SQL
        sql = self._build_template_sql(sql_template, params)
        
        # 3. SQL 安全校验
        is_safe, error_msg = await self.sql_guard.validate(sql)
        if not is_safe:
            return {
                "answer": f"查询被拦截: {error_msg}",
                "sql": sql,
                "data": None
            }
        
        # 4. 执行查询
        data = await self._execute_sql(sql)
        
        # 5. 构建回答
        answer = self._format_data_answer(template_id, data)
        
        return {
            "answer": answer,
            "sql": sql,
            "data": data,
            "intent": "fixed_query"
        }
    
    async def execute_dynamic_query(
        self,
        query: str,
        params: Dict[str, Any],
        permission: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行动态 SQL 查询"""
        # 调用 LLM 生成 SQL
        from langchain.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel
        from typing import List
        
        class SQLOutput(BaseModel):
            sql: str
            reasoning: str
        
        prompt = PromptTemplate.from_template("""
你是一个 ERP SQL 生成专家。根据用户的问题生成 SQL 查询。

已知表结构:
- customers: id, name, contact, phone, level, department_id, created_at
- orders: id, customer_id, order_no, amount, status, created_at
- inventory: id, product_id, warehouse_id, quantity, min_stock_level
- finance_records: id, customer_id, type, amount, record_date

用户问题: {query}

注意:
1. 只允许 SELECT 查询
2. 必须加上数据权限过滤 (department_id = {department_id})
3. 使用标准 SQL
4. 不要使用 DROP, DELETE, UPDATE, INSERT

输出 JSON 格式:
{{"sql": "SELECT ...", "reasoning": "..."}}
""")
        
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        chain = prompt | llm
        
        try:
            response = await chain.ainvoke({
                "query": query,
                "department_id": params.get("data_scope", {}).get("department_id", 0)
            })
            
            import json
            import re
            json_match = re.search(r'\{[^{}]*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                sql = result.get("sql", "")
                
                # 校验 SQL
                is_safe, error_msg = await self.sql_guard.validate(sql)
                if not is_safe:
                    return {
                        "answer": f"查询被拦截: {error_msg}",
                        "sql": sql,
                        "data": None
                    }
                
                # 执行查询
                data = await self._execute_sql(sql)
                answer = f"根据您的查询，共找到 {len(data.get('rows', []))} 条记录。"
                
                return {
                    "answer": answer,
                    "sql": sql,
                    "data": data,
                    "intent": "dynamic_query"
                }
        except Exception as e:
            return {
                "answer": f"查询处理失败: {str(e)}",
                "sql": None,
                "data": None
            }
        
        return {
            "answer": "抱歉，无法理解您的查询。",
            "sql": None,
            "data": None
        }
    
    def _build_template_sql(self, template: str, params: Dict) -> str:
        """构建模板 SQL"""
        sql = template
        
        # 替换基础参数
        sql = sql.replace("{customer_name}", params.get("customer_name", ""))
        sql = sql.replace("{limit}", str(params.get("limit", 20)))
        
        # 状态过滤
        status = params.get("status")
        if status:
            sql = sql.replace("{status_filter}", f"AND o.status = '{status}'")
        else:
            sql = sql.replace("{status_filter}", "")
        
        # 日期过滤
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        if start_date and end_date:
            sql = sql.replace("{date_filter}", f"AND o.created_at BETWEEN '{start_date}' AND '{end_date}'")
        else:
            sql = sql.replace("{date_filter}", "")
        
        # 类型过滤
        record_type = params.get("type")
        if record_type:
            sql = sql.replace("{type_filter}", f"AND f.type = '{record_type}'")
        else:
            sql = sql.replace("{type_filter}", "")
        
        return sql
    
    async def _execute_sql(self, sql: str) -> Dict[str, Any]:
        """执行 SQL 查询"""
        import pymysql
        
        try:
            connection = pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME
            )
            
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                
                return {
                    "columns": list(rows[0].keys()) if rows else [],
                    "rows": rows,
                    "count": len(rows)
                }
        except Exception as e:
            return {"columns": [], "rows": [], "count": 0, "error": str(e)}
        finally:
            connection.close()
    
    def _format_data_answer(self, template_id: str, data: Dict) -> str:
        """格式化数据回答"""
        rows = data.get("rows", [])
        count = len(rows)
        
        if count == 0:
            return "没有找到相关数据。"
        
        if template_id == "customer_list":
            return f"共找到 {count} 个客户。"
        elif template_id == "customer_orders":
            return f"共找到 {count} 条订单记录。"
        elif template_id == "inventory_alert":
            return f"共发现 {count} 个库存不足的商品。"
        elif template_id == "finance_records":
            return f"共找到 {count} 条财务记录。"
        
        return f"共找到 {count} 条记录。"
