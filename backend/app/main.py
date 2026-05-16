"""
TS_ERP 后端主应用入口
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging

# 初始化日志
setup_logging()

app = FastAPI(
    title="TS_ERP API",
    description="ERP 智能助手系统 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "TS_ERP API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
