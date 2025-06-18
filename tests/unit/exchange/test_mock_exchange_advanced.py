#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MockExchange高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from qte.exchange.mock_exchange import MockExchange
from qte.exchange.matching.matching_engine import Order, OrderSide, OrderType


class TestMockExchangeAdvanced:
    """MockExchange高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建模拟交易所实例（不启动服务器）
        self.exchange = MockExchange(rest_port=5001, ws_port=8766)  # 使用不同端口避免冲突
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 确保交易所停止
        try:
            self.exchange.stop()
        except:
            pass
    
    def test_init_mock_exchange(self):
        """测试模拟交易所初始化"""
        # Red: 编写失败的测试
        exchange = MockExchange(rest_host="127.0.0.1", rest_port=5002, 
                               ws_host="127.0.0.1", ws_port=8767)
        
        # 验证组件初始化
        assert exchange.matching_engine is not None
        assert exchange.account_manager is not None
        assert exchange.rest_server is not None
        assert exchange.ws_server is not None
        
        # 验证初始状态
        assert exchange.ws_loop is None
        assert exchange.ws_thread is None
        assert len(exchange.symbols) == 0
        assert len(exchange.api_keys) == 0
        
        # 验证服务器配置
        assert exchange.rest_server.host == "127.0.0.1"
        assert exchange.rest_server.port == 5002
        assert exchange.ws_server.host == "127.0.0.1"
        assert exchange.ws_server.port == 8767
    
    def test_register_symbol_new(self):
        """测试注册新交易对"""
        # Red: 编写失败的测试
        symbol = "BTCUSDT"
        base_asset = "BTC"
        quote_asset = "USDT"
        
        # 注册交易对
        result = self.exchange.register_symbol(symbol, base_asset, quote_asset)
        
        # 验证注册成功
        assert result is True
        assert symbol in self.exchange.symbols
        
        # 验证订单簿创建
        order_book = self.exchange.matching_engine.get_order_book(symbol)
        assert order_book is not None
    
    def test_register_symbol_duplicate(self):
        """测试注册重复交易对"""
        # Red: 编写失败的测试
        symbol = "BTCUSDT"
        
        # 第一次注册
        result1 = self.exchange.register_symbol(symbol, "BTC", "USDT")
        assert result1 is True
        
        # 第二次注册相同交易对
        result2 = self.exchange.register_symbol(symbol, "BTC", "USDT")
        assert result2 is False  # 应该失败
        
        # 验证只有一个交易对
        assert len(self.exchange.symbols) == 1
    
    def test_create_user(self):
        """测试创建用户"""
        # Red: 编写失败的测试
        user_id = "test_user_001"
        user_name = "Test User"
        
        # Mock API密钥生成
        with patch.object(self.exchange.rest_server, 'create_api_key', return_value="test_api_key_123"):
            # 创建用户
            api_key = self.exchange.create_user(user_id, user_name)
            
            # 验证API密钥返回
            assert api_key == "test_api_key_123"
            
            # 验证账户创建
            account = self.exchange.account_manager.get_account(user_id)
            assert account is not None
            
            # 验证API密钥共享
            assert self.exchange.ws_server.api_keys == self.exchange.rest_server.api_keys
    
    def test_deposit_success(self):
        """测试用户充值成功"""
        # Red: 编写失败的测试
        user_id = "test_user_002"
        asset = "USDT"
        amount = 1000.0
        
        # 创建用户
        self.exchange.create_user(user_id)
        
        # 充值
        result = self.exchange.deposit(user_id, asset, amount)
        
        # 验证充值成功
        assert result is True
        
        # 验证账户余额
        account = self.exchange.account_manager.get_account(user_id)
        balance = account.get_balance(asset)
        assert balance.free == Decimal(str(amount))
    
    def test_deposit_user_not_exists(self):
        """测试充值不存在的用户"""
        # Red: 编写失败的测试
        user_id = "nonexistent_user"
        asset = "USDT"
        amount = 1000.0
        
        # 尝试为不存在的用户充值
        result = self.exchange.deposit(user_id, asset, amount)
        
        # 验证充值失败
        assert result is False
    
    def test_place_order_limit_success(self):
        """测试下限价单成功"""
        # Red: 编写失败的测试
        user_id = "test_user_003"
        symbol = "BTCUSDT"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        self.exchange.deposit(user_id, "USDT", 10000.0)
        
        # 下限价买单
        order_info = self.exchange.place_order(
            user_id=user_id,
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            quantity=0.1,
            price=50000.0,
            client_order_id="test_order_001"
        )
        
        # 验证订单信息
        assert order_info is not None
        assert order_info["symbol"] == symbol
        assert order_info["side"] == "BUY"
        assert order_info["type"] == "LIMIT"
        assert order_info["price"] == 50000.0
        assert float(order_info["quantity"]) == 0.1  # Decimal转float比较
        assert order_info["client_order_id"] == "test_order_001"
        assert "order_id" in order_info
    
    def test_place_order_limit_no_price(self):
        """测试下限价单但未指定价格"""
        # Red: 编写失败的测试
        user_id = "test_user_004"
        symbol = "BTCUSDT"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        self.exchange.deposit(user_id, "USDT", 10000.0)
        
        # 下限价单但不指定价格
        order_info = self.exchange.place_order(
            user_id=user_id,
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            quantity=0.1
            # 缺少price参数
        )
        
        # 验证下单失败
        assert order_info is None
    
    def test_place_order_user_not_exists(self):
        """测试不存在用户下单"""
        # Red: 编写失败的测试
        user_id = "nonexistent_user"
        symbol = "BTCUSDT"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        
        # 尝试下单
        order_info = self.exchange.place_order(
            user_id=user_id,
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            quantity=0.1,
            price=50000.0
        )
        
        # 验证下单失败
        assert order_info is None
    
    def test_place_order_insufficient_funds(self):
        """测试资金不足下单"""
        # Red: 编写失败的测试
        user_id = "test_user_005"
        symbol = "BTCUSDT"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        self.exchange.deposit(user_id, "USDT", 100.0)  # 只充值100 USDT
        
        # Mock资金锁定失败
        with patch.object(self.exchange.account_manager, 'lock_funds_for_order', return_value=False):
            # 尝试下大额订单
            order_info = self.exchange.place_order(
                user_id=user_id,
                symbol=symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=1.0,
                price=50000.0  # 需要50000 USDT，但只有100
            )
            
            # 验证下单失败
            assert order_info is None
    
    def test_place_order_market_order_failure(self):
        """测试下市价单失败（当前实现限制）"""
        # Red: 编写失败的测试
        user_id = "test_user_006"
        symbol = "BTCUSDT"

        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        self.exchange.deposit(user_id, "USDT", 10000.0)

        # 下市价买单（当前实现会失败，因为需要价格）
        order_info = self.exchange.place_order(
            user_id=user_id,
            symbol=symbol,
            side="BUY",
            order_type="MARKET",
            quantity=0.1  # 市价单也需要quantity
        )

        # 验证下单失败（当前实现的限制）
        assert order_info is None
    
    def test_place_order_with_trades(self):
        """测试下单产生成交"""
        # Red: 编写失败的测试
        user_id = "test_user_007"
        symbol = "BTCUSDT"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        self.exchange.deposit(user_id, "USDT", 10000.0)
        
        # Mock撮合引擎返回成交
        mock_trade = Mock()
        mock_trade.trade_id = "trade_001"
        mock_trade.price = 50000.0
        mock_trade.quantity = 0.1
        mock_trade.timestamp = time.time()
        mock_trade.buyer_user_id = user_id
        mock_trade.seller_user_id = "other_user"
        
        with patch.object(self.exchange.matching_engine, 'place_order', return_value=[mock_trade]):
            # 下单
            order_info = self.exchange.place_order(
                user_id=user_id,
                symbol=symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=0.1,
                price=50000.0
            )
            
            # 验证订单包含成交信息
            assert order_info is not None
            assert len(order_info["trades"]) == 1
            assert order_info["trades"][0]["trade_id"] == "trade_001"
            assert order_info["trades"][0]["price"] == 50000.0
            assert order_info["trades"][0]["quantity"] == 0.1
    
    def test_cancel_order_success(self):
        """测试取消订单成功"""
        # Red: 编写失败的测试
        user_id = "test_user_008"
        symbol = "BTCUSDT"
        order_id = "test_order_002"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        
        # Mock订单
        mock_order = Mock()
        mock_order.user_id = user_id
        mock_order.side = OrderSide.BUY
        mock_order.remaining_quantity = 0.1
        mock_order.price = 50000.0
        
        # Mock订单簿
        mock_order_book = Mock()
        mock_order_book.get_order.return_value = mock_order
        
        with patch.object(self.exchange.matching_engine, 'get_order_book', return_value=mock_order_book), \
             patch.object(self.exchange.matching_engine, 'cancel_order', return_value=True), \
             patch.object(self.exchange.account_manager, 'unlock_funds_for_order', return_value=True):
            
            # 取消订单
            result = self.exchange.cancel_order(user_id, symbol, order_id)
            
            # 验证取消成功
            assert result is True
            
            # 验证解锁资金被调用
            self.exchange.account_manager.unlock_funds_for_order.assert_called_once()
    
    def test_cancel_order_not_exists(self):
        """测试取消不存在的订单"""
        # Red: 编写失败的测试
        user_id = "test_user_009"
        symbol = "BTCUSDT"
        order_id = "nonexistent_order"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        
        # Mock订单簿返回None
        mock_order_book = Mock()
        mock_order_book.get_order.return_value = None
        
        with patch.object(self.exchange.matching_engine, 'get_order_book', return_value=mock_order_book):
            # 尝试取消不存在的订单
            result = self.exchange.cancel_order(user_id, symbol, order_id)
            
            # 验证取消失败
            assert result is False
    
    def test_cancel_order_wrong_user(self):
        """测试取消其他用户的订单"""
        # Red: 编写失败的测试
        user_id = "test_user_010"
        other_user_id = "other_user"
        symbol = "BTCUSDT"
        order_id = "test_order_003"
        
        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        
        # Mock订单（属于其他用户）
        mock_order = Mock()
        mock_order.user_id = other_user_id  # 不同的用户ID
        
        # Mock订单簿
        mock_order_book = Mock()
        mock_order_book.get_order.return_value = mock_order
        
        with patch.object(self.exchange.matching_engine, 'get_order_book', return_value=mock_order_book):
            # 尝试取消其他用户的订单
            result = self.exchange.cancel_order(user_id, symbol, order_id)
            
            # 验证取消失败
            assert result is False

    def test_get_order_book_success(self):
        """测试获取订单簿成功"""
        # Red: 编写失败的测试
        symbol = "BTCUSDT"

        # 注册交易对
        self.exchange.register_symbol(symbol, "BTC", "USDT")

        # Mock订单簿深度数据
        mock_order_book = Mock()
        mock_order_book.get_depth.return_value = {
            "bids": [[50000.0, 0.1], [49999.0, 0.2]],
            "asks": [[50001.0, 0.1], [50002.0, 0.2]]
        }
        mock_order_book.order_map = {}  # 空订单映射

        with patch.object(self.exchange.matching_engine, 'get_order_book', return_value=mock_order_book):
            # 获取订单簿
            order_book_data = self.exchange.get_order_book(symbol, depth=5)

            # 验证订单簿数据
            assert order_book_data is not None
            assert order_book_data["symbol"] == symbol
            assert len(order_book_data["bids"]) == 2
            assert len(order_book_data["asks"]) == 2
            assert "timestamp" in order_book_data

    def test_get_order_book_symbol_not_exists(self):
        """测试获取不存在交易对的订单簿"""
        # Red: 编写失败的测试
        symbol = "NONEXISTENT"

        # 尝试获取不存在交易对的订单簿
        order_book_data = self.exchange.get_order_book(symbol)

        # 验证返回None
        assert order_book_data is None

    def test_get_account_success(self):
        """测试获取账户信息成功"""
        # Red: 编写失败的测试
        user_id = "test_user_011"

        # 创建用户
        self.exchange.create_user(user_id)

        # Mock账户快照
        mock_account = Mock()
        mock_account.get_account_snapshot.return_value = {
            "user_id": user_id,
            "balances": {"USDT": 1000.0, "BTC": 0.1},
            "locked": {"USDT": 100.0, "BTC": 0.0}
        }

        with patch.object(self.exchange.account_manager, 'get_account', return_value=mock_account):
            # 获取账户信息
            account_info = self.exchange.get_account(user_id)

            # 验证账户信息
            assert account_info is not None
            assert account_info["user_id"] == user_id
            assert "balances" in account_info
            assert "locked" in account_info

    def test_get_account_user_not_exists(self):
        """测试获取不存在用户的账户信息"""
        # Red: 编写失败的测试
        user_id = "nonexistent_user"

        # 尝试获取不存在用户的账户信息
        account_info = self.exchange.get_account(user_id)

        # 验证返回None
        assert account_info is None

    def test_get_next_order_id(self):
        """测试获取下一个订单ID"""
        # Red: 编写失败的测试
        # 获取订单ID
        order_id1 = self.exchange._get_next_order_id()
        order_id2 = self.exchange._get_next_order_id()

        # 验证订单ID格式和唯一性
        assert isinstance(order_id1, str)
        assert isinstance(order_id2, str)
        assert order_id1 != order_id2
        assert len(order_id1) > 0
        assert len(order_id2) > 0

    @patch('requests.get')
    @patch('time.sleep')
    def test_start_rest_retry_success(self, mock_sleep, mock_requests_get):
        """测试REST服务器重试后成功启动"""
        # Red: 编写失败的测试
        # Mock REST服务器前两次失败，第三次成功
        with patch.object(self.exchange.rest_server, 'start', side_effect=[False, False, True]), \
             patch.object(self.exchange.ws_server, 'start'), \
             patch('threading.Thread'), \
             patch('asyncio.new_event_loop'):

            # Mock HTTP请求成功
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests_get.return_value = mock_response

            # 启动交易所
            result = self.exchange.start()

            # 验证启动成功
            assert result is True

            # 验证重试逻辑
            assert self.exchange.rest_server.start.call_count == 3
            assert mock_sleep.call_count >= 2  # 重试间隔

    @patch('requests.get')
    @patch('time.sleep')
    def test_start_rest_all_attempts_fail(self, mock_sleep, mock_requests_get):
        """测试REST服务器所有重试都失败"""
        # Red: 编写失败的测试
        # Mock REST服务器所有尝试都失败
        with patch.object(self.exchange.rest_server, 'start', return_value=False):

            # 启动交易所
            result = self.exchange.start()

            # 验证启动失败
            assert result is False

            # 验证重试次数
            assert self.exchange.rest_server.start.call_count == 3

    @patch('requests.get')
    @patch('time.sleep')
    def test_start_verification_retry_logic(self, mock_sleep, mock_requests_get):
        """测试启动验证重试逻辑"""
        # Red: 编写失败的测试
        with patch.object(self.exchange.rest_server, 'start', return_value=True), \
             patch.object(self.exchange.ws_server, 'start'), \
             patch('threading.Thread'), \
             patch('asyncio.new_event_loop'):

            # Mock HTTP请求前几次失败，最后成功
            mock_responses = [
                Mock(status_code=500),  # 第1次失败
                Mock(status_code=404),  # 第2次失败
                Mock(status_code=200)   # 第3次成功
            ]
            mock_requests_get.side_effect = mock_responses

            # 启动交易所
            result = self.exchange.start()

            # 验证启动成功
            assert result is True

            # 验证重试次数
            assert mock_requests_get.call_count == 3

    @patch('requests.get')
    @patch('time.sleep')
    def test_start_verification_timeout_error(self, mock_sleep, mock_requests_get):
        """测试启动验证超时错误"""
        # Red: 编写失败的测试
        with patch.object(self.exchange.rest_server, 'start', return_value=True), \
             patch.object(self.exchange.ws_server, 'start'), \
             patch('threading.Thread'), \
             patch('asyncio.new_event_loop'):

            # Mock HTTP请求超时
            import requests
            mock_requests_get.side_effect = [
                requests.exceptions.Timeout("Request timeout"),
                requests.exceptions.Timeout("Request timeout"),
                Mock(status_code=200)  # 最后成功
            ]

            # 启动交易所
            result = self.exchange.start()

            # 验证启动成功（有容错机制）
            assert result is True

    @patch('requests.get')
    @patch('time.sleep')
    def test_start_verification_all_fail_but_continue(self, mock_sleep, mock_requests_get):
        """测试启动验证全部失败但继续执行"""
        # Red: 编写失败的测试
        with patch.object(self.exchange.rest_server, 'start', return_value=True), \
             patch.object(self.exchange.ws_server, 'start'), \
             patch('threading.Thread'), \
             patch('asyncio.new_event_loop'):

            # Mock HTTP请求全部失败
            import requests
            mock_requests_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            # 启动交易所
            result = self.exchange.start()

            # 验证仍然返回True（容错机制）
            assert result is True

            # 验证重试次数
            assert mock_requests_get.call_count == 5  # 最大重试次数

    @patch('asyncio.new_event_loop')
    def test_start_websocket_thread_creation(self, mock_new_event_loop):
        """测试WebSocket线程创建"""
        # Red: 编写失败的测试
        mock_loop = Mock()
        mock_new_event_loop.return_value = mock_loop

        with patch.object(self.exchange.rest_server, 'start', return_value=True), \
             patch.object(self.exchange.ws_server, 'start'), \
             patch('threading.Thread') as mock_thread_class, \
             patch('time.sleep'), \
             patch('requests.get', return_value=Mock(status_code=200)):

            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread

            # 启动交易所
            result = self.exchange.start()

            # 验证WebSocket相关设置
            assert result is True
            assert self.exchange.ws_loop == mock_loop
            assert self.exchange.ws_thread == mock_thread

            # 验证线程配置
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()

            # 验证daemon属性被设置
            assert mock_thread.daemon is True

    def test_stop_with_websocket_components(self):
        """测试停止包含WebSocket组件"""
        # Red: 编写失败的测试
        # 设置WebSocket组件
        mock_ws_loop = Mock()
        mock_ws_thread = Mock()
        mock_ws_thread.is_alive.return_value = True

        self.exchange.ws_loop = mock_ws_loop
        self.exchange.ws_thread = mock_ws_thread

        with patch.object(self.exchange.rest_server, 'stop'), \
             patch.object(self.exchange.ws_server, 'stop'), \
             patch('asyncio.run_coroutine_threadsafe') as mock_run_coroutine:

            # 停止交易所
            result = self.exchange.stop()

            # 验证停止成功
            assert result is True

            # 验证组件停止方法被调用
            self.exchange.rest_server.stop.assert_called_once()
            mock_run_coroutine.assert_called_once()
            mock_ws_loop.call_soon_threadsafe.assert_called_once()
            mock_ws_thread.join.assert_called_once_with(timeout=5)

    def test_stop_without_websocket_components(self):
        """测试停止时没有WebSocket组件"""
        # Red: 编写失败的测试
        # 确保WebSocket组件为None
        self.exchange.ws_loop = None
        self.exchange.ws_thread = None

        with patch.object(self.exchange.rest_server, 'stop'):

            # 停止交易所
            result = self.exchange.stop()

            # 验证停止成功
            assert result is True

            # 验证REST服务器停止被调用
            self.exchange.rest_server.stop.assert_called_once()

    def test_stop_websocket_thread_not_alive(self):
        """测试停止时WebSocket线程未运行"""
        # Red: 编写失败的测试
        # 设置WebSocket组件但线程未运行
        mock_ws_loop = Mock()
        mock_ws_thread = Mock()
        mock_ws_thread.is_alive.return_value = False

        self.exchange.ws_loop = mock_ws_loop
        self.exchange.ws_thread = mock_ws_thread

        with patch.object(self.exchange.rest_server, 'stop'), \
             patch.object(self.exchange.ws_server, 'stop'), \
             patch('asyncio.run_coroutine_threadsafe'):

            # 停止交易所
            result = self.exchange.stop()

            # 验证停止成功
            assert result is True

            # 验证线程join没有被调用（因为线程未运行）
            mock_ws_thread.join.assert_not_called()

    def test_get_order_book_timestamp_calculation(self):
        """测试订单簿时间戳计算"""
        # Red: 编写失败的测试
        symbol = "BTCUSDT"

        # 注册交易对
        self.exchange.register_symbol(symbol, "BTC", "USDT")

        # Mock订单簿有订单
        mock_order = Mock()
        mock_order.timestamp = 1672574400.5  # 2023-01-01 12:00:00.5

        mock_order_book = Mock()
        mock_order_book.get_depth.return_value = {
            "bids": [[50000.0, 0.1]],
            "asks": [[50001.0, 0.1]]
        }
        mock_order_book.order_map = {"order1": mock_order}

        with patch.object(self.exchange.matching_engine, 'get_order_book', return_value=mock_order_book):
            # 获取订单簿
            order_book_data = self.exchange.get_order_book(symbol)

            # 验证时间戳计算
            assert order_book_data is not None
            expected_timestamp = int(1672574400.5 * 1000)  # 转换为毫秒
            assert order_book_data["timestamp"] == expected_timestamp

    def test_get_order_book_empty_order_map(self):
        """测试订单簿空订单映射"""
        # Red: 编写失败的测试
        symbol = "BTCUSDT"

        # 注册交易对
        self.exchange.register_symbol(symbol, "BTC", "USDT")

        # Mock订单簿无订单
        mock_order_book = Mock()
        mock_order_book.get_depth.return_value = {
            "bids": [],
            "asks": []
        }
        mock_order_book.order_map = {}  # 空订单映射

        with patch.object(self.exchange.matching_engine, 'get_order_book', return_value=mock_order_book), \
             patch('time.time', return_value=1672574400.0):

            # 获取订单簿
            order_book_data = self.exchange.get_order_book(symbol)

            # 验证使用当前时间
            assert order_book_data is not None
            expected_timestamp = int(1672574400.0 * 1000)
            assert order_book_data["timestamp"] == expected_timestamp

    def test_place_order_trade_settlement(self):
        """测试下单成交结算"""
        # Red: 编写失败的测试
        user_id = "test_user_settlement"
        symbol = "BTCUSDT"

        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        self.exchange.deposit(user_id, "USDT", 10000.0)

        # Mock成交
        mock_trade = Mock()
        mock_trade.trade_id = "trade_001"
        mock_trade.price = 50000.0
        mock_trade.quantity = 0.1
        mock_trade.timestamp = 1672574400.0
        mock_trade.buyer_user_id = user_id
        mock_trade.seller_user_id = "other_user"

        with patch.object(self.exchange.matching_engine, 'place_order', return_value=[mock_trade]), \
             patch.object(self.exchange.account_manager, 'lock_funds_for_order', return_value=True), \
             patch.object(self.exchange.account_manager, 'settle_trade') as mock_settle:

            # 下单
            order_info = self.exchange.place_order(
                user_id=user_id,
                symbol=symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=0.1,
                price=50000.0
            )

            # 验证订单成功
            assert order_info is not None

            # 验证买方结算被调用
            mock_settle.assert_any_call(
                user_id=user_id,
                symbol=symbol,
                side="BUY",
                amount=Decimal('0.1'),
                price=Decimal('50000.0')
            )

    def test_place_order_no_seller_settlement(self):
        """测试下单成交无卖方结算"""
        # Red: 编写失败的测试
        user_id = "test_user_no_seller"
        symbol = "BTCUSDT"

        # 准备环境
        self.exchange.register_symbol(symbol, "BTC", "USDT")
        self.exchange.create_user(user_id)
        self.exchange.deposit(user_id, "USDT", 10000.0)

        # Mock成交（无卖方）
        mock_trade = Mock()
        mock_trade.trade_id = "trade_002"
        mock_trade.price = 50000.0
        mock_trade.quantity = 0.1
        mock_trade.timestamp = 1672574400.0
        mock_trade.buyer_user_id = user_id
        mock_trade.seller_user_id = None  # 无卖方

        with patch.object(self.exchange.matching_engine, 'place_order', return_value=[mock_trade]), \
             patch.object(self.exchange.account_manager, 'lock_funds_for_order', return_value=True), \
             patch.object(self.exchange.account_manager, 'settle_trade') as mock_settle:

            # 下单
            order_info = self.exchange.place_order(
                user_id=user_id,
                symbol=symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=0.1,
                price=50000.0
            )

            # 验证订单成功
            assert order_info is not None

            # 验证只有买方结算被调用
            assert mock_settle.call_count == 1
            mock_settle.assert_called_with(
                user_id=user_id,
                symbol=symbol,
                side="BUY",
                amount=Decimal('0.1'),
                price=Decimal('50000.0')
            )
