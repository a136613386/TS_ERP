"""
Agent Service 配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Agent Service 配置"""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", ".env"),
        case_sensitive=True,
        extra="ignore",
    )
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "ts_erp"
    
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
    
    # DeepSeek / LLM 配置（兼容 OpenAI API）
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_TEMPERATURE: float = 0.0

    # RAG embedding
    # local_hash 用于本地快速联调；bge 使用 BAAI/bge-small-zh-v1.5。
    RAG_EMBEDDING_PROVIDER: str = "local_hash"
    RAG_VECTOR_DIMS: int = 512

    # Java 后端 API
    JAVA_BACKEND_URL: str = "http://localhost:8080"
    JAVA_BACKEND_TIMEOUT: int = 30
    

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
