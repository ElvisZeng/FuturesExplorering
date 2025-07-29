"""
回测引擎模块
支持基于交易信号的策略回测和性能分析
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from trading_signals import signal_generator
from technical_indicators import tech_indicators

class Position:
    """持仓类"""
    
    def __init__(self, symbol: str, direction: str, size: float, entry_price: float, 
                 entry_date: str, stop_loss: float = None, take_profit: float = None):
        self.symbol = symbol
        self.direction = direction  # 'long' or 'short'
        self.size = size
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.exit_price = None
        self.exit_date = None
        self.is_closed = False
    
    def update_unrealized_pnl(self, current_price: float):
        """更新未实现盈亏"""
        if not self.is_closed:
            if self.direction == 'long':
                self.unrealized_pnl = (current_price - self.entry_price) * self.size
            else:  # short
                self.unrealized_pnl = (self.entry_price - current_price) * self.size
    
    def close_position(self, exit_price: float, exit_date: str):
        """平仓"""
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.is_closed = True
        
        if self.direction == 'long':
            self.realized_pnl = (exit_price - self.entry_price) * self.size
        else:  # short
            self.realized_pnl = (self.entry_price - exit_price) * self.size
        
        self.unrealized_pnl = 0.0
    
    def check_stop_loss_take_profit(self, current_price: float) -> bool:
        """检查是否触及止损或止盈"""
        if self.is_closed:
            return False
        
        if self.direction == 'long':
            if self.stop_loss and current_price <= self.stop_loss:
                return True
            if self.take_profit and current_price >= self.take_profit:
                return True
        else:  # short
            if self.stop_loss and current_price >= self.stop_loss:
                return True
            if self.take_profit and current_price <= self.take_profit:
                return True
        
        return False

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.0003,
                 slippage: float = 0.0001, position_size_pct: float = 0.1):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission = commission  # 手续费率
        self.slippage = slippage      # 滑点
        self.position_size_pct = position_size_pct  # 每次交易占用资金比例
        
        self.positions = []  # 所有持仓记录
        self.open_positions = []  # 当前持仓
        self.trades = []  # 交易记录
        self.equity_curve = []  # 资金曲线
        self.daily_returns = []  # 日收益率
        
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, price: float, atr: float = None) -> float:
        """计算仓位大小"""
        try:
            # 基于固定比例的仓位大小
            position_value = self.current_capital * self.position_size_pct
            position_size = position_value / price
            
            # 如果有ATR，可以基于风险调整仓位
            if atr and atr > 0:
                # 风险调整：限制单笔交易风险在2%以内
                risk_per_trade = self.current_capital * 0.02
                position_size_risk_adjusted = risk_per_trade / (atr * 2)  # 2倍ATR作为止损
                position_size = min(position_size, position_size_risk_adjusted)
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"计算仓位大小失败: {e}")
            return 0
    
    def calculate_stop_loss_take_profit(self, entry_price: float, direction: str, 
                                      atr: float = None) -> Tuple[float, float]:
        """计算止损和止盈价格"""
        try:
            if atr and atr > 0:
                # 基于ATR的止损止盈
                if direction == 'long':
                    stop_loss = entry_price - (atr * 2)
                    take_profit = entry_price + (atr * 3)
                else:  # short
                    stop_loss = entry_price + (atr * 2)
                    take_profit = entry_price - (atr * 3)
            else:
                # 固定百分比止损止盈
                if direction == 'long':
                    stop_loss = entry_price * 0.97  # 3%止损
                    take_profit = entry_price * 1.06  # 6%止盈
                else:  # short
                    stop_loss = entry_price * 1.03  # 3%止损
                    take_profit = entry_price * 0.94  # 6%止盈
            
            return stop_loss, take_profit
            
        except Exception as e:
            self.logger.error(f"计算止损止盈失败: {e}")
            return None, None
    
    def open_position(self, symbol: str, direction: str, price: float, 
                     date: str, atr: float = None) -> bool:
        """开仓"""
        try:
            # 计算仓位大小
            position_size = self.calculate_position_size(price, atr)
            
            if position_size <= 0:
                return False
            
            # 计算成交价格（考虑滑点）
            if direction == 'long':
                execution_price = price * (1 + self.slippage)
            else:  # short
                execution_price = price * (1 - self.slippage)
            
            # 计算交易成本
            trade_value = position_size * execution_price
            commission_cost = trade_value * self.commission
            
            # 检查资金是否充足
            required_capital = trade_value + commission_cost
            if required_capital > self.current_capital:
                self.logger.warning(f"资金不足，无法开仓: 需要{required_capital}, 可用{self.current_capital}")
                return False
            
            # 计算止损止盈
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(execution_price, direction, atr)
            
            # 创建持仓
            position = Position(
                symbol=symbol,
                direction=direction,
                size=position_size,
                entry_price=execution_price,
                entry_date=date,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # 更新资金
            self.current_capital -= commission_cost
            
            # 记录持仓和交易
            self.positions.append(position)
            self.open_positions.append(position)
            
            self.trades.append({
                'date': date,
                'symbol': symbol,
                'action': f'OPEN_{direction.upper()}',
                'price': execution_price,
                'size': position_size,
                'commission': commission_cost,
                'capital': self.current_capital
            })
            
            self.logger.info(f"开仓成功: {direction} {symbol} @{execution_price}, 数量: {position_size}")
            return True
            
        except Exception as e:
            self.logger.error(f"开仓失败: {e}")
            return False
    
    def close_position(self, position: Position, price: float, date: str, reason: str = 'signal') -> bool:
        """平仓"""
        try:
            if position.is_closed:
                return False
            
            # 计算成交价格（考虑滑点）
            if position.direction == 'long':
                execution_price = price * (1 - self.slippage)
            else:  # short
                execution_price = price * (1 + self.slippage)
            
            # 计算交易成本
            trade_value = position.size * execution_price
            commission_cost = trade_value * self.commission
            
            # 平仓
            position.close_position(execution_price, date)
            
            # 更新资金
            self.current_capital += trade_value - commission_cost + position.realized_pnl
            
            # 从开仓列表中移除
            if position in self.open_positions:
                self.open_positions.remove(position)
            
            # 记录交易
            self.trades.append({
                'date': date,
                'symbol': position.symbol,
                'action': f'CLOSE_{position.direction.upper()}',
                'price': execution_price,
                'size': position.size,
                'commission': commission_cost,
                'pnl': position.realized_pnl,
                'capital': self.current_capital,
                'reason': reason
            })
            
            self.logger.info(f"平仓成功: {position.direction} {position.symbol} @{execution_price}, "
                           f"盈亏: {position.realized_pnl:.2f}, 原因: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"平仓失败: {e}")
            return False
    
    def update_positions(self, current_price: float, date: str):
        """更新持仓状态"""
        try:
            positions_to_close = []
            
            for position in self.open_positions:
                # 更新未实现盈亏
                position.update_unrealized_pnl(current_price)
                
                # 检查止损止盈
                if position.check_stop_loss_take_profit(current_price):
                    positions_to_close.append((position, 'stop_loss_take_profit'))
            
            # 执行止损止盈平仓
            for position, reason in positions_to_close:
                self.close_position(position, current_price, date, reason)
                
        except Exception as e:
            self.logger.error(f"更新持仓状态失败: {e}")
    
    def calculate_portfolio_value(self, current_price: float) -> float:
        """计算组合总价值"""
        try:
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.open_positions)
            return self.current_capital + total_unrealized_pnl
        except Exception as e:
            self.logger.error(f"计算组合价值失败: {e}")
            return self.current_capital
    
    def run_backtest(self, data: pd.DataFrame, symbol: str = 'unknown') -> Dict:
        """运行回测"""
        try:
            self.logger.info(f"开始回测: {symbol}, 数据长度: {len(data)}")
            
            # 生成交易信号
            signal_result = signal_generator.comprehensive_signal(data)
            if not signal_result:
                self.logger.error("无法生成交易信号")
                return {}
            
            signals = signal_result['final_signal']
            
            # 计算ATR用于风险管理
            atr = tech_indicators.atr(data['high'], data['low'], data['close'])
            
            # 遍历数据执行回测
            for i, (date, row) in enumerate(data.iterrows()):
                current_price = row['close']
                current_atr = atr.iloc[i] if i < len(atr) and pd.notna(atr.iloc[i]) else None
                signal = signals.iloc[i] if i < len(signals) else 0
                
                # 更新持仓状态
                self.update_positions(current_price, str(date))
                
                # 处理交易信号
                if signal > 0:  # 买入信号
                    # 如果有空头持仓，先平仓
                    short_positions = [pos for pos in self.open_positions if pos.direction == 'short']
                    for pos in short_positions:
                        self.close_position(pos, current_price, str(date), 'signal_reversal')
                    
                    # 开多头仓位
                    if not any(pos.direction == 'long' for pos in self.open_positions):
                        self.open_position(symbol, 'long', current_price, str(date), current_atr)
                
                elif signal < 0:  # 卖出信号
                    # 如果有多头持仓，先平仓
                    long_positions = [pos for pos in self.open_positions if pos.direction == 'long']
                    for pos in long_positions:
                        self.close_position(pos, current_price, str(date), 'signal_reversal')
                    
                    # 开空头仓位
                    if not any(pos.direction == 'short' for pos in self.open_positions):
                        self.open_position(symbol, 'short', current_price, str(date), current_atr)
                
                # 记录每日组合价值
                portfolio_value = self.calculate_portfolio_value(current_price)
                self.equity_curve.append({
                    'date': date,
                    'portfolio_value': portfolio_value,
                    'capital': self.current_capital,
                    'unrealized_pnl': sum(pos.unrealized_pnl for pos in self.open_positions),
                    'open_positions': len(self.open_positions)
                })
                
                # 计算日收益率
                if len(self.equity_curve) > 1:
                    prev_value = self.equity_curve[-2]['portfolio_value']
                    daily_return = (portfolio_value - prev_value) / prev_value if prev_value > 0 else 0
                    self.daily_returns.append(daily_return)
                else:
                    self.daily_returns.append(0)
            
            # 平仓所有剩余持仓
            final_price = data['close'].iloc[-1]
            final_date = str(data.index[-1])
            for position in self.open_positions.copy():
                self.close_position(position, final_price, final_date, 'backtest_end')
            
            # 生成回测报告
            return self.generate_backtest_report()
            
        except Exception as e:
            self.logger.error(f"回测执行失败: {e}")
            return {}
    
    def generate_backtest_report(self) -> Dict:
        """生成回测报告"""
        try:
            if not self.equity_curve:
                return {}
            
            # 基础统计
            total_trades = len([t for t in self.trades if 'CLOSE' in t['action']])
            winning_trades = len([t for t in self.trades if 'CLOSE' in t['action'] and t.get('pnl', 0) > 0])
            losing_trades = total_trades - winning_trades
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # 收益统计
            total_return = (self.current_capital - self.initial_capital) / self.initial_capital
            
            # 日收益率统计
            daily_returns_array = np.array(self.daily_returns)
            annual_return = np.mean(daily_returns_array) * 252 if len(daily_returns_array) > 0 else 0
            volatility = np.std(daily_returns_array) * np.sqrt(252) if len(daily_returns_array) > 0 else 0
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # 最大回撤
            equity_values = [eq['portfolio_value'] for eq in self.equity_curve]
            peak = np.maximum.accumulate(equity_values)
            drawdown = (peak - equity_values) / peak
            max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
            
            # 盈亏比
            winning_pnls = [t.get('pnl', 0) for t in self.trades if 'CLOSE' in t['action'] and t.get('pnl', 0) > 0]
            losing_pnls = [abs(t.get('pnl', 0)) for t in self.trades if 'CLOSE' in t['action'] and t.get('pnl', 0) < 0]
            
            avg_win = np.mean(winning_pnls) if winning_pnls else 0
            avg_loss = np.mean(losing_pnls) if losing_pnls else 0
            profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
            
            report = {
                'summary': {
                    'initial_capital': self.initial_capital,
                    'final_capital': self.current_capital,
                    'total_return': total_return,
                    'annual_return': annual_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': win_rate,
                    'profit_factor': profit_factor,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss
                },
                'equity_curve': self.equity_curve,
                'daily_returns': self.daily_returns,
                'trades': self.trades,
                'positions': [pos.__dict__ for pos in self.positions]
            }
            
            self.logger.info(f"回测完成 - 总收益率: {total_return:.2%}, 夏普比率: {sharpe_ratio:.2f}, "
                           f"最大回撤: {max_drawdown:.2%}, 胜率: {win_rate:.2%}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成回测报告失败: {e}")
            return {}
    
    def plot_results(self, report: Dict, save_path: str = None):
        """绘制回测结果"""
        try:
            if not report or 'equity_curve' not in report:
                return
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('回测结果分析', fontsize=16)
            
            # 资金曲线
            equity_curve = report['equity_curve']
            dates = [eq['date'] for eq in equity_curve]
            values = [eq['portfolio_value'] for eq in equity_curve]
            
            axes[0, 0].plot(dates, values, linewidth=2, color='blue')
            axes[0, 0].set_title('资金曲线')
            axes[0, 0].set_ylabel('组合价值')
            axes[0, 0].grid(True, alpha=0.3)
            
            # 回撤图
            peak = np.maximum.accumulate(values)
            drawdown = (peak - values) / peak * 100
            axes[0, 1].fill_between(dates, 0, -drawdown, color='red', alpha=0.3)
            axes[0, 1].set_title('回撤分析')
            axes[0, 1].set_ylabel('回撤 (%)')
            axes[0, 1].grid(True, alpha=0.3)
            
            # 日收益率分布
            daily_returns = np.array(report['daily_returns']) * 100
            axes[1, 0].hist(daily_returns, bins=50, alpha=0.7, color='green')
            axes[1, 0].set_title('日收益率分布')
            axes[1, 0].set_xlabel('日收益率 (%)')
            axes[1, 0].set_ylabel('频数')
            axes[1, 0].grid(True, alpha=0.3)
            
            # 月度收益率
            if len(equity_curve) > 30:
                monthly_values = values[::21]  # 假设每月21个交易日
                monthly_returns = [(monthly_values[i] - monthly_values[i-1]) / monthly_values[i-1] * 100 
                                 for i in range(1, len(monthly_values))]
                axes[1, 1].bar(range(len(monthly_returns)), monthly_returns, 
                              color=['green' if r > 0 else 'red' for r in monthly_returns])
                axes[1, 1].set_title('月度收益率')
                axes[1, 1].set_xlabel('月份')
                axes[1, 1].set_ylabel('收益率 (%)')
                axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            plt.show()
            
        except Exception as e:
            self.logger.error(f"绘制回测结果失败: {e}")

# 全局回测引擎实例
backtest_engine = BacktestEngine()