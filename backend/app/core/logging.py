"""
日志配置
"""
import logging
import sys
from elasticsearch import Elasticsearch

from app.core.config import settings


class ESLogHandler(logging.Handler):
    """Elasticsearch 日志处理器"""
    
    def __init__(self, es_client: Elasticsearch, index: str):
        super().__init__()
        self.es_client = es_client
        self.index = index
    
    def emit(self, record):
        try:
            doc = {
                "message": self.format(record),
                "level": record.levelname,
                "logger": record.name,
                "timestamp": record.created,
            }
            self.es_client.index(index=self.index, document=doc)
        except Exception:
            self.handleError(record)


def setup_logging():
    """初始化日志配置"""
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.addHandler(console_handler)
    
    # 第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)
