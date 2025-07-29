"""
自定义指标编辑器
允许用户创建、编辑和保存自定义技术指标
"""
import pandas as pd
import numpy as np
import logging
import json
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import ast
import operator
from technical_indicators import tech_indicators

class CustomIndicatorBuilder:
    """自定义指标构建器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.indicators_dir = './custom_indicators'
        self.builtin_functions = self._init_builtin_functions()
        self.safe_operators = self._init_safe_operators()
        
        # 确保目录存在
        os.makedirs(self.indicators_dir, exist_ok=True)
    
    def _init_builtin_functions(self) -> Dict[str, Callable]:
        """初始化内置函数"""
        return {
            # 数学函数
            'abs': abs,
            'max': max,
            'min': min,
            'sum': sum,
            'mean': np.mean,
            'std': np.std,
            'sqrt': np.sqrt,
            'log': np.log,
            'exp': np.exp,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            
            # Pandas/NumPy函数
            'rolling': lambda x, window: x.rolling(window=window),
            'shift': lambda x, periods: x.shift(periods),
            'diff': lambda x, periods=1: x.diff(periods),
            'pct_change': lambda x: x.pct_change(),
            'cumsum': lambda x: x.cumsum(),
            'cummax': lambda x: x.cummax(),
            'cummin': lambda x: x.cummin(),
            'ewm': lambda x, span: x.ewm(span=span),
            'fillna': lambda x, value: x.fillna(value),
            'dropna': lambda x: x.dropna(),
            
            # 技术分析函数
            'sma': tech_indicators.sma,
            'ema': tech_indicators.ema,
            'wma': tech_indicators.wma,
            'rsi': tech_indicators.rsi,
            'atr': tech_indicators.atr,
            'macd': tech_indicators.macd,
            'bollinger_bands': tech_indicators.bollinger_bands,
            'stochastic': tech_indicators.stochastic,
            
            # 逻辑函数
            'where': np.where,
            'all': np.all,
            'any': np.any,
            'isna': pd.isna,
            'notna': pd.notna,
        }
    
    def _init_safe_operators(self) -> Dict[str, Any]:
        """初始化安全的操作符"""
        return {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: operator.and_,
            ast.Or: operator.or_,
            ast.Not: operator.not_,
        }
    
    def create_indicator(self, name: str, formula: str, description: str = "",
                        parameters: Dict[str, Any] = None) -> Dict:
        """创建自定义指标"""
        try:
            if parameters is None:
                parameters = {}
            
            # 验证指标名称
            if not name or not isinstance(name, str):
                raise ValueError("指标名称不能为空")
            
            if not formula or not isinstance(formula, str):
                raise ValueError("公式不能为空")
            
            # 验证公式语法
            validation_result = self.validate_formula(formula)
            if not validation_result['is_valid']:
                raise ValueError(f"公式验证失败: {validation_result['error']}")
            
            # 创建指标定义
            indicator_def = {
                'name': name,
                'formula': formula,
                'description': description,
                'parameters': parameters,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # 保存指标
            self.save_indicator(indicator_def)
            
            self.logger.info(f"创建自定义指标成功: {name}")
            return {
                'success': True,
                'message': f"指标 '{name}' 创建成功",
                'indicator': indicator_def
            }
            
        except Exception as e:
            self.logger.error(f"创建自定义指标失败: {e}")
            return {
                'success': False,
                'message': f"创建指标失败: {e}",
                'indicator': None
            }
    
    def validate_formula(self, formula: str) -> Dict:
        """验证公式语法和安全性"""
        try:
            # 解析AST
            tree = ast.parse(formula, mode='eval')
            
            # 检查是否包含不安全的操作
            validation_result = self._validate_ast_node(tree.body)
            
            if validation_result['is_valid']:
                return {
                    'is_valid': True,
                    'message': '公式验证通过',
                    'ast_tree': tree
                }
            else:
                return validation_result
                
        except SyntaxError as e:
            return {
                'is_valid': False,
                'error': f"语法错误: {e}",
                'message': '公式包含语法错误'
            }
        except Exception as e:
            return {
                'is_valid': False,
                'error': f"验证失败: {e}",
                'message': '公式验证失败'
            }
    
    def _validate_ast_node(self, node) -> Dict:
        """递归验证AST节点"""
        try:
            # 允许的节点类型
            safe_nodes = (
                ast.Expression, ast.BinOp, ast.UnaryOp, ast.Compare,
                ast.BoolOp, ast.Num, ast.Str, ast.NameConstant,
                ast.Name, ast.Load, ast.Store, ast.Call, ast.Attribute,
                ast.Subscript, ast.Index, ast.Slice, ast.List, ast.Tuple,
                ast.Constant  # Python 3.8+
            )
            
            if not isinstance(node, safe_nodes):
                return {
                    'is_valid': False,
                    'error': f"不允许的操作类型: {type(node).__name__}",
                    'message': '公式包含不安全的操作'
                }
            
            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name not in self.builtin_functions:
                        return {
                            'is_valid': False,
                            'error': f"未知函数: {func_name}",
                            'message': f"函数 '{func_name}' 不在允许的函数列表中"
                        }
                elif isinstance(node.func, ast.Attribute):
                    # 允许属性调用（如 data.rolling()）
                    pass
                else:
                    return {
                        'is_valid': False,
                        'error': "不允许的函数调用方式",
                        'message': '只允许调用预定义的函数'
                    }
            
            # 检查变量名
            if isinstance(node, ast.Name):
                var_name = node.id
                allowed_vars = ['open', 'high', 'low', 'close', 'volume', 'data', 'True', 'False', 'None']
                if var_name not in allowed_vars and var_name not in self.builtin_functions:
                    return {
                        'is_valid': False,
                        'error': f"未知变量: {var_name}",
                        'message': f"变量 '{var_name}' 不在允许的变量列表中"
                    }
            
            # 递归检查子节点
            for child in ast.iter_child_nodes(node):
                child_result = self._validate_ast_node(child)
                if not child_result['is_valid']:
                    return child_result
            
            return {'is_valid': True}
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f"节点验证失败: {e}",
                'message': '公式验证过程出错'
            }
    
    def evaluate_formula(self, formula: str, data: pd.DataFrame, 
                        parameters: Dict[str, Any] = None) -> pd.Series:
        """计算自定义指标"""
        try:
            if parameters is None:
                parameters = {}
            
            # 验证公式
            validation = self.validate_formula(formula)
            if not validation['is_valid']:
                raise ValueError(f"公式验证失败: {validation['error']}")
            
            # 准备执行环境
            env = self._create_execution_environment(data, parameters)
            
            # 编译并执行公式
            compiled_formula = compile(validation['ast_tree'], '<string>', 'eval')
            result = eval(compiled_formula, {"__builtins__": {}}, env)
            
            # 确保结果是Series
            if not isinstance(result, pd.Series):
                if isinstance(result, (int, float)):
                    result = pd.Series([result] * len(data), index=data.index)
                elif isinstance(result, np.ndarray):
                    result = pd.Series(result, index=data.index)
                else:
                    result = pd.Series(result, index=data.index)
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算自定义指标失败: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    def _create_execution_environment(self, data: pd.DataFrame, 
                                    parameters: Dict[str, Any]) -> Dict:
        """创建公式执行环境"""
        env = {}
        
        # 添加基础数据列
        if 'open' in data.columns:
            env['open'] = data['open']
        if 'high' in data.columns:
            env['high'] = data['high']
        if 'low' in data.columns:
            env['low'] = data['low']
        if 'close' in data.columns:
            env['close'] = data['close']
        if 'volume' in data.columns:
            env['volume'] = data['volume']
        
        # 添加整个数据框
        env['data'] = data
        
        # 添加参数
        env.update(parameters)
        
        # 添加内置函数
        env.update(self.builtin_functions)
        
        # 添加常量
        env.update({
            'True': True,
            'False': False,
            'None': None,
            'pi': np.pi,
            'e': np.e
        })
        
        return env
    
    def save_indicator(self, indicator_def: Dict) -> bool:
        """保存指标定义"""
        try:
            filename = f"{indicator_def['name']}.json"
            filepath = os.path.join(self.indicators_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(indicator_def, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"指标定义已保存: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存指标定义失败: {e}")
            return False
    
    def load_indicator(self, name: str) -> Optional[Dict]:
        """加载指标定义"""
        try:
            filename = f"{name}.json"
            filepath = os.path.join(self.indicators_dir, filename)
            
            if not os.path.exists(filepath):
                self.logger.warning(f"指标定义文件不存在: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                indicator_def = json.load(f)
            
            return indicator_def
            
        except Exception as e:
            self.logger.error(f"加载指标定义失败: {e}")
            return None
    
    def list_indicators(self) -> List[Dict]:
        """列出所有自定义指标"""
        try:
            indicators = []
            
            for filename in os.listdir(self.indicators_dir):
                if filename.endswith('.json'):
                    indicator_name = os.path.splitext(filename)[0]
                    indicator_def = self.load_indicator(indicator_name)
                    if indicator_def:
                        indicators.append(indicator_def)
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"列出指标失败: {e}")
            return []
    
    def delete_indicator(self, name: str) -> bool:
        """删除指标"""
        try:
            filename = f"{name}.json"
            filepath = os.path.join(self.indicators_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                self.logger.info(f"指标已删除: {name}")
                return True
            else:
                self.logger.warning(f"指标不存在: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除指标失败: {e}")
            return False
    
    def update_indicator(self, name: str, formula: str = None, 
                        description: str = None, parameters: Dict[str, Any] = None) -> Dict:
        """更新指标"""
        try:
            # 加载现有指标
            indicator_def = self.load_indicator(name)
            if not indicator_def:
                return {
                    'success': False,
                    'message': f"指标 '{name}' 不存在"
                }
            
            # 更新字段
            if formula is not None:
                validation_result = self.validate_formula(formula)
                if not validation_result['is_valid']:
                    return {
                        'success': False,
                        'message': f"公式验证失败: {validation_result['error']}"
                    }
                indicator_def['formula'] = formula
            
            if description is not None:
                indicator_def['description'] = description
            
            if parameters is not None:
                indicator_def['parameters'] = parameters
            
            indicator_def['updated_at'] = datetime.now().isoformat()
            
            # 保存更新后的指标
            self.save_indicator(indicator_def)
            
            return {
                'success': True,
                'message': f"指标 '{name}' 更新成功",
                'indicator': indicator_def
            }
            
        except Exception as e:
            self.logger.error(f"更新指标失败: {e}")
            return {
                'success': False,
                'message': f"更新指标失败: {e}"
            }
    
    def get_formula_help(self) -> Dict:
        """获取公式帮助信息"""
        return {
            'variables': {
                'open': '开盘价序列',
                'high': '最高价序列',
                'low': '最低价序列',
                'close': '收盘价序列',
                'volume': '成交量序列',
                'data': '完整数据框'
            },
            'functions': {
                '基础数学': {
                    'abs(x)': '绝对值',
                    'max(x)': '最大值',
                    'min(x)': '最小值',
                    'sum(x)': '求和',
                    'mean(x)': '平均值',
                    'std(x)': '标准差',
                    'sqrt(x)': '平方根',
                    'log(x)': '自然对数',
                    'exp(x)': '指数函数'
                },
                '序列操作': {
                    'rolling(x, window)': '滚动窗口',
                    'shift(x, periods)': '序列偏移',
                    'diff(x, periods)': '差分',
                    'pct_change(x)': '百分比变化',
                    'cumsum(x)': '累计求和',
                    'cummax(x)': '累计最大值',
                    'cummin(x)': '累计最小值',
                    'ewm(x, span)': '指数加权移动'
                },
                '技术指标': {
                    'sma(x, period)': '简单移动平均',
                    'ema(x, period)': '指数移动平均',
                    'rsi(x, period)': 'RSI指标',
                    'atr(high, low, close, period)': 'ATR指标',
                    'macd(x)': 'MACD指标'
                },
                '逻辑函数': {
                    'where(condition, x, y)': '条件选择',
                    'all(x)': '全部为真',
                    'any(x)': '任一为真',
                    'isna(x)': '检查缺失值',
                    'notna(x)': '检查非缺失值'
                }
            },
            'examples': {
                '简单移动平均': 'sma(close, 20)',
                'RSI': 'rsi(close, 14)',
                '布林带上轨': 'sma(close, 20) + 2 * rolling(close, 20).std()',
                '价格相对位置': '(close - sma(close, 20)) / sma(close, 20) * 100',
                '成交量比率': 'volume / sma(volume, 20)',
                '真实波幅': 'max(high - low, abs(high - shift(close, 1)), abs(low - shift(close, 1)))',
                '动量指标': 'close - shift(close, 10)',
                '威廉指标': '(shift(close, 1) - close) / (high - low) * 100'
            },
            'operators': {
                '算术运算': '+ - * / // % **',
                '比较运算': '== != < <= > >=',
                '逻辑运算': 'and or not'
            }
        }
    
    def test_indicator(self, formula: str, data: pd.DataFrame, 
                      parameters: Dict[str, Any] = None) -> Dict:
        """测试指标公式"""
        try:
            # 验证公式
            validation = self.validate_formula(formula)
            if not validation['is_valid']:
                return {
                    'success': False,
                    'message': validation['error'],
                    'result': None
                }
            
            # 计算结果
            result = self.evaluate_formula(formula, data, parameters)
            
            # 生成统计信息
            stats = {
                'count': len(result),
                'mean': float(result.mean()) if not result.empty else 0,
                'std': float(result.std()) if not result.empty else 0,
                'min': float(result.min()) if not result.empty else 0,
                'max': float(result.max()) if not result.empty else 0,
                'na_count': int(result.isna().sum())
            }
            
            return {
                'success': True,
                'message': '指标计算成功',
                'result': result,
                'stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"测试指标失败: {e}")
            return {
                'success': False,
                'message': f"测试失败: {e}",
                'result': None
            }

# 全局自定义指标构建器实例
custom_indicator_builder = CustomIndicatorBuilder()