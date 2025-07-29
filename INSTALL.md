# 期货数据管理系统 - 快速安装指南

## 快速开始

### 1. 环境准备
确保您的系统已安装：
- Python 3.8 或更高版本
- PostgreSQL 12 或更高版本

### 2. 自动安装
```bash
# 克隆或下载项目代码后，运行安装脚本
python setup.py
```

### 3. 数据库设置
创建数据库和用户：
```sql
-- 连接到PostgreSQL
psql -U postgres

-- 创建数据库和用户
CREATE DATABASE futures_data;
CREATE USER futures_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE futures_data TO futures_user;
\q
```

### 4. 配置文件
编辑 `.env` 文件，修改数据库连接信息：
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=futures_data
DB_USER=futures_user
DB_PASSWORD=your_password
```

### 5. 启动程序

#### Windows用户
双击 `run.bat` 或在命令提示符中运行：
```cmd
run.bat
```

#### Linux/macOS用户
```bash
./run.sh
```

#### 或直接运行Python
```bash
python main.py
```

## 手动安装

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 创建目录结构
```bash
mkdir -p data/{raw,processed,csv} logs
```

### 3. 配置数据库
- 安装并启动PostgreSQL
- 创建数据库和用户（见上文）
- 配置连接信息

### 4. 启动程序
```bash
python main.py
```

## 验证安装

启动程序后：

1. **检查数据库连接**
   - 进入"系统设置"标签页
   - 点击"测试数据库连接"
   - 确认显示"连接正常"

2. **下载测试数据**
   - 进入"数据管理"标签页
   - 选择最近一周的日期范围
   - 选择一个交易所
   - 点击"下载数据"

3. **查看图表**
   - 进入"数据图表"标签页
   - 选择交易所和品种
   - 点击"显示图表"

## 常见问题

### Q: 数据库连接失败
A: 
- 确认PostgreSQL服务正在运行
- 检查用户名密码是否正确
- 确认数据库名称是否存在

### Q: 依赖包安装失败
A:
- 更新pip: `pip install --upgrade pip`
- 使用国内源: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

### Q: 程序启动失败
A:
- 检查Python版本: `python --version`
- 查看错误日志: `logs/futures_system.log`
- 确认所有依赖已正确安装

## 获取帮助

如遇到问题，请：
1. 查看 `README.md` 获取详细文档
2. 检查 `logs/futures_system.log` 中的错误信息
3. 确认系统满足最低要求

---

安装完成后，您就可以开始使用期货数据管理系统了！