# VeighNa Station CTA量化策略使用说明

## 目录
1. [策略概述](#策略概述)
2. [环境准备](#环境准备)
3. [策略安装](#策略安装)
4. [策略说明](#策略说明)
5. [参数配置](#参数配置)
6. [使用方法](#使用方法)
7. [风险管理](#风险管理)
8. [常见问题](#常见问题)

## 策略概述

本项目提供了两个专为VeighNa Station设计的CTA（Commodity Trading Advisor）量化策略：

### 1. CTA双移动平均线策略 (CtaDualMaStrategy)
- **策略类型**：趋势跟踪策略
- **核心逻辑**：使用快慢移动平均线交叉信号判断趋势方向
- **适用市场**：期货、股票、外汇等
- **特点**：简单易懂，参数较少，适合新手

### 2. CTA高级动量策略 (CtaAdvancedMomentumStrategy)
- **策略类型**：多指标组合策略
- **核心逻辑**：结合MA、RSI、MACD、布林带等多个指标
- **适用市场**：期货、股票、数字货币等
- **特点**：信号质量高，风险控制完善，适合有经验的交易者

## 环境准备

### 系统要求
- Windows 10+ / Ubuntu 18.04+ / macOS 10.14+
- Python 3.7+（推荐Python 3.10）
- VeighNa Station 3.0+

### 依赖库
```bash
pip install vnpy
pip install numpy
pip install pandas
```

### VeighNa Station安装
1. 下载VeighNa Studio安装包
2. 安装后启动VeighNa Station
3. 注册并登录VeighNa Station账户

## 策略安装

### 方法一：直接复制文件
1. 将策略文件复制到VeighNa策略目录：
   ```
   C:\Users\{用户名}\.vntrader\strategies\
   ```

2. 重启VeighNa Station，策略将自动加载

### 方法二：通过VeighNa Station导入
1. 打开VeighNa Station
2. 进入策略管理界面
3. 点击"导入策略"
4. 选择策略文件导入

## 策略说明

### CTA双移动平均线策略

#### 策略逻辑
1. **趋势判断**：使用200期移动平均线作为趋势过滤器
2. **入场信号**：快线（20期）上穿慢线（50期）产生多头信号，下穿产生空头信号
3. **风险控制**：使用ATR指标设置动态止损
4. **出场条件**：价格触及止损线或反向信号出现

#### 核心参数
- `fast_window`：快速移动平均线周期（默认20）
- `slow_window`：慢速移动平均线周期（默认50）
- `trend_window`：趋势过滤器周期（默认200）
- `atr_window`：ATR计算周期（默认14）
- `atr_multiplier`：ATR止损倍数（默认2.0）

### CTA高级动量策略

#### 策略逻辑
1. **趋势分析**：多重移动平均线组合判断市场趋势
2. **动量评分**：综合RSI、MACD、布林带位置计算动量强度
3. **信号过滤**：只在明确趋势下交易，避免震荡市场
4. **仓位管理**：基于ATR动态调整仓位大小
5. **多重止损**：固定止损、跟踪止损、时间止损

#### 核心参数
- `fast_ma_period`：快速MA周期（默认12）
- `slow_ma_period`：慢速MA周期（默认26）
- `trend_ma_period`：趋势MA周期（默认100）
- `rsi_period`：RSI周期（默认14）
- `atr_period`：ATR周期（默认14）
- `stop_atr_ratio`：止损ATR倍数（默认2.0）

## 参数配置

### 双移动平均线策略参数建议

#### 短期交易（日内）
```python
{
    "fast_window": 10,
    "slow_window": 30,
    "trend_window": 100,
    "atr_window": 14,
    "atr_multiplier": 1.5,
    "fixed_size": 1
}
```

#### 中期交易（持仓几天）
```python
{
    "fast_window": 20,
    "slow_window": 50,
    "trend_window": 200,
    "atr_window": 14,
    "atr_multiplier": 2.0,
    "fixed_size": 1
}
```

#### 长期交易（持仓数周）
```python
{
    "fast_window": 50,
    "slow_window": 100,
    "trend_window": 300,
    "atr_window": 20,
    "atr_multiplier": 2.5,
    "fixed_size": 1
}
```

### 高级动量策略参数建议

#### 激进模式（高频交易）
```python
{
    "fast_ma_period": 8,
    "slow_ma_period": 21,
    "trend_ma_period": 50,
    "rsi_period": 10,
    "stop_atr_ratio": 1.5,
    "trail_atr_ratio": 1.0,
    "risk_per_trade": 0.01,
    "max_holding_bars": 50
}
```

#### 稳健模式（中长期）
```python
{
    "fast_ma_period": 12,
    "slow_ma_period": 26,
    "trend_ma_period": 100,
    "rsi_period": 14,
    "stop_atr_ratio": 2.0,
    "trail_atr_ratio": 1.5,
    "risk_per_trade": 0.02,
    "max_holding_bars": 100
}
```

## 使用方法

### 在VeighNa Station中使用

1. **启动VeighNa Station**
2. **连接交易接口**（如CTP仿真）
3. **进入CTA策略模块**
4. **添加策略实例**：
   - 选择策略类：`CtaDualMaStrategy` 或 `CtaAdvancedMomentumStrategy`
   - 设置策略名称：如"双MA_RB2305"
   - 选择交易合约：如"rb2305.SHFE"
   - 配置策略参数
5. **初始化策略**：点击"初始化"按钮
6. **启动策略**：点击"启动"按钮开始交易

### 脚本化使用

创建`run_strategy.py`文件：

```python
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ctp import CtpGateway
from vnpy_ctastrategy import CtaStrategyApp

# 导入策略
from cta_dual_ma_strategy import CtaDualMaStrategy
from cta_advanced_momentum_strategy import CtaAdvancedMomentumStrategy

def main():
    """启动VeighNa Trader"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    # 添加交易接口
    main_engine.add_gateway(CtpGateway)
    
    # 添加CTA策略应用
    cta_app = CtaStrategyApp()
    main_engine.add_app(cta_app)
    
    # 注册策略
    cta_app.add_strategy(CtaDualMaStrategy)
    cta_app.add_strategy(CtaAdvancedMomentumStrategy)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()

if __name__ == "__main__":
    main()
```

## 风险管理

### 资金管理原则
1. **单笔风险控制**：每笔交易风险不超过总资金的2%
2. **最大回撤控制**：当回撤超过10%时暂停交易
3. **仓位分散**：不要将所有资金投入单一合约
4. **止损严格执行**：绝不抗单，严格按照策略执行止损

### 策略风险控制机制

#### 双移动平均线策略
- ATR动态止损：根据市场波动性调整止损距离
- 趋势过滤：只在明确趋势方向时交易
- 固定仓位：避免过度杠杆

#### 高级动量策略
- 多重止损：固定止损 + 跟踪止损 + 时间止损
- 动态仓位：基于波动率调整仓位大小
- 信号过滤：多指标确认减少假信号
- 最大持仓时间：避免长期套牢

### 市场环境适应性
- **趋势市场**：两个策略均表现良好
- **震荡市场**：建议暂停交易或降低仓位
- **高波动市场**：适当增加止损距离
- **低波动市场**：可以适当减少止损距离

## 常见问题

### Q1：策略不产生信号怎么办？
**A1**：检查以下几点：
- 确认历史数据加载充足（至少需要200根K线）
- 检查参数设置是否合理
- 确认当前市场是否满足策略条件

### Q2：策略频繁开平仓怎么办？
**A2**：可能原因和解决方案：
- 参数设置过于敏感：增加移动平均线周期
- 市场震荡：添加趋势过滤条件
- 止损设置过紧：增加ATR倍数

### Q3：如何评估策略表现？
**A3**：关注以下指标：
- 胜率：盈利交易占比
- 盈亏比：平均盈利/平均亏损
- 最大回撤：最大亏损幅度
- 夏普比率：风险调整后收益

### Q4：策略参数如何优化？
**A4**：优化建议：
- 使用VeighNa的回测功能测试不同参数
- 考虑不同市场环境下的表现
- 避免过度拟合历史数据
- 保持参数的合理性和逻辑性

### Q5：策略运行中出错怎么办？
**A5**：错误处理步骤：
1. 查看策略日志了解错误原因
2. 检查网络连接和交易接口状态
3. 确认合约代码和交易时间正确
4. 重启策略或VeighNa Station

### Q6：如何进行策略回测？
**A6**：回测流程：
1. 准备历史数据（K线数据）
2. 在VeighNa的回测模块中加载策略
3. 设置回测参数（时间范围、初始资金等）
4. 运行回测并分析结果
5. 根据回测结果优化参数

## 免责声明

1. 本策略仅供学习和研究使用，不构成投资建议
2. 量化交易存在风险，可能导致本金损失
3. 历史表现不代表未来收益
4. 使用前请充分了解策略逻辑和风险
5. 建议先在模拟环境中测试策略

## 技术支持

如有问题或建议，请通过以下方式联系：
- VeighNa官方论坛：https://www.vnpy.com
- 策略开发者：AI量化策略开发团队

---

**祝您交易顺利！**