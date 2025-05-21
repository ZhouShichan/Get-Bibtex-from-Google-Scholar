import os
import sys

from loguru import logger


def set_proxy(proxy_url: str, proxy_port: str):
    os.environ["http_proxy"] = f"{proxy_url}:{proxy_port}"
    os.environ["https_proxy"] = f"{proxy_url}:{proxy_port}"



def setup_logger(level: str = "DEBUG"):
    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 添加文件输出，按大小滚动，保留10天
    logger.add(
        os.path.join(log_dir, "{time:YYYY-MM-DD-HH-mm-ss}.log"),
        level="DEBUG",
        rotation="1 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )