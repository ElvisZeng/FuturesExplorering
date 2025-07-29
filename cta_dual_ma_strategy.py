"""
CTA双移动平均线趋势跟踪策略
适用于VeighNa Station量化交易平台

策略说明：
1. 使用快速和慢速移动平均线的交叉信号作为趋势判断
2. 结合ATR指标进行动态止损
3. 包含趋势过滤器避免震荡市场的假信号
4. 实现完整的风险管理机制

作者：AI量化策略开发
版本：1.0
"""

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.trader.constant import Direction, Offset
from vnpy.trader.object import OrderRequest
from vnpy.trader.utility import virtual


class CtaDualMaStrategy(CtaTemplate):
    """CTA双移动平均线趋势跟踪策略"""
    
    author = "AI量化策略开发"
    
    # 策略参数
    fast_window = 20        # 快速移动平均线周期
    slow_window = 50        # 慢速移动平均线周期
    trend_window = 200      # 趋势过滤器周期
    atr_window = 14         # ATR周期
    atr_multiplier = 2.0    # ATR止损倍数
    fixed_size = 1          # 固定手数
    
    # 策略变量
    fast_ma = 0.0           # 快速移动平均线
    slow_ma = 0.0           # 慢速移动平均线
    trend_ma = 0.0          # 趋势过滤移动平均线
    atr_value = 0.0         # ATR值
    
    # 信号变量
    ma_trend = 0            # 移动平均线趋势：1多头，-1空头，0震荡
    long_entry = False      # 多头入场信号
    short_entry = False     # 空头入场信号
    
    # 止损变量
    long_stop = 0.0         # 多头止损价
    short_stop = 0.0        # 空头止损价
    
    # 交易统计
    win_count = 0           # 盈利交易次数
    loss_count = 0          # 亏损交易次数
    total_trades = 0        # 总交易次数
    
    # 参数列表
    parameters = [
        "fast_window",
        "slow_window", 
        "trend_window",
        "atr_window",
        "atr_multiplier",
        "fixed_size"
    ]
    
    # 变量列表
    variables = [
        "fast_ma",
        "slow_ma",
        "trend_ma", 
        "atr_value",
        "ma_trend",
        "long_entry",
        "short_entry",
        "long_stop",
        "short_stop",
        "win_count",
        "loss_count",
        "total_trades"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 数据管理器
        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am = ArrayManager()
        
        # 订单管理
        self.long_orders = []
        self.short_orders = []
        
    def on_init(self):
        """策略初始化"""
        self.write_log("CTA双移动平均线策略初始化")
        
        # 加载历史数据
        self.load_bar(30)

    def on_start(self):
        """策略启动"""
        self.write_log("CTA双移动平均线策略启动")

    def on_stop(self):
        """策略停止"""
        self.write_log("CTA双移动平均线策略停止")

    def on_tick(self, tick: TickData):
        """收到tick数据推送"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """收到K线数据推送"""
        self.bg.update_bar(bar)

    def on_15min_bar(self, bar: BarData):
        """15分钟K线数据处理"""
        # 更新数据到数组管理器
        self.am.update_bar(bar)
        
        # 数据不足，直接返回
        if not self.am.inited:
            return
            
        # 计算技术指标
        self.calculate_indicators()
        
        # 生成交易信号
        self.generate_signals()
        
        # 执行交易逻辑
        self.execute_trading_logic(bar)
        
        # 更新界面
        self.put_event()

    def calculate_indicators(self):
        """计算技术指标"""
        # 计算移动平均线
        self.fast_ma = self.am.sma(self.fast_window, array=True)[-1]
        self.slow_ma = self.am.sma(self.slow_window, array=True)[-1]
        self.trend_ma = self.am.sma(self.trend_window, array=True)[-1]
        
        # 计算ATR
        self.atr_value = self.am.atr(self.atr_window, array=True)[-1]

    def generate_signals(self):
        """生成交易信号"""
        # 重置信号
        self.long_entry = False
        self.short_entry = False
        
        # 获取当前和前一根K线的移动平均线
        fast_ma_array = self.am.sma(self.fast_window, array=True)
        slow_ma_array = self.am.sma(self.slow_window, array=True)
        
        # 确保有足够的数据
        if len(fast_ma_array) < 2 or len(slow_ma_array) < 2:
            return
            
        # 当前和前一根K线的MA值
        fast_ma_current = fast_ma_array[-1]
        fast_ma_previous = fast_ma_array[-2]
        slow_ma_current = slow_ma_array[-1]
        slow_ma_previous = slow_ma_array[-2]
        
        # 当前价格
        current_price = self.am.close_array[-1]
        
        # 趋势过滤器：只有价格在趋势MA上方才考虑多头，在下方才考虑空头
        trend_filter_long = current_price > self.trend_ma
        trend_filter_short = current_price < self.trend_ma
        
        # 金叉信号：快线上穿慢线
        golden_cross = (fast_ma_previous <= slow_ma_previous and 
                       fast_ma_current > slow_ma_current)
        
        # 死叉信号：快线下穿慢线  
        death_cross = (fast_ma_previous >= slow_ma_previous and 
                      fast_ma_current < slow_ma_current)
        
        # 更新趋势状态
        if golden_cross and trend_filter_long:
            self.ma_trend = 1
            self.long_entry = True
        elif death_cross and trend_filter_short:
            self.ma_trend = -1
            self.short_entry = True
        elif not trend_filter_long and not trend_filter_short:
            self.ma_trend = 0

    def execute_trading_logic(self, bar: BarData):
        """执行交易逻辑"""
        # 计算止损价格
        self.calculate_stop_prices(bar.close_price)
        
        # 如果有持仓，检查止损
        if self.pos > 0:
            self.check_long_stop(bar.close_price)
        elif self.pos < 0:
            self.check_short_stop(bar.close_price)
        
        # 无持仓时检查入场信号
        if self.pos == 0:
            if self.long_entry:
                self.buy(bar.close_price + 5, self.fixed_size)
                self.write_log(f"多头入场信号：价格{bar.close_price}, 快线{self.fast_ma:.2f}, 慢线{self.slow_ma:.2f}")
                
            elif self.short_entry:
                self.short(bar.close_price - 5, self.fixed_size)
                self.write_log(f"空头入场信号：价格{bar.close_price}, 快线{self.fast_ma:.2f}, 慢线{self.slow_ma:.2f}")

    def calculate_stop_prices(self, current_price: float):
        """计算止损价格"""
        if self.atr_value > 0:
            self.long_stop = current_price - self.atr_multiplier * self.atr_value
            self.short_stop = current_price + self.atr_multiplier * self.atr_value

    def check_long_stop(self, current_price: float):
        """检查多头止损"""
        if current_price <= self.long_stop:
            self.sell(current_price - 5, abs(self.pos))
            self.write_log(f"多头止损：当前价格{current_price}, 止损价{self.long_stop:.2f}")

    def check_short_stop(self, current_price: float):
        """检查空头止损"""
        if current_price >= self.short_stop:
            self.cover(current_price + 5, abs(self.pos))
            self.write_log(f"空头止损：当前价格{current_price}, 止损价{self.short_stop:.2f}")

    def on_order(self, order: OrderData):
        """收到委托变化推送"""
        pass

    def on_trade(self, trade: TradeData):
        """收到成交推送"""
        # 更新交易统计
        self.total_trades += 1
        
        # 计算盈亏（简化处理）
        if trade.direction == Direction.LONG:
            if self.pos <= 0:  # 平空头仓位
                # 这里可以添加更详细的盈亏计算逻辑
                self.write_log(f"平空头仓位：{trade.price}")
        else:  # SHORT
            if self.pos >= 0:  # 平多头仓位
                self.write_log(f"平多头仓位：{trade.price}")
        
        # 输出成交信息
        self.write_log(f"成交回报：{trade.direction.value} {trade.volume}手 @ {trade.price}")
        
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """收到停止单推送"""
        pass

    @virtual
    def get_strategy_statistics(self):
        """获取策略统计信息"""
        win_rate = 0
        if self.total_trades > 0:
            win_rate = self.win_count / self.total_trades * 100
            
        return {
            "总交易次数": self.total_trades,
            "盈利次数": self.win_count,
            "亏损次数": self.loss_count,
            "胜率": f"{win_rate:.1f}%",
            "当前持仓": self.pos,
            "快线MA": f"{self.fast_ma:.2f}",
            "慢线MA": f"{self.slow_ma:.2f}",
            "趋势MA": f"{self.trend_ma:.2f}",
            "ATR": f"{self.atr_value:.2f}",
            "多头止损": f"{self.long_stop:.2f}",
            "空头止损": f"{self.short_stop:.2f}"
        }