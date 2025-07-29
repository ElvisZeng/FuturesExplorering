"""
自定义指标演示示例
展示如何创建和使用自定义技术指标
"""
from custom_indicators import custom_indicator_builder
import pandas as pd
import numpy as np

def create_demo_indicators():
    """创建演示用的自定义指标"""
    
    # 示例1: 价格相对强度指标
    price_relative_strength = {
        'name': '价格相对强度',
        'formula': '(close - sma(close, 20)) / sma(close, 20) * 100',
        'description': '价格相对于20日均线的偏离程度百分比',
        'parameters': {'period': 20}
    }
    
    result1 = custom_indicator_builder.create_indicator(
        name=price_relative_strength['name'],
        formula=price_relative_strength['formula'],
        description=price_relative_strength['description'],
        parameters=price_relative_strength['parameters']
    )
    print(f"创建指标1: {result1['message']}")
    
    # 示例2: 成交量价格确认指标
    volume_price_confirmation = {
        'name': '成交量价格确认',
        'formula': 'where(close > shift(close, 1), volume, -volume)',
        'description': '上涨时成交量为正，下跌时成交量为负',
        'parameters': {}
    }
    
    result2 = custom_indicator_builder.create_indicator(
        name=volume_price_confirmation['name'],
        formula=volume_price_confirmation['formula'],
        description=volume_price_confirmation['description'],
        parameters=volume_price_confirmation['parameters']
    )
    print(f"创建指标2: {result2['message']}")
    
    # 示例3: 动态阻力支撑指标
    dynamic_support_resistance = {
        'name': '动态阻力支撑',
        'formula': 'ema(high, 20) - ema(low, 20)',
        'description': '基于EMA的动态阻力支撑区间宽度',
        'parameters': {'period': 20}
    }
    
    result3 = custom_indicator_builder.create_indicator(
        name=dynamic_support_resistance['name'],
        formula=dynamic_support_resistance['formula'],
        description=dynamic_support_resistance['description'],
        parameters=dynamic_support_resistance['parameters']
    )
    print(f"创建指标3: {result3['message']}")
    
    # 示例4: 波动率指标
    volatility_indicator = {
        'name': '波动率指标',
        'formula': 'rolling(close, 20).std() / sma(close, 20) * 100',
        'description': '20日价格标准差相对于均价的百分比',
        'parameters': {'period': 20}
    }
    
    result4 = custom_indicator_builder.create_indicator(
        name=volatility_indicator['name'],
        formula=volatility_indicator['formula'],
        description=volatility_indicator['description'],
        parameters=volatility_indicator['parameters']
    )
    print(f"创建指标4: {result4['message']}")
    
    # 示例5: 趋势跟踪指标
    trend_following = {
        'name': '趋势跟踪指标',
        'formula': 'where(ema(close, 12) > ema(close, 26), 1, where(ema(close, 12) < ema(close, 26), -1, 0))',
        'description': '基于双EMA的趋势方向指标，1为上涨趋势，-1为下跌趋势，0为震荡',
        'parameters': {'fast_period': 12, 'slow_period': 26}
    }
    
    result5 = custom_indicator_builder.create_indicator(
        name=trend_following['name'],
        formula=trend_following['formula'],
        description=trend_following['description'],
        parameters=trend_following['parameters']
    )
    print(f"创建指标5: {result5['message']}")

def test_custom_indicator(data: pd.DataFrame):
    """测试自定义指标"""
    if data.empty:
        print("没有测试数据")
        return
    
    # 测试价格相对强度指标
    formula = '(close - sma(close, 20)) / sma(close, 20) * 100'
    test_result = custom_indicator_builder.test_indicator(formula, data)
    
    if test_result['success']:
        print("指标测试成功:")
        print(f"数据统计: {test_result['stats']}")
        
        # 显示最后几个值
        result_series = test_result['result']
        if len(result_series) > 5:
            print("最后5个值:")
            print(result_series.tail().to_string())
    else:
        print(f"指标测试失败: {test_result['message']}")

def show_indicator_help():
    """显示指标帮助信息"""
    help_info = custom_indicator_builder.get_formula_help()
    
    print("=== 自定义指标公式帮助 ===\n")
    
    print("可用变量:")
    for var, desc in help_info['variables'].items():
        print(f"  {var}: {desc}")
    
    print("\n可用函数:")
    for category, functions in help_info['functions'].items():
        print(f"\n{category}:")
        for func, desc in functions.items():
            print(f"  {func}: {desc}")
    
    print("\n公式示例:")
    for example, formula in help_info['examples'].items():
        print(f"  {example}: {formula}")
    
    print(f"\n支持的运算符: {help_info['operators']['算术运算']}")
    print(f"比较运算符: {help_info['operators']['比较运算']}")
    print(f"逻辑运算符: {help_info['operators']['逻辑运算']}")

if __name__ == "__main__":
    print("=== 自定义指标演示 ===\n")
    
    # 显示帮助信息
    show_indicator_help()
    
    print("\n" + "="*50)
    print("创建演示指标...")
    
    # 创建演示指标
    create_demo_indicators()
    
    print("\n" + "="*50)
    print("已创建的自定义指标:")
    
    # 列出所有指标
    indicators = custom_indicator_builder.list_indicators()
    for i, indicator in enumerate(indicators, 1):
        print(f"{i}. {indicator['name']}")
        print(f"   公式: {indicator['formula']}")
        print(f"   描述: {indicator['description']}")
        print(f"   创建时间: {indicator['created_at'][:19]}")
        print()
    
    print("演示完成！")