"""
佣金模型和滑点模型测试
测试交易成本模型的计算功能
"""
import pytest
from unittest.mock import MagicMock
import random

from qte.core.events import OrderDirection, MarketEvent
from qte.execution.basic_broker import FixedPercentageCommission, SimpleRandomSlippage

class TestFixedPercentageCommission:
    """测试固定百分比佣金模型"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建佣金模型实例
        self.commission_rate = 0.001  # 0.1%
        self.commission_model = FixedPercentageCommission(commission_rate=self.commission_rate)
    
    def test_initialization(self):
        """测试初始化"""
        assert self.commission_model.commission_rate == self.commission_rate
    
    def test_calculate_commission_buy(self):
        """测试计算买入佣金"""
        symbol = "000001"
        quantity = 100
        price = 10.0
        direction = OrderDirection.BUY
        
        commission = self.commission_model.calculate_commission(symbol, quantity, price, direction)
        
        # 佣金应该是 数量 * 价格 * 佣金率
        expected_commission = quantity * price * self.commission_rate
        assert commission == pytest.approx(expected_commission)
    
    def test_calculate_commission_sell(self):
        """测试计算卖出佣金"""
        symbol = "000001"
        quantity = 100
        price = 10.0
        direction = OrderDirection.SELL
        
        commission = self.commission_model.calculate_commission(symbol, quantity, price, direction)
        
        # 佣金应该是 数量 * 价格 * 佣金率
        expected_commission = quantity * price * self.commission_rate
        assert commission == pytest.approx(expected_commission)
    
    def test_calculate_commission_negative_quantity(self):
        """测试计算负数数量的佣金"""
        symbol = "000001"
        quantity = -100  # 负数数量
        price = 10.0
        direction = OrderDirection.SELL
        
        commission = self.commission_model.calculate_commission(symbol, quantity, price, direction)
        
        # 佣金应该是 |数量| * 价格 * 佣金率
        expected_commission = abs(quantity) * price * self.commission_rate
        assert commission == pytest.approx(expected_commission)
    
    def test_calculate_commission_zero_quantity(self):
        """测试计算零数量的佣金"""
        symbol = "000001"
        quantity = 0
        price = 10.0
        direction = OrderDirection.BUY
        
        commission = self.commission_model.calculate_commission(symbol, quantity, price, direction)
        
        # 零数量应该有零佣金
        assert commission == 0.0
    
    def test_calculate_commission_zero_price(self):
        """测试计算零价格的佣金"""
        symbol = "000001"
        quantity = 100
        price = 0.0
        direction = OrderDirection.BUY
        
        commission = self.commission_model.calculate_commission(symbol, quantity, price, direction)
        
        # 零价格应该有零佣金
        assert commission == 0.0


class TestSimpleRandomSlippage:
    """测试简单随机滑点模型"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建滑点模型实例
        self.slippage_points = 0.01
        self.slippage_chance = 1.0  # 100%发生滑点，便于测试
        self.slippage_model = SimpleRandomSlippage(
            slippage_points=self.slippage_points,
            slippage_chance=self.slippage_chance
        )
        
        # 固定随机种子以使测试可重现
        random.seed(42)
    
    def teardown_method(self):
        """测试后清理"""
        # 重置随机种子
        random.seed()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.slippage_model.slippage_points == self.slippage_points
        assert self.slippage_model.slippage_chance == self.slippage_chance
    
    def test_slippage_buy_direction(self):
        """测试买入方向的滑点"""
        # 设置随机选择为正向滑点
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(random, "choice", lambda x: 1)
            
            symbol = "000001"
            quantity = 100
            intended_price = 10.0
            direction = OrderDirection.BUY
            
            fill_price = self.slippage_model.calculate_fill_price_with_slippage(
                symbol, quantity, intended_price, direction
            )
            
            # 买入方向的滑点应该使价格上升（不利）
            assert fill_price > intended_price
            assert fill_price == pytest.approx(intended_price + self.slippage_points)
    
    def test_slippage_sell_direction(self):
        """测试卖出方向的滑点"""
        # 设置随机选择为正向滑点
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(random, "choice", lambda x: 1)
            
            symbol = "000001"
            quantity = 100
            intended_price = 10.0
            direction = OrderDirection.SELL
            
            fill_price = self.slippage_model.calculate_fill_price_with_slippage(
                symbol, quantity, intended_price, direction
            )
            
            # 卖出方向的滑点应该使价格下降（不利）
            assert fill_price < intended_price
            assert fill_price == pytest.approx(intended_price - self.slippage_points)
    
    def test_slippage_chance(self):
        """测试滑点发生概率"""
        # 创建概率为0的滑点模型
        no_slippage_model = SimpleRandomSlippage(
            slippage_points=self.slippage_points,
            slippage_chance=0.0  # 0%发生滑点
        )
        
        symbol = "000001"
        quantity = 100
        intended_price = 10.0
        direction = OrderDirection.BUY
        
        # 测试多次，应该始终返回原始价格
        for _ in range(10):
            fill_price = no_slippage_model.calculate_fill_price_with_slippage(
                symbol, quantity, intended_price, direction
            )
            assert fill_price == intended_price
    
    def test_slippage_with_market_event(self):
        """测试带市场事件的滑点"""
        # 创建一个市场事件
        market_event = MagicMock(spec=MarketEvent)
        market_event.symbol = "000001"
        market_event.close_price = 10.0
        market_event.high_price = 10.2
        market_event.low_price = 9.8
        
        # 设置随机选择为正向滑点
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(random, "choice", lambda x: 1)
            
            symbol = "000001"
            quantity = 100
            intended_price = 10.0
            direction = OrderDirection.BUY
            
            fill_price = self.slippage_model.calculate_fill_price_with_slippage(
                symbol, quantity, intended_price, direction, market_event
            )
            
            # 滑点模型目前不使用市场事件，但价格仍应正确计算
            assert fill_price > intended_price
            assert fill_price == pytest.approx(intended_price + self.slippage_points)
    
    def test_negative_slippage_buy(self):
        """测试买入的负向滑点"""
        # 设置随机选择为负向滑点
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(random, "choice", lambda x: -1)
            
            symbol = "000001"
            quantity = 100
            intended_price = 10.0
            direction = OrderDirection.BUY
            
            fill_price = self.slippage_model.calculate_fill_price_with_slippage(
                symbol, quantity, intended_price, direction
            )
            
            # 买入方向的负向滑点应该使价格上升（不利）
            assert fill_price > intended_price
            assert fill_price == pytest.approx(intended_price + self.slippage_points)
    
    def test_negative_slippage_sell(self):
        """测试卖出的负向滑点"""
        # 设置随机选择为负向滑点
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(random, "choice", lambda x: -1)
            
            symbol = "000001"
            quantity = 100
            intended_price = 10.0
            direction = OrderDirection.SELL
            
            fill_price = self.slippage_model.calculate_fill_price_with_slippage(
                symbol, quantity, intended_price, direction
            )
            
            # 卖出方向的负向滑点应该使价格下降（不利）
            assert fill_price < intended_price
            assert fill_price == pytest.approx(intended_price - self.slippage_points) 