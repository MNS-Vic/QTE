"""
数据重放控制器与执行引擎集成测试

此测试文件测试数据重放控制器与执行引擎的集成，确保数据能正确地流向交易执行系统
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from qte.data.data_replay import (
    ReplayMode, 
    ReplayStatus, 
    BaseDataReplayController, 
    DataFrameReplayController, 
    MultiSourceReplayController
)

# 模拟执行引擎
class MockExecutionEngine:
    """模拟执行引擎，用于测试集成"""
    
    def __init__(self):
        self.orders = []
        self.executions = []
        self.market_data = []
        self.is_running = False
        self.current_price = None
    
    def start(self):
        """启动执行引擎"""
        self.is_running = True
    
    def stop(self):
        """停止执行引擎"""
        self.is_running = False
    
    def update_market_data(self, data):
        """更新市场数据"""
        self.market_data.append(data)
        
        # 提取价格数据
        if isinstance(data, dict) and 'price' in data:
            self.current_price = data['price']
        elif isinstance(data, pd.Series) and 'price' in data:
            self.current_price = data['price']
    
    def submit_order(self, symbol, quantity, order_type='market', price=None):
        """提交订单"""
        order_id = len(self.orders) + 1
        
        # 创建订单记录
        order = {
            'id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'type': order_type,
            'price': price or self.current_price,
            'status': 'submitted',
            'timestamp': datetime.now()
        }
        
        self.orders.append(order)
        
        # 如果引擎在运行，自动执行市价订单
        if self.is_running and order_type == 'market' and self.current_price:
            self._execute_order(order)
        
        return order_id
    
    def _execute_order(self, order):
        """内部方法：执行订单"""
        execution = {
            'order_id': order['id'],
            'symbol': order['symbol'],
            'quantity': order['quantity'],
            'price': self.current_price or order['price'],
            'timestamp': datetime.now()
        }
        
        self.executions.append(execution)
        order['status'] = 'executed'
        
        return execution

# 模拟策略
class MockStrategy:
    """模拟策略，用于测试与数据重放和执行引擎的集成"""
    
    def __init__(self, execution_engine):
        self.execution_engine = execution_engine
        self.received_data = []
        self.position = 0
        self.last_price = None
        self.trade_count = 0
    
    def on_data(self, data):
        """接收数据的回调方法"""
        self.received_data.append(data)
        
        # 更新执行引擎的市场数据
        self.execution_engine.update_market_data(data)
        
        # 提取价格
        current_price = None
        if isinstance(data, dict) and 'price' in data:
            current_price = data['price']
        elif isinstance(data, pd.Series) and 'price' in data:
            current_price = data['price']
        
        # 如果无法提取价格，直接返回
        if current_price is None:
            return
        
        # 简单交易逻辑：价格上涨买入，下跌卖出
        if self.last_price is not None:
            if current_price > self.last_price and self.position <= 0:
                # 价格上涨，买入
                self._place_order('SAMPLE', 1)
                self.position += 1
                self.trade_count += 1
            elif current_price < self.last_price and self.position >= 0:
                # 价格下跌，卖出
                self._place_order('SAMPLE', -1)
                self.position -= 1
                self.trade_count += 1
        
        # 更新最后价格
        self.last_price = current_price
    
    def _place_order(self, symbol, quantity):
        """内部方法：下单"""
        self.execution_engine.submit_order(symbol, quantity)
    
    def reset(self):
        """重置策略状态"""
        self.received_data.clear()
        self.position = 0
        self.last_price = None
        self.trade_count = 0

class TestReplayExecutionIntegration:
    """测试数据重放控制器与执行引擎的集成"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建执行引擎
        self.execution_engine = MockExecutionEngine()
        self.execution_engine.start()
        
        # 创建策略
        self.strategy = MockStrategy(self.execution_engine)
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        # 创建波动的价格数据，更容易触发交易信号
        self.price_data = pd.DataFrame({
            'price': [100, 102, 101, 103, 105, 104, 106, 105, 107, 109],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
        }, index=dates)
    
    def teardown_method(self):
        """清理测试环境"""
        self.execution_engine.stop()
    
    def test_replay_to_execution_sync(self):
        """测试通过同步API将数据从重放控制器传递给执行引擎"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 使用同步API处理所有数据
        results = controller.process_all_sync()
        
        # 验证策略接收到所有数据
        assert len(self.strategy.received_data) == 10
        
        # 验证执行引擎接收到市场数据
        assert len(self.execution_engine.market_data) == 10
        
        # 验证生成了订单
        assert len(self.execution_engine.orders) > 0
        
        # 验证执行了订单
        assert len(self.execution_engine.executions) > 0
        
        # 验证价格数据正确传递
        for i, price in enumerate([100, 102, 101, 103, 105, 104, 106, 105, 107, 109]):
            assert self.execution_engine.market_data[i]['price'] == price
    
    def test_replay_to_execution_async(self):
        """测试通过异步API将数据从重放控制器传递给执行引擎"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data, mode=ReplayMode.BACKTEST)
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 启动异步处理
        controller.start()
        
        # 等待处理完成
        max_wait = 20
        wait_count = 0
        while wait_count < max_wait:
            wait_count += 1
            if controller.get_status() == ReplayStatus.COMPLETED:
                break
            time.sleep(0.1)
        
        # 验证控制器完成处理
        assert controller.get_status() == ReplayStatus.COMPLETED
        
        # 验证策略接收到所有数据
        assert len(self.strategy.received_data) == 10
        
        # 验证执行引擎接收到市场数据
        assert len(self.execution_engine.market_data) == 10
        
        # 验证生成了订单
        assert len(self.execution_engine.orders) > 0
    
    def test_replay_with_stepped_execution(self):
        """测试步进模式下的数据重放与执行集成"""
        # 创建控制器
        controller = DataFrameReplayController(
            self.price_data,
            mode=ReplayMode.STEPPED
        )
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 逐步处理前5个数据点
        for _ in range(5):
            data = controller.step_sync()
            assert data is not None
        
        # 验证策略接收到数据
        assert len(self.strategy.received_data) == 5
        
        # 验证执行引擎接收到市场数据
        assert len(self.execution_engine.market_data) == 5
        
        # 验证生成了一些订单
        assert len(self.execution_engine.orders) > 0
        
        # 记录当前订单数量
        orders_after_5_steps = len(self.execution_engine.orders)
        
        # 继续处理剩余数据
        while controller.step_sync() is not None:
            pass
        
        # 验证处理了所有数据
        assert len(self.strategy.received_data) == 10
        assert len(self.execution_engine.market_data) == 10
        
        # 验证生成了更多订单
        assert len(self.execution_engine.orders) > orders_after_5_steps
    
    def test_multiple_data_sources_execution(self):
        """测试多数据源与执行引擎集成"""
        # 创建第二个数据源 - 指标数据
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        indicator_data = pd.DataFrame({
            'ma5': [99, 100, 101, 102, 103, 103, 104, 104, 105, 106],
            'rsi': [45, 55, 50, 60, 65, 60, 62, 58, 63, 67]
        }, index=dates)
        
        # 创建增强版策略，使用指标数据
        class EnhancedStrategy(MockStrategy):
            def __init__(self, execution_engine):
                super().__init__(execution_engine)
                self.current_ma5 = None
                self.current_rsi = None
            
            def on_data(self, data):
                """处理数据，根据指标做出交易决策"""
                self.received_data.append(data)
                
                # 更新执行引擎的市场数据
                self.execution_engine.update_market_data(data)
                
                # 提取数据类型
                source = data.get('_source')
                
                if source == 'price':
                    # 提取价格
                    if 'price' in data:
                        price = data['price']
                        self.last_price = price
                        
                        # 只有当同时有价格和指标数据时才交易
                        if self.current_ma5 is not None and self.current_rsi is not None:
                            if (price > self.current_ma5 and self.current_rsi < 70 and 
                                self.position <= 0):
                                # 价格高于MA5且RSI不超买，买入
                                self._place_order('SAMPLE', 1)
                                self.position += 1
                                self.trade_count += 1
                            elif (price < self.current_ma5 and self.current_rsi > 30 and 
                                 self.position >= 0):
                                # 价格低于MA5且RSI不超卖，卖出
                                self._place_order('SAMPLE', -1)
                                self.position -= 1
                                self.trade_count += 1
                
                elif source == 'indicator':
                    # 更新指标
                    if 'ma5' in data:
                        self.current_ma5 = data['ma5']
                    if 'rsi' in data:
                        self.current_rsi = data['rsi']
        
        # 创建增强版策略
        enhanced_strategy = EnhancedStrategy(self.execution_engine)
        
        # 创建多数据源控制器
        controller = MultiSourceReplayController({
            'price': self.price_data,
            'indicator': indicator_data
        })
        
        # 注册策略回调
        controller.register_callback(enhanced_strategy.on_data)
        
        # 使用同步API处理所有数据
        results = controller.process_all_sync()
        
        # 验证策略接收到所有数据
        assert len(enhanced_strategy.received_data) == 20  # 10个价格 + 10个指标
        
        # 验证生成了订单
        assert len(self.execution_engine.orders) > 0
        
        # 验证执行了订单
        assert len(self.execution_engine.executions) > 0


if __name__ == "__main__":
    pytest.main(["-v", "test_replay_integration_execution.py"]) 