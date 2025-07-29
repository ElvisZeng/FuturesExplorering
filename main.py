#!/usr/bin/env python3
"""
期货数据管理系统主启动文件
"""
import logging
import os
import sys
from datetime import datetime
from config import LOGGING_CONFIG

def setup_logging():
    """设置日志系统"""
    # 创建日志目录
    log_dir = os.path.dirname(LOGGING_CONFIG['file'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志格式
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG['level']),
        format=LOGGING_CONFIG['format'],
        handlers=[
            logging.FileHandler(LOGGING_CONFIG['file'], encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("期货数据管理系统启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

def main():
    """主函数"""
    try:
        # 设置日志
        setup_logging()
        
        # 导入并启动GUI
        from gui import FuturesDataGUI
        
        app = FuturesDataGUI()
        app.run()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        logging.error(f"程序启动失败: {e}")
        print(f"程序启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())