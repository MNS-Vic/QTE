"""
策略引擎服务 - 负责创建和管理交易策略
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        self.name = name
        self.parameters = parameters
        self.positions = {}  # symbol -> quantity
        self.logger = logging.getLogger(f'Strategy.{name}')
    
    @abstractmethod
    def process_market_data(self, market_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理市场数据并生成交易信号
        
        Args:
            market_event: 市场事件数据
            
        Returns:
            交易信号字典，如果没有信号则返回None
        """
        pass
    
    def update_position(self, symbol: str, direction: int):
        """更新持仓"""
        if symbol not in self.positions:
            self.positions[symbol] = 0
        self.positions[symbol] += direction
    
    def get_position(self, symbol: str) -> int:
        """获取持仓"""
        return self.positions.get(symbol, 0)


class MovingAverageStrategy(BaseStrategy):
    """移动平均策略"""
    
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__("MovingAverage", parameters)
        
        self.short_window = parameters.get('short_window', 5)
        self.long_window = parameters.get('long_window', 15)
        
        # 价格历史
        self.price_history = {}
        
        self.logger.info(f"📈 移动平均策略初始化: 短期={self.short_window}, 长期={self.long_window}")
    
    def process_market_data(self, market_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理市场数据"""
        symbol = market_event.get('symbol')
        close_price = market_event.get('close_price')
        timestamp = market_event.get('timestamp')
        
        if not symbol or close_price is None:
            return None
        
        # 更新价格历史
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(close_price)
        
        # 保持历史长度
        max_history = max(self.short_window, self.long_window) + 10
        if len(self.price_history[symbol]) > max_history:
            self.price_history[symbol] = self.price_history[symbol][-max_history:]
        
        # 检查是否有足够的数据
        if len(self.price_history[symbol]) < self.long_window:
            return None
        
        # 计算移动平均
        prices = self.price_history[symbol]
        short_ma = sum(prices[-self.short_window:]) / self.short_window
        long_ma = sum(prices[-self.long_window:]) / self.long_window
        
        # 生成交易信号
        current_position = self.get_position(symbol)
        
        # 金叉：短期均线上穿长期均线，买入信号
        if short_ma > long_ma and current_position <= 0:
            return {
                'symbol': symbol,
                'timestamp': timestamp,
                'signal_type': 'LONG',
                'direction': 1,
                'strength': 1.0,
                'reason': f'金叉信号: 短期MA({short_ma:.2f}) > 长期MA({long_ma:.2f})'
            }
        
        # 死叉：短期均线下穿长期均线，卖出信号
        elif short_ma < long_ma and current_position >= 0:
            return {
                'symbol': symbol,
                'timestamp': timestamp,
                'signal_type': 'SHORT',
                'direction': -1,
                'strength': 1.0,
                'reason': f'死叉信号: 短期MA({short_ma:.2f}) < 长期MA({long_ma:.2f})'
            }
        
        return None


class MomentumStrategy(BaseStrategy):
    """动量策略"""
    
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__("Momentum", parameters)
        
        self.lookback_period = parameters.get('lookback_period', 10)
        self.momentum_threshold = parameters.get('momentum_threshold', 0.02)
        
        self.price_history = {}
        
        self.logger.info(f"🚀 动量策略初始化: 回看期={self.lookback_period}, 阈值={self.momentum_threshold}")
    
    def process_market_data(self, market_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理市场数据"""
        symbol = market_event.get('symbol')
        close_price = market_event.get('close_price')
        timestamp = market_event.get('timestamp')
        
        if not symbol or close_price is None:
            return None
        
        # 更新价格历史
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(close_price)
        
        # 检查是否有足够的数据
        if len(self.price_history[symbol]) < self.lookback_period + 1:
            return None
        
        # 计算动量
        prices = self.price_history[symbol]
        current_price = prices[-1]
        past_price = prices[-(self.lookback_period + 1)]
        
        momentum = (current_price - past_price) / past_price
        
        # 生成交易信号
        current_position = self.get_position(symbol)
        
        # 正动量：价格上涨超过阈值
        if momentum > self.momentum_threshold and current_position <= 0:
            return {
                'symbol': symbol,
                'timestamp': timestamp,
                'signal_type': 'LONG',
                'direction': 1,
                'strength': min(momentum / self.momentum_threshold, 2.0),
                'reason': f'正动量信号: {momentum:.2%} > {self.momentum_threshold:.2%}'
            }
        
        # 负动量：价格下跌超过阈值
        elif momentum < -self.momentum_threshold and current_position >= 0:
            return {
                'symbol': symbol,
                'timestamp': timestamp,
                'signal_type': 'SHORT',
                'direction': -1,
                'strength': min(abs(momentum) / self.momentum_threshold, 2.0),
                'reason': f'负动量信号: {momentum:.2%} < {-self.momentum_threshold:.2%}'
            }
        
        return None


class StrategyEngineService:
    """策略引擎服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化策略引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger('StrategyEngineService')
        
        # 注册可用策略
        self.available_strategies = {
            'moving_average': MovingAverageStrategy,
            'momentum': MomentumStrategy
        }
        
        self.logger.info(f"🧠 策略引擎初始化完成，可用策略: {list(self.available_strategies.keys())}")
    
    def create_strategy(self, strategy_type: str, parameters: Optional[Dict[str, Any]] = None) -> BaseStrategy:
        """
        创建策略实例
        
        Args:
            strategy_type: 策略类型
            parameters: 策略参数
            
        Returns:
            策略实例
            
        Raises:
            ValueError: 当策略类型不存在时
        """
        if strategy_type not in self.available_strategies:
            available = list(self.available_strategies.keys())
            raise ValueError(f"未知的策略类型: {strategy_type}，可用策略: {available}")
        
        # 合并默认参数和用户参数
        default_params = self._get_default_parameters(strategy_type)
        final_params = {**default_params, **(parameters or {})}
        
        strategy_class = self.available_strategies[strategy_type]
        strategy = strategy_class(final_params)
        
        self.logger.info(f"✅ 策略创建成功: {strategy_type}")
        return strategy
    
    def _get_default_parameters(self, strategy_type: str) -> Dict[str, Any]:
        """获取策略默认参数"""
        defaults = {
            'moving_average': {
                'short_window': self.config.get('short_window', 5),
                'long_window': self.config.get('long_window', 15)
            },
            'momentum': {
                'lookback_period': self.config.get('lookback_period', 10),
                'momentum_threshold': self.config.get('momentum_threshold', 0.02)
            }
        }
        
        return defaults.get(strategy_type, {})
    
    def list_available_strategies(self) -> List[str]:
        """列出可用策略"""
        return list(self.available_strategies.keys())
    
    def get_strategy_info(self, strategy_type: str) -> Dict[str, Any]:
        """获取策略信息"""
        if strategy_type not in self.available_strategies:
            return {}
        
        strategy_class = self.available_strategies[strategy_type]
        default_params = self._get_default_parameters(strategy_type)
        
        return {
            'name': strategy_type,
            'class': strategy_class.__name__,
            'description': strategy_class.__doc__ or "无描述",
            'default_parameters': default_params
        }
    
    def register_strategy(self, name: str, strategy_class: type):
        """
        注册新策略
        
        Args:
            name: 策略名称
            strategy_class: 策略类
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError("策略类必须继承自BaseStrategy")
        
        self.available_strategies[name] = strategy_class
        self.logger.info(f"📝 注册新策略: {name}")
    
    def validate_strategy_parameters(self, strategy_type: str, parameters: Dict[str, Any]) -> bool:
        """
        验证策略参数
        
        Args:
            strategy_type: 策略类型
            parameters: 参数字典
            
        Returns:
            验证是否通过
        """
        if strategy_type not in self.available_strategies:
            return False
        
        # 这里可以添加更复杂的参数验证逻辑
        # 目前只做基本检查
        if strategy_type == 'moving_average':
            short_window = parameters.get('short_window', 5)
            long_window = parameters.get('long_window', 15)
            return short_window > 0 and long_window > short_window
        
        elif strategy_type == 'momentum':
            lookback_period = parameters.get('lookback_period', 10)
            momentum_threshold = parameters.get('momentum_threshold', 0.02)
            return lookback_period > 0 and 0 < momentum_threshold < 1
        
        return True
