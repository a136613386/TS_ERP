"""
参数提取模块
从用户查询中提取关键参数
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.memory.session import SessionMemory


class ParameterExtractor:
    """参数提取器"""
    
    # 固定模板定义
    TEMPLATES = {
        "customer_list": {
            "keywords": ["客户列表", "所有客户", "查看客户"],
            "required_params": [],
            "optional_params": ["page", "page_size"]
        },
        "customer_detail": {
            "keywords": ["客户详情", "客户信息", "客户信息"],
            "required_params": ["customer_name"],
            "optional_params": []
        },
        "customer_orders": {
            "keywords": ["客户订单", "某客户订单"],
            "required_params": ["customer_name"],
            "optional_params": ["status", "start_date", "end_date"]
        },
        "order_detail": {
            "keywords": ["订单详情", "订单信息"],
            "required_params": ["order_id"],
            "optional_params": []
        },
        "inventory_list": {
            "keywords": ["库存列表", "所有库存", "查看库存"],
            "required_params": [],
            "optional_params": ["warehouse"]
        },
        "inventory_alert": {
            "keywords": ["库存不足", "库存预警", "缺货"],
            "required_params": [],
            "optional_params": []
        },
        "finance_records": {
            "keywords": ["财务记录", "收款", "付款"],
            "required_params": ["type"],
            "optional_params": ["customer_name", "start_date", "end_date"]
        }
    }
    
    async def extract(
        self,
        query: str,
        intent: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        提取查询参数
        """
        params = {
            "query": query,
            "intent": intent
        }
        
        # 1. 识别模板
        template_id = self._match_template(query)
        params["template_id"] = template_id
        
        # 2. 提取时间参数
        params.update(self._extract_time_params(query))
        
        # 3. 提取实体参数
        params.update(self._extract_entities(query))
        
        # 4. 检查是否需要追问
        needs_clarification = self._check_needs_clarification(params, intent)
        if needs_clarification:
            params["needs_clarification"] = True
            params["clarification_message"] = self._generate_clarification_message(params)
        
        return params
    
    def _match_template(self, query: str) -> Optional[str]:
        """匹配固定模板"""
        query_lower = query.lower()
        
        for template_id, template in self.TEMPLATES.items():
            for keyword in template["keywords"]:
                if keyword in query_lower:
                    return template_id
        
        return None
    
    def _extract_time_params(self, query: str) -> Dict[str, Any]:
        """提取时间参数"""
        params = {}
        query_lower = query.lower()
        
        # 今天
        if "今天" in query:
            params["start_date"] = datetime.now().strftime("%Y-%m-%d")
            params["end_date"] = datetime.now().strftime("%Y-%m-%d")
        
        # 本月
        if "本月" in query:
            today = datetime.now()
            params["start_date"] = today.replace(day=1).strftime("%Y-%m-%d")
            params["end_date"] = today.strftime("%Y-%m-%d")
        
        # 最近 N 天
        import re
        match = re.search(r"最近(\d+)天", query)
        if match:
            days = int(match.group(1))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            params["start_date"] = start_date.strftime("%Y-%m-%d")
            params["end_date"] = end_date.strftime("%Y-%m-%d")
        
        return params
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """提取实体参数"""
        params = {}
        
        # 简单提取客户名（实际应该用 NER）
        # 这里用简单的关键词匹配
        import re
        
        # 提取"客户XXX"
        customer_match = re.search(r"客户[^\s,，]+", query)
        if customer_match:
            customer_name = customer_match.group().replace("客户", "")
            params["customer_name"] = customer_name
        
        # 提取订单ID
        order_match = re.search(r"订单[^\s,，#]+", query)
        if order_match:
            order_id = order_match.group().replace("订单", "").replace("#", "")
            params["order_id"] = order_id
        
        return params
    
    def _check_needs_clarification(self, params: Dict, intent: str) -> bool:
        """检查是否需要追问"""
        if intent == "fixed_query" and params.get("template_id"):
            template = self.TEMPLATES.get(params["template_id"])
            if template:
                for required in template.get("required_params", []):
                    if required not in params:
                        return True
        return False
    
    def _generate_clarification_message(self, params: Dict) -> str:
        """生成追问消息"""
        if params.get("template_id") == "customer_orders":
            return "请问您想查看哪个客户的订单？"
        return "请提供更多信息以便我为您查询。"
