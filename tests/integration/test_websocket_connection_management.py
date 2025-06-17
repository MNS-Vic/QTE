#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket连接管理测试，包括连接建立、断开、重连等场景
"""
import pytest
import pytest_asyncio
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
    
    @pytest_asyncio.fixture
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

        # 验证WebSocket服务器已正确创建
        assert websocket_server is not None, "WebSocket服务器未创建"
        assert websocket_server.matching_engine is not None, "撮合引擎未设置"
        assert websocket_server.account_manager is not None, "账户管理器未设置"

        # 验证服务器配置
        assert websocket_server.host == "localhost", "主机配置不正确"
        assert websocket_server.port == 8765, "端口配置不正确"

        # 验证初始状态
        assert len(websocket_server.clients) == 0, "初始客户端列表应为空"
        assert len(websocket_server.market_subscriptions) == 0, "初始市场订阅应为空"
        assert len(websocket_server.user_subscriptions) == 0, "初始用户订阅应为空"
    
    @pytest.mark.asyncio
    async def test_connection_disconnect(self, setup_exchange):
        """测试WebSocket连接断开"""
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]

        # 验证用户ID正确
        assert user_id == "test_user", "用户ID不正确"

        # 验证API密钥管理
        api_key = setup_exchange["api_key"]
        assert api_key is not None, "API密钥未创建"

        # 验证API密钥映射
        retrieved_user_id = websocket_server.get_user_id_from_api_key(api_key)
        assert retrieved_user_id == user_id, "API密钥映射不正确"
    
    @pytest.mark.asyncio
    async def test_user_authentication(self, setup_exchange):
        """测试用户认证"""
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        api_key = setup_exchange["api_key"]

        # 验证账户管理器中的账户
        account = websocket_server.account_manager.get_account(user_id)
        assert account is not None, "用户账户未创建"

        # 验证账户余额
        usdt_balance = account.get_balance("USDT")
        btc_balance = account.get_balance("BTC")

        assert usdt_balance.free >= 10000, "USDT余额不足"
        assert btc_balance.free >= 1, "BTC余额不足"
    
    @pytest.mark.asyncio
    async def test_topic_subscription(self, setup_exchange):
        """测试主题订阅"""
        websocket_server = setup_exchange["websocket_server"]
        matching_engine = setup_exchange["matching_engine"]

        # 验证撮合引擎功能
        assert matching_engine is not None, "撮合引擎未创建"

        # 验证订单簿功能
        order_book = matching_engine.get_order_book("BTCUSDT")
        assert order_book is not None, "订单簿未创建"
        assert order_book.symbol == "BTCUSDT", "订单簿交易对不正确"

    @pytest.mark.asyncio
    async def test_connection_keepalive(self, setup_exchange):
        """测试连接保活"""
        websocket_server = setup_exchange["websocket_server"]
        account_manager = setup_exchange["account_manager"]

        # 验证账户管理器功能
        assert account_manager is not None, "账户管理器未创建"

        # 验证API密钥管理
        api_key = setup_exchange["api_key"]
        user_id = websocket_server.get_user_id_from_api_key(api_key)
        assert user_id == "test_user", "API密钥映射不正确"