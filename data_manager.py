"""
数据管理模块
集成数据下载、处理、导入数据库和定时更新功能
"""
import pandas as pd
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import os
from database import db_manager
from data_downloader import data_downloader
from data_processor import data_processor
from config import CSV_DATA_DIR

class FuturesDataManager:
    """期货数据管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.scheduler_thread = None
        self.update_callbacks = []  # 用于UI更新的回调函数
        
        # 初始化数据库表
        try:
            db_manager.initialize_tables()
            self.logger.info("数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"数据库表初始化失败: {e}")
    
    def add_update_callback(self, callback: Callable):
        """添加更新回调函数"""
        self.update_callbacks.append(callback)
    
    def notify_update(self, message: str):
        """通知所有回调函数"""
        for callback in self.update_callbacks:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")
    
    def download_historical_data(self, start_date: str, end_date: str, 
                               exchanges: List[str] = None) -> Dict[str, pd.DataFrame]:
        """下载历史数据"""
        try:
            self.logger.info(f"开始下载历史数据: {start_date} - {end_date}")
            self.notify_update(f"开始下载历史数据: {start_date} - {end_date}")
            
            # 下载原始数据
            raw_data = data_downloader.download_all_exchanges_data(
                start_date, end_date, exchanges
            )
            
            if not any(not df.empty for df in raw_data.values()):
                self.logger.warning("未下载到任何数据")
                self.notify_update("未下载到任何数据")
                return {}
            
            # 保存原始数据
            date_suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
            data_downloader.save_raw_data(raw_data, date_suffix)
            
            self.logger.info("历史数据下载完成")
            self.notify_update("历史数据下载完成")
            return raw_data
            
        except Exception as e:
            self.logger.error(f"下载历史数据失败: {e}")
            self.notify_update(f"下载历史数据失败: {e}")
            return {}
    
    def process_and_import_data(self, raw_data: Dict[str, pd.DataFrame]) -> bool:
        """处理并导入数据到数据库"""
        try:
            self.logger.info("开始处理和导入数据")
            self.notify_update("开始处理和导入数据")
            
            # 处理数据
            processed_data = data_processor.process_all_exchanges_data(raw_data)
            
            if not processed_data:
                self.logger.warning("没有有效的处理后数据")
                self.notify_update("没有有效的处理后数据")
                return False
            
            # 合并所有交易所数据
            merged_data = data_processor.merge_all_exchanges(processed_data)
            
            if merged_data.empty:
                self.logger.warning("合并后数据为空")
                self.notify_update("合并后数据为空")
                return False
            
            # 保存到CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"futures_data_{timestamp}.csv"
            data_processor.save_to_csv(merged_data, csv_filename)
            
            # 导入到数据库
            success = db_manager.insert_futures_data(merged_data)
            if success:
                self.notify_update(f"成功导入 {len(merged_data)} 条期货数据")
            
            # 创建并导入连续合约数据
            continuous_data = data_processor.create_continuous_contracts(merged_data)
            if not continuous_data.empty:
                continuous_success = db_manager.insert_continuous_contract_data(continuous_data)
                if continuous_success:
                    self.notify_update(f"成功导入 {len(continuous_data)} 条连续合约数据")
            
            self.logger.info("数据处理和导入完成")
            self.notify_update("数据处理和导入完成")
            return success
            
        except Exception as e:
            self.logger.error(f"处理和导入数据失败: {e}")
            self.notify_update(f"处理和导入数据失败: {e}")
            return False
    
    def import_csv_to_database(self, csv_file_path: str) -> bool:
        """从CSV文件导入数据到数据库"""
        try:
            self.logger.info(f"开始从CSV导入数据: {csv_file_path}")
            self.notify_update(f"开始从CSV导入数据: {csv_file_path}")
            
            # 读取CSV文件
            df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
            
            if df.empty:
                self.logger.warning("CSV文件为空")
                self.notify_update("CSV文件为空")
                return False
            
            # 验证数据格式
            required_columns = ['trade_date', 'exchange', 'product_code', 'contract_code']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.error(f"CSV文件缺少必要字段: {missing_columns}")
                self.notify_update(f"CSV文件缺少必要字段: {missing_columns}")
                return False
            
            # 导入数据库
            success = db_manager.insert_futures_data(df)
            
            if success:
                self.logger.info(f"成功从CSV导入 {len(df)} 条数据")
                self.notify_update(f"成功从CSV导入 {len(df)} 条数据")
            
            return success
            
        except Exception as e:
            self.logger.error(f"从CSV导入数据失败: {e}")
            self.notify_update(f"从CSV导入数据失败: {e}")
            return False
    
    def update_daily_data(self) -> bool:
        """更新当日数据"""
        try:
            self.logger.info("开始更新当日数据")
            self.notify_update("开始更新当日数据")
            
            # 获取最新交易日
            latest_date = data_downloader.get_latest_trading_day()
            
            # 下载当日数据
            raw_data = data_downloader.download_all_exchanges_data(latest_date, latest_date)
            
            if not any(not df.empty for df in raw_data.values()):
                self.logger.info("当日无新数据")
                self.notify_update("当日无新数据")
                return True
            
            # 处理并导入数据
            success = self.process_and_import_data(raw_data)
            
            if success:
                self.logger.info("当日数据更新完成")
                self.notify_update("当日数据更新完成")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新当日数据失败: {e}")
            self.notify_update(f"更新当日数据失败: {e}")
            return False
    
    def start_scheduled_updates(self, update_time: str = "18:00"):
        """启动定时更新任务"""
        try:
            if self.is_running:
                self.logger.warning("定时更新任务已在运行")
                return
            
            # 设置定时任务
            schedule.clear()  # 清除之前的任务
            schedule.every().monday.at(update_time).do(self.update_daily_data)
            schedule.every().tuesday.at(update_time).do(self.update_daily_data)
            schedule.every().wednesday.at(update_time).do(self.update_daily_data)
            schedule.every().thursday.at(update_time).do(self.update_daily_data)
            schedule.every().friday.at(update_time).do(self.update_daily_data)
            
            self.is_running = True
            
            # 在单独线程中运行调度器
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            self.logger.info(f"定时更新任务已启动，更新时间: {update_time}")
            self.notify_update(f"定时更新任务已启动，更新时间: {update_time}")
            
        except Exception as e:
            self.logger.error(f"启动定时更新失败: {e}")
            self.notify_update(f"启动定时更新失败: {e}")
    
    def stop_scheduled_updates(self):
        """停止定时更新任务"""
        try:
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                # 等待线程结束
                self.scheduler_thread.join(timeout=5)
            
            self.logger.info("定时更新任务已停止")
            self.notify_update("定时更新任务已停止")
            
        except Exception as e:
            self.logger.error(f"停止定时更新失败: {e}")
            self.notify_update(f"停止定时更新失败: {e}")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"调度器运行错误: {e}")
    
    def get_data_summary(self) -> Dict[str, any]:
        """获取数据概要信息"""
        try:
            summary = {
                'database_status': db_manager.check_connection(),
                'available_exchanges': [],
                'available_products': [],
                'date_range': {},
                'total_records': 0
            }
            
            if summary['database_status']:
                # 获取可用交易所
                connection = db_manager.get_connection()
                cursor = connection.cursor()
                
                cursor.execute("SELECT DISTINCT exchange FROM futures_daily_data ORDER BY exchange")
                summary['available_exchanges'] = [row[0] for row in cursor.fetchall()]
                
                # 获取可用产品
                cursor.execute("SELECT DISTINCT product_code FROM futures_daily_data ORDER BY product_code")
                summary['available_products'] = [row[0] for row in cursor.fetchall()]
                
                # 获取日期范围
                cursor.execute("SELECT MIN(trade_date), MAX(trade_date) FROM futures_daily_data")
                date_result = cursor.fetchone()
                if date_result[0] and date_result[1]:
                    summary['date_range'] = {
                        'start_date': date_result[0].strftime('%Y-%m-%d'),
                        'end_date': date_result[1].strftime('%Y-%m-%d')
                    }
                
                # 获取总记录数
                cursor.execute("SELECT COUNT(*) FROM futures_daily_data")
                summary['total_records'] = cursor.fetchone()[0]
                
                cursor.close()
                db_manager.return_connection(connection)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取数据概要失败: {e}")
            return {
                'database_status': False,
                'error': str(e)
            }
    
    def export_data_to_csv(self, exchange: str = None, product_code: str = None,
                          start_date: str = None, end_date: str = None,
                          filename: str = None) -> str:
        """导出数据到CSV文件"""
        try:
            # 从数据库获取数据
            data = db_manager.get_futures_data(exchange, product_code, start_date, end_date)
            
            if data.empty:
                self.logger.warning("没有找到符合条件的数据")
                return ""
            
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"export_{timestamp}.csv"
            
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            # 保存文件
            filepath = os.path.join(CSV_DATA_DIR, filename)
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"数据已导出到: {filepath}")
            self.notify_update(f"数据已导出到: {filepath}")
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            self.notify_update(f"导出数据失败: {e}")
            return ""
    
    def import_fundamentals_data(self, data: pd.DataFrame) -> bool:
        """导入基本面数据"""
        try:
            self.logger.info("开始导入基本面数据")
            self.notify_update("开始导入基本面数据")
            
            # 验证基本面数据格式
            required_columns = ['data_date', 'product_code', 'data_type', 'data_name', 'data_value']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                self.logger.error(f"基本面数据缺少必要字段: {missing_columns}")
                self.notify_update(f"基本面数据缺少必要字段: {missing_columns}")
                return False
            
            # 导入数据库
            success = db_manager.insert_fundamentals_data(data)
            
            if success:
                self.logger.info(f"成功导入 {len(data)} 条基本面数据")
                self.notify_update(f"成功导入 {len(data)} 条基本面数据")
            
            return success
            
        except Exception as e:
            self.logger.error(f"导入基本面数据失败: {e}")
            self.notify_update(f"导入基本面数据失败: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """清理旧数据"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
            
            connection = db_manager.get_connection()
            cursor = connection.cursor()
            
            # 删除旧的期货数据
            cursor.execute(
                "DELETE FROM futures_daily_data WHERE trade_date < %s",
                (cutoff_date,)
            )
            deleted_futures = cursor.rowcount
            
            # 删除旧的连续合约数据
            cursor.execute(
                "DELETE FROM continuous_contracts WHERE trade_date < %s",
                (cutoff_date,)
            )
            deleted_continuous = cursor.rowcount
            
            connection.commit()
            cursor.close()
            db_manager.return_connection(connection)
            
            self.logger.info(f"清理完成: 删除了 {deleted_futures} 条期货数据, {deleted_continuous} 条连续合约数据")
            self.notify_update(f"清理完成: 删除了 {deleted_futures} 条期货数据, {deleted_continuous} 条连续合约数据")
            
            return True
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            self.notify_update(f"清理旧数据失败: {e}")
            return False

# 全局数据管理器实例
data_manager = FuturesDataManager()