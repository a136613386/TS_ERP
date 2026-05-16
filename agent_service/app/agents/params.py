"""
ERP 智能助手参数提取模块。

自然语言在模板匹配前需要先做归一化。例如：
“查詢最近的3个客戶”和“查询最近的3个客户”应该进入同一条查询链路。
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import re


class ParameterExtractor:
    """从用户问题中提取模板编号和轻量实体。"""

    TRADITIONAL_TRANSLATION = str.maketrans({
        "詢": "询",
        "戶": "户",
        "個": "个",
        "門": "门",
        "庫": "库",
        "貨": "货",
        "財": "财",
        "務": "务",
        "訂": "订",
        "單": "单",
        "資": "资",
        "訊": "讯",
        "狀": "状",
        "態": "态",
        "聯": "联",
        "繫": "系",
        "總": "总",
        "額": "额",
        "數": "数",
        "據": "据",
        "統": "统",
        "計": "计",
        "檢": "检",
        "視": "视",
    })

    TEMPLATES = {
        "customer_list": {
            "keywords": [
                "客户有哪些",
                "有哪些客户",
                "客户列表",
                "所有客户",
                "查看客户",
                "查询客户",
                "客户信息",
            ],
            "required_params": [],
            "optional_params": ["page", "page_size"],
        },
        "customer_detail": {
            "keywords": ["客户详情", "客户资料"],
            "required_params": ["customer_name"],
            "optional_params": [],
        },
        "customer_orders": {
            "keywords": ["客户订单", "客户的订单"],
            "required_params": ["customer_name"],
            "optional_params": ["status", "start_date", "end_date"],
        },
        "order_detail": {
            "keywords": ["订单详情", "订单信息"],
            "required_params": ["order_id"],
            "optional_params": [],
        },
        "inventory_list": {
            "keywords": ["库存列表", "所有库存", "查看库存", "查询库存"],
            "required_params": [],
            "optional_params": ["warehouse"],
        },
        "inventory_alert": {
            "keywords": ["库存不足", "库存预警", "缺货", "低库存"],
            "required_params": [],
            "optional_params": [],
        },
        "finance_records": {
            "keywords": ["财务记录", "收款", "付款"],
            "required_params": ["type"],
            "optional_params": ["customer_name", "start_date", "end_date"],
        },
    }

    LIST_QUESTION_WORDS = ["有哪些", "有那些", "列表", "所有", "全部", "查看", "查询", "最近", "最新", "前"]

    async def extract(self, query: str, intent: str, session_id: str) -> Dict[str, Any]:
        """从单轮用户问题中提取参数。"""
        normalized_query = self._normalize_query(query)
        params: Dict[str, Any] = {
            "query": query,
            "normalized_query": normalized_query,
            "intent": intent,
        }

        template_id = self._match_template(normalized_query)
        params["template_id"] = template_id
        params.update(self._extract_time_params(normalized_query))
        params.update(self._extract_limit_params(normalized_query))
        params.update(self._extract_entities(normalized_query, template_id))

        if self._check_needs_clarification(params, intent):
            params["needs_clarification"] = True
            params["clarification_message"] = self._generate_clarification_message(params)

        return params

    def _match_template(self, normalized_query: str) -> Optional[str]:
        """使用确定性规则匹配高频查询模板。"""
        clean_query = self._clean_query(normalized_query)

        if "客户" in clean_query and any(word in clean_query for word in self.LIST_QUESTION_WORDS):
            return "customer_list"
        if "库存" in clean_query and any(word in clean_query for word in ["不足", "预警", "缺货", "低库存"]):
            return "inventory_alert"

        for template_id, template in self.TEMPLATES.items():
            for keyword in template["keywords"]:
                if keyword in clean_query:
                    return template_id

        return None

    def _extract_time_params(self, query: str) -> Dict[str, Any]:
        """提取简单日期范围。"""
        params: Dict[str, Any] = {}

        if "今天" in query:
            today = datetime.now().strftime("%Y-%m-%d")
            params["start_date"] = today
            params["end_date"] = today

        if "本月" in query:
            today = datetime.now()
            params["start_date"] = today.replace(day=1).strftime("%Y-%m-%d")
            params["end_date"] = today.strftime("%Y-%m-%d")

        match = re.search(r"最近的?(\d+)天", query)
        if match:
            days = int(match.group(1))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            params["start_date"] = start_date.strftime("%Y-%m-%d")
            params["end_date"] = end_date.strftime("%Y-%m-%d")

        return params

    def _extract_limit_params(self, query: str) -> Dict[str, Any]:
        """从“最近的3个客户”这类表达中提取返回数量。"""
        match = re.search(r"(?:最近|前|最新)?的?\s*(\d+)\s*(?:个|条|笔)", query)
        if not match:
            return {}
        limit = max(1, min(int(match.group(1)), 100))
        return {"limit": limit}

    def _extract_entities(self, query: str, template_id: Optional[str]) -> Dict[str, Any]:
        """只在模板需要实体时提取实体参数。"""
        params: Dict[str, Any] = {}

        if template_id in {"customer_detail", "customer_orders"}:
            customer_name = self._extract_customer_name(query)
            if customer_name:
                params["customer_name"] = customer_name

        order_match = re.search(r"订单\s*#?([A-Za-z0-9_-]+)", query)
        if order_match:
            params["order_id"] = order_match.group(1)

        return params

    def _extract_customer_name(self, query: str) -> Optional[str]:
        """提取客户名称，并避免把列表类问题误识别成客户名。"""
        clean_query = self._clean_query(query)
        if any(word in clean_query for word in self.LIST_QUESTION_WORDS):
            return None

        patterns = [
            r"客户(.+?)的订单",
            r"客户(.+?)详情",
            r"客户(.+?)资料",
        ]
        for pattern in patterns:
            match = re.search(pattern, clean_query)
            if match:
                value = match.group(1).strip()
                return value or None
        return None

    def _check_needs_clarification(self, params: Dict[str, Any], intent: str) -> bool:
        """检查是否缺少必要参数。"""
        if intent == "fixed_query" and params.get("template_id"):
            template = self.TEMPLATES.get(params["template_id"])
            if template:
                return any(required not in params for required in template.get("required_params", []))
        return False

    def _generate_clarification_message(self, params: Dict[str, Any]) -> str:
        """生成简短澄清问题。"""
        if params.get("template_id") == "customer_orders":
            return "请问您想查看哪个客户的订单？"
        if params.get("template_id") == "customer_detail":
            return "请问您想查看哪个客户的详情？"
        return "请提供更多信息以便我为您查询。"

    @classmethod
    def _normalize_query(cls, query: str) -> str:
        return query.translate(cls.TRADITIONAL_TRANSLATION)

    @staticmethod
    def _clean_query(query: str) -> str:
        return re.sub(r"[\s?？。!！,，；;]", "", query)
