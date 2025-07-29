# 期货数据管理系统

一个功能完整的期货数据管理和分析系统，支持从中国各大期货交易所下载历史数据、数据清洗处理、数据库存储、图表展示和自动化更新。

## 主要功能

### 1. 数据下载与管理
- **多交易所支持**: 支持上海期货交易所(SHFE)、郑州商品交易所(CZCE)、大连商品交易所(DCE)、中国金融期货交易所(CFFEX)、广州期货交易所(GFEX)
- **历史数据下载**: 可下载指定日期范围的历史数据
- **数据格式统一**: 自动将不同交易所的数据格式统一为标准CSV格式
- **数据质量控制**: 内置数据清洗和验证功能

### 2. 数据库管理
- **PostgreSQL存储**: 使用PostgreSQL数据库存储期货数据
- **数据导入导出**: 支持CSV文件与数据库之间的双向数据传输
- **连续合约生成**: 自动计算主力合约和加权合约数据
- **基本面数据扩展**: 预留基本面数据导入接口

### 3. 自动化更新
- **定时更新**: 支持每个交易日自动更新最新数据
- **增量更新**: 智能识别新数据，避免重复下载
- **错误处理**: 完善的异常处理和日志记录

### 4. 图形化界面
- **现代化UI**: 基于tkinter和ttkthemes的美观界面
- **多标签页设计**: 数据管理、图表显示、系统设置分离
- **实时状态更新**: 显示操作进度和系统状态

### 5. 数据可视化
- **K线图**: 支持OHLC蜡烛图显示
- **价格走势图**: 收盘价线图展示
- **成交量图**: 成交量柱状图分析
- **交互式图表**: 支持日期范围选择和品种切换

## 系统架构

```
期货数据管理系统/
├── main.py              # 主启动文件
├── config.py            # 配置文件
├── database.py          # 数据库管理模块
├── data_downloader.py   # 数据下载模块
├── data_processor.py    # 数据处理模块
├── data_manager.py      # 数据管理模块
├── gui.py              # 图形界面模块
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明
├── data/               # 数据目录
│   ├── raw/           # 原始数据
│   ├── processed/     # 处理后数据
│   └── csv/           # CSV文件
└── logs/              # 日志文件
```

## 安装配置

### 1. 环境要求
- Python 3.8+
- PostgreSQL 12+
- 操作系统: Windows/Linux/macOS

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 数据库配置
#### 创建数据库
```sql
CREATE DATABASE futures_data;
CREATE USER futures_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE futures_data TO futures_user;
```

#### 环境变量配置（可选）
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=futures_data
export DB_USER=futures_user
export DB_PASSWORD=your_password
```

### 4. 启动程序
```bash
python main.py
```

## 使用指南

### 数据管理操作

#### 1. 下载历史数据
1. 切换到"数据管理"标签页
2. 选择开始和结束日期
3. 选择交易所（可选择"全部"）
4. 点击"下载数据"按钮
5. 系统会自动下载、处理并导入数据库

#### 2. CSV文件导入
1. 点击"选择CSV文件"按钮
2. 选择格式正确的CSV文件
3. 系统会验证数据格式并导入数据库

#### 3. 定时更新设置
1. 在"系统设置"中设置更新时间
2. 点击"启动定时更新"
3. 系统会在每个交易日自动更新数据

### 图表分析操作

#### 1. 查看价格走势
1. 切换到"数据图表"标签页
2. 选择交易所和品种
3. 选择合约类型（主力合约/加权合约）
4. 设置日期范围
5. 选择图表类型
6. 点击"显示图表"

#### 2. 数据导出
1. 在数据管理页面点击"导出数据"
2. 选择保存位置和文件名
3. 数据将以CSV格式导出

## 数据表结构

### 期货日行情数据表 (futures_daily_data)
| 字段 | 类型 | 说明 |
|------|------|------|
| trade_date | DATE | 交易日期 |
| exchange | VARCHAR(10) | 交易所代码 |
| product_code | VARCHAR(10) | 品种代码 |
| contract_code | VARCHAR(20) | 合约代码 |
| open_price | DECIMAL(10,2) | 开盘价 |
| high_price | DECIMAL(10,2) | 最高价 |
| low_price | DECIMAL(10,2) | 最低价 |
| close_price | DECIMAL(10,2) | 收盘价 |
| settle_price | DECIMAL(10,2) | 结算价 |
| volume | BIGINT | 成交量 |
| turnover | DECIMAL(15,2) | 成交额 |
| open_interest | BIGINT | 持仓量 |

### 连续合约数据表 (continuous_contracts)
| 字段 | 类型 | 说明 |
|------|------|------|
| trade_date | DATE | 交易日期 |
| exchange | VARCHAR(10) | 交易所代码 |
| product_code | VARCHAR(10) | 品种代码 |
| contract_type | VARCHAR(20) | 合约类型 (main/weighted) |
| 价格字段 | DECIMAL(10,2) | 同期货日行情表 |

### 基本面数据表 (fundamentals_data)
| 字段 | 类型 | 说明 |
|------|------|------|
| data_date | DATE | 数据日期 |
| product_code | VARCHAR(10) | 品种代码 |
| data_type | VARCHAR(50) | 数据类型 |
| data_name | VARCHAR(100) | 数据名称 |
| data_value | DECIMAL(15,4) | 数据值 |
| data_unit | VARCHAR(20) | 数据单位 |
| source | VARCHAR(50) | 数据来源 |

## 配置说明

### 数据库配置 (config.py)
```python
DATABASE_CONFIG = {
    'host': 'localhost',      # 数据库主机
    'port': '5432',          # 数据库端口
    'database': 'futures_data', # 数据库名称
    'user': 'postgres',       # 用户名
    'password': 'password'    # 密码
}
```

### 交易所配置
系统支持的交易所及其产品代码都在`config.py`中的`EXCHANGES`配置中定义，可根据需要进行调整。

## 扩展开发

### 添加新的数据源
1. 在`data_downloader.py`中添加新的下载方法
2. 在`data_processor.py`中添加对应的数据处理逻辑
3. 更新`config.py`中的交易所配置

### 添加新的图表类型
1. 在`gui.py`的图表相关方法中添加新的绘图函数
2. 更新图表类型选择列表

### 自定义数据处理
可以在`data_processor.py`中修改数据清洗和处理逻辑，以适应特定的数据质量要求。

## 注意事项

### 1. 网络连接
- 数据下载需要稳定的网络连接
- 某些数据源可能有访问频率限制

### 2. 数据准确性
- 系统提供的数据仅供参考，不构成投资建议
- 建议对重要数据进行人工核验

### 3. 性能优化
- 大量历史数据下载可能需要较长时间
- 建议分批次下载大量数据

### 4. 数据备份
- 定期备份PostgreSQL数据库
- 重要的CSV文件也应进行备份

## 故障排除

### 常见问题

#### 1. 数据库连接失败
- 检查PostgreSQL服务是否运行
- 验证数据库配置信息
- 确认网络连接正常

#### 2. 数据下载失败
- 检查网络连接
- 确认数据源可访问
- 查看日志文件了解详细错误

#### 3. 图表显示异常
- 确认已安装matplotlib依赖
- 检查数据是否存在
- 验证日期范围设置

### 日志文件
系统日志保存在`logs/futures_system.log`中，包含详细的操作记录和错误信息。

## 技术支持

如遇到技术问题或需要功能扩展，请查看系统日志并联系开发团队。

## 许可证

本项目仅供学习和研究使用。使用本系统进行实际交易决策风险自负。

---

**版本**: 1.0.0  
**更新日期**: 2024年  
**开发语言**: Python 3.8+
