"""
VeighNa Station CTA策略运行示例
演示如何在VeighNa中使用CTA策略进行量化交易

使用说明：
1. 确保已安装VeighNa和相关依赖
2. 配置交易接口参数
3. 修改策略参数
4. 运行脚本启动策略

作者：AI量化策略开发团队
"""

import sys
from pathlib import Path
from datetime import datetime, time
from logging import INFO

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy.trader.setting import SETTINGS

# 导入交易接口
from vnpy_ctp import CtpGateway
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_datamanager import DataManagerApp

# 导入策略
from cta_dual_ma_strategy import CtaDualMaStrategy
from cta_advanced_momentum_strategy import CtaAdvancedMomentumStrategy


class CtaStrategyRunner:
    """CTA策略运行器"""
    
    def __init__(self):
        """初始化"""
        self.event_engine = None
        self.main_engine = None
        self.cta_engine = None
        
    def setup_environment(self):
        """设置环境"""
        # 设置日志级别
        SETTINGS["log.level"] = INFO
        
        # 创建事件引擎
        self.event_engine = EventEngine()
        
        # 创建主引擎
        self.main_engine = MainEngine(self.event_engine)
        
        # 添加交易接口
        self.main_engine.add_gateway(CtpGateway)
        
        # 添加CTA策略应用
        self.main_engine.add_app(CtaStrategyApp)
        self.main_engine.add_app(CtaBacktesterApp)  # 回测模块
        self.main_engine.add_app(DataManagerApp)    # 数据管理模块
        
        print("VeighNa环境初始化完成")
    
    def connect_gateway(self):
        """连接交易接口"""
        # CTP仿真连接配置
        ctp_setting = {
            "用户名": "your_username",      # 替换为您的用户名
            "密码": "your_password",        # 替换为您的密码
            "经纪商代码": "9999",           # 替换为您的经纪商代码
            "交易服务器": "180.168.146.187:10130",  # CTP交易服务器
            "行情服务器": "180.168.146.187:10131",  # CTP行情服务器
            "产品名称": "simnow_client_test",
            "授权编码": "0000000000000000",
        }
        
        # 连接CTP接口
        self.main_engine.connect(ctp_setting, "CTP")
        print("正在连接CTP接口...")
        
    def setup_strategies(self):
        """设置策略"""
        # 获取CTA策略引擎
        self.cta_engine = self.main_engine.get_app("CtaStrategy")
        
        # 双移动平均线策略配置
        dual_ma_setting = {
            "class_name": "CtaDualMaStrategy",
            "vt_symbol": "rb2305.SHFE",     # 螺纹钢主力合约
            "fast_window": 20,              # 快线周期
            "slow_window": 50,              # 慢线周期
            "trend_window": 200,            # 趋势过滤器周期
            "atr_window": 14,               # ATR周期
            "atr_multiplier": 2.0,          # ATR止损倍数
            "fixed_size": 1,                # 固定手数
        }
        
        # 高级动量策略配置
        momentum_setting = {
            "class_name": "CtaAdvancedMomentumStrategy", 
            "vt_symbol": "cu2305.SHFE",     # 铜主力合约
            "fast_ma_period": 12,           # 快速MA周期
            "slow_ma_period": 26,           # 慢速MA周期
            "trend_ma_period": 100,         # 趋势MA周期
            "rsi_period": 14,               # RSI周期
            "rsi_oversold": 30,             # RSI超卖
            "rsi_overbought": 70,           # RSI超买
            "atr_period": 14,               # ATR周期
            "stop_atr_ratio": 2.0,          # 止损ATR倍数
            "trail_atr_ratio": 1.5,         # 跟踪止损ATR倍数
            "base_size": 1,                 # 基础仓位
            "risk_per_trade": 0.02,         # 每笔交易风险比例
            "max_holding_bars": 100,        # 最大持仓K线数
        }
        
        # 添加策略到引擎
        try:
            self.cta_engine.add_strategy(
                "CtaDualMaStrategy",
                "双MA策略_RB",
                "rb2305.SHFE", 
                dual_ma_setting
            )
            print("双移动平均线策略添加成功")
            
            self.cta_engine.add_strategy(
                "CtaAdvancedMomentumStrategy",
                "高级动量策略_CU",
                "cu2305.SHFE",
                momentum_setting
            )
            print("高级动量策略添加成功")
            
        except Exception as e:
            print(f"策略添加失败: {e}")
    
    def start_strategies(self):
        """启动策略"""
        try:
            # 初始化策略
            self.cta_engine.init_strategy("双MA策略_RB")
            self.cta_engine.init_strategy("高级动量策略_CU")
            print("策略初始化完成")
            
            # 等待用户确认后启动策略
            input("按回车键启动策略...")
            
            # 启动策略
            self.cta_engine.start_strategy("双MA策略_RB")
            self.cta_engine.start_strategy("高级动量策略_CU")
            print("策略启动成功")
            
        except Exception as e:
            print(f"策略启动失败: {e}")
    
    def run_gui(self):
        """运行图形界面"""
        # 创建QT应用
        qapp = create_qapp()
        
        # 创建主窗口
        main_window = MainWindow(self.main_engine, self.event_engine)
        main_window.showMaximized()
        
        print("VeighNa Station启动成功！")
        print("可以在CTA策略模块中查看策略运行状态")
        
        # 运行应用
        qapp.exec()


