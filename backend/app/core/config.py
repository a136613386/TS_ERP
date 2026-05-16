"""
应用配置管理
"""
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        case_sensitive=True,
        extra="ignore",
    )
    
    # 应用基础配置
    APP_NAME: str = "TS_ERP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "erp_db"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    # Elasticsearch 配置
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ES_USER: str = ""
    ES_PASSWORD: str = ""
    
    @property
    def ES_URL(self) -> str:
        return f"http://{self.ES_HOST}:{self.ES_PORT}"
    
    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Agent Service 配置
    AGENT_SERVICE_URL: str = "http://localhost:8001"

    # Java 后端 API
    JAVA_BACKEND_URL: str = "http://localhost:8080"
    JAVA_BACKEND_TIMEOUT: int = 30

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_ES_INDEX: str = "ts-erp-logs"
    

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
