#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket客户端的单元测试
"""
import pytest
import asyncio
import json
import time
from unittest.mock import MagicMock, patch, AsyncMock

# 导入被测试的模块
from qte.exchange.websocket.websocket_client import ExchangeWebSocketClient


class TestWebSocketClient:
    """WebSocket客户端测试类"""
    
    @pytest.fixture
    def mock_websocket(self):
        """模拟WebSocket连接"""
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.close = AsyncMock()
        
        # 模拟接收消息的生成器
        class MockAsyncIterator:
            async def __aiter__(self):
                return self
            
            async def __anext__(self):
                # 永远不会返回消息，我们会在测试中手动调用_process_message
                await asyncio.sleep(3600)  # 长时间睡眠，实际不会执行到这里
                raise StopAsyncIteration()
        
        # 设置异步迭代器
        mock_ws.__aiter__.return_value = MockAsyncIterator()
        
        return mock_ws
    
    @pytest.fixture
    def client(self, mock_websocket):
        """设置测试客户端"""
        with patch('websockets.connect', AsyncMock(return_value=mock_websocket)):
            client = ExchangeWebSocketClient(host="localhost", port=8765)
            # 手动设置连接状态，以便其他测试可以正常运行
            client.connected = True
            client.connection = mock_websocket
            return client
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """测试客户端初始化"""
        client = ExchangeWebSocketClient(host="testhost", port=9876, api_key="test_key")
        
        assert client.host == "testhost"
        assert client.port == 9876
        assert client.api_key == "test_key"
        assert client.ws_url == "ws://testhost:9876"
        assert client.connected is False
        assert client.connection is None
        assert client.user_id is None
        assert len(client.subscriptions) == 0
        assert len(client.message_callbacks) == 0
    
    @pytest.mark.asyncio
    async def test_connect(self, mock_websocket):
        """测试连接功能"""
        # 为这个测试创建新的客户端，不使用fixture
        with patch('websockets.connect', AsyncMock(return_value=mock_websocket)):
            client = ExchangeWebSocketClient(host="localhost", port=8765)
            # 确保客户端初始状态未连接
            assert client.connected is False
            assert client.connection is None
            
            # 连接到服务器
            connect_result = await client.connect()
            
            # 验证连接状态
            assert connect_result is True
            assert client.connected is True
            assert client.connection is mock_websocket
            
            # 验证websockets.connect被调用
            websockets_connect = pytest.importorskip("websockets").connect
            websockets_connect.assert_called_once_with("ws://localhost:8765")
    
    @pytest.mark.asyncio
    async def test_connect_with_auto_auth(self, mock_websocket):
        """测试连接时自动认证"""
        # 模拟认证成功响应
        async def mock_auth_response(*args, **kwargs):
            # 解析发送的消息
            message = json.loads(args[0])
            request_id = message["id"]
            
            # 手动触发认证成功响应
            auth_response = {
                "result": "success",
                "user_id": "test_user",
                "id": request_id
            }
            
            # 模拟接收到响应
            await client._process_message(json.dumps(auth_response))
        
        # 创建带API密钥的客户端
        with patch('websockets.connect', AsyncMock(return_value=mock_websocket)):
            client = ExchangeWebSocketClient(host="localhost", port=8765, api_key="test_key")
            
            # 设置模拟响应
            mock_websocket.send.side_effect = mock_auth_response
            
            # 连接并自动认证
            connect_result = await client.connect()
        
        # 验证连接和认证结果
        assert connect_result is True
        assert client.connected is True
        assert client.user_id == "test_user"
        assert client.api_key == "test_key"
        
        # 验证发送了认证请求
        mock_websocket.send.assert_called_once()
        auth_request = json.loads(mock_websocket.send.call_args[0][0])
        assert auth_request["method"] == "auth"
        assert auth_request["params"]["api_key"] == "test_key"
    
    @pytest.mark.asyncio
    async def test_disconnect(self, client, mock_websocket):
        """测试断开连接"""
        # 不需要连接，client fixture已经设置了连接状态
        assert client.connected is True
        
        # 断开连接
        disconnect_result = await client.disconnect()
        
        # 验证断开连接结果
        assert disconnect_result is True
        assert client.connected is False
        assert client.connection is None
        
        # 验证close被调用
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate(self, client, mock_websocket):
        """测试认证功能"""
        # 不需要连接，client fixture已经设置了连接状态
        
        # 模拟认证响应
        async def mock_auth_response(*args, **kwargs):
            # 解析发送的消息
            message = json.loads(args[0])
            request_id = message["id"]
            
            # 手动触发认证成功响应
            auth_response = {
                "result": "success",
                "user_id": "test_user_123",
                "id": request_id
            }
            
            # 模拟接收到响应
            await client._process_message(json.dumps(auth_response))
        
        # 设置模拟响应
        mock_websocket.send.side_effect = mock_auth_response
        
        # 执行认证
        auth_result = await client.authenticate("test_api_key_123")
        
        # 验证认证结果
        assert auth_result is True
        assert client.user_id == "test_user_123"
        assert client.api_key == "test_api_key_123"
        
        # 验证发送了认证请求
        mock_websocket.send.assert_called_once()
        auth_request = json.loads(mock_websocket.send.call_args[0][0])
        assert auth_request["method"] == "auth"
        assert auth_request["params"]["api_key"] == "test_api_key_123"
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, client, mock_websocket):
        """测试认证失败"""
        # 不需要连接，client fixture已经设置了连接状态
        
        # 模拟认证失败响应
        async def mock_auth_response(*args, **kwargs):
            # 解析发送的消息
            message = json.loads(args[0])
            request_id = message["id"]
            
            # 手动触发认证失败响应
            auth_response = {
                "error": "无效的API密钥",
                "id": request_id
            }
            
            # 模拟接收到响应
            await client._process_message(json.dumps(auth_response))
        
        # 设置模拟响应
        mock_websocket.send.side_effect = mock_auth_response
        
        # 记住原始API密钥
        original_api_key = client.api_key
        
        # 执行认证
        auth_result = await client.authenticate("invalid_api_key")
        
        # 验证认证结果
        assert auth_result is False
        assert client.user_id is None
        # 认证失败时，API密钥不会被更新
        assert client.api_key == original_api_key
    
    @pytest.mark.asyncio
    async def test_subscribe(self, client, mock_websocket):
        """测试订阅功能"""
        # 不需要连接，client fixture已经设置了连接状态
        
        # 模拟订阅响应
        async def mock_subscribe_response(*args, **kwargs):
            # 解析发送的消息
            message = json.loads(args[0])
            request_id = message["id"]
            streams = message["params"]["streams"]
            
            # 手动触发订阅成功响应
            subscribe_response = {
                "result": "success",
                "streams": streams,
                "id": request_id
            }
            
            # 模拟接收到响应
            await client._process_message(json.dumps(subscribe_response))
        
        # 设置模拟响应
        mock_websocket.send.side_effect = mock_subscribe_response
        
        # 执行订阅
        streams = ["BTCUSDT@trade", "ETHUSDT@kline"]
        subscribe_result = await client.subscribe(streams)
        
        # 验证订阅结果
        assert subscribe_result is True
        assert "BTCUSDT@trade" in client.subscriptions
        assert "ETHUSDT@kline" in client.subscriptions
        
        # 验证发送了订阅请求
        mock_websocket.send.assert_called_once()
        subscribe_request = json.loads(mock_websocket.send.call_args[0][0])
        assert subscribe_request["method"] == "subscribe"
        assert subscribe_request["params"]["streams"] == streams
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, client, mock_websocket):
        """测试取消订阅功能"""
        # 不需要连接，client fixture已经设置了连接状态
        
        # 设置已有订阅
        client.subscriptions.add("BTCUSDT@trade")
        client.subscriptions.add("ETHUSDT@kline")
        
        # 模拟取消订阅响应
        async def mock_unsubscribe_response(*args, **kwargs):
            # 解析发送的消息
            message = json.loads(args[0])
            request_id = message["id"]
            
            # 手动触发取消订阅成功响应
            unsubscribe_response = {
                "result": "success",
                "id": request_id
            }
            
            # 模拟接收到响应
            await client._process_message(json.dumps(unsubscribe_response))
        
        # 设置模拟响应
        mock_websocket.send.side_effect = mock_unsubscribe_response
        
        # 执行取消订阅
        streams = ["BTCUSDT@trade"]
        unsubscribe_result = await client.unsubscribe(streams)
        
        # 验证取消订阅结果
        assert unsubscribe_result is True
        assert "BTCUSDT@trade" not in client.subscriptions
        assert "ETHUSDT@kline" in client.subscriptions
        
        # 验证发送了取消订阅请求
        mock_websocket.send.assert_called_once()
        unsubscribe_request = json.loads(mock_websocket.send.call_args[0][0])
        assert unsubscribe_request["method"] == "unsubscribe"
        assert unsubscribe_request["params"]["streams"] == streams
    
    @pytest.mark.asyncio
    async def test_unsubscribe_all(self, client, mock_websocket):
        """测试取消所有订阅"""
        # 不需要连接，client fixture已经设置了连接状态
        
        # 设置已有订阅
        client.subscriptions.add("BTCUSDT@trade")
        client.subscriptions.add("ETHUSDT@kline")
        
        # 模拟取消订阅响应
        async def mock_unsubscribe_response(*args, **kwargs):
            # 解析发送的消息
            message = json.loads(args[0])
            request_id = message["id"]
            
            # 手动触发取消订阅成功响应
            unsubscribe_response = {
                "result": "success",
                "id": request_id
            }
            
            # 模拟接收到响应
            await client._process_message(json.dumps(unsubscribe_response))
        
        # 设置模拟响应
        mock_websocket.send.side_effect = mock_unsubscribe_response
        
        # 执行取消所有订阅
        unsubscribe_result = await client.unsubscribe()
        
        # 验证取消订阅结果
        assert unsubscribe_result is True
        assert len(client.subscriptions) == 0
        
        # 验证发送了取消订阅请求
        mock_websocket.send.assert_called_once()
        unsubscribe_request = json.loads(mock_websocket.send.call_args[0][0])
        assert unsubscribe_request["method"] == "unsubscribe"
        assert "params" not in unsubscribe_request
    
    @pytest.mark.asyncio
    async def test_message_callbacks(self, client, mock_websocket):
        """测试消息回调功能"""
        # 不需要连接，client fixture已经设置了连接状态
        
        # 创建回调
        callback_data = {}
        
        def market_callback(data):
            callback_data["market"] = data
            
        def user_callback(data):
            callback_data["user"] = data
        
        # 添加回调
        client.add_message_callback("BTCUSDT@trade", market_callback)
        client.add_message_callback("user123@account", user_callback)
        
        # 模拟收到市场数据消息
        market_message = {
            "stream": "BTCUSDT@trade",
            "data": {
                "e": "trade",
                "E": 1589437618213,
                "s": "BTCUSDT",
                "t": 1234567,
                "p": "9000.00",
                "q": "1.5"
            }
        }
        
        # 模拟收到用户数据消息
        user_message = {
            "stream": "user123@account",
            "data": {
                "e": "outboundAccountPosition",
                "E": 1589437618213,
                "B": [
                    {
                        "a": "BTC",
                        "f": "1.0",
                        "l": "0.5"
                    }
                ]
            }
        }
        
        # 手动触发消息处理
        await client._process_message(json.dumps(market_message))
        await client._process_message(json.dumps(user_message))
        
        # 验证回调被调用
        assert "market" in callback_data
        assert callback_data["market"] == market_message["data"]
        
        assert "user" in callback_data
        assert callback_data["user"] == user_message["data"]
        
        # 测试移除回调
        result = client.remove_message_callback("BTCUSDT@trade", market_callback)
        assert result is True
        
        # 清空回调数据
        callback_data.clear()
        
        # 再次触发消息
        await client._process_message(json.dumps(market_message))
        await client._process_message(json.dumps(user_message))
        
        # 验证只有未移除的回调被调用
        assert "market" not in callback_data
        assert "user" in callback_data 