"""
执行模块性能测试
测试执行处理器在高频交易场景下的性能
"""
import pytest
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import random
from typing import List, Dict

from qte.core.events import OrderEvent, FillEvent, MarketEvent, EventType, OrderDirection, OrderType
from qte.core.event_loop import EventLoop
from qte.execution.simple_execution_handler import SimpleExecutionHandler
from qte.execution.basic_broker import BasicBroker, FixedPercentageCommission, SimpleRandomSlippage

class TestExecutionPerformance:
    """测试执行处理器的性能"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建事件循环
        self.event_loop = EventLoop()
        
        # 创建简单执行处理器
        self.execution_handler = SimpleExecutionHandler(
            event_loop=self.event_loop,
            commission_rate=0.0003  # 万分之三佣金
        )
        
        # 生成测试数据
        self.symbols = [f"SH{i:06d}" for i in range(1, 101)]  # 100个股票代码
        self.prices = {symbol: random.uniform(10.0, 100.0) for symbol in self.symbols}
        
        # 设置最新价格
        self.execution_handler.latest_prices = self.prices.copy()
        
        # 记录成交事件
        self.fill_events = []
        self.event_loop.register_handler(EventType.FILL, self.on_fill)
    
    def on_fill(self, event):
        """处理成交事件"""
        self.fill_events.append(event)
    
    def test_order_processing_performance(self):
        """测试订单处理性能"""
        # 生成大量订单
        num_orders = 1000
        orders = []
        
        for i in range(num_orders):
            symbol = random.choice(self.symbols)
            order = OrderEvent(
                order_id=f"perf_test_order_{i}",
                symbol=symbol,
                timestamp=datetime.now() + timedelta(microseconds=i*100),
                direction=OrderDirection.BUY if i % 2 == 0 else OrderDirection.SELL,
                quantity=random.randint(100, 1000),
                order_type=OrderType.MARKET
            )
            orders.append(order)
        
        # 测量处理时间
        start_time = time.time()
        
        # 添加所有订单到事件循环
        for order in orders:
            self.event_loop.put_event(order)
        
        # 处理所有事件
        self.event_loop.run()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证所有订单都被处理
        assert len(self.fill_events) == num_orders
        
        # 输出性能统计
        orders_per_second = num_orders / processing_time
        print(f"\n订单处理性能: {processing_time:.4f} 秒处理 {num_orders} 个订单")
        print(f"平均每秒处理订单数: {orders_per_second:.2f}")
        
        # 有效的性能基准应该是什么取决于实际需求，这里我们设置一个合理的下限
        assert orders_per_second > 100  # 每秒至少处理100个订单
    
    def test_market_and_order_processing_performance(self):
        """测试市场数据和订单的混合处理性能"""
        # 生成市场数据和订单的混合序列
        num_events = 2000  # 总事件数
        mixed_events = []
        
        for i in range(num_events):
            if i % 2 == 0:  # 50%的事件是市场数据
                symbol = random.choice(self.symbols)
                price = self.prices[symbol] * (1 + random.uniform(-0.01, 0.01))
                event = MarketEvent(
                    symbol=symbol,
                    timestamp=datetime.now() + timedelta(microseconds=i*100),
                    open_price=price * 0.995,
                    high_price=price * 1.005,
                    low_price=price * 0.99,
                    close_price=price,
                    volume=random.randint(1000, 10000)
                )
            else:  # 50%的事件是订单
                symbol = random.choice(self.symbols)
                event = OrderEvent(
                    order_id=f"perf_test_mixed_order_{i}",
                    symbol=symbol,
                    timestamp=datetime.now() + timedelta(microseconds=i*100),
                    direction=OrderDirection.BUY if i % 4 == 1 else OrderDirection.SELL,
                    quantity=random.randint(100, 1000),
                    order_type=OrderType.MARKET
                )
            
            mixed_events.append(event)
        
        # 测量处理时间
        start_time = time.time()
        
        # 添加所有事件到事件循环
        for event in mixed_events:
            self.event_loop.put_event(event)
        
        # 处理所有事件
        self.event_loop.run()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证所有订单都被处理 (应有1000个订单事件)
        assert len(self.fill_events) == num_events // 2
        
        # 输出性能统计
        events_per_second = num_events / processing_time
        print(f"\n混合事件处理性能: {processing_time:.4f} 秒处理 {num_events} 个事件")
        print(f"平均每秒处理事件数: {events_per_second:.2f}")
        
        # 设置一个合理的性能下限
        assert events_per_second > 200  # 每秒至少处理200个混合事件
    
    def test_concurrent_market_and_order_performance(self):
        """测试并发市场数据和订单处理性能"""
        # 创建多个线程并发生成市场数据和订单
        num_threads = 4
        num_events_per_thread = 500
        
        self.is_running = True
        self.thread_events_count = 0
        
        def worker_thread(thread_id):
            """工作线程函数"""
            for i in range(num_events_per_thread):
                if not self.is_running:
                    break
                
                # 随机生成市场数据或订单
                if random.random() < 0.5:  # 50%的概率生成市场数据
                    symbol = random.choice(self.symbols)
                    price = self.prices[symbol] * (1 + random.uniform(-0.01, 0.01))
                    event = MarketEvent(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        open_price=price * 0.995,
                        high_price=price * 1.005,
                        low_price=price * 0.99,
                        close_price=price,
                        volume=random.randint(1000, 10000)
                    )
                else:  # 50%的概率生成订单
                    symbol = random.choice(self.symbols)
                    event = OrderEvent(
                        order_id=f"thread_{thread_id}_order_{i}",
                        symbol=symbol,
                        timestamp=datetime.now(),
                        direction=OrderDirection.BUY if random.random() < 0.5 else OrderDirection.SELL,
                        quantity=random.randint(100, 1000),
                        order_type=OrderType.MARKET
                    )
                
                # 添加事件到事件循环
                self.event_loop.put_event(event)
                self.thread_events_count += 1
                
                # 模拟实际环境中的短暂延迟
                time.sleep(0.001)
        
        # 启动线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 开始测量时间
        start_time = time.time()
        
        # 处理线程生成的事件，直到达到预期数量
        expected_order_count = num_threads * num_events_per_thread // 2  # 预期的订单数量
        max_wait_time = 30  # 最大等待时间（秒）
        wait_interval = 0.1  # 检查间隔（秒）
        
        elapsed = 0
        while len(self.fill_events) < expected_order_count and elapsed < max_wait_time:
            # 运行事件循环处理事件
            events_processed = self.event_loop.run(max_events=100)
            
            # 如果没有事件处理，等待一小段时间
            if events_processed == 0:
                time.sleep(wait_interval)
                elapsed += wait_interval
        
        # 停止线程
        self.is_running = False
        
        # 等待所有线程结束
        for thread in threads:
            thread.join(timeout=1.0)
        
        # 确保处理所有剩余事件
        while not self.event_loop.event_queue.empty():
            self.event_loop.run(max_events=100)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 输出性能统计
        total_events = self.thread_events_count
        orders_processed = len(self.fill_events)
        events_per_second = total_events / processing_time
        
        print(f"\n并发事件处理性能: {processing_time:.4f} 秒处理约 {total_events} 个事件")
        print(f"生成的总事件数: {total_events}")
        print(f"处理的订单数: {orders_processed}")
        print(f"平均每秒处理事件数: {events_per_second:.2f}")
        
        # 验证处理的订单数量接近预期值
        # 注意：由于并发性，我们可能无法精确控制生成的订单数量
        assert orders_processed > expected_order_count * 0.8  # 允许80%的完成率


class TestBrokerPerformance:
    """测试经纪商模拟器的性能"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建事件循环
        self.event_loop = EventLoop()
        
        # 创建佣金和滑点模型
        self.commission_model = FixedPercentageCommission(commission_rate=0.001)
        self.slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=0.5)
        
        # 创建模拟数据提供者
        class MockDataProvider:
            def __init__(self, symbols):
                self.latest_bars = {
                    symbol: {
                        'datetime': datetime.now(),
                        'symbol': symbol,
                        'open': random.uniform(10.0, 100.0),
                        'high': random.uniform(10.0, 100.0),
                        'low': random.uniform(10.0, 100.0),
                        'close': random.uniform(10.0, 100.0),
                        'volume': random.randint(1000, 10000)
                    }
                    for symbol in symbols
                }
            
            def get_latest_bar(self, symbol):
                return self.latest_bars.get(symbol)
        
        # 生成测试数据
        self.symbols = [f"SH{i:06d}" for i in range(1, 101)]  # 100个股票代码
        self.data_provider = MockDataProvider(self.symbols)
        
        # 创建经纪商
        self.broker = BasicBroker(
            event_loop=self.event_loop,
            commission_model=self.commission_model,
            slippage_model=self.slippage_model,
            data_provider=self.data_provider
        )
        
        # 记录成交事件
        self.fill_events = []
        self.event_loop.register_handler(EventType.FILL, self.on_fill)
    
    def on_fill(self, event):
        """处理成交事件"""
        self.fill_events.append(event)
    
    def test_broker_order_processing_performance(self):
        """测试经纪商订单处理性能"""
        # 生成大量订单
        num_orders = 1000
        orders = []
        
        for i in range(num_orders):
            symbol = random.choice(self.symbols)
            order = OrderEvent(
                order_id=f"broker_perf_test_order_{i}",
                symbol=symbol,
                timestamp=datetime.now() + timedelta(microseconds=i*100),
                direction=OrderDirection.BUY if i % 2 == 0 else OrderDirection.SELL,
                quantity=random.randint(100, 1000),
                order_type=OrderType.MARKET
            )
            orders.append(order)
        
        # 测量处理时间
        start_time = time.time()
        
        # 提交所有订单到经纪商
        for order in orders:
            self.broker.submit_order(order)
        
        # 处理所有事件
        self.event_loop.run()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证所有订单都被处理
        assert len(self.fill_events) == num_orders
        
        # 输出性能统计
        orders_per_second = num_orders / processing_time
        print(f"\n经纪商订单处理性能: {processing_time:.4f} 秒处理 {num_orders} 个订单")
        print(f"平均每秒处理订单数: {orders_per_second:.2f}")
        
        # 设置一个合理的性能下限
        assert orders_per_second > 100  # 每秒至少处理100个订单
    
    def test_broker_high_frequency_performance(self):
        """测试经纪商在高频交易场景下的性能"""
        # 模拟高频交易场景，大量快速连续的订单
        num_orders = 5000
        
        # 创建订单生成器，避免一次性创建所有订单占用过多内存
        def order_generator():
            for i in range(num_orders):
                symbol = random.choice(self.symbols)
                yield OrderEvent(
                    order_id=f"hft_order_{i}",
                    symbol=symbol,
                    timestamp=datetime.now() + timedelta(microseconds=i*10),  # 更短的时间间隔
                    direction=OrderDirection.BUY if i % 2 == 0 else OrderDirection.SELL,
                    quantity=random.randint(10, 100),  # 较小的交易量
                    order_type=OrderType.MARKET
                )
        
        # 测量处理时间
        start_time = time.time()
        
        # 分批提交订单并处理事件
        batch_size = 100
        orders_submitted = 0
        
        for batch_idx in range(0, num_orders, batch_size):
            # 提交一批订单
            for i, order in enumerate(order_generator()):
                if i >= batch_size:
                    break
                self.broker.submit_order(order)
                orders_submitted += 1
            
            # 处理事件
            self.event_loop.run()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证处理的订单数量
        assert len(self.fill_events) == orders_submitted
        
        # 输出性能统计
        orders_per_second = orders_submitted / processing_time
        print(f"\n高频交易场景性能: {processing_time:.4f} 秒处理 {orders_submitted} 个订单")
        print(f"平均每秒处理订单数: {orders_per_second:.2f}")
        print(f"平均每个订单处理时间: {processing_time/orders_submitted*1000:.4f} 毫秒")
        
        # 高频交易场景的性能要求更高
        assert orders_per_second > 500  # 每秒至少处理500个订单 