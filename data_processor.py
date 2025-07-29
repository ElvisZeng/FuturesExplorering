"""
数据处理模块
负责数据清洗、格式统一、主力合约和加权合约计算
"""
import pandas as pd
import numpy as np
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import os
from config import CSV_DATA_DIR, PROCESSED_DATA_DIR

class FuturesDataProcessor:
    """期货数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 确保目录存在
        os.makedirs(CSV_DATA_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        
        # 字段映射配置，统一不同交易所的字段名称
        self.field_mapping = {
            'SHFE': {
                'symbol': 'contract_code',
                'date': 'trade_date',
                'open': 'open_price',
                'high': 'high_price',
                'low': 'low_price',
                'close': 'close_price',
                'settle': 'settle_price',
                'volume': 'volume',
                'amount': 'turnover',
                'open_interest': 'open_interest'
            },
            'CZCE': {
                'symbol': 'contract_code',
                'date': 'trade_date',
                'open': 'open_price',
                'high': 'high_price',
                'low': 'low_price',
                'close': 'close_price',
                'settle': 'settle_price',
                'volume': 'volume',
                'amount': 'turnover',
                'open_interest': 'open_interest'
            },
            'DCE': {
                'symbol': 'contract_code',
                'date': 'trade_date',
                'open': 'open_price',
                'high': 'high_price',
                'low': 'low_price',
                'close': 'close_price',
                'settle': 'settle_price',
                'volume': 'volume',
                'amount': 'turnover',
                'open_interest': 'open_interest'
            },
            'CFFEX': {
                'symbol': 'contract_code',
                'date': 'trade_date',
                'open': 'open_price',
                'high': 'high_price',
                'low': 'low_price',
                'close': 'close_price',
                'settle': 'settle_price',
                'volume': 'volume',
                'amount': 'turnover',
                'open_interest': 'open_interest'
            }
        }
    
    def clean_and_standardize_data(self, data: pd.DataFrame, exchange: str) -> pd.DataFrame:
        """清洗和标准化数据"""
        try:
            if data.empty:
                return pd.DataFrame()
            
            self.logger.info(f"开始清洗{exchange}数据，原始数据 {len(data)} 条")
            
            # 复制数据避免修改原始数据
            df = data.copy()
            
            # 重命名字段
            if exchange in self.field_mapping:
                df = self._rename_columns(df, exchange)
            
            # 提取产品代码
            df['product_code'] = df['contract_code'].apply(self._extract_product_code)
            
            # 确保必要字段存在
            required_fields = ['trade_date', 'exchange', 'product_code', 'contract_code']
            for field in required_fields:
                if field not in df.columns:
                    if field == 'exchange':
                        df[field] = exchange
                    else:
                        self.logger.warning(f"缺少必要字段: {field}")
                        return pd.DataFrame()
            
            # 数据类型转换和清洗
            df = self._clean_numeric_fields(df)
            df = self._clean_date_fields(df)
            
            # 过滤无效数据
            df = self._filter_invalid_data(df)
            
            # 按日期和合约排序
            df = df.sort_values(['trade_date', 'contract_code']).reset_index(drop=True)
            
            self.logger.info(f"{exchange}数据清洗完成，处理后数据 {len(df)} 条")
            return df
            
        except Exception as e:
            self.logger.error(f"清洗{exchange}数据失败: {e}")
            return pd.DataFrame()
    
    def _rename_columns(self, df: pd.DataFrame, exchange: str) -> pd.DataFrame:
        """重命名列"""
        mapping = self.field_mapping.get(exchange, {})
        
        # 创建反向映射
        rename_dict = {}
        for original_name, standard_name in mapping.items():
            if original_name in df.columns:
                rename_dict[original_name] = standard_name
        
        return df.rename(columns=rename_dict)
    
    def _extract_product_code(self, contract_code: str) -> str:
        """从合约代码中提取产品代码"""
        if pd.isna(contract_code):
            return ''
        
        # 使用正则表达式提取产品代码（字母部分）
        match = re.match(r'([A-Za-z]+)', str(contract_code))
        if match:
            return match.group(1).upper()
        else:
            return ''
    
    def _clean_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数值字段"""
        numeric_fields = ['open_price', 'high_price', 'low_price', 'close_price', 
                         'settle_price', 'volume', 'turnover', 'open_interest']
        
        for field in numeric_fields:
            if field in df.columns:
                # 转换为数值类型
                df[field] = pd.to_numeric(df[field], errors='coerce')
                
                # 处理异常值
                if field in ['open_price', 'high_price', 'low_price', 'close_price', 'settle_price']:
                    # 价格字段：小于等于0的设为NaN
                    df.loc[df[field] <= 0, field] = np.nan
                elif field in ['volume', 'open_interest']:
                    # 成交量和持仓量：小于0的设为0
                    df.loc[df[field] < 0, field] = 0
                elif field == 'turnover':
                    # 成交额：小于0的设为0
                    df.loc[df[field] < 0, field] = 0
        
        return df
    
    def _clean_date_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗日期字段"""
        if 'trade_date' in df.columns:
            # 转换日期格式
            df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
            # 过滤无效日期
            df = df.dropna(subset=['trade_date'])
            # 转换为字符串格式
            df['trade_date'] = df['trade_date'].dt.strftime('%Y-%m-%d')
        
        return df
    
    def _filter_invalid_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤无效数据"""
        # 过滤空的合约代码
        df = df.dropna(subset=['contract_code'])
        df = df[df['contract_code'] != '']
        
        # 过滤空的产品代码
        df = df[df['product_code'] != '']
        
        # 过滤全部价格为NaN的记录
        price_fields = ['open_price', 'high_price', 'low_price', 'close_price']
        available_price_fields = [f for f in price_fields if f in df.columns]
        if available_price_fields:
            df = df.dropna(subset=available_price_fields, how='all')
        
        return df
    
    def calculate_main_contract(self, df: pd.DataFrame, method: str = 'volume') -> pd.DataFrame:
        """计算主力合约数据"""
        try:
            self.logger.info(f"开始计算主力合约数据，方法: {method}")
            
            if df.empty:
                return pd.DataFrame()
            
            main_contracts = []
            
            # 按交易日期和产品分组
            for (date, exchange, product), group in df.groupby(['trade_date', 'exchange', 'product_code']):
                if method == 'volume':
                    # 按成交量选择主力合约
                    main_contract = group.loc[group['volume'].idxmax()]
                elif method == 'open_interest':
                    # 按持仓量选择主力合约
                    main_contract = group.loc[group['open_interest'].idxmax()]
                else:
                    # 默认按成交量
                    main_contract = group.loc[group['volume'].idxmax()]
                
                main_contract_data = {
                    'trade_date': date,
                    'exchange': exchange,
                    'product_code': product,
                    'contract_type': 'main',
                    'open_price': main_contract['open_price'],
                    'high_price': main_contract['high_price'],
                    'low_price': main_contract['low_price'],
                    'close_price': main_contract['close_price'],
                    'settle_price': main_contract['settle_price'],
                    'volume': main_contract['volume'],
                    'turnover': main_contract['turnover'],
                    'open_interest': main_contract['open_interest']
                }
                
                main_contracts.append(main_contract_data)
            
            result_df = pd.DataFrame(main_contracts)
            self.logger.info(f"主力合约计算完成，共 {len(result_df)} 条记录")
            return result_df
            
        except Exception as e:
            self.logger.error(f"计算主力合约失败: {e}")
            return pd.DataFrame()
    
    def calculate_weighted_contract(self, df: pd.DataFrame, 
                                  weight_field: str = 'volume') -> pd.DataFrame:
        """计算加权合约数据"""
        try:
            self.logger.info(f"开始计算加权合约数据，权重字段: {weight_field}")
            
            if df.empty:
                return pd.DataFrame()
            
            weighted_contracts = []
            
            # 按交易日期和产品分组
            for (date, exchange, product), group in df.groupby(['trade_date', 'exchange', 'product_code']):
                # 过滤掉权重为0或NaN的记录
                valid_group = group.dropna(subset=[weight_field])
                valid_group = valid_group[valid_group[weight_field] > 0]
                
                if valid_group.empty:
                    continue
                
                # 计算权重
                total_weight = valid_group[weight_field].sum()
                weights = valid_group[weight_field] / total_weight
                
                # 计算加权价格
                weighted_data = {
                    'trade_date': date,
                    'exchange': exchange,
                    'product_code': product,
                    'contract_type': 'weighted',
                    'open_price': (valid_group['open_price'] * weights).sum(),
                    'high_price': (valid_group['high_price'] * weights).sum(),
                    'low_price': (valid_group['low_price'] * weights).sum(),
                    'close_price': (valid_group['close_price'] * weights).sum(),
                    'settle_price': (valid_group['settle_price'] * weights).sum(),
                    'volume': valid_group['volume'].sum(),
                    'turnover': valid_group['turnover'].sum(),
                    'open_interest': valid_group['open_interest'].sum()
                }
                
                weighted_contracts.append(weighted_data)
            
            result_df = pd.DataFrame(weighted_contracts)
            self.logger.info(f"加权合约计算完成，共 {len(result_df)} 条记录")
            return result_df
            
        except Exception as e:
            self.logger.error(f"计算加权合约失败: {e}")
            return pd.DataFrame()
    
    def process_all_exchanges_data(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """处理所有交易所数据"""
        processed_data = {}
        
        for exchange, df in raw_data.items():
            try:
                # 清洗和标准化数据
                cleaned_df = self.clean_and_standardize_data(df, exchange)
                
                if not cleaned_df.empty:
                    processed_data[exchange] = cleaned_df
                    self.logger.info(f"{exchange}数据处理完成")
                else:
                    self.logger.warning(f"{exchange}数据处理后为空")
                    
            except Exception as e:
                self.logger.error(f"处理{exchange}数据失败: {e}")
        
        return processed_data
    
    def save_to_csv(self, data: pd.DataFrame, filename: str, 
                   directory: str = None) -> bool:
        """保存数据到CSV文件"""
        try:
            if directory is None:
                directory = CSV_DATA_DIR
            
            filepath = os.path.join(directory, filename)
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f"数据已保存到: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存CSV文件失败: {e}")
            return False
    
    def merge_all_exchanges(self, processed_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """合并所有交易所的数据"""
        try:
            all_data = []
            
            for exchange, df in processed_data.items():
                if not df.empty:
                    all_data.append(df)
            
            if all_data:
                merged_df = pd.concat(all_data, ignore_index=True)
                merged_df = merged_df.sort_values(['trade_date', 'exchange', 'product_code', 'contract_code'])
                merged_df = merged_df.reset_index(drop=True)
                
                self.logger.info(f"合并完成，总计 {len(merged_df)} 条记录")
                return merged_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"合并数据失败: {e}")
            return pd.DataFrame()
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """验证数据质量"""
        quality_report = {
            'total_records': len(df),
            'missing_data': {},
            'data_ranges': {},
            'duplicates': 0,
            'errors': []
        }
        
        try:
            if df.empty:
                quality_report['errors'].append("数据集为空")
                return quality_report
            
            # 检查重复数据
            duplicates = df.duplicated(subset=['trade_date', 'exchange', 'contract_code']).sum()
            quality_report['duplicates'] = duplicates
            
            # 检查缺失数据
            for col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    quality_report['missing_data'][col] = missing_count
            
            # 检查数据范围
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if not df[col].empty:
                    quality_report['data_ranges'][col] = {
                        'min': df[col].min(),
                        'max': df[col].max(),
                        'mean': df[col].mean()
                    }
            
            # 检查逻辑错误
            if 'high_price' in df.columns and 'low_price' in df.columns:
                invalid_high_low = (df['high_price'] < df['low_price']).sum()
                if invalid_high_low > 0:
                    quality_report['errors'].append(f"发现 {invalid_high_low} 条高价低于低价的记录")
            
            self.logger.info("数据质量验证完成")
            
        except Exception as e:
            self.logger.error(f"数据质量验证失败: {e}")
            quality_report['errors'].append(f"验证过程出错: {e}")
        
        return quality_report
    
    def create_continuous_contracts(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建连续合约数据（包括主力合约和加权合约）"""
        try:
            self.logger.info("开始创建连续合约数据")
            
            if df.empty:
                return pd.DataFrame()
            
            all_continuous = []
            
            # 计算主力合约
            main_contracts = self.calculate_main_contract(df, method='volume')
            if not main_contracts.empty:
                all_continuous.append(main_contracts)
            
            # 计算加权合约
            weighted_contracts = self.calculate_weighted_contract(df, weight_field='volume')
            if not weighted_contracts.empty:
                all_continuous.append(weighted_contracts)
            
            if all_continuous:
                result_df = pd.concat(all_continuous, ignore_index=True)
                result_df = result_df.sort_values(['trade_date', 'exchange', 'product_code', 'contract_type'])
                result_df = result_df.reset_index(drop=True)
                
                self.logger.info(f"连续合约数据创建完成，共 {len(result_df)} 条记录")
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"创建连续合约数据失败: {e}")
            return pd.DataFrame()

# 全局数据处理器实例
data_processor = FuturesDataProcessor()