#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket服务器修复的单元测试
"""
import pytest
import asyncio
import json
import time
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
    async def test_ws001_client_state_sync(self, setup_server):
        """测试WS-001：客户端状态同步问题
        
        验证客户端断开连接后，相关状态是否正确清理
        """
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.send = AsyncMock()
        
        # 初始化客户端状态
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": self.test_user_id,
            "subscriptions": set(["BTCUSDT@trade", "account@balance"])
        }
        
        # 添加到市场订阅
        self.server.market_subscriptions["BTCUSDT@trade"] = set([mock_websocket])
        
        # 添加到用户订阅
        self.server.user_subscriptions[f"{self.test_user_id}@balance"] = set([mock_websocket])
        
        # 调用清理方法
        await self.server._cleanup_client(mock_websocket)
        
        # 验证结果 - 客户端应该被移除
        assert mock_websocket not in self.server.clients
        
        # 验证订阅也应该被移除
        assert mock_websocket not in self.server.market_subscriptions.get("BTCUSDT@trade", set())
        assert mock_websocket not in self.server.user_subscriptions.get(f"{self.test_user_id}@balance", set())
    
    @pytest.mark.asyncio
    async def test_ws002_error_handling(self, setup_server):
        """测试WS-002：错误处理逻辑问题
        
        验证在处理消息时出现异常是否正确处理
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
        
        # 模拟一个无效的JSON消息
        invalid_message = "{invalid json"
        
        # 调用消息处理方法
        await self.server._process_message(mock_websocket, invalid_message)
        
        # 验证错误响应
        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert "error" in response
    
    @pytest.mark.asyncio
    async def test_sync_after_auth(self, setup_server):
        """测试认证后状态同步
        
        验证用户认证后是否正确更新了状态
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
        
        # 构造认证参数
        params = {"api_key": self.test_api_key}
        request_id = "test_auth_sync"
        
        # 调用认证方法
        await self.server._handle_auth(mock_websocket, params, request_id)
        
        # 验证结果 - 用户ID应该被更新
        assert self.server.clients[mock_websocket]["user_id"] == self.test_user_id
        
        # 验证响应
        mock_websocket.send.assert_called_once()
        response_json = json.loads(mock_websocket.send.call_args[0][0])
        assert response_json["id"] == request_id
        assert response_json["result"] == "success"