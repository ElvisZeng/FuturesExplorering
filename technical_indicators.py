"""
技术指标模块
包含各种技术分析指标的计算
"""
import numpy as np
import pandas as pd
import logging
from typing import Tuple, Dict, List, Optional
from datetime import datetime, timedelta

class TechnicalIndicators:
    """技术指标计算类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # 基础移动平均线
    def sma(self, data: pd.Series, period: int) -> pd.Series:
        """简单移动平均线 (Simple Moving Average)"""
        try:
            return data.rolling(window=period).mean()
        except Exception as e:
            self.logger.error(f"SMA计算失败: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def ema(self, data: pd.Series, period: int) -> pd.Series:
        """指数移动平均线 (Exponential Moving Average)"""
        try:
            return data.ewm(span=period).mean()
        except Exception as e:
            self.logger.error(f"EMA计算失败: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def wma(self, data: pd.Series, period: int) -> pd.Series:
        """加权移动平均线 (Weighted Moving Average)"""
        try:
            weights = np.arange(1, period + 1)
            def weighted_mean(x):
                if len(x) == period:
                    return np.sum(weights * x) / np.sum(weights)
                return np.nan
            
            return data.rolling(window=period).apply(weighted_mean, raw=True)
        except Exception as e:
            self.logger.error(f"WMA计算失败: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    # 趋势指标
    def macd(self, price: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD指标"""
        try:
            ema_fast = self.ema(price, fast)
            ema_slow = self.ema(price, slow)
            
            macd_line = ema_fast - ema_slow
            signal_line = self.ema(macd_line, signal)
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except Exception as e:
            self.logger.error(f"MACD计算失败: {e}")
            return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}
    
    def rsi(self, price: pd.Series, period: int = 14) -> pd.Series:
        """相对强弱指标 (RSI)"""
        try:
            delta = price.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            self.logger.error(f"RSI计算失败: {e}")
            return pd.Series(index=price.index, dtype=float)
    
    def bollinger_bands(self, price: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """布林带"""
        try:
            middle = self.sma(price, period)
            std = price.rolling(window=period).std()
            
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower,
                'bandwidth': (upper - lower) / middle * 100
            }
        except Exception as e:
            self.logger.error(f"布林带计算失败: {e}")
            return {'upper': pd.Series(), 'middle': pd.Series(), 'lower': pd.Series(), 'bandwidth': pd.Series()}
    
    # 维科夫量价分析指标
    def wyckoff_accumulation_distribution(self, high: pd.Series, low: pd.Series, 
                                        close: pd.Series, volume: pd.Series) -> pd.Series:
        """维科夫累积/分布指标"""
        try:
            # 计算价格区间的中点
            money_flow_multiplier = ((close - low) - (high - close)) / (high - low)
            money_flow_multiplier = money_flow_multiplier.fillna(0)
            
            # 计算资金流量
            money_flow_volume = money_flow_multiplier * volume
            
            # 累积资金流量
            ad_line = money_flow_volume.cumsum()
            
            return ad_line
        except Exception as e:
            self.logger.error(f"维科夫累积/分布计算失败: {e}")
            return pd.Series(index=close.index, dtype=float)
    
    def wyckoff_price_volume_trend(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """维科夫价量趋势指标"""
        try:
            price_change = close.pct_change()
            pvt = (price_change * volume).cumsum()
            
            return pvt
        except Exception as e:
            self.logger.error(f"维科夫价量趋势计算失败: {e}")
            return pd.Series(index=close.index, dtype=float)
    
    def volume_profile(self, high: pd.Series, low: pd.Series, 
                      close: pd.Series, volume: pd.Series, bins: int = 20) -> Dict:
        """成交量分布"""
        try:
            price_range = np.linspace(low.min(), high.max(), bins + 1)
            volume_at_price = np.zeros(bins)
            
            for i in range(len(close)):
                if pd.notna(close.iloc[i]) and pd.notna(volume.iloc[i]):
                    price_bin = np.digitize(close.iloc[i], price_range) - 1
                    if 0 <= price_bin < bins:
                        volume_at_price[price_bin] += volume.iloc[i]
            
            price_levels = (price_range[:-1] + price_range[1:]) / 2
            
            # 找到最大成交量价位（POC - Point of Control）
            poc_index = np.argmax(volume_at_price)
            poc_price = price_levels[poc_index]
            
            return {
                'price_levels': price_levels,
                'volume_at_price': volume_at_price,
                'poc_price': poc_price,
                'total_volume': volume.sum()
            }
        except Exception as e:
            self.logger.error(f"成交量分布计算失败: {e}")
            return {}
    
    def support_resistance_levels(self, high: pd.Series, low: pd.Series, 
                                 close: pd.Series, lookback: int = 20) -> Dict:
        """支撑阻力位识别"""
        try:
            # 寻找局部高点和低点
            highs = []
            lows = []
            
            for i in range(lookback, len(close) - lookback):
                # 检查是否为局部高点
                if high.iloc[i] == high.iloc[i-lookback:i+lookback+1].max():
                    highs.append((close.index[i], high.iloc[i]))
                
                # 检查是否为局部低点
                if low.iloc[i] == low.iloc[i-lookback:i+lookback+1].min():
                    lows.append((close.index[i], low.iloc[i]))
            
            # 统计价格出现频率
            all_levels = [level for _, level in highs + lows]
            
            if not all_levels:
                return {'resistance_levels': [], 'support_levels': []}
            
            # 使用聚类找到主要支撑阻力位
            price_range = max(all_levels) - min(all_levels)
            tolerance = price_range * 0.02  # 2%的容忍度
            
            resistance_levels = []
            support_levels = []
            
            for _, level in highs:
                # 检查是否与现有阻力位接近
                is_new = True
                for existing in resistance_levels:
                    if abs(level - existing) <= tolerance:
                        is_new = False
                        break
                if is_new:
                    resistance_levels.append(level)
            
            for _, level in lows:
                # 检查是否与现有支撑位接近
                is_new = True
                for existing in support_levels:
                    if abs(level - existing) <= tolerance:
                        is_new = False
                        break
                if is_new:
                    support_levels.append(level)
            
            return {
                'resistance_levels': sorted(resistance_levels, reverse=True),
                'support_levels': sorted(support_levels)
            }
        except Exception as e:
            self.logger.error(f"支撑阻力位计算失败: {e}")
            return {'resistance_levels': [], 'support_levels': []}
    
    # 震荡识别指标
    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """平均真实范围 (Average True Range)"""
        try:
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return atr
        except Exception as e:
            self.logger.error(f"ATR计算失败: {e}")
            return pd.Series(index=close.index, dtype=float)
    
    def adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """平均方向指数 (ADX)"""
        try:
            # 计算方向移动
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            plus_dm = pd.Series(plus_dm, index=close.index)
            minus_dm = pd.Series(minus_dm, index=close.index)
            
            # 计算真实范围
            atr_values = self.atr(high, low, close, period)
            
            # 计算方向指标
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_values)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_values)
            
            # 计算ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            return {
                'adx': adx,
                'plus_di': plus_di,
                'minus_di': minus_di
            }
        except Exception as e:
            self.logger.error(f"ADX计算失败: {e}")
            return {'adx': pd.Series(), 'plus_di': pd.Series(), 'minus_di': pd.Series()}
    
    def stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                  k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """随机指标 (KD)"""
        try:
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            
            k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'k': k_percent,
                'd': d_percent
            }
        except Exception as e:
            self.logger.error(f"随机指标计算失败: {e}")
            return {'k': pd.Series(), 'd': pd.Series()}
    
    # 趋势强度和震荡识别
    def trend_strength(self, close: pd.Series, period: int = 20) -> pd.Series:
        """趋势强度指标"""
        try:
            # 使用线性回归计算趋势强度
            def calculate_r_squared(y):
                if len(y) < period:
                    return np.nan
                
                x = np.arange(len(y))
                if np.std(y) == 0:
                    return 0
                
                correlation = np.corrcoef(x, y)[0, 1]
                return correlation ** 2 if not np.isnan(correlation) else 0
            
            r_squared = close.rolling(window=period).apply(calculate_r_squared, raw=True)
            
            return r_squared
        except Exception as e:
            self.logger.error(f"趋势强度计算失败: {e}")
            return pd.Series(index=close.index, dtype=float)
    
    def sideways_market_detection(self, high: pd.Series, low: pd.Series, 
                                 close: pd.Series, period: int = 20, 
                                 threshold: float = 0.02) -> pd.Series:
        """横盘震荡识别"""
        try:
            # 计算价格波动范围
            price_range = (high.rolling(window=period).max() - 
                          low.rolling(window=period).min()) / close
            
            # 计算趋势强度
            trend_strength = self.trend_strength(close, period)
            
            # 震荡市场：价格波动小且趋势强度弱
            is_sideways = (price_range < threshold) & (trend_strength < 0.3)
            
            return is_sideways.astype(int)
        except Exception as e:
            self.logger.error(f"震荡识别计算失败: {e}")
            return pd.Series(index=close.index, dtype=int)
    
    def breakout_potential(self, high: pd.Series, low: pd.Series, 
                          close: pd.Series, volume: pd.Series, 
                          period: int = 20) -> Dict[str, pd.Series]:
        """突破潜力分析"""
        try:
            # 计算布林带收缩
            bb = self.bollinger_bands(close, period)
            bb_squeeze = bb['bandwidth'] < bb['bandwidth'].rolling(window=period).mean() * 0.8
            
            # 计算成交量异常
            avg_volume = volume.rolling(window=period).mean()
            volume_spike = volume > avg_volume * 1.5
            
            # 计算价格接近边界
            near_resistance = close > high.rolling(window=period).max() * 0.98
            near_support = close < low.rolling(window=period).min() * 1.02
            
            # 综合突破信号
            breakout_up_potential = bb_squeeze & volume_spike & near_resistance
            breakout_down_potential = bb_squeeze & volume_spike & near_support
            
            return {
                'breakout_up': breakout_up_potential.astype(int),
                'breakout_down': breakout_down_potential.astype(int),
                'bb_squeeze': bb_squeeze.astype(int),
                'volume_spike': volume_spike.astype(int)
            }
        except Exception as e:
            self.logger.error(f"突破潜力分析失败: {e}")
            return {
                'breakout_up': pd.Series(dtype=int),
                'breakout_down': pd.Series(dtype=int),
                'bb_squeeze': pd.Series(dtype=int),
                'volume_spike': pd.Series(dtype=int)
            }
    
    # 综合分析
    def comprehensive_analysis(self, data: pd.DataFrame) -> Dict:
        """综合技术分析"""
        try:
            required_columns = ['high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_columns):
                raise ValueError(f"数据必须包含列: {required_columns}")
            
            result = {}
            
            # 基础移动平均线
            result['sma_5'] = self.sma(data['close'], 5)
            result['sma_20'] = self.sma(data['close'], 20)
            result['sma_60'] = self.sma(data['close'], 60)
            result['ema_12'] = self.ema(data['close'], 12)
            result['ema_26'] = self.ema(data['close'], 26)
            
            # 趋势指标
            macd_data = self.macd(data['close'])
            result.update(macd_data)
            
            result['rsi'] = self.rsi(data['close'])
            
            bb_data = self.bollinger_bands(data['close'])
            result.update(bb_data)
            
            # 维科夫分析
            result['wyckoff_ad'] = self.wyckoff_accumulation_distribution(
                data['high'], data['low'], data['close'], data['volume']
            )
            result['wyckoff_pvt'] = self.wyckoff_price_volume_trend(data['close'], data['volume'])
            
            # 震荡和趋势分析
            result['atr'] = self.atr(data['high'], data['low'], data['close'])
            
            adx_data = self.adx(data['high'], data['low'], data['close'])
            result.update(adx_data)
            
            result['trend_strength'] = self.trend_strength(data['close'])
            result['sideways_market'] = self.sideways_market_detection(
                data['high'], data['low'], data['close']
            )
            
            # 突破分析
            breakout_data = self.breakout_potential(
                data['high'], data['low'], data['close'], data['volume']
            )
            result.update(breakout_data)
            
            # 支撑阻力位
            sr_levels = self.support_resistance_levels(
                data['high'], data['low'], data['close']
            )
            result['support_resistance'] = sr_levels
            
            return result
            
        except Exception as e:
            self.logger.error(f"综合分析失败: {e}")
            return {}

# 全局技术指标实例
tech_indicators = TechnicalIndicators()