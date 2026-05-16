"""
查询路由模块
根据意图、参数、权限决定查询路由
"""
from typing import Dict, Any, Optional

from app.guards.permission_guard import PermissionGuard
from app.guards.sql_guard import SQLGuard


class QueryRouter:
    """查询路由器"""
    
    def __init__(self):
        self.permission_guard = PermissionGuard()
        self.sql_guard = SQLGuard()
    
    async def route(
        self,
        intent: str,
        params: Dict[str, Any],
        permission: Dict[str, Any]
    ) -> str:
        """
        决定查询路由
        返回: fixed_query / dynamic_query / rag_query / mixed_query / 
              permission_denied / need_clarification
        """
        # 1. 权限检查
        # 路由器是安全边界之一：先判断是否需要追问，再检查模块权限，
        # 最后才允许进入 SQL/RAG 执行阶段，避免越权查询。
        if params.get("needs_clarification"):
            return "need_clarification"
        
        # 2. 模块权限检查
        module = self._get_module_from_intent(intent)
        if module and not await self.permission_guard.check_module_permission(
            permission=permission,
            module=module
        ):
            return "permission_denied"
        
        # 3. 业务权限检查
        if intent in ["fixed_query", "dynamic_query"]:
            data_scope = await self.permission_guard.get_data_scope(
                permission=permission,
                module=module
            )
            params["data_scope"] = data_scope
        
        # 4. 返回路由
        return intent
     
    def _get_module_from_intent(self, intent: str) -> Optional[str]:
        """从意图获取模块"""
        module_map = {
            "fixed_query": "erp",
            "dynamic_query": "erp",
            "rag_query": "knowledge",
            "mixed_query": "erp"
        }
        return module_map.get(intent)
