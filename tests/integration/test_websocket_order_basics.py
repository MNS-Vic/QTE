#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket订单更新基本功能测试
使用WebSocketOrderListener实现更可靠的订单状态监听
"""
import pytest
import pytest_asyncio
import asyncio
import logging
from decimal import Decimal

from qte.exchange.matching.matching_engine import (
    MatchingEngine, Order, OrderSide, OrderType, OrderStatus
)
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer
from tests.integration.websocket_order_listener import WebSocketOrderListener

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestWebSocketOrderBasics:
    """WebSocket订单更新推送基本功能测试"""
    
    @pytest.fixture
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
        
        # 创建第二个用户账户（用于对手方订单）
        second_user_id = "second_user"
        account_manager.create_account(second_user_id)
        second_account = account_manager.get_account(second_user_id)
        second_account.deposit("USDT", Decimal("10000"))
        second_account.deposit("BTC", Decimal("1"))
        
        # 创建WebSocket服务器
        websocket_server = ExchangeWebSocketServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=8765
        )
        
        # 创建API密钥
        api_key = websocket_server.create_api_key(user_id)
        websocket_server.create_api_key(second_user_id)
        
        # 返回测试环境
        result = {
            "matching_engine": matching_engine,
            "account_manager": account_manager,
            "websocket_server": websocket_server,
            "user_id": user_id,
            "second_user_id": second_user_id,
            "api_key": api_key
        }
        yield result
        
        # 测试完成后清理资源
        logger.info("清理测试资源...")
        await asyncio.sleep(0.2)
    
    @pytest.mark.asyncio
    async def test_order_lifecycle_updates(self, setup_exchange):
        """测试订单生命周期的WebSocket更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 创建订单监听器
        order_listener = WebSocketOrderListener(websocket_server, user_id)
        
        try:
            # 创建买单
            buy_order_id = "test_buy_order_lifecycle"
            buy_order = Order(
                order_id=buy_order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,
                client_order_id="client_buy_order_lifecycle"
            )
            
            # 设置订单状态监听
            order_listener.watch_order_status(
                order_id=buy_order_id,
                update_types=["NEW", "TRADE", "FILLED"],
                statuses=["NEW", "PARTIALLY_FILLED", "FILLED"],
                final_status="FILLED"
            )
            
            # 创建卖单（对手方）
            sell_order_id = "test_sell_order_lifecycle"
            sell_order = Order(
                order_id=sell_order_id,
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=second_user_id,
                client_order_id="client_sell_order_lifecycle"
            )
            
            # 放置买单和卖单
            matching_engine.place_order(buy_order)
            matching_engine.place_order(sell_order)
            
            # 等待完成或超时
            await order_listener.wait_for_completion(timeout=5.0)
            
            # 验证是否收到所有订单状态更新
            assert await order_listener.wait_for_update_type(buy_order_id, "NEW", 0.1), "未收到NEW订单更新"
            assert await order_listener.wait_for_update_type(buy_order_id, "TRADE", 0.1), "未收到TRADE订单更新"
            assert await order_listener.wait_for_update_type(buy_order_id, "FILLED", 0.1), "未收到FILLED订单更新"
            assert await order_listener.wait_for_status(buy_order_id, "NEW", 0.1), "未收到NEW状态"
            assert await order_listener.wait_for_status(buy_order_id, "FILLED", 0.1), "未收到FILLED状态"
            
        finally:
            # 清理资源
            order_listener.cleanup()
    
    @pytest.mark.asyncio
    async def test_partial_fill_order_updates(self, setup_exchange):
        """测试部分成交订单的WebSocket更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 创建订单监听器
        order_listener = WebSocketOrderListener(websocket_server, user_id)
        
        try:
            # 创建买单（数量大）
            buy_order_id = "test_buy_order_partial"
            buy_order = Order(
                order_id=buy_order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.2,  # 大于卖单数量
                price=50000.0,
                user_id=user_id,
                client_order_id="client_buy_order_partial"
            )
            
            # 设置订单状态监听
            order_listener.watch_order_status(
                order_id=buy_order_id,
                update_types=["NEW", "TRADE"],
                statuses=["NEW", "PARTIALLY_FILLED"],
                final_status="PARTIALLY_FILLED"
            )
            
            # 创建卖单（数量小，导致部分成交）
            sell_order_id = "test_sell_order_partial"
            sell_order = Order(
                order_id=sell_order_id,
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.1,  # 小于买单数量
                price=50000.0,
                user_id=second_user_id,
                client_order_id="client_sell_order_partial"
            )
            
            # 放置买单和卖单
            matching_engine.place_order(buy_order)
            matching_engine.place_order(sell_order)
            
            # 等待完成或超时
            await order_listener.wait_for_completion(timeout=5.0)
            
            # 验证是否收到所有订单状态更新
            assert await order_listener.wait_for_update_type(buy_order_id, "NEW", 0.1), "未收到NEW订单更新"
            assert await order_listener.wait_for_update_type(buy_order_id, "TRADE", 0.1), "未收到TRADE订单更新"
            assert await order_listener.wait_for_status(buy_order_id, "NEW", 0.1), "未收到NEW状态"
            assert await order_listener.wait_for_status(buy_order_id, "PARTIALLY_FILLED", 0.1), "未收到PARTIALLY_FILLED状态"
            
            # 检查最后一条部分成交消息
            partially_filled_message = None
            for message in reversed(order_listener.received_messages):
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == buy_order_id and 
                        order_data.get("X") == "PARTIALLY_FILLED"):
                        partially_filled_message = message
                        break
            
            assert partially_filled_message is not None, "未找到部分成交消息"
            order_data = partially_filled_message["data"]["o"]
            
            # 验证成交数量
            assert float(order_data.get("z")) == 0.1, "累计成交数量应为0.1"
            # 验证订单总数量
            assert float(order_data.get("q")) == 0.2, "订单总数量应为0.2"
            
        finally:
            # 清理资源
            order_listener.cleanup()
    
    @pytest.mark.asyncio
    async def test_cancel_order_updates(self, setup_exchange):
        """测试取消订单的WebSocket更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        
        # 创建订单监听器
        order_listener = WebSocketOrderListener(websocket_server, user_id)
        
        try:
            # 创建限价单（低于市场价，不会立即成交）
            order_id = "test_cancel_order"
            order = Order(
                order_id=order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=40000.0,
                user_id=user_id,
                client_order_id="client_cancel_order"
            )
            
            # 设置订单状态监听
            order_listener.watch_order_status(
                order_id=order_id,
                update_types=["NEW", "CANCELED"],
                statuses=["NEW", "CANCELED"],
                final_status="CANCELED"
            )
            
            # 放置订单
            matching_engine.place_order(order)
            
            # 等待NEW状态
            assert await order_listener.wait_for_status(order_id, "NEW", 1.0), "未收到NEW状态"
            
            # 取消订单
            matching_engine.cancel_order(order_id, "BTCUSDT")
            
            # 等待完成或超时
            await order_listener.wait_for_completion(timeout=5.0)
            
            # 验证是否收到所有订单状态更新
            assert await order_listener.wait_for_update_type(order_id, "NEW", 0.1), "未收到NEW订单更新"
            assert await order_listener.wait_for_update_type(order_id, "CANCELED", 0.1), "未收到CANCELED订单更新"
            assert await order_listener.wait_for_status(order_id, "NEW", 0.1), "未收到NEW状态"
            assert await order_listener.wait_for_status(order_id, "CANCELED", 0.1), "未收到CANCELED状态"
            
        finally:
            # 清理资源
            order_listener.cleanup() 