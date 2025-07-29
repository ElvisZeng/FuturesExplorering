"""
期货数据下载模块
支持从中国各大期货交易所下载历史数据
"""
import requests
import pandas as pd
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import os
from config import EXCHANGES, RAW_DATA_DIR, PROCESSED_DATA_DIR
import akshare as ak

class FuturesDataDownloader:
    """期货数据下载器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 确保数据目录存在
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    def download_shfe_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """下载上海期货交易所数据"""
        try:
            self.logger.info(f"开始下载上期所数据: {start_date} - {end_date}")
            
            # 使用akshare获取上期所数据
            all_data = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current_date <= end_date_obj:
                date_str = current_date.strftime('%Y%m%d')
                try:
                    # 获取当日数据
                    df = ak.futures_zh_daily_shfe(date=date_str)
                    if not df.empty:
                        df['trade_date'] = current_date.strftime('%Y-%m-%d')
                        df['exchange'] = 'SHFE'
                        all_data.append(df)
                        self.logger.info(f"获取上期所数据成功: {date_str}")
                    
                    time.sleep(0.5)  # 避免请求过快
                    
                except Exception as e:
                    self.logger.warning(f"获取上期所数据失败 {date_str}: {e}")
                
                current_date += timedelta(days=1)
            
            if all_data:
                result_df = pd.concat(all_data, ignore_index=True)
                self.logger.info(f"上期所数据下载完成，共 {len(result_df)} 条记录")
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"下载上期所数据失败: {e}")
            return pd.DataFrame()
    
    def download_czce_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """下载郑州商品交易所数据"""
        try:
            self.logger.info(f"开始下载郑商所数据: {start_date} - {end_date}")
            
            all_data = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current_date <= end_date_obj:
                date_str = current_date.strftime('%Y%m%d')
                try:
                    # 获取当日数据
                    df = ak.futures_zh_daily_czce(date=date_str)
                    if not df.empty:
                        df['trade_date'] = current_date.strftime('%Y-%m-%d')
                        df['exchange'] = 'CZCE'
                        all_data.append(df)
                        self.logger.info(f"获取郑商所数据成功: {date_str}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"获取郑商所数据失败 {date_str}: {e}")
                
                current_date += timedelta(days=1)
            
            if all_data:
                result_df = pd.concat(all_data, ignore_index=True)
                self.logger.info(f"郑商所数据下载完成，共 {len(result_df)} 条记录")
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"下载郑商所数据失败: {e}")
            return pd.DataFrame()
    
    def download_dce_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """下载大连商品交易所数据"""
        try:
            self.logger.info(f"开始下载大商所数据: {start_date} - {end_date}")
            
            all_data = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current_date <= end_date_obj:
                date_str = current_date.strftime('%Y%m%d')
                try:
                    # 获取当日数据
                    df = ak.futures_zh_daily_dce(date=date_str)
                    if not df.empty:
                        df['trade_date'] = current_date.strftime('%Y-%m-%d')
                        df['exchange'] = 'DCE'
                        all_data.append(df)
                        self.logger.info(f"获取大商所数据成功: {date_str}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"获取大商所数据失败 {date_str}: {e}")
                
                current_date += timedelta(days=1)
            
            if all_data:
                result_df = pd.concat(all_data, ignore_index=True)
                self.logger.info(f"大商所数据下载完成，共 {len(result_df)} 条记录")
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"下载大商所数据失败: {e}")
            return pd.DataFrame()
    
    def download_gfex_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """下载广州期货交易所数据"""
        try:
            self.logger.info(f"开始下载广期所数据: {start_date} - {end_date}")
            
            # 由于广期所数据较少，可能需要手动处理或使用其他数据源
            # 这里提供一个基础框架
            all_data = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current_date <= end_date_obj:
                date_str = current_date.strftime('%Y%m%d')
                try:
                    # 广期所数据需要特殊处理，这里先提供框架
                    # 可以根据实际情况调整数据获取方式
                    pass
                    
                except Exception as e:
                    self.logger.warning(f"获取广期所数据失败 {date_str}: {e}")
                
                current_date += timedelta(days=1)
            
            if all_data:
                result_df = pd.concat(all_data, ignore_index=True)
                self.logger.info(f"广期所数据下载完成，共 {len(result_df)} 条记录")
                return result_df
            else:
                self.logger.warning("广期所数据暂无可用数据源")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"下载广期所数据失败: {e}")
            return pd.DataFrame()
    
    def download_cffex_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """下载中国金融期货交易所数据"""
        try:
            self.logger.info(f"开始下载中金所数据: {start_date} - {end_date}")
            
            all_data = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current_date <= end_date_obj:
                date_str = current_date.strftime('%Y%m%d')
                try:
                    # 获取当日数据
                    df = ak.futures_zh_daily_cffex(date=date_str)
                    if not df.empty:
                        df['trade_date'] = current_date.strftime('%Y-%m-%d')
                        df['exchange'] = 'CFFEX'
                        all_data.append(df)
                        self.logger.info(f"获取中金所数据成功: {date_str}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"获取中金所数据失败 {date_str}: {e}")
                
                current_date += timedelta(days=1)
            
            if all_data:
                result_df = pd.concat(all_data, ignore_index=True)
                self.logger.info(f"中金所数据下载完成，共 {len(result_df)} 条记录")
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"下载中金所数据失败: {e}")
            return pd.DataFrame()
    
    def download_all_exchanges_data(self, start_date: str, end_date: str, 
                                  exchanges: List[str] = None) -> Dict[str, pd.DataFrame]:
        """下载所有交易所数据"""
        if exchanges is None:
            exchanges = ['SHFE', 'CZCE', 'DCE', 'CFFEX']  # GFEX数据源不稳定，暂时排除
        
        results = {}
        
        for exchange in exchanges:
            try:
                if exchange == 'SHFE':
                    results[exchange] = self.download_shfe_data(start_date, end_date)
                elif exchange == 'CZCE':
                    results[exchange] = self.download_czce_data(start_date, end_date)
                elif exchange == 'DCE':
                    results[exchange] = self.download_dce_data(start_date, end_date)
                elif exchange == 'GFEX':
                    results[exchange] = self.download_gfex_data(start_date, end_date)
                elif exchange == 'CFFEX':
                    results[exchange] = self.download_cffex_data(start_date, end_date)
                else:
                    self.logger.warning(f"不支持的交易所: {exchange}")
                    
            except Exception as e:
                self.logger.error(f"下载{exchange}数据失败: {e}")
                results[exchange] = pd.DataFrame()
        
        return results
    
    def save_raw_data(self, data: Dict[str, pd.DataFrame], date_suffix: str = None):
        """保存原始数据到文件"""
        if date_suffix is None:
            date_suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for exchange, df in data.items():
            if not df.empty:
                filename = f"{exchange}_raw_{date_suffix}.csv"
                filepath = os.path.join(RAW_DATA_DIR, filename)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f"保存{exchange}原始数据到: {filepath}")
    
    def get_latest_trading_day(self) -> str:
        """获取最新交易日"""
        try:
            # 使用akshare获取最新交易日
            today = datetime.now()
            for i in range(10):  # 最多向前查找10天
                check_date = today - timedelta(days=i)
                date_str = check_date.strftime('%Y%m%d')
                
                try:
                    # 尝试获取当日数据来判断是否为交易日
                    df = ak.futures_zh_daily_shfe(date=date_str)
                    if not df.empty:
                        return check_date.strftime('%Y-%m-%d')
                except:
                    continue
            
            # 如果都获取不到，返回昨天
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
        except Exception as e:
            self.logger.error(f"获取最新交易日失败: {e}")
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    def download_specific_product(self, exchange: str, product: str, 
                                start_date: str, end_date: str) -> pd.DataFrame:
        """下载特定品种的数据"""
        try:
            # 下载整个交易所的数据，然后筛选特定品种
            if exchange == 'SHFE':
                data = self.download_shfe_data(start_date, end_date)
            elif exchange == 'CZCE':
                data = self.download_czce_data(start_date, end_date)
            elif exchange == 'DCE':
                data = self.download_dce_data(start_date, end_date)
            elif exchange == 'GFEX':
                data = self.download_gfex_data(start_date, end_date)
            elif exchange == 'CFFEX':
                data = self.download_cffex_data(start_date, end_date)
            else:
                self.logger.error(f"不支持的交易所: {exchange}")
                return pd.DataFrame()
            
            if not data.empty and 'symbol' in data.columns:
                # 筛选特定品种
                filtered_data = data[data['symbol'].str.contains(product, na=False)]
                return filtered_data
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"下载特定品种数据失败 {exchange}-{product}: {e}")
            return pd.DataFrame()

# 全局数据下载器实例
data_downloader = FuturesDataDownloader()