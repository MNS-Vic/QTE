#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket订单更新推送的高级场景测试
测试不同价格匹配模式和自成交预防功能
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

class TestWebSocketOrderScenariosIntegration:
    """WebSocket订单更新推送的高级场景测试"""
    
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
    async def test_price_match_mode_opponent(self, setup_exchange, setup_mock_websocket):
        """测试OPPONENT价格匹配模式的订单更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        order_id = "opponent_buy"
        events["order_updates"][f"{order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{order_id}_TRADE"] = asyncio.Event()
        events["order_updates"][f"{order_id}_FILLED"] = asyncio.Event()
        events["order_updates"][f"{order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{order_id}_status_FILLED"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{order_id}_status_FILLED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 首先创建卖单以提供深度
            for i in range(5):
                sell_price = 50000.0 + i * 100  # 不同价格的卖单
                sell_order = Order(
                    order_id=f"sell_order_{i}",
                    symbol="BTCUSDT",
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    quantity=0.1,
                    price=sell_price,
                    user_id=second_user_id
                )
                matching_engine.place_order(sell_order)
            
            # 短暂等待确保卖单进入订单簿
            await asyncio.sleep(0.1)
            
            # 创建使用OPPONENT价格匹配模式的买单
            buy_order = Order(
                order_id=order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50100.0,  # 高于最低卖单价格
                user_id=user_id,
                client_order_id="client_opponent_buy",
                price_match="OPPONENT"  # 使用对手方价格
            )
            
            # 放置买单
            matching_engine.place_order(buy_order)
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{order_id}_NEW"].is_set(), "未收到NEW订单更新"
            assert events["order_updates"][f"{order_id}_TRADE"].is_set(), "未收到TRADE订单更新"
            assert events["order_updates"][f"{order_id}_FILLED"].is_set(), "未收到FILLED订单更新"
            assert events["order_updates"][f"{order_id}_status_FILLED"].is_set(), "未收到FILLED状态更新"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 3, "应至少收到3条消息"
            
            # 验证使用了对手方价格
            found_correct_price = False
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == order_id and 
                        order_data.get("x") == "TRADE"):
                        # 验证成交价格是对手方价格（最低卖单价格）
                        if float(order_data.get("L")) == 50000.0:
                            found_correct_price = True
                            # 验证价格匹配模式字段
                            assert order_data.get("pm") == "OPPONENT", "价格匹配模式字段不正确"
                            break
            
            assert found_correct_price, "未找到使用对手方价格的成交记录"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_price_match_mode_queue(self, setup_exchange, setup_mock_websocket):
        """测试QUEUE价格匹配模式的订单更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        second_user_id = setup_exchange["second_user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        order_id = "queue_buy"
        events["order_updates"][f"{order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{order_id}_TRADE"] = asyncio.Event()
        events["order_updates"][f"{order_id}_FILLED"] = asyncio.Event()
        events["order_updates"][f"{order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{order_id}_status_FILLED"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{order_id}_status_FILLED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 首先创建一些买单以提供深度
            for i in range(5):
                buy_price = 49000.0 + i * 100  # 不同价格的买单
                buy_order = Order(
                    order_id=f"buy_order_{i}",
                    symbol="BTCUSDT",
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    quantity=0.1,
                    price=buy_price,
                    user_id=second_user_id
                )
                matching_engine.place_order(buy_order)
            
            # 短暂等待确保买单进入订单簿
            await asyncio.sleep(0.1)
            
            # 创建卖单以提供流动性
            sell_order = Order(
                order_id="sell_for_queue",
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=48500.0,  # 低于所有买单
                user_id=second_user_id
            )
            
            # 创建使用QUEUE价格匹配模式的买单
            buy_order = Order(
                order_id=order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,  # 高于最高买单价格
                user_id=user_id,
                client_order_id="client_queue_buy",
                price_match="QUEUE"  # 使用队列价格
            )
            
            # 放置卖单和买单
            matching_engine.place_order(sell_order)
            matching_engine.place_order(buy_order)
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{order_id}_NEW"].is_set(), "未收到NEW订单更新"
            assert events["order_updates"][f"{order_id}_TRADE"].is_set(), "未收到TRADE订单更新"
            assert events["order_updates"][f"{order_id}_FILLED"].is_set(), "未收到FILLED订单更新"
            assert events["order_updates"][f"{order_id}_status_FILLED"].is_set(), "未收到FILLED状态更新"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 3, "应至少收到3条消息"
            
            # 验证使用了队列价格（买方订单簿中最高价格）
            found_correct_price = False
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == order_id and 
                        order_data.get("x") == "TRADE"):
                        # 验证成交价格是队列价格（最高买单价格）
                        trade_price = float(order_data.get("L"))
                        if abs(trade_price - 49400.0) < 0.01:  # 允许小误差
                            found_correct_price = True
                            # 验证价格匹配模式字段
                            assert order_data.get("pm") == "QUEUE", "价格匹配模式字段不正确"
                            break
            
            assert found_correct_price, "未找到使用队列价格的成交记录"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_self_trade_prevention_expire_taker(self, setup_exchange, setup_mock_websocket):
        """测试自成交预防EXPIRE_TAKER模式的订单更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        maker_order_id = "self_trade_maker"
        taker_order_id = "self_trade_taker"
        events["order_updates"][f"{maker_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{maker_order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_EXPIRED"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_status_EXPIRED"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{taker_order_id}_status_EXPIRED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 创建maker订单（先下的订单）
            maker_order = Order(
                order_id=maker_order_id,
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,
                client_order_id="client_self_trade_maker"
            )
            
            # 放置maker订单
            matching_engine.place_order(maker_order)
            
            # 等待maker订单NEW状态
            await events["order_updates"][f"{maker_order_id}_status_NEW"].wait()
            
            # 创建taker订单（后下的订单），使用自成交预防模式EXPIRE_TAKER
            taker_order = Order(
                order_id=taker_order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,  # 与maker订单相同的用户
                client_order_id="client_self_trade_taker",
                self_trade_prevention_mode="EXPIRE_TAKER"  # 启用自成交预防
            )
            
            # 放置taker订单
            matching_engine.place_order(taker_order)
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{maker_order_id}_NEW"].is_set(), "未收到maker订单NEW更新"
            assert events["order_updates"][f"{taker_order_id}_NEW"].is_set(), "未收到taker订单NEW更新"
            assert events["order_updates"][f"{taker_order_id}_EXPIRED"].is_set(), "未收到taker订单EXPIRED更新"
            assert events["order_updates"][f"{taker_order_id}_status_EXPIRED"].is_set(), "未收到taker订单EXPIRED状态"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 3, "应至少收到3条消息"
            
            # 验证订单过期的详细信息
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == taker_order_id and 
                        order_data.get("X") == "EXPIRED"):
                        # 验证自成交预防模式字段
                        assert order_data.get("V") == "EXPIRE_TAKER", "自成交预防模式字段不正确"
                        break
            else:
                assert False, "未找到taker订单EXPIRED消息"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_self_trade_prevention_expire_maker(self, setup_exchange, setup_mock_websocket):
        """测试自成交预防EXPIRE_MAKER模式的订单更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        maker_order_id = "self_trade_maker2"
        taker_order_id = "self_trade_taker2"
        events["order_updates"][f"{maker_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{maker_order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{maker_order_id}_EXPIRED"] = asyncio.Event()
        events["order_updates"][f"{maker_order_id}_status_EXPIRED"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_status_NEW"] = asyncio.Event()
        
        # 设置最终期望状态
        events["final_status_key"] = f"{maker_order_id}_status_EXPIRED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 创建maker订单（先下的订单）
            maker_order = Order(
                order_id=maker_order_id,
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,
                client_order_id="client_self_trade_maker2"
            )
            
            # 放置maker订单
            matching_engine.place_order(maker_order)
            
            # 等待maker订单NEW状态
            await events["order_updates"][f"{maker_order_id}_status_NEW"].wait()
            
            # 创建taker订单（后下的订单），使用自成交预防模式EXPIRE_MAKER
            taker_order = Order(
                order_id=taker_order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,  # 与maker订单相同的用户
                client_order_id="client_self_trade_taker2",
                self_trade_prevention_mode="EXPIRE_MAKER"  # 启用自成交预防
            )
            
            # 放置taker订单
            matching_engine.place_order(taker_order)
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{maker_order_id}_NEW"].is_set(), "未收到maker订单NEW更新"
            assert events["order_updates"][f"{maker_order_id}_EXPIRED"].is_set(), "未收到maker订单EXPIRED更新"
            assert events["order_updates"][f"{maker_order_id}_status_EXPIRED"].is_set(), "未收到maker订单EXPIRED状态"
            assert events["order_updates"][f"{taker_order_id}_NEW"].is_set(), "未收到taker订单NEW更新"
            assert events["order_updates"][f"{taker_order_id}_status_NEW"].is_set(), "未收到taker订单NEW状态"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 3, "应至少收到3条消息"
            
            # 验证订单过期的详细信息
            found_expired_message = False
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if (order_data.get("i") == maker_order_id and 
                        order_data.get("X") == "EXPIRED"):
                        # 验证变更类型
                        assert order_data.get("x") == "EXPIRED", "变更类型不正确"
                        found_expired_message = True
                        break
            
            assert found_expired_message, "未找到maker订单EXPIRED消息"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_self_trade_prevention_expire_both(self, setup_exchange, setup_mock_websocket):
        """测试自成交预防EXPIRE_BOTH模式的订单更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        maker_order_id = "self_trade_maker3"
        taker_order_id = "self_trade_taker3"
        events["order_updates"][f"{maker_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{maker_order_id}_status_NEW"] = asyncio.Event()
        events["order_updates"][f"{maker_order_id}_EXPIRED"] = asyncio.Event()
        events["order_updates"][f"{maker_order_id}_status_EXPIRED"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_NEW"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_EXPIRED"] = asyncio.Event()
        events["order_updates"][f"{taker_order_id}_status_EXPIRED"] = asyncio.Event()
        
        # 设置最终期望状态 - 检查两者都过期
        events["final_status_key"] = f"{taker_order_id}_status_EXPIRED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            # 创建maker订单（先下的订单）
            maker_order = Order(
                order_id=maker_order_id,
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,
                client_order_id="client_self_trade_maker3"
            )
            
            # 放置maker订单
            matching_engine.place_order(maker_order)
            
            # 等待maker订单NEW状态
            await events["order_updates"][f"{maker_order_id}_status_NEW"].wait()
            
            # 创建taker订单（后下的订单），使用自成交预防模式EXPIRE_BOTH
            taker_order = Order(
                order_id=taker_order_id,
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,  # 与maker订单相同的用户
                client_order_id="client_self_trade_taker3",
                self_trade_prevention_mode="EXPIRE_BOTH"  # 启用自成交预防
            )
            
            # 放置taker订单
            matching_engine.place_order(taker_order)
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 验证是否收到所有订单状态更新
            assert events["order_updates"][f"{maker_order_id}_NEW"].is_set(), "未收到maker订单NEW更新"
            assert events["order_updates"][f"{maker_order_id}_EXPIRED"].is_set(), "未收到maker订单EXPIRED更新"
            assert events["order_updates"][f"{maker_order_id}_status_EXPIRED"].is_set(), "未收到maker订单EXPIRED状态"
            assert events["order_updates"][f"{taker_order_id}_NEW"].is_set(), "未收到taker订单NEW更新"
            assert events["order_updates"][f"{taker_order_id}_EXPIRED"].is_set(), "未收到taker订单EXPIRED更新"
            assert events["order_updates"][f"{taker_order_id}_status_EXPIRED"].is_set(), "未收到taker订单EXPIRED状态"
            
            # 验证收到消息的内容
            assert len(received_messages) >= 4, "应至少收到4条消息"
            
            # 验证两个订单都收到了过期消息
            found_maker_expired = False
            found_taker_expired = False
            
            for message in received_messages:
                if message.get("data", {}).get("e") == "ORDER_TRADE_UPDATE":
                    order_data = message.get("data", {}).get("o", {})
                    if order_data.get("X") == "EXPIRED":
                        if order_data.get("i") == maker_order_id:
                            found_maker_expired = True
                        elif order_data.get("i") == taker_order_id:
                            found_taker_expired = True
                            # 验证自成交预防模式字段
                            assert order_data.get("V") == "EXPIRE_BOTH", "自成交预防模式字段不正确"
            
            assert found_maker_expired, "未找到maker订单EXPIRED消息"
            assert found_taker_expired, "未找到taker订单EXPIRED消息"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass 