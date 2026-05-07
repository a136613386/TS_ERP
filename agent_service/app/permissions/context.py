"""
权限上下文
"""
from typing import Dict, Any, Optional


class PermissionContext:
    """权限上下文"""
    
    async def get_user_permission(
        self,
        user_id: int,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取用户权限上下文
        """
        # TODO: 从数据库/缓存获取真实权限
        # 这里返回模拟数据
        return {
            "user_id": user_id,
            "department_id": department_id or 1,
            "roles": ["sales", "manager"],
            "modules": ["customer", "order", "inventory", "finance", "knowledge"],
            "data_scope": {
                "type": "department",  # department / all / self
                "department_ids": [department_id] if department_id else [1]
            }
        }
