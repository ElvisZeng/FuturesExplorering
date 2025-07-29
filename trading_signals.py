"""
交易信号生成模块
包含买卖点识别、信号生成、策略组合等功能
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from technical_indicators import tech_indicators

class TradingSignalGenerator:
    """交易信号生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.signals_history = []
    
    def ma_crossover_signal(self, data: pd.DataFrame, fast_period: int = 5, 
                           slow_period: int = 20, signal_type: str = 'sma') -> pd.Series:
        """移动平均线交叉信号"""
        try:
            if signal_type == 'sma':
                fast_ma = tech_indicators.sma(data['close'], fast_period)
                slow_ma = tech_indicators.sma(data['close'], slow_period)
            elif signal_type == 'ema':
                fast_ma = tech_indicators.ema(data['close'], fast_period)
                slow_ma = tech_indicators.ema(data['close'], slow_period)
            else:
                raise ValueError("signal_type must be 'sma' or 'ema'")
            
            # 计算交叉信号
            signals = pd.Series(0, index=data.index)
            
            # 金叉：快线上穿慢线 = 1 (买入信号)
            signals[(fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))] = 1
            
            # 死叉：快线下穿慢线 = -1 (卖出信号)  
            signals[(fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))] = -1
            
            return signals
            
        except Exception as e:
            self.logger.error(f"移动平均线交叉信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def macd_signal(self, data: pd.DataFrame) -> pd.Series:
        """MACD信号"""
        try:
            macd_data = tech_indicators.macd(data['close'])
            macd_line = macd_data['macd']
            signal_line = macd_data['signal']
            histogram = macd_data['histogram']
            
            signals = pd.Series(0, index=data.index)
            
            # MACD金叉且在零轴上方
            golden_cross = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
            above_zero = macd_line > 0
            signals[golden_cross & above_zero] = 1
            
            # MACD死叉且在零轴下方
            death_cross = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
            below_zero = macd_line < 0
            signals[death_cross & below_zero] = -1
            
            # 柱状图背离信号
            price_higher = data['close'] > data['close'].shift(5)
            histogram_lower = histogram < histogram.shift(5)
            bearish_divergence = price_higher & histogram_lower & (histogram > 0)
            signals[bearish_divergence] = -1
            
            price_lower = data['close'] < data['close'].shift(5)
            histogram_higher = histogram > histogram.shift(5)
            bullish_divergence = price_lower & histogram_higher & (histogram < 0)
            signals[bullish_divergence] = 1
            
            return signals
            
        except Exception as e:
            self.logger.error(f"MACD信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def rsi_signal(self, data: pd.DataFrame, oversold: float = 30, 
                   overbought: float = 70) -> pd.Series:
        """RSI信号"""
        try:
            rsi = tech_indicators.rsi(data['close'])
            signals = pd.Series(0, index=data.index)
            
            # RSI从超卖区域向上突破
            rsi_bullish = (rsi > oversold) & (rsi.shift(1) <= oversold)
            signals[rsi_bullish] = 1
            
            # RSI从超买区域向下突破
            rsi_bearish = (rsi < overbought) & (rsi.shift(1) >= overbought)
            signals[rsi_bearish] = -1
            
            # RSI背离
            price_higher = data['close'] > data['close'].shift(10)
            rsi_lower = rsi < rsi.shift(10)
            bearish_divergence = price_higher & rsi_lower & (rsi > 50)
            signals[bearish_divergence] = -1
            
            price_lower = data['close'] < data['close'].shift(10)
            rsi_higher = rsi > rsi.shift(10)
            bullish_divergence = price_lower & rsi_higher & (rsi < 50)
            signals[bullish_divergence] = 1
            
            return signals
            
        except Exception as e:
            self.logger.error(f"RSI信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def bollinger_bands_signal(self, data: pd.DataFrame) -> pd.Series:
        """布林带信号"""
        try:
            bb_data = tech_indicators.bollinger_bands(data['close'])
            upper = bb_data['upper']
            lower = bb_data['lower']
            middle = bb_data['middle']
            bandwidth = bb_data['bandwidth']
            
            signals = pd.Series(0, index=data.index)
            
            # 价格从下轨反弹
            bounce_from_lower = (data['close'] > lower) & (data['close'].shift(1) <= lower.shift(1))
            signals[bounce_from_lower] = 1
            
            # 价格从上轨回落
            rejection_from_upper = (data['close'] < upper) & (data['close'].shift(1) >= upper.shift(1))
            signals[rejection_from_upper] = -1
            
            # 布林带收缩后的突破
            squeeze = bandwidth < bandwidth.rolling(window=20).mean() * 0.8
            breakout_up = squeeze & (data['close'] > upper)
            breakout_down = squeeze & (data['close'] < lower)
            
            signals[breakout_up] = 1
            signals[breakout_down] = -1
            
            return signals
            
        except Exception as e:
            self.logger.error(f"布林带信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def wyckoff_signal(self, data: pd.DataFrame) -> pd.Series:
        """维科夫量价分析信号"""
        try:
            # 计算维科夫指标
            ad_line = tech_indicators.wyckoff_accumulation_distribution(
                data['high'], data['low'], data['close'], data['volume']
            )
            pvt = tech_indicators.wyckoff_price_volume_trend(data['close'], data['volume'])
            
            signals = pd.Series(0, index=data.index)
            
            # 价格上涨但A/D线下降 - 看跌背离
            price_rising = data['close'] > data['close'].shift(5)
            ad_falling = ad_line < ad_line.shift(5)
            bearish_divergence = price_rising & ad_falling
            signals[bearish_divergence] = -1
            
            # 价格下跌但A/D线上升 - 看涨背离
            price_falling = data['close'] < data['close'].shift(5)
            ad_rising = ad_line > ad_line.shift(5)
            bullish_divergence = price_falling & ad_rising
            signals[bullish_divergence] = 1
            
            # PVT确认信号
            pvt_rising = pvt > pvt.shift(3)
            pvt_falling = pvt < pvt.shift(3)
            
            # 加强信号强度
            signals[bullish_divergence & pvt_rising] = 2
            signals[bearish_divergence & pvt_falling] = -2
            
            # 成交量分析
            avg_volume = data['volume'].rolling(window=20).mean()
            high_volume = data['volume'] > avg_volume * 1.5
            
            # 高成交量确认突破
            price_breakout_up = data['close'] > data['high'].rolling(window=20).max().shift(1)
            price_breakout_down = data['close'] < data['low'].rolling(window=20).min().shift(1)
            
            signals[price_breakout_up & high_volume] = 2
            signals[price_breakout_down & high_volume] = -2
            
            return signals
            
        except Exception as e:
            self.logger.error(f"维科夫信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def support_resistance_signal(self, data: pd.DataFrame) -> pd.Series:
        """支撑阻力位信号"""
        try:
            sr_levels = tech_indicators.support_resistance_levels(
                data['high'], data['low'], data['close']
            )
            
            resistance_levels = sr_levels['resistance_levels']
            support_levels = sr_levels['support_levels']
            
            signals = pd.Series(0, index=data.index)
            
            if not resistance_levels or not support_levels:
                return signals
            
            # 检查价格与支撑阻力位的关系
            for i, price in enumerate(data['close']):
                if pd.isna(price):
                    continue
                
                # 检查是否接近支撑位
                for support in support_levels:
                    if abs(price - support) / support < 0.02:  # 2%容忍度
                        # 如果价格从下方接近支撑位
                        if i > 0 and data['close'].iloc[i-1] < support:
                            signals.iloc[i] = 1
                        break
                
                # 检查是否接近阻力位
                for resistance in resistance_levels:
                    if abs(price - resistance) / resistance < 0.02:  # 2%容忍度
                        # 如果价格从上方接近阻力位
                        if i > 0 and data['close'].iloc[i-1] > resistance:
                            signals.iloc[i] = -1
                        break
            
            return signals
            
        except Exception as e:
            self.logger.error(f"支撑阻力位信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def trend_following_signal(self, data: pd.DataFrame) -> pd.Series:
        """趋势跟随信号"""
        try:
            # 计算ADX判断趋势强度
            adx_data = tech_indicators.adx(data['high'], data['low'], data['close'])
            adx = adx_data['adx']
            plus_di = adx_data['plus_di']
            minus_di = adx_data['minus_di']
            
            # 计算趋势强度
            trend_strength = tech_indicators.trend_strength(data['close'])
            
            signals = pd.Series(0, index=data.index)
            
            # 强趋势定义：ADX > 25 且趋势强度 > 0.5
            strong_trend = (adx > 25) & (trend_strength > 0.5)
            
            # 上升趋势：+DI > -DI
            uptrend = plus_di > minus_di
            # 下降趋势：-DI > +DI
            downtrend = minus_di > plus_di
            
            # 趋势跟随信号
            signals[strong_trend & uptrend] = 1
            signals[strong_trend & downtrend] = -1
            
            # 趋势反转信号
            trend_reversal_up = (plus_di > minus_di) & (plus_di.shift(1) <= minus_di.shift(1))
            trend_reversal_down = (minus_di > plus_di) & (minus_di.shift(1) <= plus_di.shift(1))
            
            signals[trend_reversal_up & (adx > 20)] = 1
            signals[trend_reversal_down & (adx > 20)] = -1
            
            return signals
            
        except Exception as e:
            self.logger.error(f"趋势跟随信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def breakout_signal(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        """突破信号"""
        try:
            breakout_data = tech_indicators.breakout_potential(
                data['high'], data['low'], data['close'], data['volume']
            )
            
            signals = pd.Series(0, index=data.index)
            
            # 向上突破信号
            upward_breakout = (
                (data['close'] > data['high'].rolling(window=lookback).max().shift(1)) &
                (breakout_data['volume_spike'] == 1)
            )
            signals[upward_breakout] = 2  # 强烈买入信号
            
            # 向下突破信号
            downward_breakout = (
                (data['close'] < data['low'].rolling(window=lookback).min().shift(1)) &
                (breakout_data['volume_spike'] == 1)
            )
            signals[downward_breakout] = -2  # 强烈卖出信号
            
            # 布林带收缩突破
            bb_breakout_up = breakout_data['breakout_up'] == 1
            bb_breakout_down = breakout_data['breakout_down'] == 1
            
            signals[bb_breakout_up] = 1
            signals[bb_breakout_down] = -1
            
            return signals
            
        except Exception as e:
            self.logger.error(f"突破信号计算失败: {e}")
            return pd.Series(0, index=data.index)
    
    def comprehensive_signal(self, data: pd.DataFrame, weights: Dict[str, float] = None) -> Dict:
        """综合信号生成"""
        try:
            if weights is None:
                weights = {
                    'ma_crossover': 1.0,
                    'macd': 1.2,
                    'rsi': 0.8,
                    'bollinger': 1.0,
                    'wyckoff': 1.5,
                    'support_resistance': 1.1,
                    'trend_following': 1.3,
                    'breakout': 1.4
                }
            
            # 计算各个信号
            signals = {}
            signals['ma_crossover'] = self.ma_crossover_signal(data)
            signals['macd'] = self.macd_signal(data)
            signals['rsi'] = self.rsi_signal(data)
            signals['bollinger'] = self.bollinger_bands_signal(data)
            signals['wyckoff'] = self.wyckoff_signal(data)
            signals['support_resistance'] = self.support_resistance_signal(data)
            signals['trend_following'] = self.trend_following_signal(data)
            signals['breakout'] = self.breakout_signal(data)
            
            # 计算加权综合信号
            weighted_signal = pd.Series(0.0, index=data.index)
            total_weight = 0
            
            for signal_name, signal_values in signals.items():
                if signal_name in weights:
                    weighted_signal += signal_values * weights[signal_name]
                    total_weight += weights[signal_name]
            
            # 标准化信号强度
            if total_weight > 0:
                weighted_signal = weighted_signal / total_weight
            
            # 生成最终交易信号
            final_signals = pd.Series(0, index=data.index)
            final_signals[weighted_signal > 0.3] = 1    # 买入信号
            final_signals[weighted_signal > 0.6] = 2    # 强烈买入信号
            final_signals[weighted_signal < -0.3] = -1  # 卖出信号
            final_signals[weighted_signal < -0.6] = -2  # 强烈卖出信号
            
            # 计算信号统计
            signal_stats = {
                'total_signals': (final_signals != 0).sum(),
                'buy_signals': (final_signals > 0).sum(),
                'sell_signals': (final_signals < 0).sum(),
                'strong_buy': (final_signals == 2).sum(),
                'strong_sell': (final_signals == -2).sum(),
                'signal_strength': weighted_signal
            }
            
            return {
                'individual_signals': signals,
                'weighted_signal': weighted_signal,
                'final_signal': final_signals,
                'signal_stats': signal_stats
            }
            
        except Exception as e:
            self.logger.error(f"综合信号计算失败: {e}")
            return {}
    
    def market_regime_detection(self, data: pd.DataFrame) -> pd.Series:
        """市场状态检测"""
        try:
            # 检测震荡市场
            sideways = tech_indicators.sideways_market_detection(
                data['high'], data['low'], data['close']
            )
            
            # 检测趋势市场
            trend_strength = tech_indicators.trend_strength(data['close'])
            adx_data = tech_indicators.adx(data['high'], data['low'], data['close'])
            adx = adx_data['adx']
            
            # 市场状态分类
            market_regime = pd.Series('unknown', index=data.index)
            
            # 震荡市场
            market_regime[sideways == 1] = 'sideways'
            
            # 强趋势市场
            strong_trend = (adx > 25) & (trend_strength > 0.6)
            market_regime[strong_trend] = 'trending'
            
            # 弱趋势市场
            weak_trend = (adx > 15) & (adx <= 25) & (trend_strength > 0.3)
            market_regime[weak_trend] = 'weak_trend'
            
            return market_regime
            
        except Exception as e:
            self.logger.error(f"市场状态检测失败: {e}")
            return pd.Series('unknown', index=data.index)
    
    def risk_adjustment(self, signals: pd.Series, data: pd.DataFrame) -> pd.Series:
        """风险调整信号"""
        try:
            # 计算ATR用于止损
            atr = tech_indicators.atr(data['high'], data['low'], data['close'])
            
            # 检测市场状态
            market_regime = self.market_regime_detection(data)
            
            # 调整后的信号
            adjusted_signals = signals.copy()
            
            # 在震荡市场中减弱信号强度
            sideways_mask = market_regime == 'sideways'
            adjusted_signals[sideways_mask] = adjusted_signals[sideways_mask] * 0.5
            
            # 在高波动期间降低信号强度
            high_volatility = atr > atr.rolling(window=20).mean() * 1.5
            adjusted_signals[high_volatility] = adjusted_signals[high_volatility] * 0.7
            
            return adjusted_signals.round().astype(int)
            
        except Exception as e:
            self.logger.error(f"风险调整失败: {e}")
            return signals
    
    def generate_trading_recommendation(self, data: pd.DataFrame) -> Dict:
        """生成交易建议"""
        try:
            # 获取综合信号
            signal_result = self.comprehensive_signal(data)
            
            if not signal_result:
                return {}
            
            final_signals = signal_result['final_signal']
            signal_strength = signal_result['signal_strength']
            
            # 风险调整
            adjusted_signals = self.risk_adjustment(final_signals, data)
            
            # 获取最新信号
            latest_signal = adjusted_signals.iloc[-1] if len(adjusted_signals) > 0 else 0
            latest_strength = signal_strength.iloc[-1] if len(signal_strength) > 0 else 0
            
            # 生成建议
            if latest_signal == 2:
                recommendation = "强烈买入"
                action = "建议开多仓或加仓"
            elif latest_signal == 1:
                recommendation = "买入"
                action = "建议小仓位做多"
            elif latest_signal == -1:
                recommendation = "卖出"
                action = "建议小仓位做空"
            elif latest_signal == -2:
                recommendation = "强烈卖出"
                action = "建议开空仓或加仓"
            else:
                recommendation = "观望"
                action = "建议保持当前仓位"
            
            # 计算支撑阻力位
            sr_levels = tech_indicators.support_resistance_levels(
                data['high'], data['low'], data['close']
            )
            
            current_price = data['close'].iloc[-1]
            
            return {
                'recommendation': recommendation,
                'action': action,
                'signal_strength': float(latest_strength),
                'current_price': float(current_price),
                'support_levels': sr_levels['support_levels'][:3],  # 前3个支撑位
                'resistance_levels': sr_levels['resistance_levels'][:3],  # 前3个阻力位
                'market_regime': self.market_regime_detection(data).iloc[-1],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"生成交易建议失败: {e}")
            return {}

# 全局交易信号生成器实例
signal_generator = TradingSignalGenerator()