#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
vnpy数据源适配器

通过vnpy Gateway获取实时行情数据，支持多种数据源
"""

import time
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timezone
from threading import Thread, Event
import pandas as pd

try:
    from vnpy.trader.engine import MainEngine
    from vnpy.trader.gateway import BaseGateway
    from vnpy.trader.object import TickData, BarData, ContractData, SubscribeRequest
    from vnpy.trader.constant import Exchange, Interval
    from vnpy.event import EventEngine, Event as VnpyEvent
    from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT
    VNPY_AVAILABLE = True
except ImportError:
    VNPY_AVAILABLE = False
    MainEngine = object
    BaseGateway = object
    EventEngine = object
    # 添加缺失的类型定义
    TickData = object
    BarData = object
    ContractData = object
    SubscribeRequest = object
    Exchange = object
    Interval = object
    VnpyEvent = object
    EVENT_TICK = "EVENT_TICK"
    EVENT_CONTRACT = "EVENT_CONTRACT"

from qte.data.data_source_interface import BaseDataSource
from qte.vnpy import check_vnpy_availability

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.event import EventEngine, Event as VnpyEvent
    from vnpy.trader.constant import Exchange, Interval
    from vnpy.trader.object import TickData, BarData, ContractData, SubscribeRequest
    from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT
    from vnpy.trader.gateway import BaseGateway
    
    # MainEngine可能不可用，提供替代方案
    if "MainEngine" in VNPY_INFO["available_components"]:
        from vnpy.trader.engine import MainEngine
        MAIN_ENGINE_AVAILABLE = True
    else:
        MainEngine = None
        MAIN_ENGINE_AVAILABLE = False
        print("警告: vnpy MainEngine不可用，使用简化版数据源")
else:
    # vnpy不可用时的Mock类
    EventEngine = object
    MainEngine = object
    BaseGateway = object
    TickData = object
    BarData = object
    ContractData = object
    SubscribeRequest = object
    Exchange = object
    Interval = object
    VnpyEvent = object
    EVENT_TICK = "EVENT_TICK"
    EVENT_CONTRACT = "EVENT_CONTRACT"
    MAIN_ENGINE_AVAILABLE = False

class VnpyDataSource(BaseDataSource):
    """
    vnpy数据源适配器
    
    通过vnpy Gateway从QTE虚拟交易所获取实时和历史数据
    注意：数据获取由虚拟交易所负责，本模块只负责从虚拟交易所读取
    """
    
    def __init__(self, 
                 gateway_names: List[str] = None,
                 gateway_settings: Dict[str, dict] = None,
                 virtual_exchange_host: str = "localhost:5000",
                 use_simple_mode: bool = None):
        """
        初始化vnpy数据源
        
        Args:
            gateway_names: 要使用的网关名称列表
            gateway_settings: 网关配置字典
            virtual_exchange_host: QTE虚拟交易所地址
            use_simple_mode: 是否使用简化模式（当MainEngine不可用时）
        """
        if not VNPY_AVAILABLE:
            raise ImportError(f"vnpy核心组件不可用：{VNPY_INFO['missing_deps']}")
        
        super().__init__()
        
        # 确定运行模式
        if use_simple_mode is None:
            use_simple_mode = not MAIN_ENGINE_AVAILABLE
        
        self.simple_mode = use_simple_mode
        self.virtual_exchange_host = virtual_exchange_host
        
        # vnpy组件
        self.event_engine: Optional[EventEngine] = None
        self.main_engine: Optional[MainEngine] = None
        self.gateways: Dict[str, BaseGateway] = {}
        
        # 配置
        self.gateway_names = gateway_names or ["QTE_BINANCE_SPOT"]
        self.gateway_settings = gateway_settings or {}
        
        # 数据存储
        self.tick_data: Dict[str, TickData] = {}
        self.contract_data: Dict[str, ContractData] = {}
        self.subscriptions: Set[str] = set()
        
        # 状态
        self.connected = False
        self.initialized = False
        
        print(f"VnpyDataSource初始化 - 模式: {'简化' if self.simple_mode else '完整'}")

    def connect(self) -> bool:
        """连接到vnpy引擎和网关"""
        try:
            if self.simple_mode:
                return self._connect_simple_mode()
            else:
                return self._connect_full_mode()
        except Exception as e:
            print(f"VnpyDataSource连接失败: {e}")
            return False

    def _connect_simple_mode(self) -> bool:
        """简化模式连接 - 直接使用事件引擎"""
        print("使用简化模式连接vnpy...")
        
        # 创建事件引擎
        self.event_engine = EventEngine()
        
        # 注册事件处理器
        self.event_engine.register(EVENT_TICK, self._process_tick_event)
        self.event_engine.register(EVENT_CONTRACT, self._process_contract_event)
        
        # 启动事件引擎
        self.event_engine.start()
        
        # 创建并连接网关
        for gateway_name in self.gateway_names:
            gateway = self._create_gateway(gateway_name)
            if gateway:
                self.gateways[gateway_name] = gateway
                # 在简化模式下直接连接网关
                gateway.connect()
        
        self.connected = True
        print("简化模式连接成功")
        return True

    def _connect_full_mode(self) -> bool:
        """完整模式连接 - 使用MainEngine"""
        print("使用完整模式连接vnpy...")
        
        # 创建事件引擎
        self.event_engine = EventEngine()
        
        # 创建主引擎
        self.main_engine = MainEngine(self.event_engine)
        
        # 注册事件处理器
        self.main_engine.event_engine.register(EVENT_TICK, self._process_tick_event)
        self.main_engine.event_engine.register(EVENT_CONTRACT, self._process_contract_event)
        
        # 添加并连接网关
        for gateway_name in self.gateway_names:
            gateway_settings = self.gateway_settings.get(gateway_name, {})
            self.main_engine.add_gateway(self._get_gateway_class(gateway_name))
            self.main_engine.connect(gateway_settings, gateway_name)
        
        self.connected = True
        print("完整模式连接成功")
        return True

    def _create_gateway(self, gateway_name: str) -> Optional[BaseGateway]:
        """创建网关实例（简化模式用）"""
        try:
            if gateway_name == "QTE_BINANCE_SPOT":
                from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
                gateway = QTEBinanceSpotGateway(self.event_engine)
                
                # 配置网关
                settings = self.gateway_settings.get(gateway_name, {
                    "API密钥": "qte_test_key",
                    "私钥": "qte_test_secret", 
                    "服务器": "QTE_MOCK"
                })
                
                # 连接网关时传入设置
                gateway.connect(settings)
                
                return gateway
            else:
                print(f"未知网关类型: {gateway_name}")
                return None
        except Exception as e:
            print(f"创建网关失败: {e}")
            return None

    def disconnect(self):
        """断开vnpy数据源连接"""
        self._stop_event.set()
        
        if self.main_engine:
            # 断开所有网关
            for gateway_name in self.gateway_names:
                self.main_engine.close_gateway(gateway_name)
        
        if self.event_engine:
            self.event_engine.stop()
        
        self.connected = False
        print("vnpy数据源已断开")
    
    def get_tick_data(self, 
                     symbol: str, 
                     exchange: str = "BINANCE",
                     start_time: datetime = None, 
                     end_time: datetime = None) -> pd.DataFrame:
        """
        获取Tick数据
        
        Args:
            symbol: 交易品种
            exchange: 交易所
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            包含tick数据的DataFrame
        """
        # 实时tick数据从缓存获取
        symbol_key = f"{symbol}.{exchange}"
        
        if symbol_key in self.tick_data:
            tick = self.tick_data[symbol_key]
            
            # 转换为DataFrame格式
            data = {
                'timestamp': [tick.datetime],
                'symbol': [tick.symbol],
                'last_price': [tick.last_price],
                'volume': [tick.volume],
                'bid_price_1': [tick.bid_price_1],
                'ask_price_1': [tick.ask_price_1],
                'bid_volume_1': [tick.bid_volume_1],
                'ask_volume_1': [tick.ask_volume_1],
            }
            
            return pd.DataFrame(data)
        
        return pd.DataFrame()
    
    def get_bar_data(self, 
                    symbol: str, 
                    interval: str = "1m",
                    exchange: str = "BINANCE",
                    start_time: datetime = None, 
                    end_time: datetime = None,
                    limit: int = 1000) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易品种
            interval: 时间间隔 (1m, 5m, 15m, 1h, 1d等)
            exchange: 交易所
            start_time: 开始时间
            end_time: 结束时间
            limit: 数据条数限制
            
        Returns:
            包含K线数据的DataFrame
        """
        # vnpy历史数据查询
        # 这里需要根据具体的vnpy版本和网关实现
        # 暂时返回空DataFrame，实际实现需要调用网关的历史数据接口
        
        return pd.DataFrame(columns=[
            'timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'
        ])
    
    def subscribe_tick_data(self, 
                           symbols: List[str], 
                           exchange: str = "BINANCE",
                           callback: Callable = None):
        """
        订阅实时tick数据
        
        Args:
            symbols: 要订阅的交易品种列表
            exchange: 交易所
            callback: 数据回调函数
        """
        if not self.connected:
            print("数据源未连接，无法订阅")
            return
        
        # 添加回调函数
        if callback and callback not in self.tick_callbacks:
            self.tick_callbacks.append(callback)
        
        # 创建订阅请求
        for symbol in symbols:
            req = SubscribeRequest(
                symbol=symbol,
                exchange=Exchange[exchange.upper()]
            )
            
            # 发送订阅请求到所有网关
            for gateway_name in self.gateway_names:
                self.main_engine.subscribe(req, gateway_name)
                
            self.subscriptions.add(f"{symbol}.{exchange}")
        
        print(f"已订阅tick数据：{symbols}")
    
    def subscribe_bar_data(self,
                          symbols: List[str],
                          interval: str = "1m", 
                          exchange: str = "BINANCE",
                          callback: Callable = None):
        """
        订阅实时K线数据
        
        Args:
            symbols: 要订阅的交易品种列表
            interval: 时间间隔
            exchange: 交易所
            callback: 数据回调函数
        """
        # 添加回调函数
        if callback and callback not in self.bar_callbacks:
            self.bar_callbacks.append(callback)
        
        # vnpy的K线订阅实现
        # 具体实现取决于网关支持
        print(f"已订阅K线数据：{symbols}, 间隔：{interval}")
    
    def get_contracts(self, exchange: str = "BINANCE") -> Dict[str, ContractData]:
        """获取合约信息"""
        filtered_contracts = {}
        
        for symbol, contract in self.contract_data.items():
            if contract.exchange.value == exchange.upper():
                filtered_contracts[symbol] = contract
        
        return filtered_contracts
    
    def is_market_open(self, exchange: str = "BINANCE") -> bool:
        """检查市场是否开放"""
        # Binance 24/7开放
        if exchange.upper() == "BINANCE":
            return True
        
        # 其他交易所需要根据具体时间判断
        return True
    
    def get_bars(self, symbol: str, exchange: str, interval: str, 
                 start_time: datetime, end_time: datetime) -> List[Dict]:
        """获取历史K线数据"""
        # 这是一个基本实现，实际应该从QTE虚拟交易所获取
        print(f"从QTE虚拟交易所获取K线数据: {symbol}.{exchange} {interval} {start_time} - {end_time}")
        
        # 模拟返回一些空数据
        return []

    def get_ticks(self, symbol: str, exchange: str,
                  start_time: datetime, end_time: datetime) -> List[Dict]:
        """获取历史tick数据"""
        print(f"从QTE虚拟交易所获取tick数据: {symbol}.{exchange} {start_time} - {end_time}")
        return []

    def get_contracts(self, exchange: str = None) -> Dict[str, Dict]:
        """获取合约信息"""
        print(f"从QTE虚拟交易所获取合约信息: {exchange}")
        return {}
    
    # ================ 私有方法 ================
    
    def _process_tick_event(self, event: VnpyEvent):
        """处理tick数据事件"""
        tick: TickData = event.data
        symbol_key = f"{tick.symbol}.{tick.exchange.value}"
        
        # 更新缓存
        self.tick_data[symbol_key] = tick
        
        # 调用回调函数
        for callback in self.tick_callbacks:
            try:
                callback(tick)
            except Exception as e:
                print(f"Tick回调函数执行错误：{e}")
    
    def _process_contract_event(self, event: VnpyEvent):
        """处理合约数据事件"""
        contract: ContractData = event.data
        self.contract_data[contract.symbol] = contract


# 如果vnpy不可用，提供一个空的实现
if not VNPY_AVAILABLE:
    class VnpyDataSource:
        """vnpy不可用时的空实现"""
        def __init__(self, *args, **kwargs):
            raise ImportError("vnpy未安装，请先安装vnpy包")

__all__ = ["VnpyDataSource"] 