"""
响应格式化
"""
from typing import Dict, Any, Optional


class ResponseFormatter:
    """响应格式化器"""
    
    async def format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化响应结果
        """
        answer = result.get("answer", "")
        sql = result.get("sql")
        citations = result.get("citations")
        data = result.get("data")
        intent = result.get("intent", "unknown")
        meta = result.get("meta") or {}
        
        return {
            "answer": answer,
            "sql": sql,
            "citations": citations or [],
            "data": data,
            "intent": intent,
            "meta": meta,
        }
    
    def format_table(self, data: Dict[str, Any]) -> str:
        """
        格式化表格数据
        """
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        
        if not rows:
            return "没有数据"
        
        # 生成 Markdown 表格
        header = "| " + " | ".join(columns) + " |"
        separator = "|" + "|".join([" --- " for _ in columns]) + "|"
        
        body_lines = []
        for row in rows[:10]:  # 最多显示10行
            row_values = [str(row.get(col, "")) for col in columns]
            body_lines.append("| " + " | ".join(row_values) + " |")
        
        return "\n".join([header, separator] + body_lines)
