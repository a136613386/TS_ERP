"""
权限校验
"""
from typing import Dict, Any


class PermissionGuard:
    """权限校验器"""
    
    # 模块权限映射
    MODULE_PERMISSIONS = {
        "customer": "customer:view",
        "order": "order:view",
        "inventory": "inventory:view",
        "finance": "finance:view",
        "knowledge": "knowledge:view"
    }
    
    async def check_module_permission(
        self,
        permission: Dict[str, Any],
        module: str
    ) -> bool:
        """
        检查模块权限
        """
        required = self.MODULE_PERMISSIONS.get(module)
        if not required:
            return True
        
        user_permissions = permission.get("permissions", [])
        modules = permission.get("modules", [])
        
        # 检查是否在用户有权限的模块中
        return module in modules or required in user_permissions
    
    async def get_data_scope(
        self,
        permission: Dict[str, Any],
        module: str
    ) -> Dict[str, Any]:
        """
        获取数据权限范围
        """
        data_scope = permission.get("data_scope", {})
        
        return {
            "type": data_scope.get("type", "department"),
            "department_ids": data_scope.get("department_ids", []),
            "user_ids": data_scope.get("user_ids", [])
        }