def run_backtest_example():
    """回测示例"""
    from vnpy.app.cta_backtester import BacktesterEngine
    from vnpy.trader.database import get_database
    
    print("=" * 50)
    print("CTA策略回测示例")
    print("=" * 50)
    
    # 创建回测引擎
    engine = BacktesterEngine()
    
    # 设置回测参数
    engine.set_parameters(
        vt_symbol="rb2305.SHFE",
        interval="15m",
        start=datetime(2022, 1, 1),
        end=datetime(2023, 1, 1),
        rate=0.3/10000,      # 手续费率
        slippage=0.2,        # 滑点
        size=10,             # 合约大小
        pricetick=1,         # 最小价格变动
        capital=1000000,     # 初始资金
    )
    
    # 添加策略
    engine.add_strategy(CtaDualMaStrategy, {
        "fast_window": 20,
        "slow_window": 50,
        "trend_window": 200,
        "atr_window": 14,
        "atr_multiplier": 2.0,
        "fixed_size": 1,
    })
    
    # 加载历史数据
    print("正在加载历史数据...")
    engine.load_data()
    
    # 运行回测
    print("开始回测...")
    engine.run_backtesting()
    
    # 计算统计数据
    df = engine.calculate_result()
    statistics = engine.calculate_statistics()
    
    # 打印回测结果
    print("回测结果：")
    for key, value in statistics.items():
        print(f"{key}: {value}")


def print_strategy_info():
    """打印策略信息"""
    print("=" * 80)
    print("VeighNa Station CTA策略运行程序")
    print("=" * 80)
    print("包含策略：")
    print("1. CTA双移动平均线策略")
    print("   - 基于快慢移动平均线交叉的趋势跟踪策略")
    print("   - 适合趋势明显的市场环境")
    print("   - 参数简单，适合新手")
    print()
    print("2. CTA高级动量策略")
    print("   - 多指标组合的高级策略")
    print("   - 包含RSI、MACD、布林带等技术指标")
    print("   - 风险控制完善，适合有经验的交易者")
    print()
    print("注意事项：")
    print("- 请确保已正确配置CTP账户信息")
    print("- 建议先在仿真环境中测试策略")
    print("- 量化交易存在风险，请合理控制仓位")
    print("=" * 80)


def main():
    """主函数"""
    print_strategy_info()
    
    # 询问用户选择
    print("请选择运行模式：")
    print("1. 实时交易模式")
    print("2. 策略回测模式")
    print("3. 退出程序")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        # 实时交易模式
        runner = CtaStrategyRunner()
        
        try:
            # 设置环境
            runner.setup_environment()
            
            # 连接交易接口
            print("\n请确认已正确配置CTP账户信息")
            confirm = input("是否继续连接CTP接口？(y/n): ").strip().lower()
            
            if confirm == 'y':
                runner.connect_gateway()
                
                # 等待连接
                import time
                time.sleep(3)
                
                # 设置策略
                runner.setup_strategies()
                
                # 启动策略
                runner.start_strategies()
                
                # 运行GUI
                runner.run_gui()
            else:
                print("程序退出")
                
        except Exception as e:
            print(f"程序运行出错: {e}")
            input("按回车键退出...")
    
    elif choice == "2":
        # 回测模式
        try:
            run_backtest_example()
        except Exception as e:
            print(f"回测运行出错: {e}")
        finally:
            input("按回车键退出...")
    
    elif choice == "3":
        print("程序退出")
    
    else:
        print("无效选择，程序退出")


if __name__ == "__main__":
    main()