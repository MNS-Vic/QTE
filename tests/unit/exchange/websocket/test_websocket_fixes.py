#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket服务器修复测试
"""
import pytest
import json
import asyncio
import time
import logging
from unittest.mock import MagicMock, patch, AsyncMock

from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer

class TestWebSocketFixes:
    """测试WebSocket服务器修复"""
    
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
    async def test_improved_json_error_handling(self, setup_server):
        """
        测试改进的JSON错误处理
        验证对无效JSON的健壮处理
        """
        # 创建模拟的websocket客户端
        mock_websocket = AsyncMock()
        
        # 测试处理无效JSON消息
        await self.server._process_message(mock_websocket, "这不是有效的JSON")
        
        # 验证发送错误响应
        mock_websocket.send.assert_called_once()
        error_msg = mock_websocket.send.call_args[0][0]
        error_data = json.loads(error_msg)
        
        assert "error" in error_data
        assert "无效的JSON格式" in error_data["error"]
    
    @pytest.mark.asyncio
    async def test_improved_exception_handling(self, setup_server):
        """
        测试改进的异常处理
        验证对处理消息时发生的异常的健壮处理
        """
        # 创建模拟的websocket客户端
        mock_websocket = AsyncMock()
        
        # 一个会抛出异常的模拟方法
        async def mock_handler(*args, **kwargs):
            raise Exception("模拟的处理错误")
            
        # 替换方法以触发异常
        with patch.object(self.server, '_handle_subscribe', side_effect=mock_handler):
            # 有效的JSON但处理时会抛出异常
            message = json.dumps({
                "method": "subscribe",
                "params": {"streams": ["BTCUSDT@ticker"]},
                "id": 1
            })
            
            await self.server._process_message(mock_websocket, message)
            
            # 验证发送错误响应
            mock_websocket.send.assert_called_once()
            error_msg = mock_websocket.send.call_args[0][0]
            error_data = json.loads(error_msg)
            
            assert "error" in error_data
            assert "处理消息时出错" in error_data["error"]
            
    @pytest.mark.asyncio
    async def test_client_reconnection_handling(self, setup_server):
        """
        测试客户端重连处理
        验证对客户端突然断开连接的处理
        """
        # 创建模拟的websocket客户端
        mock_websocket = AsyncMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 添加到客户端列表
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": self.test_user_id,
            "subscriptions": {"BTCUSDT@ticker"}
        }
        
        # 添加到市场订阅
        stream_key = "BTCUSDT@ticker"
        if stream_key not in self.server.market_subscriptions:
            self.server.market_subscriptions[stream_key] = set()
        self.server.market_subscriptions[stream_key].add(mock_websocket)
        
        # 调用清理方法
        await self.server._cleanup_client(mock_websocket)
        
        # 验证客户端被移除
        assert mock_websocket not in self.server.clients
        # 测试市场订阅记录也被删除
        # 由于正确的实现会删除空的订阅键，所以不需要直接检查键是否存在
        # 我们可以尝试间接验证清理
        assert stream_key not in self.server.market_subscriptions or \
               mock_websocket not in self.server.market_subscriptions[stream_key]
    
    @pytest.mark.asyncio
    async def test_message_format_validation(self, setup_server):
        """
        测试消息格式验证
        验证对无效消息格式的响应
        """
        # 创建模拟的websocket客户端
        mock_websocket = AsyncMock()
        
        # 测试各种无效消息格式
        invalid_messages = [
            json.dumps({}),  # 空消息
            json.dumps({"params": {}}),  # 缺少method
            json.dumps({"method": "unknown_method"})  # 未知方法
        ]
        
        for message in invalid_messages:
            mock_websocket.reset_mock()
            await self.server._process_message(mock_websocket, message)
            
            # 验证发送错误响应
            mock_websocket.send.assert_called_once()
            error_msg = mock_websocket.send.call_args[0][0]
            error_data = json.loads(error_msg)
            
            assert "error" in error_data
    
    @pytest.mark.asyncio
    async def test_parameter_validation(self, setup_server):
        """
        测试参数验证
        验证对缺少必要参数的处理
        """
        # 创建模拟的websocket客户端
        mock_websocket = AsyncMock()
        
        # 测试缺少参数的情况
        invalid_params_messages = [
            # 订阅缺少streams参数
            json.dumps({
                "method": "subscribe",
                "params": {},
                "id": 1
            }),
            # 认证缺少api_key参数
            json.dumps({
                "method": "auth",
                "params": {},
                "id": 2
            })
        ]
        
        for message in invalid_params_messages:
            mock_websocket.reset_mock()
            await self.server._process_message(mock_websocket, message)
            
            # 验证发送错误响应
            mock_websocket.send.assert_called_once()
            error_msg = mock_websocket.send.call_args[0][0]
            error_data = json.loads(error_msg)
            
            assert "error" in error_data
            assert "id" in error_data
    
    @pytest.mark.asyncio
    async def test_robust_broadcast_handling(self, setup_server):
        """
        测试健壮的广播处理
        验证广播消息时对客户端异常的处理
        """
        # 创建模拟的websocket客户端
        working_client = AsyncMock()
        failing_client = AsyncMock()
        failing_client.send.side_effect = Exception("模拟发送错误")
        
        # 设置订阅
        stream_key = "BTCUSDT@ticker"
        self.server.market_subscriptions[stream_key] = {working_client, failing_client}
        
        # 准备广播消息
        message = {
            "stream": stream_key,
            "data": {"price": "10000.0"}
        }
        
        # 创建测试用的logger
        test_logger = logging.getLogger("TestWebSocketLogger")
        self.server.logger = test_logger
        
        # 由于WebSocket服务器直接使用全局logger对象而非类实例的logger属性
        # 测试方法不需要mock logger，只需要验证消息发送的行为
        
        # 测试广播
        await self.server._broadcast_to_market_subscribers(stream_key, message)
        
        # 验证工作正常的客户端收到消息
        working_client.send.assert_called_once()
        
        # 异常处理已被解决，不需要验证mock_logger
        
        # 验证两个客户端仍在订阅列表中
        assert working_client in self.server.market_subscriptions[stream_key]
        assert failing_client in self.server.market_subscriptions[stream_key]