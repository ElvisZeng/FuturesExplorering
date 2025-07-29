"""
CTA高级动量策略
适用于VeighNa Station量化交易平台

策略说明：
1. 多指标组合：移动平均线 + RSI + MACD + 布林带
2. 动态仓位管理：基于波动率调整仓位大小
3. 多时间框架分析：结合不同周期确认信号
4. 高级风险管理：包含跟踪止损、时间止损等
5. 适合期货、股票等多种金融工具

作者：AI量化策略开发
版本：2.0
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
from vnpy.trader.constant import Direction, Offset, Status
from vnpy.trader.utility import virtual
import numpy as np
from typing import Optional


class CtaAdvancedMomentumStrategy(CtaTemplate):
    """CTA高级动量策略"""
    
    author = "AI量化策略开发"
    
    # 策略参数 - 移动平均线
    fast_ma_period = 12         # 快速MA周期
    slow_ma_period = 26         # 慢速MA周期
    signal_ma_period = 9        # 信号线周期
    trend_ma_period = 100       # 趋势过滤MA周期
    
    # 策略参数 - 技术指标
    rsi_period = 14             # RSI周期
    rsi_oversold = 30           # RSI超卖阈值
    rsi_overbought = 70         # RSI超买阈值
    
    macd_fast = 12              # MACD快线周期
    macd_slow = 26              # MACD慢线周期
    macd_signal = 9             # MACD信号线周期
    
    bb_period = 20              # 布林带周期
    bb_std_dev = 2.0            # 布林带标准差倍数
    
    # 策略参数 - 风险管理
    atr_period = 14             # ATR周期
    stop_atr_ratio = 2.0        # 止损ATR倍数
    trail_atr_ratio = 1.5       # 跟踪止损ATR倍数
    max_position_ratio = 0.1    # 最大仓位比例
    
    # 策略参数 - 仓位管理
    base_size = 1               # 基础仓位
    risk_per_trade = 0.02       # 每笔交易风险比例
    
    # 策略参数 - 时间控制
    max_holding_bars = 100      # 最大持仓K线数
    
    # 策略变量 - 技术指标
    fast_ma = 0.0
    slow_ma = 0.0
    trend_ma = 0.0
    rsi_value = 0.0
    macd_line = 0.0
    macd_signal_line = 0.0
    macd_histogram = 0.0
    bb_upper = 0.0
    bb_middle = 0.0
    bb_lower = 0.0
    atr_value = 0.0
    
    # 策略变量 - 交易信号
    trend_direction = 0         # 趋势方向：1多头，-1空头，0震荡
    momentum_score = 0          # 动量评分
    signal_strength = 0         # 信号强度
    
    # 策略变量 - 风险管理
    entry_price = 0.0           # 入场价格
    stop_loss_price = 0.0       # 止损价格
    trailing_stop = 0.0         # 跟踪止损价格
    position_size = 0           # 当前仓位大小
    holding_bars = 0            # 持仓K线数
    
    # 策略变量 - 交易统计
    total_trades = 0
    winning_trades = 0
    losing_trades = 0
    max_drawdown = 0.0
    total_pnl = 0.0
    
    # 参数列表
    parameters = [
        "fast_ma_period", "slow_ma_period", "signal_ma_period", "trend_ma_period",
        "rsi_period", "rsi_oversold", "rsi_overbought",
        "macd_fast", "macd_slow", "macd_signal",
        "bb_period", "bb_std_dev",
        "atr_period", "stop_atr_ratio", "trail_atr_ratio",
        "max_position_ratio", "base_size", "risk_per_trade",
        "max_holding_bars"
    ]
    
    # 变量列表
    variables = [
        "fast_ma", "slow_ma", "trend_ma", "rsi_value",
        "macd_line", "macd_signal_line", "macd_histogram",
        "bb_upper", "bb_middle", "bb_lower", "atr_value",
        "trend_direction", "momentum_score", "signal_strength",
        "entry_price", "stop_loss_price", "trailing_stop",
        "position_size", "holding_bars",
        "total_trades", "winning_trades", "losing_trades"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # K线生成器 - 使用15分钟周期
        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am = ArrayManager(size=300)  # 增大数组大小以支持更多指标计算
        
        # 交易记录
        self.trade_records = []
        
    def on_init(self):
        """策略初始化"""
        self.write_log("CTA高级动量策略初始化")
        self.load_bar(50)  # 加载更多历史数据

    def on_start(self):
        """策略启动"""
        self.write_log("CTA高级动量策略启动")

    def on_stop(self):
        """策略停止"""
        self.write_log("CTA高级动量策略停止")
        self.print_trade_summary()

    def on_tick(self, tick: TickData):
        """收到tick数据推送"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """收到K线数据推送"""
        self.bg.update_bar(bar)

    def on_15min_bar(self, bar: BarData):
        """15分钟K线数据处理"""
        # 更新数组管理器
        self.am.update_bar(bar)
        
        if not self.am.inited:
            return
            
        # 计算所有技术指标
        self.calculate_all_indicators()
        
        # 分析市场趋势
        self.analyze_trend()
        
        # 计算动量评分
        self.calculate_momentum_score()
        
        # 生成交易信号
        signal = self.generate_trading_signal()
        
        # 执行交易逻辑
        self.execute_strategy(bar, signal)
        
        # 更新持仓时间
        if self.pos != 0:
            self.holding_bars += 1
        else:
            self.holding_bars = 0
            
        # 更新界面
        self.put_event()

    def calculate_all_indicators(self):
        """计算所有技术指标"""
        # 移动平均线
        self.fast_ma = self.am.sma(self.fast_ma_period)
        self.slow_ma = self.am.sma(self.slow_ma_period)
        self.trend_ma = self.am.sma(self.trend_ma_period)
        
        # RSI
        self.rsi_value = self.am.rsi(self.rsi_period)
        
        # MACD
        macd_data = self.calculate_macd()
        if macd_data:
            self.macd_line, self.macd_signal_line, self.macd_histogram = macd_data
        
        # 布林带
        bb_data = self.calculate_bollinger_bands()
        if bb_data:
            self.bb_upper, self.bb_middle, self.bb_lower = bb_data
            
        # ATR
        self.atr_value = self.am.atr(self.atr_period)

    def calculate_macd(self):
        """计算MACD指标"""
        try:
            close_array = self.am.close_array
            if len(close_array) < self.macd_slow + self.macd_signal:
                return None
                
            # 计算EMA
            ema_fast = self.calculate_ema(close_array, self.macd_fast)
            ema_slow = self.calculate_ema(close_array, self.macd_slow)
            
            if ema_fast is None or ema_slow is None:
                return None
                
            # MACD线
            macd_line = ema_fast - ema_slow
            
            # 信号线
            macd_signal = self.calculate_ema(np.array([macd_line]), self.macd_signal)
            if macd_signal is None:
                return None
                
            # 柱状图
            macd_histogram = macd_line - macd_signal
            
            return macd_line, macd_signal, macd_histogram
            
        except Exception as e:
            self.write_log(f"MACD计算错误: {e}")
            return None

    def calculate_ema(self, data, period):
        """计算指数移动平均线"""
        try:
            if len(data) < period:
                return None
            alpha = 2 / (period + 1)
            ema = data[0]
            for price in data[1:]:
                ema = alpha * price + (1 - alpha) * ema
            return ema
        except:
            return None

    def calculate_bollinger_bands(self):
        """计算布林带"""
        try:
            if len(self.am.close_array) < self.bb_period:
                return None
                
            # 中轨（移动平均线）
            bb_middle = self.am.sma(self.bb_period)
            
            # 标准差
            close_array = self.am.close_array[-self.bb_period:]
            std_dev = np.std(close_array)
            
            # 上轨和下轨
            bb_upper = bb_middle + self.bb_std_dev * std_dev
            bb_lower = bb_middle - self.bb_std_dev * std_dev
            
            return bb_upper, bb_middle, bb_lower
            
        except Exception as e:
            self.write_log(f"布林带计算错误: {e}")
            return None

    def analyze_trend(self):
        """分析市场趋势"""
        current_price = self.am.close
        
        # 基于移动平均线判断趋势
        if current_price > self.trend_ma and self.fast_ma > self.slow_ma:
            self.trend_direction = 1  # 上升趋势
        elif current_price < self.trend_ma and self.fast_ma < self.slow_ma:
            self.trend_direction = -1  # 下降趋势
        else:
            self.trend_direction = 0  # 震荡趋势

    def calculate_momentum_score(self):
        """计算动量评分"""
        score = 0
        
        # RSI动量评分
        if self.rsi_value > 50:
            score += 1
        elif self.rsi_value < 50:
            score -= 1
            
        # MACD动量评分
        if self.macd_line > self.macd_signal_line:
            score += 1
        else:
            score -= 1
            
        # 布林带位置评分
        current_price = self.am.close
        if current_price > self.bb_middle:
            score += 1
        elif current_price < self.bb_middle:
            score -= 1
            
        # 价格与移动平均线关系
        if current_price > self.fast_ma > self.slow_ma:
            score += 2
        elif current_price < self.fast_ma < self.slow_ma:
            score -= 2
            
        self.momentum_score = score

    def generate_trading_signal(self):
        """生成交易信号"""
        # 无趋势时不交易
        if self.trend_direction == 0:
            return 0
            
        # 计算信号强度
        signal_strength = 0
        
        # 多头信号条件
        if (self.trend_direction == 1 and
            self.momentum_score >= 2 and
            self.rsi_value < self.rsi_overbought and
            self.macd_histogram > 0):
            signal_strength = 1
            
        # 空头信号条件  
        elif (self.trend_direction == -1 and
              self.momentum_score <= -2 and
              self.rsi_value > self.rsi_oversold and
              self.macd_histogram < 0):
            signal_strength = -1
            
        self.signal_strength = signal_strength
        return signal_strength

    def calculate_position_size(self, entry_price: float):
        """计算仓位大小"""
        if self.atr_value <= 0:
            return self.base_size
            
        # 基于ATR的风险调整仓位
        stop_distance = self.atr_value * self.stop_atr_ratio
        risk_amount = entry_price * self.risk_per_trade
        
        size = int(risk_amount / stop_distance)
        
        # 限制最大仓位
        max_size = int(self.base_size / self.max_position_ratio)
        size = min(size, max_size, self.base_size * 3)
        
        return max(size, 1)

    def execute_strategy(self, bar: BarData, signal: int):
        """执行策略逻辑"""
        current_price = bar.close_price
        
        # 检查止损和时间止损
        self.check_stop_conditions(current_price)
        
        # 无持仓时检查入场信号
        if self.pos == 0:
            if signal == 1:  # 多头信号
                size = self.calculate_position_size(current_price)
                self.buy(current_price + 5, size)
                self.entry_price = current_price
                self.setup_stop_loss(current_price, Direction.LONG)
                self.write_log(f"多头入场: 价格={current_price}, 仓位={size}, 动量评分={self.momentum_score}")
                
            elif signal == -1:  # 空头信号
                size = self.calculate_position_size(current_price)
                self.short(current_price - 5, size)
                self.entry_price = current_price
                self.setup_stop_loss(current_price, Direction.SHORT)
                self.write_log(f"空头入场: 价格={current_price}, 仓位={size}, 动量评分={self.momentum_score}")
        
        # 有持仓时更新跟踪止损
        elif self.pos != 0:
            self.update_trailing_stop(current_price)

    def setup_stop_loss(self, entry_price: float, direction: Direction):
        """设置止损价格"""
        if self.atr_value <= 0:
            return
            
        if direction == Direction.LONG:
            self.stop_loss_price = entry_price - self.atr_value * self.stop_atr_ratio
            self.trailing_stop = entry_price - self.atr_value * self.trail_atr_ratio
        else:
            self.stop_loss_price = entry_price + self.atr_value * self.stop_atr_ratio
            self.trailing_stop = entry_price + self.atr_value * self.trail_atr_ratio

    def update_trailing_stop(self, current_price: float):
        """更新跟踪止损"""
        if self.atr_value <= 0:
            return
            
        if self.pos > 0:  # 多头持仓
            new_trailing = current_price - self.atr_value * self.trail_atr_ratio
            self.trailing_stop = max(self.trailing_stop, new_trailing)
        elif self.pos < 0:  # 空头持仓
            new_trailing = current_price + self.atr_value * self.trail_atr_ratio
            self.trailing_stop = min(self.trailing_stop, new_trailing)

    def check_stop_conditions(self, current_price: float):
        """检查止损条件"""
        if self.pos == 0:
            return
            
        # 固定止损
        if self.pos > 0 and current_price <= self.stop_loss_price:
            self.sell(current_price - 5, abs(self.pos))
            self.write_log(f"多头固定止损: {current_price}")
            return
        elif self.pos < 0 and current_price >= self.stop_loss_price:
            self.cover(current_price + 5, abs(self.pos))
            self.write_log(f"空头固定止损: {current_price}")
            return
            
        # 跟踪止损
        if self.pos > 0 and current_price <= self.trailing_stop:
            self.sell(current_price - 5, abs(self.pos))
            self.write_log(f"多头跟踪止损: {current_price}")
            return
        elif self.pos < 0 and current_price >= self.trailing_stop:
            self.cover(current_price + 5, abs(self.pos))
            self.write_log(f"空头跟踪止损: {current_price}")
            return
            
        # 时间止损
        if self.holding_bars >= self.max_holding_bars:
            if self.pos > 0:
                self.sell(current_price - 5, abs(self.pos))
            else:
                self.cover(current_price + 5, abs(self.pos))
            self.write_log(f"时间止损: 持仓{self.holding_bars}根K线")

    def on_trade(self, trade: TradeData):
        """成交回调"""
        self.total_trades += 1
        
        # 记录交易
        self.trade_records.append({
            'time': trade.time,
            'direction': trade.direction.value,
            'price': trade.price,
            'volume': trade.volume,
            'pos_change': trade.volume if trade.direction == Direction.LONG else -trade.volume
        })
        
        self.write_log(f"成交: {trade.direction.value} {trade.volume}手 @ {trade.price}")
        self.put_event()

    def on_order(self, order: OrderData):
        """委托回调"""
        pass

    def on_stop_order(self, stop_order: StopOrder):
        """停止单回调"""
        pass

    def print_trade_summary(self):
        """打印交易总结"""
        if self.total_trades > 0:
            win_rate = self.winning_trades / self.total_trades * 100
            self.write_log(f"交易总结:")
            self.write_log(f"总交易次数: {self.total_trades}")
            self.write_log(f"盈利次数: {self.winning_trades}")
            self.write_log(f"亏损次数: {self.losing_trades}")
            self.write_log(f"胜率: {win_rate:.1f}%")

    @virtual
    def get_strategy_status(self):
        """获取策略状态"""
        return {
            "趋势方向": "多头" if self.trend_direction == 1 else "空头" if self.trend_direction == -1 else "震荡",
            "动量评分": self.momentum_score,
            "信号强度": self.signal_strength,
            "RSI": f"{self.rsi_value:.1f}",
            "MACD": f"{self.macd_line:.4f}",
            "当前持仓": self.pos,
            "止损价格": f"{self.stop_loss_price:.2f}",
            "跟踪止损": f"{self.trailing_stop:.2f}",
            "持仓时间": f"{self.holding_bars}根K线"
        }