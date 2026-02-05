"""日志配置"""
import logging
from app.config import settings

def setup_logger():
    """配置日志"""
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('./data/app.log')
        ]
    )
    
    return logging.getLogger(__name__)
