#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket服务器边界条件测试
测试WebSocket服务器在各种边界和异常情况下的行为
"""
import pytest
import asyncio
import json
import time
from unittest.mock import MagicMock, patch, AsyncMock

from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer
from qte.exchange.matching.matching_engine import Trade

class TestWebSocketBoundary:
    """WebSocket服务器边界条件测试类"""
    
    @pytest.fixture
    def setup_server(self):
        """设置测试环境"""
        # 创建模拟对象
        self.matching_engine = MagicMock()
        self.account_manager = MagicMock()
        
        # 创建WebSocket服务器
        self.server = ExchangeWebSocketServer(
            matching_engine=self.matching_engine,
            account_manager=self.account_manager,
            host="localhost",
            port=8765
        )
        
        # 添加测试用户和API密钥
        self.test_user_id = "test_user"
        self.test_api_key = self.server.create_api_key(self.test_user_id)
        
        return self.server
    
    @pytest.mark.asyncio
    async def test_ws001_client_state_cleanup_comprehensive(self, setup_server):
        """
        WS-001综合测试：客户端状态同步问题
        验证客户端断开连接后，所有相关状态是否正确清理
        """
        # 模拟多个WebSocket连接
        client1 = MagicMock(name="client1")
        client1.send = AsyncMock()
        client1.remote_address = ("127.0.0.1", 12345)
        
        client2 = MagicMock(name="client2")
        client2.send = AsyncMock()
        client2.remote_address = ("127.0.0.1", 12346)
        
        # 初始化客户端状态
        self.server.clients[client1] = {
            "connected_at": time.time(),
            "user_id": self.test_user_id,
            "subscriptions": set(["BTCUSDT@trade", "ETHUSDT@trade", f"{self.test_user_id}@account"])
        }
        
        self.server.clients[client2] = {
            "connected_at": time.time(),
            "user_id": "another_user",
            "subscriptions": set(["BTCUSDT@trade"])
        }
        
        # 添加到市场订阅
        self.server.market_subscriptions["BTCUSDT@trade"] = set([client1, client2])
        self.server.market_subscriptions["ETHUSDT@trade"] = set([client1])
        
        # 添加到用户订阅
        self.server.user_subscriptions[f"{self.test_user_id}@account"] = set([client1])
        
        # 调用清理方法
        await self.server._cleanup_client(client1)
        
        # 验证结果 - 客户端应该被移除
        assert client1 not in self.server.clients
        assert client2 in self.server.clients
        
        # 验证市场订阅更新
        assert client1 not in self.server.market_subscriptions["BTCUSDT@trade"]
        assert client2 in self.server.market_subscriptions["BTCUSDT@trade"]
        
        # ETHUSDT@trade订阅应该被完全删除，因为没有其他订阅者
        assert "ETHUSDT@trade" not in self.server.market_subscriptions
        
        # 验证用户订阅更新
        assert f"{self.test_user_id}@account" not in self.server.user_subscriptions
    
    @pytest.mark.asyncio
    async def test_ws001_empty_subscriptions(self, setup_server):
        """
        测试WS-001：空订阅集合的客户端断开连接
        验证当客户端没有任何订阅时清理过程是否正常工作
        """
        # 模拟WebSocket连接
        client = MagicMock()
        client.send = AsyncMock()
        
        # 初始化客户端状态 - 没有任何订阅
        self.server.clients[client] = {
            "connected_at": time.time(),
            "user_id": self.test_user_id,
            "subscriptions": set()
        }
        
        # 调用清理方法
        await self.server._cleanup_client(client)
        
        # 验证结果 - 客户端应该被移除
        assert client not in self.server.clients
    
    @pytest.mark.asyncio
    async def test_ws002_invalid_json_handling(self, setup_server):
        """
        测试WS-002：无效JSON消息处理
        验证服务器在收到无效JSON格式的消息时能否正确处理
        """
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.send = AsyncMock()
        
        # 初始化客户端状态
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": None,
            "subscriptions": set()
        }
        
        # 调用消息处理方法 - 无效JSON格式
        invalid_messages = [
            "{invalid json",
            "{]",
            "not a json",
            "12345",
            ""
        ]
        
        for message in invalid_messages:
            mock_websocket.send.reset_mock()
            await self.server._process_message(mock_websocket, message)
            
            # 验证错误响应
            mock_websocket.send.assert_called_once()
            response = json.loads(mock_websocket.send.call_args[0][0])
            assert "error" in response
            assert "无效的JSON格式" in response["error"]
    
    @pytest.mark.asyncio
    async def test_ws002_missing_method(self, setup_server):
        """
        测试WS-002：缺少method字段的消息处理
        验证服务器在收到缺少method字段的JSON消息时能否正确处理
        """
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.send = AsyncMock()
        
        # 初始化客户端状态
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": None,
            "subscriptions": set()
        }
        
        # 调用消息处理方法 - 缺少method字段
        invalid_messages = [
            "{}",
            '{"params": {}}',
            '{"id": 123}'
        ]
        
        for message in invalid_messages:
            mock_websocket.send.reset_mock()
            await self.server._process_message(mock_websocket, message)
            
            # 验证错误响应
            mock_websocket.send.assert_called_once()
            response = json.loads(mock_websocket.send.call_args[0][0])
            assert "error" in response
            assert "无效的消息格式，缺少method字段" in response["error"]
    
    @pytest.mark.asyncio
    async def test_ws002_unsupported_method(self, setup_server):
        """
        测试WS-002：不支持的method处理
        验证服务器在收到不支持的method时能否正确处理
        """
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.send = AsyncMock()
        
        # 初始化客户端状态
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": None,
            "subscriptions": set()
        }
        
        # 调用消息处理方法 - 不支持的method
        unsupported_methods = [
            '{"method": "unknown", "params": {}, "id": 123}',
            '{"method": "ping", "params": {}, "id": 123}',
            '{"method": "disconnect", "params": {}, "id": 123}'
        ]
        
        for message in unsupported_methods:
            mock_websocket.send.reset_mock()
            await self.server._process_message(mock_websocket, message)
            
            # 验证错误响应
            mock_websocket.send.assert_called_once()
            response = json.loads(mock_websocket.send.call_args[0][0])
            assert "error" in response
            assert "不支持的方法" in response["error"]
    
    @pytest.mark.asyncio
    async def test_ws002_exception_in_handler(self, setup_server):
        """
        测试WS-002：处理器中的异常处理
        验证服务器在处理消息的过程中出现异常时能否正确处理
        """
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.send = AsyncMock()
        
        # 初始化客户端状态
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": None,
            "subscriptions": set()
        }
        
        # 使处理器抛出异常
        with patch.object(self.server, '_handle_subscribe', side_effect=Exception("模拟的处理异常")):
            # 调用消息处理方法
            message = '{"method": "subscribe", "params": {"streams": ["BTCUSDT@trade"]}, "id": 123}'
            await self.server._process_message(mock_websocket, message)
            
            # 验证错误响应
            mock_websocket.send.assert_called_once()
            response = json.loads(mock_websocket.send.call_args[0][0])
            assert "error" in response
            assert "处理消息时出错" in response["error"]
    
    @pytest.mark.asyncio
    async def test_client_connection_error_handling(self, setup_server):
        """
        测试客户端连接错误处理
        验证在发送消息给客户端时出现异常能否正确处理
        """
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.send = AsyncMock(side_effect=Exception("连接已关闭"))
        
        # 初始化客户端状态
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": self.test_user_id,
            "subscriptions": set(["BTCUSDT@trade"])
        }
        
        # 添加到市场订阅
        self.server.market_subscriptions["BTCUSDT@trade"] = set([mock_websocket])
        
        # 尝试发送响应
        await self.server._send_response(mock_websocket, {"result": "test"}, "123")
        
        # 尝试发送错误
        await self.server._send_error(mock_websocket, "测试错误", "456")
        
        # 验证没有异常抛出（异常被捕获和记录）
        assert True
    
    @pytest.mark.asyncio
    async def test_broadcast_to_non_existent_subscription(self, setup_server):
        """
        测试向不存在的订阅广播数据
        验证当向不存在的订阅键广播数据时能否正确处理
        """
        # 尝试向不存在的市场数据订阅广播
        await self.server._broadcast_to_market_subscribers("non_existent_key", {"data": "test"})
        
        # 尝试向不存在的用户数据订阅广播
        await self.server._broadcast_to_user_subscribers("non_existent_key", {"data": "test"})
        
        # 验证没有异常抛出
        assert True
    
    @pytest.mark.asyncio
    async def test_broadcast_with_client_error(self, setup_server):
        """
        测试广播时客户端错误处理
        验证在广播过程中某个客户端出错时能否正确处理并继续广播给其他客户端
        """
        # 创建多个模拟客户端
        client1 = MagicMock(name="client1")
        client1.send = AsyncMock()
        
        client2 = MagicMock(name="client2")
        client2.send = AsyncMock(side_effect=Exception("模拟的发送异常"))
        
        client3 = MagicMock(name="client3")
        client3.send = AsyncMock()
        
        # 添加到市场订阅
        subscription_key = "BTCUSDT@trade"
        self.server.market_subscriptions[subscription_key] = set([client1, client2, client3])
        
        # 创建测试消息
        test_message = {"stream": subscription_key, "data": {"test": "data"}}
        
        # 广播消息
        await self.server._broadcast_to_market_subscribers(subscription_key, test_message)
        
        # 验证结果：client1和client3应该收到消息，client2抛出异常但不应该影响其他客户端
        client1.send.assert_called_once()
        client3.send.assert_called_once()
        
        # 验证发送的是相同的消息
        message1 = json.loads(client1.send.call_args[0][0])
        message3 = json.loads(client3.send.call_args[0][0])
        assert message1 == test_message
        assert message3 == test_message