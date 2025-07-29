"""
期货数据管理系统配置文件
"""
import os

# 数据库配置
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'futures_data'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# 期货交易所配置
EXCHANGES = {
    'SHFE': {  # 上海期货交易所
        'name': '上海期货交易所',
        'code': 'SHFE',
        'url': 'http://www.shfe.com.cn/',
        'data_url': 'http://www.shfe.com.cn/data/dailydata/',
        'products': ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AG', 'AU', 'RB', 'WR', 'HC', 'SS', 'FU', 'BU', 'RU', 'SP', 'SC', 'LU', 'NR', 'BC']
    },
    'CZCE': {  # 郑州商品交易所
        'name': '郑州商品交易所',
        'code': 'CZCE',
        'url': 'http://www.czce.com.cn/',
        'data_url': 'http://www.czce.com.cn/cn/DFSStaticFiles/Future/',
        'products': ['SR', 'CF', 'PF', 'OI', 'TA', 'MA', 'FG', 'SF', 'SM', 'RS', 'RM', 'JR', 'LR', 'PM', 'RI', 'WH', 'AP', 'CJ', 'UR', 'SA', 'ZC', 'TC', 'PK', 'ER']
    },
    'DCE': {  # 大连商品交易所
        'name': '大连商品交易所',
        'code': 'DCE',
        'url': 'http://www.dce.com.cn/',
        'data_url': 'http://www.dce.com.cn/publicweb/quotesdata/',
        'products': ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'FB', 'BB', 'JD', 'L', 'V', 'PP', 'J', 'JM', 'I', 'EG', 'EB', 'PG', 'RR', 'LH', 'C2']
    },
    'GFEX': {  # 广州期货交易所
        'name': '广州期货交易所',
        'code': 'GFEX',
        'url': 'http://www.gfex.com.cn/',
        'data_url': 'http://www.gfex.com.cn/gfex/rihq/',
        'products': ['SI']
    },
    'CFFEX': {  # 中国金融期货交易所
        'name': '中国金融期货交易所',
        'code': 'CFFEX',
        'url': 'http://www.cffex.com.cn/',
        'data_url': 'http://www.cffex.com.cn/sj/hqsj/rtj/',
        'products': ['IF', 'IC', 'IH', 'TS', 'TF', 'T']
    }
}

# 数据文件存储路径
DATA_DIR = './data'
RAW_DATA_DIR = './data/raw'
PROCESSED_DATA_DIR = './data/processed'
CSV_DATA_DIR = './data/csv'

# 数据表结构
FUTURES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS futures_daily_data (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    product_code VARCHAR(10) NOT NULL,
    contract_code VARCHAR(20) NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    settle_price DECIMAL(10,2),
    volume BIGINT,
    turnover DECIMAL(15,2),
    open_interest BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, exchange, contract_code)
);

CREATE INDEX IF NOT EXISTS idx_futures_date_exchange ON futures_daily_data(trade_date, exchange);
CREATE INDEX IF NOT EXISTS idx_futures_product ON futures_daily_data(product_code);
CREATE INDEX IF NOT EXISTS idx_futures_contract ON futures_daily_data(contract_code);
"""

CONTINUOUS_CONTRACT_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS continuous_contracts (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    product_code VARCHAR(10) NOT NULL,
    contract_type VARCHAR(20) NOT NULL, -- 'main' for 主力合约, 'weighted' for 加权合约
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    settle_price DECIMAL(10,2),
    volume BIGINT,
    turnover DECIMAL(15,2),
    open_interest BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, exchange, product_code, contract_type)
);

CREATE INDEX IF NOT EXISTS idx_continuous_date_product ON continuous_contracts(trade_date, product_code);
"""

FUNDAMENTALS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS fundamentals_data (
    id SERIAL PRIMARY KEY,
    data_date DATE NOT NULL,
    product_code VARCHAR(10) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data_name VARCHAR(100) NOT NULL,
    data_value DECIMAL(15,4),
    data_unit VARCHAR(20),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(data_date, product_code, data_type, data_name)
);

CREATE INDEX IF NOT EXISTS idx_fundamentals_date_product ON fundamentals_data(data_date, product_code);
"""

# GUI配置
GUI_CONFIG = {
    'window_title': '期货数据管理系统',
    'window_size': '1200x800',
    'theme': 'clam'
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': './logs/futures_system.log'
}