#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket订单更新推送基本功能测试
测试订单状态变化的实时推送功能
"""
import pytest
import pytest_asyncio
import asyncio
import json
import time
import logging
from decimal import Decimal
from unittest.mock import MagicMock, patch

from qte.exchange.matching.matching_engine import (
    MatchingEngine, Order, OrderSide, OrderType, OrderStatus, Trade
)
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestWebSocketOrderUpdatesIntegration:
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
    
    @pytest_asyncio.fixture
    async def setup_mock_websocket(self, setup_exchange):
        """创建模拟WebSocket客户端环境"""
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        
        # 创建事件标志
        events = {
            "done": asyncio.Event(),
            "order_updates": {}  # 将在测试中添加特定的订单状态事件
        }
        
        # 模拟WebSocket客户端连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 使用列表存储收到的消息
        received_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            logger.debug(f"收到消息: {message[:200]}...")
            data = json.loads(message)
            received_messages.append(data)
            
            # 检查订单状态更新
            if (data.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"):
                order_data = data.get("data", {}).get("o", {})
                order_id = order_data.get("i")
                update_type = order_data.get("x")
                status = order_data.get("X")
                logger.info(f"收到订单 {order_id} 状态更新: {update_type}, 状态: {status}")
                
                # 设置特定状态事件
                status_key = f"{order_id}_{update_type}"
                if status_key in events["order_updates"]:
                    events["order_updates"][status_key].set()
                
                # 设置特定订单状态事件
                status_key = f"{order_id}_status_{status}"
                if status_key in events["order_updates"]:
                    events["order_updates"][status_key].set()
                    
                # 如果这是测试中期望的最终状态，设置done事件
                if events.get("final_status_key") == status_key:
                    events["done"].set()
            
        mock_websocket.send = mock_send
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 模拟用户订阅订单更新
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 返回模拟环境
        result = {
            "mock_websocket": mock_websocket,
            "received_messages": received_messages,
            "events": events,
            "subscription_key": order_subscription_key
        }
        yield result
        
        # 清理订阅和客户端
        logger.info("清理WebSocket资源")
        if order_subscription_key in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key].discard(mock_websocket)
        
        if websocket_server.clients.get(mock_websocket):
            del websocket_server.clients[mock_websocket]
    
    @pytest_asyncio.fixture
    async def setup_second_mock_websocket(self, setup_exchange):
        """创建第二个用户的模拟WebSocket客户端环境"""
        websocket_server = setup_exchange["websocket_server"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 创建事件标志
        events = {
            "done": asyncio.Event(),
            "order_updates": {}  # 将在测试中添加特定的订单状态事件
        }
        
        # 模拟WebSocket客户端连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12346)
        
        # 使用列表存储收到的消息
        received_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            logger.debug(f"第二用户收到消息: {message[:200]}...")
            data = json.loads(message)
            received_messages.append(data)
            
            # 检查订单状态更新
            if (data.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"):
                order_data = data.get("data", {}).get("o", {})
                order_id = order_data.get("i")
                update_type = order_data.get("x")
                status = order_data.get("X")
                logger.info(f"第二用户收到订单 {order_id} 状态更新: {update_type}, 状态: {status}")
                
                # 设置特定状态事件
                status_key = f"{order_id}_{update_type}"
                if status_key in events["order_updates"]:
                    events["order_updates"][status_key].set()
                
                # 设置特定订单状态事件
                status_key = f"{order_id}_status_{status}"
                if status_key in events["order_updates"]:
                    events["order_updates"][status_key].set()
                    
                # 如果这是测试中期望的最终状态，设置done事件
                if events.get("final_status_key") == status_key:
                    events["done"].set()
            
        mock_websocket.send = mock_send
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": second_user_id,
            "subscriptions": set()
        }
        
        # 模拟用户订阅订单更新
        order_subscription_key = f"{second_user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 返回模拟环境
        result = {
            "mock_websocket": mock_websocket,
            "received_messages": received_messages,
            "events": events,
            "subscription_key": order_subscription_key
        }
        yield result
        
        # 清理订阅和客户端
        logger.info("清理WebSocket资源")
        if order_subscription_key in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key].discard(mock_websocket)
        
        if websocket_server.clients.get(mock_websocket):
            del websocket_server.clients[mock_websocket]
    
    async def create_timeout_task(self, events, timeout_seconds=5):
        """创建超时任务"""
        async def timeout_handler():
            await asyncio.sleep(timeout_seconds)
            if not events["done"].is_set():
                logger.error(f"测试超时({timeout_seconds}秒)，强制结束测试")
                events["done"].set()
                # 记录当前已收到的消息状态
                for status_key, event in events["order_updates"].items():
                    logger.warning(f"{status_key} 状态已收到: {event.is_set()}")
        
        return asyncio.create_task(timeout_handler())
    
    @pytest.mark.asyncio
    async def test_order_lifecycle_updates(self, setup_exchange, setup_mock_websocket, setup_second_mock_websocket):
        """测试订单生命周期的WebSocket更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        buy_order_id = "test_buy_order_lifecycle"
        events["order_updates"][f"{buy_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_TRADE"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_FILLED"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_status_PARTIALLY_FILLED"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_status_FILLED"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{buy_order_id}_status_FILLED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 创建买单
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
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{buy_order_id}_NEW"].is_set(), "未收到NEW订单更新"
            assert events["order_updates"][f"{buy_order_id}_TRADE"].is_set(), "未收到TRADE订单更新"
            assert events["order_updates"][f"{buy_order_id}_FILLED"].is_set(), "未收到FILLED订单更新"
            assert events["order_updates"][f"{buy_order_id}_status_NEW"].is_set(), "未收到NEW状态更新"
            assert events["order_updates"][f"{buy_order_id}_status_FILLED"].is_set(), "未收到FILLED状态更新"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 3, "应至少收到3条消息"
            
            # 验证消息顺序和内容
            status_sequence = []
            update_type_sequence = []
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if order_data.get("i") == buy_order_id:
                        status = order_data.get("X")
                        update_type = order_data.get("x")
                        status_sequence.append(status)
                        update_type_sequence.append(update_type)
            
            # 确保状态和更新类型序列正确
            assert "NEW" in status_sequence, "状态序列中没有NEW"
            assert "FILLED" in status_sequence, "状态序列中没有FILLED"
            assert "NEW" in update_type_sequence, "更新类型序列中没有NEW"
            assert "TRADE" in update_type_sequence, "更新类型序列中没有TRADE"
            assert "FILLED" in update_type_sequence, "更新类型序列中没有FILLED"
            
            # 确保状态转换正确
            new_idx = status_sequence.index("NEW")
            filled_idx = status_sequence.index("FILLED")
            assert new_idx < filled_idx, "状态顺序不正确，NEW应该在FILLED之前"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
            
    @pytest.mark.asyncio
    async def test_partial_fill_order_updates(self, setup_exchange, setup_mock_websocket, setup_second_mock_websocket):
        """测试部分成交订单的WebSocket更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        buy_order_id = "test_buy_order_partial"
        events["order_updates"][f"{buy_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_TRADE"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{buy_order_id}_status_PARTIALLY_FILLED"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{buy_order_id}_status_PARTIALLY_FILLED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 创建买单（数量大）
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
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{buy_order_id}_NEW"].is_set(), "未收到NEW订单更新"
            assert events["order_updates"][f"{buy_order_id}_TRADE"].is_set(), "未收到TRADE订单更新"
            assert events["order_updates"][f"{buy_order_id}_status_NEW"].is_set(), "未收到NEW状态更新"
            assert events["order_updates"][f"{buy_order_id}_status_PARTIALLY_FILLED"].is_set(), "未收到PARTIALLY_FILLED状态更新"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 2, "应至少收到2条消息"
            
            # 验证部分成交消息的详细信息
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == buy_order_id and 
                        order_data.get("X") == "PARTIALLY_FILLED"):
                        # 验证成交数量
                        assert float(order_data.get("z")) == 0.1, "累计成交数量应为0.1"
                        # 验证剩余数量 (l = z - q)
                        assert float(order_data.get("q")) == 0.2, "订单总数量应为0.2"
                        assert float(order_data.get("l")) == 0.1, "剩余数量应为0.1"
                        break
            else:
                assert False, "未找到PARTIALLY_FILLED状态的消息"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_cancel_order_updates(self, setup_exchange, setup_mock_websocket):
        """测试取消订单的WebSocket更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        order_id = "test_cancel_order"
        events["order_updates"][f"{order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{order_id}_CANCELED"] = asyncio.Event()
        events["order_updates"][f"{order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{order_id}_status_CANCELED"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{order_id}_status_CANCELED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 创建限价单
            order = Order(
                order_id=order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=40000.0,  # 低于市场价，不会立即成交
                user_id=user_id,
                client_order_id="client_cancel_order"
            )
            
            # 放置订单
            matching_engine.place_order(order)
            
            # 等待NEW状态更新
            await events["order_updates"][f"{order_id}_status_NEW"].wait()
            
            # 取消订单
            matching_engine.cancel_order(order_id, "BTCUSDT")
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{order_id}_NEW"].is_set(), "未收到NEW订单更新"
            assert events["order_updates"][f"{order_id}_CANCELED"].is_set(), "未收到CANCELED订单更新"
            assert events["order_updates"][f"{order_id}_status_NEW"].is_set(), "未收到NEW状态更新"
            assert events["order_updates"][f"{order_id}_status_CANCELED"].is_set(), "未收到CANCELED状态更新"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 2, "应至少收到2条消息"
            
            # 验证取消消息的详细信息
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == order_id and 
                        order_data.get("X") == "CANCELED"):
                        # 验证取消时间存在
                        assert "T" in order_data, "缺少执行时间字段"
                        break
            else:
                assert False, "未找到CANCELED状态的消息"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_market_order_updates(self, setup_exchange, setup_mock_websocket, setup_second_mock_websocket):
        """测试市价单的WebSocket更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        market_order_id = "test_market_order"
        events["order_updates"][f"{market_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{market_order_id}_TRADE"] = asyncio.Event()
        events["order_updates"][f"{market_order_id}_FILLED"] = asyncio.Event()
        events["order_updates"][f"{market_order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{market_order_id}_status_FILLED"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{market_order_id}_status_FILLED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 首先创建一个限价卖单作为对手方
            limit_sell_id = "test_limit_sell_for_market"
            limit_sell = Order(
                order_id=limit_sell_id,
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=second_user_id,
                client_order_id="client_limit_sell_for_market"
            )
            
            # 放置限价卖单
            matching_engine.place_order(limit_sell)
            
            # 短暂等待确保卖单进入订单簿
            await asyncio.sleep(0.1)
            
            # 创建市价买单
            market_order = Order(
                order_id=market_order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.1,
                user_id=user_id,
                client_order_id="client_market_order"
            )
            
            # 放置市价单
            matching_engine.place_order(market_order)
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{market_order_id}_NEW"].is_set(), "未收到NEW订单更新"
            assert events["order_updates"][f"{market_order_id}_TRADE"].is_set(), "未收到TRADE订单更新"
            assert events["order_updates"][f"{market_order_id}_FILLED"].is_set(), "未收到FILLED订单更新"
            assert events["order_updates"][f"{market_order_id}_status_NEW"].is_set(), "未收到NEW状态更新"
            assert events["order_updates"][f"{market_order_id}_status_FILLED"].is_set(), "未收到FILLED状态更新"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 3, "应至少收到3条消息"
            
            # 验证市价单消息的特殊字段
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == market_order_id and 
                        order_data.get("X") == "FILLED"):
                        # 验证市价单特有字段
                        assert order_data.get("o") == "MARKET", "订单类型应为MARKET"
                        assert order_data.get("p") == "0", "市价单价格应为0"
                        break
            else:
                assert False, "未找到市价单FILLED状态的消息"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass 