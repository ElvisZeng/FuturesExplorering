"""
数据上传模块
支持批量上传历史数据文件和数据验证
"""
import pandas as pd
import numpy as np
import logging
import os
import zipfile
import glob
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import chardet
from database import db_manager
from data_processor import data_processor
from config import CSV_DATA_DIR, RAW_DATA_DIR

class DataUploader:
    """数据上传器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.txt']
        self.encoding_options = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030']
        
    def detect_file_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 读取前10KB检测编码
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                
                self.logger.info(f"检测到文件编码: {encoding}, 置信度: {confidence:.2f}")
                
                # 如果置信度低于0.7，尝试常用编码
                if confidence < 0.7:
                    for enc in self.encoding_options:
                        try:
                            with open(file_path, 'r', encoding=enc) as test_file:
                                test_file.read(1000)
                            return enc
                        except:
                            continue
                
                return encoding if encoding else 'utf-8'
                
        except Exception as e:
            self.logger.warning(f"编码检测失败: {e}, 使用默认编码utf-8")
            return 'utf-8'
    
    def read_file(self, file_path: str) -> pd.DataFrame:
        """读取文件"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv' or file_ext == '.txt':
                # 检测编码
                encoding = self.detect_file_encoding(file_path)
                
                # 尝试不同的分隔符
                separators = [',', '\t', ';', '|']
                for sep in separators:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                        if len(df.columns) > 1:  # 至少有2列才认为分隔符正确
                            self.logger.info(f"成功读取文件: {file_path}, 分隔符: {sep}")
                            return df
                    except:
                        continue
                
                # 如果都失败，使用默认逗号分隔符
                df = pd.read_csv(file_path, encoding=encoding)
                
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
            
            self.logger.info(f"文件读取成功: {file_path}, 数据形状: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            return pd.DataFrame()
    
    def validate_data_format(self, df: pd.DataFrame, file_path: str) -> Dict:
        """验证数据格式"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'detected_columns': {},
            'data_summary': {}
        }
        
        try:
            if df.empty:
                validation_result['errors'].append("数据文件为空")
                return validation_result
            
            # 检测可能的列名映射
            column_mappings = {
                'date': ['date', 'datetime', 'time', '日期', '时间', 'trade_date', 'trading_date'],
                'open': ['open', 'o', '开盘', '开盘价', 'open_price'],
                'high': ['high', 'h', '最高', '最高价', 'high_price'],
                'low': ['low', 'l', '最低', '最低价', 'low_price'],
                'close': ['close', 'c', '收盘', '收盘价', 'close_price'],
                'volume': ['volume', 'vol', 'v', '成交量', '量', 'trade_volume'],
                'amount': ['amount', 'turnover', '成交额', '金额', 'trade_amount'],
                'settlement': ['settlement', 'settle', '结算', '结算价', 'settle_price'],
                'open_interest': ['open_interest', 'oi', '持仓量', 'position']
            }
            
            detected_columns = {}
            df_columns_lower = [col.lower() for col in df.columns]
            
            for standard_name, possible_names in column_mappings.items():
                for col in df.columns:
                    if col.lower() in possible_names or any(name in col.lower() for name in possible_names):
                        detected_columns[standard_name] = col
                        break
            
            validation_result['detected_columns'] = detected_columns
            
            # 必需字段检查
            required_fields = ['date', 'close']
            missing_required = []
            for field in required_fields:
                if field not in detected_columns:
                    missing_required.append(field)
            
            if missing_required:
                validation_result['errors'].append(f"缺少必需字段: {missing_required}")
            
            # 推荐字段检查
            recommended_fields = ['open', 'high', 'low', 'volume']
            missing_recommended = []
            for field in recommended_fields:
                if field not in detected_columns:
                    missing_recommended.append(field)
            
            if missing_recommended:
                validation_result['warnings'].append(f"缺少推荐字段: {missing_recommended}")
            
            # 数据类型验证
            if 'date' in detected_columns:
                date_col = detected_columns['date']
                try:
                    pd.to_datetime(df[date_col])
                except:
                    validation_result['errors'].append(f"日期列 '{date_col}' 格式无法识别")
            
            # 数值字段验证
            numeric_fields = ['open', 'high', 'low', 'close', 'volume', 'amount', 'settlement']
            for field in numeric_fields:
                if field in detected_columns:
                    col = detected_columns[field]
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        try:
                            pd.to_numeric(df[col], errors='coerce')
                        except:
                            validation_result['warnings'].append(f"数值列 '{col}' 包含非数值数据")
            
            # 逻辑验证
            if all(field in detected_columns for field in ['open', 'high', 'low', 'close']):
                # 检查OHLC逻辑
                o_col = detected_columns['open']
                h_col = detected_columns['high']
                l_col = detected_columns['low']
                c_col = detected_columns['close']
                
                # 转换为数值类型
                for col in [o_col, h_col, l_col, c_col]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 检查高价是否为最高
                invalid_high = ((df[h_col] < df[o_col]) | 
                              (df[h_col] < df[l_col]) | 
                              (df[h_col] < df[c_col])).sum()
                
                # 检查低价是否为最低
                invalid_low = ((df[l_col] > df[o_col]) | 
                             (df[l_col] > df[h_col]) | 
                             (df[l_col] > df[c_col])).sum()
                
                if invalid_high > 0:
                    validation_result['warnings'].append(f"发现 {invalid_high} 条记录的最高价小于其他价格")
                
                if invalid_low > 0:
                    validation_result['warnings'].append(f"发现 {invalid_low} 条记录的最低价大于其他价格")
            
            # 数据完整性检查
            total_rows = len(df)
            missing_data_summary = {}
            
            for field, col in detected_columns.items():
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    missing_data_summary[field] = missing_count
                    missing_pct = missing_count / total_rows * 100
                    if missing_pct > 10:
                        validation_result['warnings'].append(
                            f"字段 '{field}' 缺失数据过多: {missing_count} 条 ({missing_pct:.1f}%)"
                        )
            
            # 数据摘要
            validation_result['data_summary'] = {
                'total_rows': total_rows,
                'columns_count': len(df.columns),
                'detected_fields_count': len(detected_columns),
                'missing_data': missing_data_summary,
                'date_range': None
            }
            
            # 获取日期范围
            if 'date' in detected_columns:
                try:
                    date_series = pd.to_datetime(df[detected_columns['date']])
                    validation_result['data_summary']['date_range'] = {
                        'start': date_series.min().strftime('%Y-%m-%d'),
                        'end': date_series.max().strftime('%Y-%m-%d'),
                        'days': (date_series.max() - date_series.min()).days
                    }
                except:
                    pass
            
            # 数据质量建议
            if missing_recommended:
                validation_result['suggestions'].append("建议补充 OHLC 和成交量数据以获得更好的分析效果")
            
            if 'volume' not in detected_columns:
                validation_result['suggestions'].append("建议添加成交量数据，这对于维科夫分析很重要")
            
            # 最终验证结果
            validation_result['is_valid'] = len(validation_result['errors']) == 0
            
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"数据验证过程出错: {e}")
            self.logger.error(f"数据验证失败: {e}")
            return validation_result
    
    def standardize_data(self, df: pd.DataFrame, detected_columns: Dict[str, str],
                        symbol: str, exchange: str) -> pd.DataFrame:
        """标准化数据格式"""
        try:
            standardized_df = pd.DataFrame()
            
            # 标准化日期
            if 'date' in detected_columns:
                date_col = detected_columns['date']
                standardized_df['trade_date'] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
            
            # 添加交易所和产品信息
            standardized_df['exchange'] = exchange
            standardized_df['contract_code'] = symbol
            
            # 提取产品代码（从合约代码中提取字母部分）
            import re
            match = re.match(r'([A-Za-z]+)', symbol)
            product_code = match.group(1).upper() if match else symbol[:2].upper()
            standardized_df['product_code'] = product_code
            
            # 标准化价格数据
            price_mappings = {
                'open_price': 'open',
                'high_price': 'high', 
                'low_price': 'low',
                'close_price': 'close',
                'settle_price': 'settlement'
            }
            
            for standard_col, detected_key in price_mappings.items():
                if detected_key in detected_columns:
                    col = detected_columns[detected_key]
                    standardized_df[standard_col] = pd.to_numeric(df[col], errors='coerce')
            
            # 标准化成交量和成交额
            if 'volume' in detected_columns:
                vol_col = detected_columns['volume']
                standardized_df['volume'] = pd.to_numeric(df[vol_col], errors='coerce').fillna(0)
            else:
                standardized_df['volume'] = 0
            
            if 'amount' in detected_columns:
                amt_col = detected_columns['amount']
                standardized_df['turnover'] = pd.to_numeric(df[amt_col], errors='coerce').fillna(0)
            else:
                standardized_df['turnover'] = 0
            
            if 'open_interest' in detected_columns:
                oi_col = detected_columns['open_interest']
                standardized_df['open_interest'] = pd.to_numeric(df[oi_col], errors='coerce').fillna(0)
            else:
                standardized_df['open_interest'] = 0
            
            # 如果缺少某些价格数据，尝试用其他价格填充
            if 'open_price' not in standardized_df.columns and 'close_price' in standardized_df.columns:
                standardized_df['open_price'] = standardized_df['close_price']
            
            for price_col in ['high_price', 'low_price']:
                if price_col not in standardized_df.columns and 'close_price' in standardized_df.columns:
                    standardized_df[price_col] = standardized_df['close_price']
            
            # 删除空行
            standardized_df = standardized_df.dropna(subset=['trade_date', 'close_price'])
            
            # 按日期排序
            standardized_df = standardized_df.sort_values('trade_date').reset_index(drop=True)
            
            self.logger.info(f"数据标准化完成: {len(standardized_df)} 条记录")
            return standardized_df
            
        except Exception as e:
            self.logger.error(f"数据标准化失败: {e}")
            return pd.DataFrame()
    
    def upload_file(self, file_path: str, symbol: str, exchange: str) -> Dict:
        """上传单个文件"""
        result = {
            'success': False,
            'file_path': file_path,
            'symbol': symbol,
            'exchange': exchange,
            'message': '',
            'validation': {},
            'imported_records': 0
        }
        
        try:
            self.logger.info(f"开始上传文件: {file_path}")
            
            # 读取文件
            df = self.read_file(file_path)
            if df.empty:
                result['message'] = "文件为空或读取失败"
                return result
            
            # 验证数据格式
            validation = self.validate_data_format(df, file_path)
            result['validation'] = validation
            
            if not validation['is_valid']:
                result['message'] = f"数据验证失败: {'; '.join(validation['errors'])}"
                return result
            
            # 标准化数据
            standardized_data = self.standardize_data(
                df, validation['detected_columns'], symbol, exchange
            )
            
            if standardized_data.empty:
                result['message'] = "数据标准化失败"
                return result
            
            # 导入数据库
            success = db_manager.insert_futures_data(standardized_data)
            
            if success:
                result['success'] = True
                result['imported_records'] = len(standardized_data)
                result['message'] = f"成功导入 {len(standardized_data)} 条记录"
                
                # 保存处理后的CSV文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_filename = f"{exchange}_{symbol}_uploaded_{timestamp}.csv"
                csv_path = os.path.join(CSV_DATA_DIR, csv_filename)
                standardized_data.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
            else:
                result['message'] = "数据库导入失败"
            
            return result
            
        except Exception as e:
            result['message'] = f"上传失败: {e}"
            self.logger.error(f"文件上传失败: {e}")
            return result
    
    def batch_upload_directory(self, directory_path: str, 
                              default_exchange: str = None) -> Dict:
        """批量上传目录中的文件"""
        results = {
            'total_files': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'total_records': 0,
            'file_results': [],
            'summary': {}
        }
        
        try:
            if not os.path.exists(directory_path):
                results['summary']['error'] = "目录不存在"
                return results
            
            # 查找所有支持的文件
            files_found = []
            for ext in self.supported_formats:
                pattern = os.path.join(directory_path, f"*{ext}")
                files_found.extend(glob.glob(pattern))
            
            results['total_files'] = len(files_found)
            
            if results['total_files'] == 0:
                results['summary']['warning'] = "目录中未找到支持的数据文件"
                return results
            
            self.logger.info(f"找到 {results['total_files']} 个文件待上传")
            
            # 逐个处理文件
            for file_path in files_found:
                filename = os.path.basename(file_path)
                
                # 尝试从文件名推断合约和交易所信息
                symbol, exchange = self._extract_symbol_exchange_from_filename(
                    filename, default_exchange
                )
                
                if not symbol:
                    self.logger.warning(f"无法从文件名推断合约信息: {filename}")
                    symbol = os.path.splitext(filename)[0]
                
                if not exchange:
                    exchange = default_exchange or 'UNKNOWN'
                
                # 上传文件
                upload_result = self.upload_file(file_path, symbol, exchange)
                results['file_results'].append(upload_result)
                
                if upload_result['success']:
                    results['successful_uploads'] += 1
                    results['total_records'] += upload_result['imported_records']
                else:
                    results['failed_uploads'] += 1
            
            # 生成摘要
            results['summary'] = {
                'success_rate': results['successful_uploads'] / results['total_files'] * 100,
                'total_records_imported': results['total_records'],
                'message': f"批量上传完成: {results['successful_uploads']}/{results['total_files']} 文件成功"
            }
            
            return results
            
        except Exception as e:
            results['summary']['error'] = f"批量上传失败: {e}"
            self.logger.error(f"批量上传失败: {e}")
            return results
    
    def _extract_symbol_exchange_from_filename(self, filename: str, 
                                             default_exchange: str = None) -> Tuple[str, str]:
        """从文件名中提取合约和交易所信息"""
        try:
            # 移除文件扩展名
            name_without_ext = os.path.splitext(filename)[0]
            
            # 常见的文件名模式
            patterns = [
                r'([A-Z]+)(\d+)',  # 如 CU2024
                r'([a-z]+)(\d+)',  # 如 cu2024
                r'([A-Z]+)_(\d+)', # 如 CU_2024
                r'([A-Z]+)-(\d+)', # 如 CU-2024
            ]
            
            symbol = None
            exchange = default_exchange
            
            for pattern in patterns:
                import re
                match = re.search(pattern, name_without_ext)
                if match:
                    product = match.group(1).upper()
                    contract_month = match.group(2)
                    symbol = f"{product}{contract_month}"
                    
                    # 根据产品代码推断交易所
                    if not exchange:
                        exchange = self._infer_exchange_from_product(product)
                    
                    break
            
            if not symbol:
                # 如果匹配不到，使用文件名作为合约代码
                symbol = name_without_ext.upper()
            
            return symbol, exchange
            
        except Exception as e:
            self.logger.warning(f"解析文件名失败: {e}")
            return None, default_exchange
    
    def _infer_exchange_from_product(self, product_code: str) -> str:
        """根据产品代码推断交易所"""
        from config import EXCHANGES
        
        for exchange_code, exchange_info in EXCHANGES.items():
            if product_code in exchange_info.get('products', []):
                return exchange_code
        
        return 'UNKNOWN'
    
    def extract_and_upload_zip(self, zip_path: str, default_exchange: str = None) -> Dict:
        """解压并上传ZIP文件"""
        try:
            # 创建临时解压目录
            extract_dir = os.path.join(RAW_DATA_DIR, 'temp_extract')
            os.makedirs(extract_dir, exist_ok=True)
            
            # 解压文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.logger.info(f"ZIP文件解压完成: {zip_path}")
            
            # 批量上传解压后的文件
            result = self.batch_upload_directory(extract_dir, default_exchange)
            
            # 清理临时文件
            import shutil
            shutil.rmtree(extract_dir, ignore_errors=True)
            
            return result
            
        except Exception as e:
            self.logger.error(f"ZIP文件处理失败: {e}")
            return {
                'total_files': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'total_records': 0,
                'file_results': [],
                'summary': {'error': f"ZIP文件处理失败: {e}"}
            }

# 全局数据上传器实例
data_uploader = DataUploader()