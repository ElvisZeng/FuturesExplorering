#!/usr/bin/env python3
"""
期货数据管理系统安装脚本
"""
import os
import sys
import subprocess
import platform

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    else:
        print(f"✓ Python版本检查通过: {sys.version.split()[0]}")
        return True

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: 依赖包安装失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    directories = [
        "data",
        "data/raw",
        "data/processed", 
        "data/csv",
        "logs"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ 创建目录: {directory}")
        else:
            print(f"✓ 目录已存在: {directory}")

def check_postgresql():
    """检查PostgreSQL是否可用"""
    try:
        import psycopg2
        print("✓ PostgreSQL驱动已安装")
        return True
    except ImportError:
        print("警告: PostgreSQL驱动未安装，将尝试安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
            print("✓ PostgreSQL驱动安装完成")
            return True
        except subprocess.CalledProcessError:
            print("错误: 无法安装PostgreSQL驱动")
            return False

def create_config_file():
    """创建配置文件"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ 已创建.env配置文件，请根据实际情况修改数据库配置")
        else:
            print("警告: 未找到.env.example文件")
    else:
        print("✓ .env配置文件已存在")

def print_next_steps():
    """打印后续步骤"""
    print("\n" + "="*50)
    print("安装完成！后续步骤:")
    print("="*50)
    print("1. 安装并启动PostgreSQL数据库")
    print("2. 创建数据库和用户:")
    print("   CREATE DATABASE futures_data;")
    print("   CREATE USER futures_user WITH PASSWORD 'your_password';")
    print("   GRANT ALL PRIVILEGES ON DATABASE futures_data TO futures_user;")
    print()
    print("3. 修改.env文件中的数据库配置")
    print()
    print("4. 运行程序:")
    print("   python main.py")
    print("="*50)

def main():
    """主安装函数"""
    print("期货数据管理系统安装程序")
    print("="*40)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 创建目录
    create_directories()
    
    # 安装依赖
    if not install_requirements():
        return 1
    
    # 检查PostgreSQL
    check_postgresql()
    
    # 创建配置文件
    create_config_file()
    
    # 打印后续步骤
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())