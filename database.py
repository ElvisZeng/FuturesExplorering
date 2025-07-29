"""
数据库连接和管理模块
"""
import psycopg2
from psycopg2 import pool, sql
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from config import DATABASE_CONFIG, FUTURES_TABLE_SCHEMA, CONTINUOUS_CONTRACT_TABLE_SCHEMA, FUNDAMENTALS_TABLE_SCHEMA
import os

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self):
        self.connection_pool = None
        self.logger = logging.getLogger(__name__)
        self._initialize_connection_pool()
    
    def _initialize_connection_pool(self):
        """初始化数据库连接池"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,  # 最小和最大连接数
                **DATABASE_CONFIG
            )
            self.logger.info("数据库连接池初始化成功")
        except Exception as e:
            self.logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            return self.connection_pool.getconn()
        except Exception as e:
            self.logger.error(f"获取数据库连接失败: {e}")
            raise
    
    def return_connection(self, connection):
        """归还数据库连接"""
        try:
            self.connection_pool.putconn(connection)
        except Exception as e:
            self.logger.error(f"归还数据库连接失败: {e}")
    
    def close_all_connections(self):
        """关闭所有数据库连接"""
        try:
            self.connection_pool.closeall()
            self.logger.info("所有数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接失败: {e}")
    
    def initialize_tables(self):
        """初始化数据库表"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # 创建期货日行情数据表
            cursor.execute(FUTURES_TABLE_SCHEMA)
            
            # 创建连续合约数据表
            cursor.execute(CONTINUOUS_CONTRACT_TABLE_SCHEMA)
            
            # 创建基本面数据表
            cursor.execute(FUNDAMENTALS_TABLE_SCHEMA)
            
            connection.commit()
            self.logger.info("数据库表初始化成功")
            
        except Exception as e:
            if connection:
                connection.rollback()
            self.logger.error(f"数据库表初始化失败: {e}")
            raise
        finally:
            if connection:
                cursor.close()
                self.return_connection(connection)
    
    def insert_futures_data(self, data: pd.DataFrame) -> bool:
        """插入期货日行情数据"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # 准备插入SQL
            insert_sql = """
            INSERT INTO futures_daily_data 
            (trade_date, exchange, product_code, contract_code, open_price, 
             high_price, low_price, close_price, settle_price, volume, 
             turnover, open_interest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trade_date, exchange, contract_code) 
            DO UPDATE SET 
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                settle_price = EXCLUDED.settle_price,
                volume = EXCLUDED.volume,
                turnover = EXCLUDED.turnover,
                open_interest = EXCLUDED.open_interest,
                updated_at = CURRENT_TIMESTAMP
            """
            
            # 批量插入数据
            data_tuples = []
            for _, row in data.iterrows():
                data_tuples.append((
                    row['trade_date'], row['exchange'], row['product_code'],
                    row['contract_code'], row['open_price'], row['high_price'],
                    row['low_price'], row['close_price'], row['settle_price'],
                    row['volume'], row['turnover'], row['open_interest']
                ))
            
            cursor.executemany(insert_sql, data_tuples)
            connection.commit()
            
            self.logger.info(f"成功插入 {len(data_tuples)} 条期货数据")
            return True
            
        except Exception as e:
            if connection:
                connection.rollback()
            self.logger.error(f"插入期货数据失败: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                self.return_connection(connection)
    
    def insert_continuous_contract_data(self, data: pd.DataFrame) -> bool:
        """插入连续合约数据"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            insert_sql = """
            INSERT INTO continuous_contracts 
            (trade_date, exchange, product_code, contract_type, open_price, 
             high_price, low_price, close_price, settle_price, volume, 
             turnover, open_interest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trade_date, exchange, product_code, contract_type) 
            DO UPDATE SET 
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                settle_price = EXCLUDED.settle_price,
                volume = EXCLUDED.volume,
                turnover = EXCLUDED.turnover,
                open_interest = EXCLUDED.open_interest,
                updated_at = CURRENT_TIMESTAMP
            """
            
            data_tuples = []
            for _, row in data.iterrows():
                data_tuples.append((
                    row['trade_date'], row['exchange'], row['product_code'],
                    row['contract_type'], row['open_price'], row['high_price'],
                    row['low_price'], row['close_price'], row['settle_price'],
                    row['volume'], row['turnover'], row['open_interest']
                ))
            
            cursor.executemany(insert_sql, data_tuples)
            connection.commit()
            
            self.logger.info(f"成功插入 {len(data_tuples)} 条连续合约数据")
            return True
            
        except Exception as e:
            if connection:
                connection.rollback()
            self.logger.error(f"插入连续合约数据失败: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                self.return_connection(connection)
    
    def insert_fundamentals_data(self, data: pd.DataFrame) -> bool:
        """插入基本面数据"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            insert_sql = """
            INSERT INTO fundamentals_data 
            (data_date, product_code, data_type, data_name, data_value, data_unit, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (data_date, product_code, data_type, data_name) 
            DO UPDATE SET 
                data_value = EXCLUDED.data_value,
                data_unit = EXCLUDED.data_unit,
                source = EXCLUDED.source
            """
            
            data_tuples = []
            for _, row in data.iterrows():
                data_tuples.append((
                    row['data_date'], row['product_code'], row['data_type'],
                    row['data_name'], row['data_value'], row['data_unit'], row['source']
                ))
            
            cursor.executemany(insert_sql, data_tuples)
            connection.commit()
            
            self.logger.info(f"成功插入 {len(data_tuples)} 条基本面数据")
            return True
            
        except Exception as e:
            if connection:
                connection.rollback()
            self.logger.error(f"插入基本面数据失败: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                self.return_connection(connection)
    
    def get_futures_data(self, exchange: str = None, product_code: str = None, 
                        start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取期货数据"""
        connection = None
        try:
            connection = self.get_connection()
            
            query = "SELECT * FROM futures_daily_data WHERE 1=1"
            params = []
            
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange)
            
            if product_code:
                query += " AND product_code = %s"
                params.append(product_code)
            
            if start_date:
                query += " AND trade_date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND trade_date <= %s"
                params.append(end_date)
            
            query += " ORDER BY trade_date, exchange, contract_code"
            
            df = pd.read_sql_query(query, connection, params=params)
            self.logger.info(f"获取到 {len(df)} 条期货数据")
            return df
            
        except Exception as e:
            self.logger.error(f"获取期货数据失败: {e}")
            return pd.DataFrame()
        finally:
            if connection:
                self.return_connection(connection)
    
    def get_continuous_contract_data(self, exchange: str = None, product_code: str = None,
                                   contract_type: str = None, start_date: str = None, 
                                   end_date: str = None) -> pd.DataFrame:
        """获取连续合约数据"""
        connection = None
        try:
            connection = self.get_connection()
            
            query = "SELECT * FROM continuous_contracts WHERE 1=1"
            params = []
            
            if exchange:
                query += " AND exchange = %s"
                params.append(exchange)
            
            if product_code:
                query += " AND product_code = %s"
                params.append(product_code)
            
            if contract_type:
                query += " AND contract_type = %s"
                params.append(contract_type)
            
            if start_date:
                query += " AND trade_date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND trade_date <= %s"
                params.append(end_date)
            
            query += " ORDER BY trade_date, exchange, product_code"
            
            df = pd.read_sql_query(query, connection, params=params)
            self.logger.info(f"获取到 {len(df)} 条连续合约数据")
            return df
            
        except Exception as e:
            self.logger.error(f"获取连续合约数据失败: {e}")
            return pd.DataFrame()
        finally:
            if connection:
                self.return_connection(connection)
    
    def get_available_products(self, exchange: str = None) -> List[str]:
        """获取可用的品种列表"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if exchange:
                cursor.execute(
                    "SELECT DISTINCT product_code FROM futures_daily_data WHERE exchange = %s ORDER BY product_code",
                    (exchange,)
                )
            else:
                cursor.execute("SELECT DISTINCT product_code FROM futures_daily_data ORDER BY product_code")
            
            products = [row[0] for row in cursor.fetchall()]
            return products
            
        except Exception as e:
            self.logger.error(f"获取产品列表失败: {e}")
            return []
        finally:
            if connection:
                cursor.close()
                self.return_connection(connection)
    
    def check_connection(self) -> bool:
        """检查数据库连接状态"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception as e:
            self.logger.error(f"数据库连接检查失败: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                self.return_connection(connection)

# 全局数据库管理器实例
db_manager = DatabaseManager()