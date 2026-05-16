"""
Java 后端 API 客户端
负责与 Spring Boot Java 后端进行 HTTP 通信
"""
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings


class JavaApiClient:
    """Java 后端 API 客户端"""

    def __init__(self):
        self.base_url = settings.JAVA_BACKEND_URL.rstrip("/")
        self.timeout = settings.JAVA_BACKEND_TIMEOUT
        self._token: Optional[str] = None

    def set_token(self, token: str):
        """设置 JWT Token"""
        self._token = token

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """发起 HTTP 请求"""
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()

    # ── 通用模块 CRUD ──────────────────────────

    async def list_module(self, module_path: str, keyword: str = "", status: str = "") -> Dict[str, Any]:
        """查询模块列表"""
        params = {}
        if keyword:
            params["keyword"] = keyword
        if status:
            params["status"] = status
        return await self._request("GET", f"/api/{module_path}", params=params)

    async def create_module(self, module_path: str, data: Dict) -> Dict[str, Any]:
        """创建模块记录"""
        return await self._request("POST", f"/api/{module_path}", json_data=data)

    async def update_module(self, module_path: str, record_id: int, data: Dict) -> Dict[str, Any]:
        """更新模块记录"""
        return await self._request("PUT", f"/api/{module_path}/{record_id}", json_data=data)

    async def delete_module(self, module_path: str, record_id: int) -> None:
        """删除模块记录"""
        await self._request("DELETE", f"/api/{module_path}/{record_id}")

    async def submit_module(self, module_path: str, record_id: int) -> Dict[str, Any]:
        """提交审核"""
        return await self._request("POST", f"/api/{module_path}/{record_id}/submit")

    # ── 认证 ──────────────────────────────────

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """登录获取 Token"""
        return await self._request("POST", "/api/auth/login", json_data={
            "username": username,
            "password": password,
        })

    # ── 专有业务接口 ──────────────────────────

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """获取经营看板摘要"""
        return await self._request("GET", "/api/dashboard/summary")

    async def get_customer_detail(self, customer_id: int) -> Dict[str, Any]:
        """获取客户详情"""
        return await self._request("GET", f"/api/master-data/customers/{customer_id}")

    async def get_supplier_detail(self, supplier_id: int) -> Dict[str, Any]:
        """获取供应商详情"""
        return await self._request("GET", f"/api/master-data/suppliers/{supplier_id}")

    async def search_knowledge(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """搜索知识库"""
        return await self._request("POST", "/api/knowledge/search", json_data={
            "query": query,
            "top_k": top_k,
        })


# 全局单例
java_api = JavaApiClient()
