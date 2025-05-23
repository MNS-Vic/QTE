#!/usr/bin/env python3
"""
市场数据管理模块

提供市场数据的存储、查询和更新功能
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

logger = logging.getLogger(__name__)


class MarketDataManager:
    """市场数据管理器
    
    管理所有交易标的的市场数据，包括：
    - 实时价格数据
    - 历史价格记录
    - 成交量数据
    - 深度数据
    """
    
    def __init__(self, max_history_size: int = 1000):
        """初始化市场数据管理器
        
        Args:
            max_history_size: 每个标的保留的最大历史记录数
        """
        self.max_history_size = max_history_size
        
        # 当前市场数据
        self.current_data: Dict[str, dict] = {}
        
        # 历史数据（使用deque限制大小）
        self.history_data: Dict[str, deque] = {}
        
        # 最新价格
        self.latest_prices: Dict[str, float] = {}
        
        # 深度数据
        self.depth_data: Dict[str, dict] = {}
        
        logger.info("市场数据管理器初始化完成")
    
    def update_market_data(self, symbol: str, data: dict) -> None:
        """更新市场数据
        
        Args:
            symbol: 交易标的
            data: 市场数据字典
        """
        try:
            # 更新当前数据
            self.current_data[symbol] = data
            
            # 更新最新价格
            if 'price' in data:
                self.latest_prices[symbol] = float(data['price'])
            
            # 添加到历史记录
            if symbol not in self.history_data:
                self.history_data[symbol] = deque(maxlen=self.max_history_size)
            
            # 添加时间戳
            data_with_timestamp = data.copy()
            data_with_timestamp['update_time'] = datetime.now()
            
            self.history_data[symbol].append(data_with_timestamp)
            
            logger.debug(f"更新 {symbol} 市场数据: 价格={data.get('price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"更新市场数据失败 {symbol}: {e}")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格
        
        Args:
            symbol: 交易标的
            
        Returns:
            当前价格，如果不存在返回None
        """
        return self.latest_prices.get(symbol)
    
    def get_current_data(self, symbol: str) -> Optional[dict]:
        """获取当前市场数据
        
        Args:
            symbol: 交易标的
            
        Returns:
            当前市场数据字典，如果不存在返回None
        """
        return self.current_data.get(symbol)
    
    def get_history_data(self, symbol: str, limit: int = None) -> List[dict]:
        """获取历史数据
        
        Args:
            symbol: 交易标的
            limit: 获取的记录数量限制
            
        Returns:
            历史数据列表
        """
        if symbol not in self.history_data:
            return []
        
        history = list(self.history_data[symbol])
        
        if limit:
            return history[-limit:]
        
        return history
    
    def update_depth_data(self, symbol: str, bids: List[tuple], asks: List[tuple]) -> None:
        """更新深度数据
        
        Args:
            symbol: 交易标的
            bids: 买盘数据 [(价格, 数量), ...]
            asks: 卖盘数据 [(价格, 数量), ...]
        """
        try:
            self.depth_data[symbol] = {
                'bids': bids,
                'asks': asks,
                'update_time': datetime.now()
            }
            
            logger.debug(f"更新 {symbol} 深度数据: 买盘{len(bids)}档, 卖盘{len(asks)}档")
            
        except Exception as e:
            logger.error(f"更新深度数据失败 {symbol}: {e}")
    
    def get_depth_data(self, symbol: str) -> Optional[dict]:
        """获取深度数据
        
        Args:
            symbol: 交易标的
            
        Returns:
            深度数据字典，包含bids和asks
        """
        return self.depth_data.get(symbol)
    
    def get_best_bid(self, symbol: str) -> Optional[tuple]:
        """获取最佳买价
        
        Args:
            symbol: 交易标的
            
        Returns:
            (价格, 数量) 或 None
        """
        depth = self.get_depth_data(symbol)
        if depth and depth.get('bids'):
            return depth['bids'][0]  # 买盘按价格降序排列，第一个是最高价
        return None
    
    def get_best_ask(self, symbol: str) -> Optional[tuple]:
        """获取最佳卖价
        
        Args:
            symbol: 交易标的
            
        Returns:
            (价格, 数量) 或 None
        """
        depth = self.get_depth_data(symbol)
        if depth and depth.get('asks'):
            return depth['asks'][0]  # 卖盘按价格升序排列，第一个是最低价
        return None
    
    def get_symbols(self) -> List[str]:
        """获取所有交易标的列表
        
        Returns:
            交易标的符号列表
        """
        return list(self.current_data.keys())
    
    def get_statistics(self) -> dict:
        """获取市场数据统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_symbols': len(self.current_data),
            'symbols_with_price': len(self.latest_prices),
            'symbols_with_depth': len(self.depth_data),
            'total_history_records': sum(len(history) for history in self.history_data.values()),
            'max_history_size': self.max_history_size
        }
    
    def clear_symbol_data(self, symbol: str) -> None:
        """清除指定标的的所有数据
        
        Args:
            symbol: 交易标的
        """
        self.current_data.pop(symbol, None)
        self.latest_prices.pop(symbol, None)
        self.depth_data.pop(symbol, None)
        self.history_data.pop(symbol, None)
        
        logger.info(f"已清除 {symbol} 的所有市场数据")
    
    def clear_all_data(self) -> None:
        """清除所有市场数据"""
        self.current_data.clear()
        self.latest_prices.clear()
        self.depth_data.clear()
        self.history_data.clear()
        
        logger.info("已清除所有市场数据") 