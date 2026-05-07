"""
意图识别模块
识别用户查询类型：fixed_query / dynamic_query / rag_query / mixed_query
"""
from typing import Dict, Any
import httpx
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class IntentRecognizer:
    """意图识别器"""
    
    # 意图分类 prompt
    INTENT_PROMPT = """
你是一个 ERP 智能助手，你需要根据用户的问题判断其查询意图。

用户问题: {query}

可能的意图类型:
1. fixed_query: 固定模板查询，适合高频、稳定、可控的问题
   - 例如："查看客户列表"、"客户张三的订单"、"库存预警"
   
2. dynamic_query: 动态查询，适合统计分析、排名、组合筛选问题
   - 例如："本月订单金额最高的客户是谁"、"最近30天哪些客户下过2次以上订单"
   
3. rag_query: 知识问答，适合制度、流程、操作说明、FAQ 类问题
   - 例如："客户等级规则是什么"、"订单状态分别代表什么"
   
4. mixed_query: 混合查询，需要同时查询业务数据和知识库
   - 例如："哪些商品库存不足，按公司制度应该怎么处理"

请输出 JSON 格式:
{{"intent": "意图类型", "confidence": 0.95, "reasoning": "判断理由"}}
"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0
        )
    
    async def recognize(self, query: str) -> Dict[str, Any]:
        """
        识别用户查询意图
        """
        # 使用 LLM 进行意图识别
        prompt = PromptTemplate.from_template(self.INTENT_PROMPT)
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({"query": query})
            content = response.content
            
            # 简单解析 JSON
            import json
            import re
            
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "intent": result.get("intent", "unknown"),
                    "confidence": result.get("confidence", 0.0),
                    "reasoning": result.get("reasoning", "")
                }
        except Exception as e:
            print(f"Intent recognition error: {e}")
        
        # 降级处理：基于关键词匹配
        return self._fallback_recognize(query)
    
    def _fallback_recognize(self, query: str) -> Dict[str, Any]:
        """基于关键词的降级识别"""
        query_lower = query.lower()
        
        # RAG 关键词
        rag_keywords = ["规则", "流程", "制度", "说明", "怎么", "如何", "是什么", "哪些"]
        if any(kw in query_lower for kw in rag_keywords):
            intent = "rag_query"
        # 动态查询关键词
        elif any(kw in query_lower for kw in ["最高", "最低", "最多", "最少", "排名", "统计"]):
            intent = "dynamic_query"
        else:
            intent = "fixed_query"
        
        return {
            "intent": intent,
            "confidence": 0.5,
            "reasoning": "基于关键词匹配"
        }
