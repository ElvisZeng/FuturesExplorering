@echo off
chcp 65001
title 期货数据管理系统

echo 期货数据管理系统启动中...
echo ================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖是否安装
if not exist "requirements.txt" (
    echo 错误: 未找到requirements.txt文件
    pause
    exit /b 1
)

REM 启动程序
python main.py

pause