"""
数据重放控制器高级集成测试

此测试文件测试数据重放控制器与策略、执行引擎等其他系统组件的深度集成
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading

from qte.data.data_replay import (
    ReplayMode, 
    ReplayStatus, 
    BaseDataReplayController, 
    DataFrameReplayController, 
    MultiSourceReplayController
)

# 模拟执行引擎
class MockExecutionEngine:
    """模拟执行引擎，用于测试与数据重放控制器的集成"""
    
    def __init__(self):
        self.orders = []
        self.executions = []
        self.current_price = None
        self.is_running = False
    
    def submit_order(self, symbol, quantity, price=None):
        """提交订单"""
        order_id = len(self.orders) + 1
        order = {
            'id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'price': price or self.current_price,
            'status': 'submitted',
            'timestamp': datetime.now()
        }
        self.orders.append(order)
        
        # 模拟执行
        if self.is_running and self.current_price:
            self._execute_order(order)
            
        return order_id
    
    def _execute_order(self, order):
        """模拟订单执行"""
        execution = {
            'order_id': order['id'],
            'symbol': order['symbol'],
            'quantity': order['quantity'],
            'price': self.current_price,  # 使用当前市场价格
            'timestamp': datetime.now()
        }
        self.executions.append(execution)
        order['status'] = 'executed'
        
    def start(self):
        """启动执行引擎"""
        self.is_running = True
        
    def stop(self):
        """停止执行引擎"""
        self.is_running = False
    
    def update_market_data(self, data):
        """更新市场数据"""
        if isinstance(data, dict) and 'price' in data:
            self.current_price = data['price']
        elif isinstance(data, pd.Series) and 'price' in data:
            self.current_price = data['price']
        elif hasattr(data, 'price'):
            self.current_price = data.price

# 模拟策略
class MockStrategy:
    """模拟策略，用于测试与数据重放和执行引擎的集成"""
    
    def __init__(self, execution_engine):
        self.execution_engine = execution_engine
        self.received_data = []
        self.current_position = 0
        self.trade_count = 0
        self.last_trade_price = None
    
    def on_data(self, data):
        """接收数据的回调方法"""
        self.received_data.append(data)
        
        # 更新执行引擎的市场数据
        self.execution_engine.update_market_data(data)
        
        # 简单的交易逻辑：价格上涨时买入，下跌时卖出
        if len(self.received_data) > 1:
            prev_price = self._extract_price(self.received_data[-2])
            curr_price = self._extract_price(data)
            
            if prev_price is not None and curr_price is not None:
                if curr_price > prev_price and self.current_position <= 0:
                    # 价格上涨且没有多头仓位，买入
                    self._place_buy_order('SAMPLE', 1, curr_price)
                elif curr_price < prev_price and self.current_position >= 0:
                    # 价格下跌且没有空头仓位，卖出
                    self._place_sell_order('SAMPLE', 1, curr_price)
    
    def _extract_price(self, data):
        """从数据中提取价格"""
        if isinstance(data, dict) and 'price' in data:
            return data['price']
        elif isinstance(data, pd.Series) and 'price' in data:
            return data['price']
        elif hasattr(data, 'price'):
            return data.price
        return None
    
    def _place_buy_order(self, symbol, quantity, price):
        """下买单"""
        order_id = self.execution_engine.submit_order(symbol, quantity, price)
        self.current_position += quantity
        self.trade_count += 1
        self.last_trade_price = price
        return order_id
    
    def _place_sell_order(self, symbol, quantity, price):
        """下卖单"""
        order_id = self.execution_engine.submit_order(symbol, -quantity, price)
        self.current_position -= quantity
        self.trade_count += 1
        self.last_trade_price = price
        return order_id
    
    def reset(self):
        """重置策略状态"""
        self.received_data.clear()
        self.current_position = 0
        self.trade_count = 0
        self.last_trade_price = None

class TestAdvancedIntegration:
    """测试数据重放控制器与其他系统组件的高级集成"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建执行引擎
        self.execution_engine = MockExecutionEngine()
        self.execution_engine.start()
        
        # 创建策略
        self.strategy = MockStrategy(self.execution_engine)
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        # 创建有波动的价格数据，便于测试策略逻辑
        self.price_data = pd.DataFrame({
            'price': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                     111, 110, 112, 114, 113, 115, 117, 116, 118, 120],
            'volume': np.random.randint(1000, 10000, 20)
        }, index=dates)
    
    def teardown_method(self):
        """清理测试环境"""
        self.execution_engine.stop()
    
    def test_full_data_replay_trading_cycle(self):
        """测试完整的数据回放-策略-交易执行循环"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 使用同步API处理所有数据
        results = controller.process_all_sync()
        
        # 验证数据流
        assert len(self.strategy.received_data) == 20
        
        # 验证交易执行
        # 价格是上涨-下跌交替的模式，应该触发多次交易
        assert self.strategy.trade_count > 0
        assert len(self.execution_engine.orders) > 0
        assert len(self.execution_engine.executions) > 0
        
        # 验证最终状态
        assert controller.get_status() == ReplayStatus.COMPLETED
    
    def test_stepped_replay_trading_cycle(self):
        """测试步进模式下的数据回放-策略-交易循环"""
        # 创建控制器
        controller = DataFrameReplayController(
            self.price_data, 
            mode=ReplayMode.STEPPED
        )
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 逐步处理数据
        for _ in range(10):  # 只处理前10个数据点
            data = controller.step_sync()
            if data is None:
                break
                
        # 验证数据流和交易
        assert len(self.strategy.received_data) == 10
        assert self.strategy.trade_count > 0
        
        # 重置策略状态
        self.strategy.reset()
        controller.reset()
        
        # 重新处理所有数据
        controller.process_all_sync()
        
        # 验证重置后可以重新进行完整处理
        assert len(self.strategy.received_data) == 20
    
    def test_multi_source_trading_integration(self):
        """测试多数据源与交易系统集成"""
        # 创建第二个数据源 - 模拟指标数据
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        indicator_data = pd.DataFrame({
            'ma5': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108,
                   109, 110, 111, 112, 113, 114, 115, 116, 117, 118],
            'rsi': [30, 40, 50, 60, 70, 65, 55, 45, 35, 45,
                   55, 65, 75, 70, 60, 50, 40, 50, 60, 70]
        }, index=dates)
        
        # 创建多数据源控制器
        controller = MultiSourceReplayController({
            'price': self.price_data,
            'indicator': indicator_data
        })
        
        # 创建更复杂的策略
        class EnhancedStrategy(MockStrategy):
            """使用额外指标的增强策略"""
            
            def __init__(self, execution_engine):
                super().__init__(execution_engine)
                self.last_ma5 = None
                self.last_rsi = None
            
            def on_data(self, data):
                """接收并处理数据"""
                self.received_data.append(data)
                
                # 提取数据
                source = data.get('_source', '')
                
                if source == 'price':
                    # 更新执行引擎的市场数据
                    self.execution_engine.update_market_data(data)
                    price = self._extract_price(data)
                    
                    # 使用指标进行交易决策
                    if price and self.last_ma5 and self.last_rsi:
                        if price > self.last_ma5 and self.last_rsi < 70 and self.current_position <= 0:
                            # 价格高于MA5且RSI不超买，买入
                            self._place_buy_order('SAMPLE', 1, price)
                        elif price < self.last_ma5 and self.last_rsi > 30 and self.current_position >= 0:
                            # 价格低于MA5且RSI不超卖，卖出
                            self._place_sell_order('SAMPLE', 1, price)
                
                elif source == 'indicator':
                    # 更新指标
                    if 'ma5' in data:
                        self.last_ma5 = data['ma5']
                    if 'rsi' in data:
                        self.last_rsi = data['rsi']
        
        # 使用增强策略
        enhanced_strategy = EnhancedStrategy(self.execution_engine)
        controller.register_callback(enhanced_strategy.on_data)
        
        # 处理所有数据
        controller.process_all_sync()
        
        # 验证数据和交易
        assert len(enhanced_strategy.received_data) == 40  # 20个价格 + 20个指标
        assert enhanced_strategy.trade_count > 0
    
    def test_realtime_trading_simulation(self):
        """测试实时模式下的交易模拟"""
        # 创建加速的实时模式控制器
        controller = DataFrameReplayController(
            self.price_data,
            mode=ReplayMode.ACCELERATED,
            speed_factor=10.0  # 10倍速
        )
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 启动异步回放
        controller.start()
        
        # 等待一段时间让处理完成
        start_time = time.time()
        max_wait = 5  # 最多等待5秒
        
        while (controller.get_status() != ReplayStatus.COMPLETED and 
               time.time() - start_time < max_wait):
            time.sleep(0.1)
        
        # 验证处理状态
        assert controller.get_status() in [ReplayStatus.COMPLETED, ReplayStatus.RUNNING]
        
        # 确保至少处理了一些数据
        assert len(self.strategy.received_data) > 0
        
        # 停止控制器
        controller.stop()
    
    def test_error_handling_during_trading(self):
        """测试交易过程中的错误处理"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 创建有故障的策略
        class FaultyStrategy(MockStrategy):
            """模拟会出错的策略"""
            
            def on_data(self, data):
                """处理数据时会在第5个数据点抛出异常"""
                self.received_data.append(data)
                
                if len(self.received_data) == 5:
                    raise ValueError("模拟策略错误")
                    
                # 正常处理其他数据点
                super().on_data(data)
        
        # 使用故障策略
        faulty_strategy = FaultyStrategy(self.execution_engine)
        controller.register_callback(faulty_strategy.on_data)
        
        # 处理数据，应该能捕获错误并继续
        results = controller.process_all_sync()
        
        # 验证虽然有错误，但处理继续进行
        assert len(results) == 20
        assert len(faulty_strategy.received_data) == 20
        
        # 验证发生错误前的交易被执行
        assert faulty_strategy.trade_count > 0


if __name__ == "__main__":
    pytest.main(["-v", "test_replay_advanced_integration.py"]) 