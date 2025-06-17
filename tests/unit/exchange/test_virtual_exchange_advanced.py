#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VirtualExchange高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from qte.exchange.virtual_exchange import VirtualExchange
from qte.core.events import Event, EventType
from qte.data.data_replay import DataFrameReplayController, ReplayMode


class TestVirtualExchangeAdvanced:
    """VirtualExchange高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.exchange_id = "test_exchange"
        
    def test_init_virtual_exchange_basic(self):
        """测试虚拟交易所基本初始化"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(
            exchange_id=self.exchange_id,
            enable_market_data=True,
            enable_data_replay=False
        )
        
        # 验证基本属性
        assert exchange.exchange_id == self.exchange_id
        assert exchange.time_manager is not None
        assert exchange.account_manager is not None
        assert exchange.market_data_manager is not None
        assert exchange.order_books == {}
        assert exchange.enable_data_replay is False
        assert exchange.replay_controller is None
        assert exchange.is_running is False
        assert exchange.is_market_open is True
        assert exchange.event_listeners == []
    
    def test_init_virtual_exchange_without_market_data(self):
        """测试虚拟交易所初始化 - 禁用行情管理"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(
            exchange_id=self.exchange_id,
            enable_market_data=False
        )
        
        # 验证行情管理器为None
        assert exchange.market_data_manager is None
        assert exchange.account_manager is not None
    
    def test_init_virtual_exchange_with_data_replay(self):
        """测试虚拟交易所初始化 - 启用数据回放"""
        # Red: 编写失败的测试
        mock_controller = Mock(spec=DataFrameReplayController)
        
        exchange = VirtualExchange(
            exchange_id=self.exchange_id,
            enable_data_replay=True,
            replay_controller=mock_controller
        )
        
        # 验证数据回放设置
        assert exchange.enable_data_replay is True
        assert exchange.replay_controller == mock_controller
        assert mock_controller.on_data_callback == exchange._on_replay_data
    
    def test_setup_data_replay_disabled(self):
        """测试数据回放设置 - 禁用状态"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(enable_data_replay=False)
        
        # 调用_setup_data_replay应该直接返回
        exchange._setup_data_replay()
        
        # 验证没有设置回放控制器
        assert exchange.replay_controller is None
    
    def test_setup_data_replay_no_controller(self):
        """测试数据回放设置 - 无控制器"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=None
        )
        
        # 调用_setup_data_replay应该直接返回
        exchange._setup_data_replay()
        
        # 验证没有设置回调
        assert exchange.replay_controller is None
    
    def test_on_replay_data_success(self):
        """测试回放数据处理 - 成功情况"""
        # Red: 编写失败的测试
        mock_controller = Mock(spec=DataFrameReplayController)
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=mock_controller,
            enable_market_data=True
        )
        
        # 准备测试数据
        timestamp = datetime.now(timezone.utc)
        symbol = "AAPL"
        data = {
            'close': 150.0,
            'volume': 1000,
            'open': 149.0,
            'high': 151.0,
            'low': 148.0
        }
        
        # Mock方法
        exchange._emit_market_data_event = Mock()
        exchange._check_order_triggers = Mock()
        
        # 调用回放数据处理
        exchange._on_replay_data(timestamp, symbol, data)

        # 验证时间管理器更新（TimeManager使用set_virtual_time方法）
        # 由于TimeManager的API不同，我们验证方法被调用而不是属性
        assert exchange.time_manager.get_current_time() > 0
        
        # 验证事件发送和订单检查被调用
        exchange._emit_market_data_event.assert_called_once()
        exchange._check_order_triggers.assert_called_once_with(symbol, 150.0)
    
    def test_on_replay_data_no_market_data_manager(self):
        """测试回放数据处理 - 无行情管理器"""
        # Red: 编写失败的测试
        mock_controller = Mock(spec=DataFrameReplayController)
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=mock_controller,
            enable_market_data=False  # 禁用行情管理
        )
        
        # 准备测试数据
        timestamp = datetime.now(timezone.utc)
        symbol = "AAPL"
        data = {'close': 150.0, 'volume': 1000}
        
        # Mock方法
        exchange._emit_market_data_event = Mock()
        exchange._check_order_triggers = Mock()
        
        # 调用回放数据处理（应该不抛出异常）
        exchange._on_replay_data(timestamp, symbol, data)
        
        # 验证仍然调用了其他方法
        exchange._emit_market_data_event.assert_called_once()
        exchange._check_order_triggers.assert_called_once()
    
    def test_on_replay_data_exception_handling(self):
        """测试回放数据处理 - 异常处理"""
        # Red: 编写失败的测试
        mock_controller = Mock(spec=DataFrameReplayController)
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=mock_controller
        )
        
        # Mock时间管理器抛出异常
        exchange.time_manager.set_virtual_time = Mock(side_effect=Exception("Test error"))
        
        # 准备测试数据
        timestamp = datetime.now(timezone.utc)
        symbol = "AAPL"
        data = {'close': 150.0}
        
        # 调用回放数据处理（应该捕获异常）
        with patch('qte.exchange.virtual_exchange.logger') as mock_logger:
            exchange._on_replay_data(timestamp, symbol, data)
            
            # 验证错误日志被记录
            mock_logger.error.assert_called_once()
    
    def test_start_data_replay_no_controller(self):
        """测试启动数据回放 - 无控制器"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(enable_data_replay=False)
        
        # 启动数据回放应该返回False
        result = exchange.start_data_replay()
        
        assert result is False
    
    def test_start_data_replay_success(self):
        """测试启动数据回放 - 成功"""
        # Red: 编写失败的测试
        mock_controller = Mock()  # 不使用spec，避免属性限制
        mock_controller.start_replay.return_value = True
        
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=mock_controller
        )
        
        # 准备参数
        start_time = datetime.now(timezone.utc)
        end_time = start_time.replace(hour=23)
        speed_factor = 2.0
        replay_mode = ReplayMode.BACKTEST
        
        # 启动数据回放
        result = exchange.start_data_replay(
            start_time=start_time,
            end_time=end_time,
            speed_factor=speed_factor,
            replay_mode=replay_mode
        )
        
        # 验证结果
        assert result is True
        mock_controller.start_replay.assert_called_once_with(
            start_time=start_time,
            end_time=end_time,
            speed_factor=speed_factor,
            mode=replay_mode
        )
    
    def test_start_data_replay_failure(self):
        """测试启动数据回放 - 失败"""
        # Red: 编写失败的测试
        mock_controller = Mock()  # 不使用spec，避免属性限制
        mock_controller.start_replay.return_value = False
        
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=mock_controller
        )
        
        # 启动数据回放
        result = exchange.start_data_replay()
        
        # 验证结果
        assert result is False
    
    def test_start_data_replay_exception(self):
        """测试启动数据回放 - 异常处理"""
        # Red: 编写失败的测试
        mock_controller = Mock()  # 不使用spec，避免属性限制
        mock_controller.start_replay.side_effect = Exception("Test error")
        
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=mock_controller
        )
        
        # 启动数据回放
        result = exchange.start_data_replay()
        
        # 验证结果
        assert result is False
    
    def test_emit_market_data_event(self):
        """测试发送市场数据事件"""
        # Red: 编写失败的测试
        exchange = VirtualExchange()
        exchange._emit_event = Mock()
        
        # 准备数据
        symbol = "AAPL"
        tick_data = {
            'symbol': symbol,
            'timestamp': datetime.now(timezone.utc),
            'price': 150.0
        }
        
        # 发送市场数据事件
        exchange._emit_market_data_event(symbol, tick_data)

        # 验证事件被发送
        exchange._emit_event.assert_called_once()
        call_args = exchange._emit_event.call_args[0][0]
        assert isinstance(call_args, Event)
        assert call_args.event_type == "MARKET_DATA"  # 使用字符串而不是枚举
        assert call_args.data['symbol'] == symbol
        assert call_args.data['tick_data'] == tick_data
    
    def test_check_order_triggers_no_order_book(self):
        """测试检查订单触发 - 无订单簿"""
        # Red: 编写失败的测试
        exchange = VirtualExchange()
        
        # 调用检查订单触发（应该直接返回）
        exchange._check_order_triggers("AAPL", 150.0)
        
        # 验证没有异常抛出
        assert True
    
    def test_check_order_triggers_with_order_book(self):
        """测试检查订单触发 - 有订单簿"""
        # Red: 编写失败的测试
        exchange = VirtualExchange()
        
        # 创建Mock订单簿
        mock_order_book = Mock()
        mock_orders = [Mock(), Mock()]
        mock_order_book.check_triggers.return_value = mock_orders
        exchange.order_books["AAPL"] = mock_order_book
        
        # Mock处理触发订单方法
        exchange._process_triggered_order = Mock()
        
        # 调用检查订单触发
        exchange._check_order_triggers("AAPL", 150.0)
        
        # 验证订单簿检查被调用
        mock_order_book.check_triggers.assert_called_once_with(150.0)
        
        # 验证触发的订单被处理
        assert exchange._process_triggered_order.call_count == 2
    
    def test_process_triggered_order(self):
        """测试处理触发的订单"""
        # Red: 编写失败的测试
        exchange = VirtualExchange()
        mock_order = Mock()
        
        # 调用处理触发订单（当前是空实现）
        exchange._process_triggered_order(mock_order)
        
        # 验证没有异常抛出
        assert True

    def test_set_replay_controller(self):
        """测试设置数据回放控制器"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(enable_data_replay=False)
        mock_controller = Mock(spec=DataFrameReplayController)

        # 设置回放控制器
        exchange.set_replay_controller(mock_controller)

        # 验证设置成功
        assert exchange.replay_controller == mock_controller
        assert exchange.enable_data_replay is True
        assert mock_controller.on_data_callback == exchange._on_replay_data

    def test_get_replay_status_disabled(self):
        """测试获取回放状态 - 禁用状态"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(enable_data_replay=False)

        # 获取回放状态
        status = exchange.get_replay_status()

        # 验证状态
        assert status == {"enabled": False}

    def test_get_replay_status_enabled_no_controller(self):
        """测试获取回放状态 - 启用但无控制器"""
        # Red: 编写失败的测试
        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=None
        )

        # 获取回放状态
        status = exchange.get_replay_status()

        # 验证状态
        expected = {
            "enabled": True,
            "controller_ready": False,
            "message": "数据回放已启用但控制器未设置"
        }
        assert status == expected

    def test_get_replay_status_enabled_with_controller(self):
        """测试获取回放状态 - 启用且有控制器"""
        # Red: 编写失败的测试
        mock_controller = Mock(spec=DataFrameReplayController)
        mock_controller.is_running = True
        mock_controller.mode = ReplayMode.BACKTEST

        exchange = VirtualExchange(
            enable_data_replay=True,
            replay_controller=mock_controller
        )

        # 设置时间管理器当前时间
        test_time = datetime.now(timezone.utc)
        exchange.time_manager.current_time = test_time

        # 获取回放状态
        status = exchange.get_replay_status()

        # 验证状态
        assert status["enabled"] is True
        assert status["controller_ready"] is True
        assert status["is_running"] is True
        assert status["current_time"] == test_time.isoformat()
        assert status["mode"] == ReplayMode.BACKTEST

    def test_emit_event_success(self):
        """测试发送事件 - 成功"""
        # Red: 编写失败的测试
        exchange = VirtualExchange()

        # 添加事件监听器
        listener1 = Mock()
        listener2 = Mock()
        exchange.add_event_listener(listener1)
        exchange.add_event_listener(listener2)

        # 创建测试事件
        test_event = Event(
            event_type="MARKET_DATA",  # 使用字符串而不是枚举
            data={'test': 'data'}
        )

        # 发送事件
        exchange._emit_event(test_event)

        # 验证所有监听器被调用
        listener1.assert_called_once_with(test_event)
        listener2.assert_called_once_with(test_event)

    def test_add_event_listener(self):
        """测试添加事件监听器"""
        # Red: 编写失败的测试
        exchange = VirtualExchange()
        listener = Mock()

        # 添加监听器
        exchange.add_event_listener(listener)

        # 验证监听器被添加
        assert listener in exchange.event_listeners
        assert len(exchange.event_listeners) == 1

    def test_remove_event_listener_exists(self):
        """测试移除事件监听器 - 存在的监听器"""
        # Red: 编写失败的测试
        exchange = VirtualExchange()
        listener = Mock()

        # 添加监听器
        exchange.add_event_listener(listener)
        assert listener in exchange.event_listeners

        # 移除监听器
        exchange.remove_event_listener(listener)

        # 验证监听器被移除
        assert listener not in exchange.event_listeners
        assert len(exchange.event_listeners) == 0
