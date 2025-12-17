"""
日誌記錄器模組

提供統一的日誌記錄功能
"""

import logging
import sys


def setup_logger(level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """
    設置日誌記錄器
    
    Args:
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日誌文件路徑（可選）
        
    Returns:
        配置好的 Logger 對象
    """
    # 創建 logger
    logger = logging.getLogger('AddressTaggingService')
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除現有的 handlers
    logger.handlers = []
    
    # 創建格式化器
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件 handler（如果指定）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
