"""
基础经纪商测试
测试模拟交易执行、滑点和佣金计算功能
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pandas as pd

from qte.core.events import OrderEvent, FillEvent, EventType, OrderDirection, OrderType
from qte.core.event_loop import EventLoop
from qte.execution.basic_broker import BasicBroker, FixedPercentageCommission, SimpleRandomSlippage

class TestBasicBroker:
    """测试基础经纪商"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建事件循环的模拟对象
        self.mock_event_loop = MagicMock(spec=EventLoop)
        
        # 创建佣金模型
        self.commission_model = FixedPercentageCommission(commission_rate=0.001)  # 0.1%佣金
        
        # 创建滑点模型，设置100%概率发生滑点以便于测试
        self.slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=1.0)
        
        # 创建数据提供者模拟对象
        self.mock_data_provider = MagicMock()
        self.mock_data_provider.get_latest_bar.return_value = {
            'datetime': datetime.now(),
            'symbol': '000001',
            'open': 10.0,
            'high': 10.2,
            'low': 9.8,
            'close': 10.0,
            'volume': 1000
        }
        
        # 创建经纪商
        self.broker = BasicBroker(
            event_loop=self.mock_event_loop,
            commission_model=self.commission_model,
            slippage_model=self.slippage_model,
            data_provider=self.mock_data_provider
        )
        
        # 重置滑点模型的随机选择，确保测试可重现
        self.random_choice_patcher = patch('random.choice', return_value=1)
        self.mock_random_choice = self.random_choice_patcher.start()
    
    def teardown_method(self):
        """测试后清理"""
        self.random_choice_patcher.stop()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.broker.commission_model == self.commission_model
        assert self.broker.slippage_model == self.slippage_model
        assert self.broker.data_provider == self.mock_data_provider
        assert self.broker.event_loop == self.mock_event_loop
    
    def test_submit_market_order_buy(self):
        """测试提交市价买单"""
        # 创建市价买单
        market_order = OrderEvent(
            order_id="test_market_buy",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 提交订单
        self.broker.submit_order(market_order)
        
        # 验证数据提供者被调用
        self.mock_data_provider.get_latest_bar.assert_called_once_with("000001")
        
        # 验证成交事件
        self.mock_event_loop.put_event.assert_called_once()
        fill_event = self.mock_event_loop.put_event.call_args[0][0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id == "test_market_buy"
        assert fill_event.symbol == "000001"
        assert fill_event.direction == 1  # OrderDirection.BUY的值
        assert fill_event.quantity == 100
        assert fill_event.fill_price == pytest.approx(9.99)  # 价格 - 滑点
        assert fill_event.commission == pytest.approx(100 * 9.99 * 0.001)  # 佣金
        assert fill_event.slippage == pytest.approx(0.01)  # 滑点
    
    def test_submit_market_order_sell(self):
        """测试提交市价卖单"""
        # 创建市价卖单
        market_order = OrderEvent(
            order_id="test_market_sell",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.SELL,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 提交订单
        self.broker.submit_order(market_order)
        
        # 验证数据提供者被调用
        self.mock_data_provider.get_latest_bar.assert_called_once_with("000001")
        
        # 验证成交事件
        self.mock_event_loop.put_event.assert_called_once()
        fill_event = self.mock_event_loop.put_event.call_args[0][0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id == "test_market_sell"
        assert fill_event.symbol == "000001"
        assert fill_event.direction == -1  # OrderDirection.SELL的值
        assert fill_event.quantity == 100
        assert fill_event.fill_price == pytest.approx(9.99)  # 价格 - 滑点
        assert fill_event.commission == pytest.approx(100 * 9.99 * 0.001)  # 佣金
        assert fill_event.slippage == pytest.approx(0.01)  # 滑点
    
    def test_submit_market_order_no_data(self):
        """测试提交无法获取价格的市价单"""
        # 修改数据提供者返回None
        self.mock_data_provider.get_latest_bar.return_value = None
        
        # 创建市价单
        market_order = OrderEvent(
            order_id="test_market_no_data",
            symbol="000099",  # 不存在的标的
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 提交订单
        self.broker.submit_order(market_order)
        
        # 验证数据提供者被调用
        self.mock_data_provider.get_latest_bar.assert_called_once_with("000099")
        
        # 验证没有生成成交事件
        self.mock_event_loop.put_event.assert_not_called()
    
    def test_submit_market_order_no_price(self):
        """测试提交价格为空的市价单"""
        # 修改数据提供者返回没有close价格的数据
        self.mock_data_provider.get_latest_bar.return_value = {
            'datetime': datetime.now(),
            'symbol': '000002',
            'open': None,
            'high': None,
            'low': None,
            'close': None,
            'volume': 0
        }
        
        # 创建市价单
        market_order = OrderEvent(
            order_id="test_market_no_price",
            symbol="000002",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 提交订单
        self.broker.submit_order(market_order)
        
        # 验证数据提供者被调用
        self.mock_data_provider.get_latest_bar.assert_called_once_with("000002")
        
        # 验证没有生成成交事件
        self.mock_event_loop.put_event.assert_not_called()
    
    def test_submit_limit_order(self):
        """测试提交限价单（当前实现不支持限价单）"""
        # 创建限价单，不使用limit_price参数
        limit_order = OrderEvent(
            order_id="test_limit_buy",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.LIMIT
        )
        
        # 提交订单
        self.broker.submit_order(limit_order)
        
        # 验证没有生成成交事件（当前实现不支持限价单）
        self.mock_event_loop.put_event.assert_not_called()
    
    def test_submit_unknown_order_type(self):
        """测试提交未知类型的订单"""
        # 创建未知类型的订单
        unknown_order = OrderEvent(
            order_id="test_unknown_type",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type="UNKNOWN"  # 未知订单类型
        )
        
        # 提交订单
        self.broker.submit_order(unknown_order)
        
        # 验证没有生成成交事件
        self.mock_event_loop.put_event.assert_not_called()
    
    def test_submit_market_order_with_no_id(self):
        """测试提交没有ID的市价单"""
        # 创建没有ID的市价单
        market_order = OrderEvent(
            order_id=None,
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 提交订单
        self.broker.submit_order(market_order)
        
        # 验证成交事件生成了ID
        self.mock_event_loop.put_event.assert_called_once()
        fill_event = self.mock_event_loop.put_event.call_args[0][0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id is not None
        assert fill_event.order_id.startswith("sim_ord_")
    
    def test_submit_order_no_data_provider(self):
        """测试没有数据提供者的经纪商"""
        # 创建没有数据提供者的经纪商
        broker_no_dp = BasicBroker(
            event_loop=self.mock_event_loop,
            commission_model=self.commission_model,
            slippage_model=self.slippage_model,
            data_provider=None
        )
        
        # 创建市价单
        market_order = OrderEvent(
            order_id="test_no_dp",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 提交订单
        broker_no_dp.submit_order(market_order)
        
        # 验证没有生成成交事件（没有数据提供者无法获取价格）
        self.mock_event_loop.put_event.assert_not_called()
    
    # 以下是集成测试（可选）
    
    def test_integration_with_models(self):
        """测试与佣金和滑点模型的集成"""
        # 使用真实对象而非模拟
        commission_model = FixedPercentageCommission(commission_rate=0.001)
        slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=1.0)
        
        with patch('random.choice', return_value=1):
            # 计算预期的滑点和佣金
            original_price = 10.0
            quantity = 100
            direction = OrderDirection.BUY
            
            # 手动计算滑点后的价格
            slippage_amount = 0.01
            fill_price = original_price + slippage_amount
            
            # 手动计算佣金
            commission = quantity * fill_price * 0.001
            
            # 验证滑点模型计算
            calculated_price = slippage_model.calculate_fill_price_with_slippage(
                "000001", quantity, original_price, direction
            )
            assert calculated_price == pytest.approx(fill_price)
            
            # 验证佣金模型计算
            calculated_commission = commission_model.calculate_commission(
                "000001", quantity, fill_price, direction
            )
            assert calculated_commission == pytest.approx(commission) 