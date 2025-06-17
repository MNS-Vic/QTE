import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from qte.core.events import Event, EventType
from qte.core.time_manager import TimeManager
from qte.exchange.market_data import MarketDataManager
from qte.exchange.matching.order_book import OrderBook
from qte.exchange.account.account_manager import AccountManager
from qte.data.data_replay import DataFrameReplayController, ReplayMode

logger = logging.getLogger(__name__)

class VirtualExchange:
    """虚拟交易所主引擎
    
    提供完整的交易所功能：
    - 账户管理
    - 订单撮合
    - 行情管理
    - 数据回放支持
    """
    
    def __init__(self, 
                 exchange_id: str = "virtual", 
                 enable_market_data: bool = True,
                 enable_data_replay: bool = False,
                 replay_controller: Optional[DataFrameReplayController] = None):
        """初始化虚拟交易所
        
        Args:
            exchange_id: 交易所标识
            enable_market_data: 是否启用行情管理
            enable_data_replay: 是否启用数据回放
            replay_controller: 数据回放控制器
        """
        self.exchange_id = exchange_id
        self.time_manager = TimeManager()
        
        # 核心组件
        self.account_manager = AccountManager()
        self.market_data_manager = MarketDataManager() if enable_market_data else None
        self.order_books: Dict[str, OrderBook] = {}
        
        # 数据回放功能
        self.enable_data_replay = enable_data_replay
        self.replay_controller = replay_controller
        self._setup_data_replay()
        
        # 交易所状态
        self.is_running = False
        self.is_market_open = True
        
        # 事件监听器
        self.event_listeners = []
        
        logger.info(f"虚拟交易所 {exchange_id} 初始化完成")
    
    def _setup_data_replay(self):
        """设置数据回放功能"""
        if not self.enable_data_replay or not self.replay_controller:
            return
            
        # 注册回放数据回调
        self.replay_controller.on_data_callback = self._on_replay_data
        logger.info("数据回放功能已启用")
    
    def _on_replay_data(self, timestamp: datetime, symbol: str, data: dict):
        """处理回放数据回调
        
        Args:
            timestamp: 数据时间戳
            symbol: 交易标的
            data: 行情数据
        """
        try:
            # 更新时间管理器
            self.time_manager.set_virtual_time(timestamp)
            
            # 构造Tick数据
            tick_data = {
                'symbol': symbol,
                'timestamp': timestamp,
                'price': float(data.get('close', 0)),
                'volume': float(data.get('volume', 0)),
                'open': float(data.get('open', 0)),
                'high': float(data.get('high', 0)),
                'low': float(data.get('low', 0))
            }
            
            # 更新市场数据
            if self.market_data_manager:
                self.market_data_manager.update_market_data(symbol, tick_data)
            
            # 触发价格更新事件
            self._emit_market_data_event(symbol, tick_data)
            
            # 检查订单触发条件
            self._check_order_triggers(symbol, tick_data['price'])
            
        except Exception as e:
            logger.error(f"处理回放数据失败: {e}")
    
    def start_data_replay(self, 
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         speed_factor: float = 1.0,
                         replay_mode: ReplayMode = ReplayMode.BACKTEST):
        """启动数据回放
        
        Args:
            start_time: 开始时间
            end_time: 结束时间  
            speed_factor: 回放速度倍数
            replay_mode: 回放模式
        """
        if not self.replay_controller:
            logger.warning("数据回放控制器未初始化")
            return False
            
        try:
            # 配置回放参数
            config = {
                'start_time': start_time,
                'end_time': end_time,
                'speed_factor': speed_factor,
                'mode': replay_mode
            }
            
            # 启动回放
            success = self.replay_controller.start_replay(**config)
            if success:
                logger.info(f"数据回放已启动: {start_time} -> {end_time}, 速度: {speed_factor}x")
                return True
            else:
                logger.error("数据回放启动失败")
                return False
                
        except Exception as e:
            logger.error(f"启动数据回放异常: {e}")
            return False
    
    def _emit_market_data_event(self, symbol: str, tick_data: dict):
        """发送市场数据事件"""
        event = Event(
            event_type="MARKET_DATA",  # 使用字符串而不是枚举
            data={
                'symbol': symbol,
                'tick_data': tick_data,
                'timestamp': tick_data['timestamp']
            }
        )
        self._emit_event(event)
    
    def _check_order_triggers(self, symbol: str, current_price: float):
        """检查订单触发条件
        
        Args:
            symbol: 交易标的
            current_price: 当前价格
        """
        if symbol not in self.order_books:
            return
            
        order_book = self.order_books[symbol]
        triggered_orders = order_book.check_triggers(current_price)
        
        for order in triggered_orders:
            self._process_triggered_order(order)
    
    def _process_triggered_order(self, order):
        """处理被触发的订单"""
        # 实现订单执行逻辑
        pass
        
    def set_replay_controller(self, controller: DataFrameReplayController):
        """设置数据回放控制器"""
        self.replay_controller = controller
        self.enable_data_replay = True
        self._setup_data_replay()
        logger.info("数据回放控制器已设置")
    
    def get_replay_status(self) -> dict:
        """获取回放状态"""
        if not self.enable_data_replay:
            return {"enabled": False}
            
        if not self.replay_controller:
            return {
                "enabled": True,
                "controller_ready": False,
                "message": "数据回放已启用但控制器未设置"
            }
            
        return {
            "enabled": True,
            "controller_ready": True,
            "is_running": self.replay_controller.is_running if hasattr(self.replay_controller, 'is_running') else False,
            "current_time": self.time_manager.current_time.isoformat() if self.time_manager.current_time else None,
            "mode": self.replay_controller.mode if hasattr(self.replay_controller, 'mode') else "unknown"
        }
    
    def _emit_event(self, event: Event):
        """发送事件给监听器"""
        for listener in self.event_listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"事件监听器执行失败: {e}")
    
    def add_event_listener(self, listener):
        """添加事件监听器"""
        self.event_listeners.append(listener)
    
    def remove_event_listener(self, listener):
        """移除事件监听器"""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener) 