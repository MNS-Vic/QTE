#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket连接管理测试，包括连接建立、断开、重连等场景
"""
import pytest
import asyncio
import json
import time
import logging
from decimal import Decimal
from unittest.mock import MagicMock, patch

from qte.exchange.matching.matching_engine import MatchingEngine
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestWebSocketConnectionManagement:
    """WebSocket连接管理测试"""
    
    @pytest.fixture(scope="function")
    def event_loop(self):
        """创建一个新的事件循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        # 确保所有待处理任务都被正确取消
        pending = asyncio.all_tasks(loop)
        if pending:
            logger.info(f"取消 {len(pending)} 个未完成的任务")
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            logger.info("所有任务已取消")
        loop.close()
    
    @pytest.fixture
    async def setup_exchange(self):
        """创建交易所环境"""
        # 创建撮合引擎
        matching_engine = MatchingEngine()
        
        # 创建账户管理器
        account_manager = AccountManager()
        
        # 创建用户账户
        user_id = "test_user"
        account_manager.create_account(user_id)
        account = account_manager.get_account(user_id)
        account.deposit("USDT", Decimal("10000"))
        account.deposit("BTC", Decimal("1"))
        
        # 创建WebSocket服务器
        websocket_server = ExchangeWebSocketServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=8765
        )
        
        # 创建API密钥
        api_key = websocket_server.create_api_key(user_id)
        
        # 返回测试环境
        yield {
            "matching_engine": matching_engine,
            "account_manager": account_manager,
            "websocket_server": websocket_server,
            "user_id": user_id,
            "api_key": api_key
        }
        
        # 测试完成后清理资源
        logger.info("清理测试资源...")
        await asyncio.sleep(0.2)
    
    @pytest.mark.asyncio
    async def test_connection_establishment(self, setup_exchange):
        """测试WebSocket连接建立"""
        websocket_server = setup_exchange["websocket_server"]
        
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 存储发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
            
        mock_websocket.send = mock_send
        
        # 调用连接建立处理方法
        await websocket_server.ws_connect(mock_websocket)
        
        # 验证连接被添加到客户端列表
        assert mock_websocket in websocket_server.clients, "WebSocket连接未被添加到客户端列表"
        
        # 验证连接信息
        client_info = websocket_server.clients[mock_websocket]
        assert "connected_at" in client_info, "连接时间未记录"
        assert "subscriptions" in client_info, "订阅列表未初始化"
        assert isinstance(client_info["subscriptions"], set), "订阅列表不是集合类型"
        
        # 验证是否发送了欢迎消息
        welcome_msg = next((msg for msg in sent_messages if msg.get("type") == "welcome"), None)
        assert welcome_msg is not None, "未发送欢迎消息"
        
        # 清理连接
        await websocket_server.ws_disconnect(mock_websocket)
    
    @pytest.mark.asyncio
    async def test_connection_disconnect(self, setup_exchange):
        """测试WebSocket连接断开"""
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set(["kline", "trade"])
        }
        
        # 添加模拟订阅
        topics = ["kline", "trade"]
        for topic in topics:
            subscription_key = f"{user_id}@{topic}"
            if subscription_key not in websocket_server.user_subscriptions:
                websocket_server.user_subscriptions[subscription_key] = set()
            websocket_server.user_subscriptions[subscription_key].add(mock_websocket)
        
        # 调用连接断开处理方法
        await websocket_server.ws_disconnect(mock_websocket)
        
        # 验证客户端已从列表中移除
        assert mock_websocket not in websocket_server.clients, "WebSocket连接未从客户端列表中移除"
        
        # 验证所有订阅均已移除
        for topic in topics:
            subscription_key = f"{user_id}@{topic}"
            if subscription_key in websocket_server.user_subscriptions:
                assert mock_websocket not in websocket_server.user_subscriptions[subscription_key], \
                    f"WebSocket连接仍在 {subscription_key} 订阅中"
    
    @pytest.mark.asyncio
    async def test_user_authentication(self, setup_exchange):
        """测试用户认证"""
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        api_key = setup_exchange["api_key"]
        
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "subscriptions": set()
        }
        
        # 存储发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
            
        mock_websocket.send = mock_send
        
        # 构建认证消息
        auth_message = json.dumps({
            "method": "auth",
            "params": {
                "api_key": api_key
            },
            "id": 123
        })
        
        # 调用消息处理方法
        await websocket_server.ws_message(mock_websocket, auth_message)
        
        # 验证认证响应
        auth_response = next((msg for msg in sent_messages if msg.get("id") == 123), None)
        assert auth_response is not None, "未收到认证响应"
        assert auth_response.get("success") is True, "认证未成功"
        
        # 验证用户ID已设置
        assert websocket_server.clients[mock_websocket].get("user_id") == user_id, "用户ID未正确设置"
        
        # 尝试无效认证
        invalid_auth_message = json.dumps({
            "method": "auth",
            "params": {
                "api_key": "invalid_key"
            },
            "id": 124
        })
        
        # 重置sent_messages
        sent_messages.clear()
        
        # 调用消息处理方法
        await websocket_server.ws_message(mock_websocket, invalid_auth_message)
        
        # 验证认证失败响应
        auth_response = next((msg for msg in sent_messages if msg.get("id") == 124), None)
        assert auth_response is not None, "未收到认证响应"
        assert auth_response.get("success") is False, "无效认证未被拒绝"
        
        # 清理连接
        await websocket_server.ws_disconnect(mock_websocket)
    
    @pytest.mark.asyncio
    async def test_topic_subscription(self, setup_exchange):
        """测试主题订阅"""
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 存储发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
            
        mock_websocket.send = mock_send
        
        # 构建订阅消息
        subscribe_message = json.dumps({
            "method": "subscribe",
            "params": ["order", "kline_1m_BTCUSDT"],
            "id": 125
        })
        
        # 调用消息处理方法
        await websocket_server.ws_message(mock_websocket, subscribe_message)
        
        # 验证订阅响应
        sub_response = next((msg for msg in sent_messages if msg.get("id") == 125), None)
        assert sub_response is not None, "未收到订阅响应"
        assert sub_response.get("success") is True, "订阅未成功"
        
        # 验证客户端订阅已更新
        client_subscriptions = websocket_server.clients[mock_websocket]["subscriptions"]
        assert "order" in client_subscriptions, "订单订阅未添加到客户端"
        assert "kline_1m_BTCUSDT" in client_subscriptions, "K线订阅未添加到客户端"
        
        # 验证用户订阅已更新
        order_subscription_key = f"{user_id}@order"
        kline_subscription_key = f"{user_id}@kline_1m_BTCUSDT"
        
        assert mock_websocket in websocket_server.user_subscriptions.get(order_subscription_key, set()), \
            "WebSocket未在订单订阅列表中"
        assert mock_websocket in websocket_server.user_subscriptions.get(kline_subscription_key, set()), \
            "WebSocket未在K线订阅列表中"
        
        # 构建取消订阅消息
        unsubscribe_message = json.dumps({
            "method": "unsubscribe",
            "params": ["order"],
            "id": 126
        })
        
        # 调用消息处理方法
        await websocket_server.ws_message(mock_websocket, unsubscribe_message)
        
        # 验证取消订阅响应
        unsub_response = next((msg for msg in sent_messages if msg.get("id") == 126), None)
        assert unsub_response is not None, "未收到取消订阅响应"
        assert unsub_response.get("success") is True, "取消订阅未成功"
        
        # 验证客户端订阅已更新
        client_subscriptions = websocket_server.clients[mock_websocket]["subscriptions"]
        assert "order" not in client_subscriptions, "订单订阅未从客户端移除"
        assert "kline_1m_BTCUSDT" in client_subscriptions, "K线订阅被错误移除"
        
        # 验证用户订阅已更新
        assert mock_websocket not in websocket_server.user_subscriptions.get(order_subscription_key, set()), \
            "WebSocket仍在订单订阅列表中"
        assert mock_websocket in websocket_server.user_subscriptions.get(kline_subscription_key, set()), \
            "WebSocket被错误从K线订阅列表中移除"
        
        # 清理连接
        await websocket_server.ws_disconnect(mock_websocket)
    
    @pytest.mark.asyncio
    async def test_connection_keepalive(self, setup_exchange):
        """测试连接保活"""
        websocket_server = setup_exchange["websocket_server"]
        
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "subscriptions": set()
        }
        
        # 存储发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
            
        mock_websocket.send = mock_send
        
        # 构建ping消息
        ping_message = json.dumps({
            "method": "ping",
            "id": 127
        })
        
        # 调用消息处理方法
        await websocket_server.ws_message(mock_websocket, ping_message)
        
        # 验证pong响应
        pong_response = next((msg for msg in sent_messages if msg.get("id") == 127), None)
        assert pong_response is not None, "未收到pong响应"
        assert pong_response.get("method") == "pong", "响应方法不正确"
        
        # 验证时间戳存在
        assert "ts" in pong_response, "pong响应中未包含时间戳"
        
        # 清理连接
        await websocket_server.ws_disconnect(mock_websocket)
    
    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, setup_exchange):
        """测试无效消息处理"""
        websocket_server = setup_exchange["websocket_server"]
        
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "subscriptions": set()
        }
        
        # 存储发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
            
        mock_websocket.send = mock_send
        
        # 测试各种无效消息
        invalid_messages = [
            # 无效JSON
            "invalid json",
            
            # 缺少方法
            json.dumps({"id": 128}),
            
            # 未知方法
            json.dumps({"method": "unknown", "id": 129}),
            
            # 缺少订阅参数
            json.dumps({"method": "subscribe", "id": 130}),
            
            # 空订阅参数
            json.dumps({"method": "subscribe", "params": [], "id": 131})
        ]
        
        for i, message in enumerate(invalid_messages):
            # 调用消息处理方法
            await websocket_server.ws_message(mock_websocket, message)
            
            # 验证错误响应
            error_response = next((msg for msg in sent_messages 
                                  if msg.get("id") in [128, 129, 130, 131] and msg.get("success") is False), None)
            
            assert error_response is not None, f"未收到第{i+1}个无效消息的错误响应"
            assert "error" in error_response, f"第{i+1}个无效消息的错误响应中未包含错误信息"
            
            # 清空sent_messages以便下一次验证
            sent_messages.clear()
        
        # 清理连接
        await websocket_server.ws_disconnect(mock_websocket)
    
    @pytest.mark.asyncio
    async def test_multiple_connections_per_user(self, setup_exchange):
        """测试每个用户的多个连接"""
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        api_key = setup_exchange["api_key"]
        
        # 为同一用户创建3个模拟WebSocket连接
        mock_websockets = []
        auth_successful = []
        
        for i in range(3):
            # 模拟WebSocket连接
            mock_websocket = MagicMock()
            mock_websocket.remote_address = (f"127.0.0.1", 12350 + i)
            mock_websockets.append(mock_websocket)
            
            # 初始化客户端信息
            websocket_server.clients[mock_websocket] = {
                "connected_at": time.time(),
                "subscriptions": set()
            }
            
            # 创建一个Response对象来存储认证结果
            response = {"success": False}
            
            # 模拟send方法
            async def create_mock_send(ws_index, resp_obj):
                async def mock_send(message):
                    data = json.loads(message)
                    if data.get("id") == 100 + ws_index:
                        resp_obj["success"] = data.get("success", False)
                return mock_send
            
            mock_websocket.send = await create_mock_send(i, response)
            auth_successful.append(response)
            
            # 构建认证消息
            auth_message = json.dumps({
                "method": "auth",
                "params": {
                    "api_key": api_key
                },
                "id": 100 + i
            })
            
            # 调用消息处理方法
            await websocket_server.ws_message(mock_websocket, auth_message)
        
        # 验证所有连接都认证成功
        for i, success in enumerate(auth_successful):
            assert success["success"] is True, f"连接 {i} 认证失败"
        
        # 验证所有连接都使用相同的用户ID
        for mock_websocket in mock_websockets:
            assert websocket_server.clients[mock_websocket].get("user_id") == user_id, \
                "连接的用户ID不匹配"
        
        # 验证订阅功能 - 让第一个连接订阅订单更新
        mock_websocket = mock_websockets[0]
        
        # 存储发送的消息
        sent_messages = []
        
        # 更新send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
            
        mock_websocket.send = mock_send
        
        # 构建订阅消息
        subscribe_message = json.dumps({
            "method": "subscribe",
            "params": ["order"],
            "id": 200
        })
        
        # 调用消息处理方法
        await websocket_server.ws_message(mock_websocket, subscribe_message)
        
        # 验证订阅响应
        sub_response = next((msg for msg in sent_messages if msg.get("id") == 200), None)
        assert sub_response is not None, "未收到订阅响应"
        assert sub_response.get("success") is True, "订阅未成功"
        
        # 验证订阅已添加
        order_subscription_key = f"{user_id}@order"
        assert mock_websocket in websocket_server.user_subscriptions.get(order_subscription_key, set()), \
            "WebSocket未在订阅列表中"
        
        # 清理连接
        for mock_websocket in mock_websockets:
            await websocket_server.ws_disconnect(mock_websocket)
        
        # 验证订阅已清除
        assert order_subscription_key not in websocket_server.user_subscriptions or \
               len(websocket_server.user_subscriptions[order_subscription_key]) == 0, \
               "断开连接后订阅未清除" 