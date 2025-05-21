#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket订单更新推送功能边界情况与错误处理测试
"""
import pytest
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

class TestWebSocketOrderEdgeCasesIntegration:
    """WebSocket订单更新推送功能边界情况测试"""
    
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
        
        # 创建第二个用户账户（用于对手方订单）
        second_user_id = "second_user"
        account_manager.create_account(second_user_id)
        second_account = account_manager.get_account(second_user_id)
        second_account.deposit("USDT", Decimal("10000"))
        second_account.deposit("BTC", Decimal("1"))
        
        # 创建余额不足的账户
        low_balance_user_id = "low_balance_user"
        account_manager.create_account(low_balance_user_id)
        low_balance_account = account_manager.get_account(low_balance_user_id)
        low_balance_account.deposit("USDT", Decimal("10"))  # 不足以完成大额交易
        low_balance_account.deposit("BTC", Decimal("0.001"))
        
        # 创建WebSocket服务器
        websocket_server = ExchangeWebSocketServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=8765
        )
        
        # 创建API密钥
        api_key = websocket_server.create_api_key(user_id)
        websocket_server.create_api_key(low_balance_user_id)
        
        # 返回测试环境
        yield {
            "matching_engine": matching_engine,
            "account_manager": account_manager,
            "websocket_server": websocket_server,
            "user_id": user_id,
            "second_user_id": second_user_id,
            "low_balance_user_id": low_balance_user_id,
            "api_key": api_key
        }
        
        # 测试完成后清理资源
        logger.info("清理测试资源...")
        await asyncio.sleep(0.2)
    
    @pytest.fixture
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
        yield {
            "mock_websocket": mock_websocket,
            "received_messages": received_messages,
            "events": events,
            "subscription_key": order_subscription_key
        }
        
        # 清理订阅和客户端
        logger.info("清理WebSocket资源")
        if order_subscription_key in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key].discard(mock_websocket)
        
        if websocket_server.clients.get(mock_websocket):
            del websocket_server.clients[mock_websocket]
    
    @pytest.fixture
    async def setup_low_balance_websocket(self, setup_exchange):
        """创建低余额用户的WebSocket客户端环境"""
        websocket_server = setup_exchange["websocket_server"]
        low_balance_user_id = setup_exchange["low_balance_user_id"]
        
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
            logger.debug(f"低余额用户收到消息: {message[:200]}...")
            data = json.loads(message)
            received_messages.append(data)
            
            # 检查订单状态更新
            if (data.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"):
                order_data = data.get("data", {}).get("o", {})
                order_id = order_data.get("i")
                update_type = order_data.get("x")
                status = order_data.get("X")
                logger.info(f"低余额用户收到订单 {order_id} 状态更新: {update_type}, 状态: {status}")
                
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
            "user_id": low_balance_user_id,
            "subscriptions": set()
        }
        
        # 模拟用户订阅订单更新
        order_subscription_key = f"{low_balance_user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 返回模拟环境
        yield {
            "mock_websocket": mock_websocket,
            "received_messages": received_messages,
            "events": events,
            "subscription_key": order_subscription_key
        }
        
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
                    logger.error(f"{status_key} 状态已收到: {event.is_set()}")
        
        return asyncio.create_task(timeout_handler())
    
    @pytest.mark.asyncio
    async def test_insufficient_balance_order(self, setup_exchange, setup_low_balance_websocket):
        """测试余额不足时的订单处理"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        low_balance_user_id = setup_exchange["low_balance_user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_low_balance_websocket["events"]
        received_messages = setup_low_balance_websocket["received_messages"]
        
        # 添加订单状态事件
        events["order_updates"]["insufficient_order_REJECTED"] = asyncio.Event()
        events["order_updates"]["insufficient_order_status_REJECTED"] = asyncio.Event()
        events["final_status_key"] = "insufficient_order_status_REJECTED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            logger.info("开始测试余额不足的订单...")
            
            # 创建一个超出余额的买单
            buy_order = Order(
                order_id="insufficient_order",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=1.0,  # 大于用户BTC余额
                price=50000.0,  # 总价值大于用户USDT余额
                user_id=low_balance_user_id,
                client_order_id="client_insufficient_order"
            )
            
            logger.info("尝试下余额不足的买单")
            # 下单
            matching_engine.place_order(buy_order)
            
            # 等待REJECTED状态
            await events["done"].wait()
            
            # 验证订单状态
            assert events["order_updates"]["insufficient_order_status_REJECTED"].is_set(), "订单未被拒绝"
            
            # 验证订单消息
            order_messages = [msg for msg in received_messages 
                            if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"]
            
            # 验证REJECTED状态
            reject_msg = next((msg for msg in order_messages 
                            if msg["data"]["o"]["X"] == "REJECTED"), None)
            assert reject_msg is not None, "未收到REJECTED状态消息"
            assert reject_msg["data"]["o"]["i"] == "insufficient_order"
            
            # 验证拒绝原因
            assert "r" in reject_msg["data"]["o"], "拒绝原因字段(r)不存在"
            assert "INSUFFICIENT_BALANCE" in reject_msg["data"]["o"]["r"], "拒绝原因不正确"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_invalid_price_precision(self, setup_exchange, setup_mock_websocket):
        """测试价格精度无效的订单处理"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        events["order_updates"]["invalid_price_REJECTED"] = asyncio.Event()
        events["order_updates"]["invalid_price_status_REJECTED"] = asyncio.Event()
        events["final_status_key"] = "invalid_price_status_REJECTED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            logger.info("开始测试价格精度无效的订单...")
            
            # 创建一个价格精度过高的订单
            order = Order(
                order_id="invalid_price",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.123456789,  # 假设BTCUSDT的价格精度为2位小数
                user_id=user_id,
                client_order_id="client_invalid_price"
            )
            
            logger.info("尝试下价格精度无效的订单")
            # 下单
            matching_engine.place_order(order)
            
            # 等待REJECTED状态
            await events["done"].wait()
            
            # 验证订单状态
            assert events["order_updates"]["invalid_price_status_REJECTED"].is_set(), "订单未被拒绝"
            
            # 验证订单消息
            order_messages = [msg for msg in received_messages 
                            if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"]
            
            # 验证REJECTED状态
            reject_msg = next((msg for msg in order_messages 
                            if msg["data"]["o"]["X"] == "REJECTED" and 
                               msg["data"]["o"]["i"] == "invalid_price"), None)
            assert reject_msg is not None, "未收到REJECTED状态消息"
            
            # 验证拒绝原因
            assert "r" in reject_msg["data"]["o"], "拒绝原因字段(r)不存在"
            assert "PRICE_FILTER" in reject_msg["data"]["o"]["r"], "拒绝原因不正确"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_invalid_quantity(self, setup_exchange, setup_mock_websocket):
        """测试数量无效的订单处理"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        events["order_updates"]["invalid_qty_REJECTED"] = asyncio.Event()
        events["order_updates"]["invalid_qty_status_REJECTED"] = asyncio.Event()
        events["final_status_key"] = "invalid_qty_status_REJECTED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            logger.info("开始测试数量无效的订单...")
            
            # 创建一个数量过小的订单
            order = Order(
                order_id="invalid_qty",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.0000001,  # 假设最小数量为0.00001
                price=50000.0,
                user_id=user_id,
                client_order_id="client_invalid_qty"
            )
            
            logger.info("尝试下数量无效的订单")
            # 下单
            matching_engine.place_order(order)
            
            # 等待REJECTED状态
            await events["done"].wait()
            
            # 验证订单状态
            assert events["order_updates"]["invalid_qty_status_REJECTED"].is_set(), "订单未被拒绝"
            
            # 验证订单消息
            order_messages = [msg for msg in received_messages 
                            if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"]
            
            # 验证REJECTED状态
            reject_msg = next((msg for msg in order_messages 
                            if msg["data"]["o"]["X"] == "REJECTED" and 
                               msg["data"]["o"]["i"] == "invalid_qty"), None)
            assert reject_msg is not None, "未收到REJECTED状态消息"
            
            # 验证拒绝原因
            assert "r" in reject_msg["data"]["o"], "拒绝原因字段(r)不存在"
            assert "LOT_SIZE" in reject_msg["data"]["o"]["r"], "拒绝原因不正确"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_order(self, setup_exchange, setup_mock_websocket):
        """测试取消不存在的订单"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        events["order_updates"]["nonexist_order_REJECTED"] = asyncio.Event()
        events["done"] = events["order_updates"]["nonexist_order_REJECTED"]  # 直接使用已有事件
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            logger.info("开始测试取消不存在的订单...")
            
            # 尝试取消一个不存在的订单
            nonexistent_order_id = "nonexist_order"
            logger.info(f"尝试取消不存在的订单: {nonexistent_order_id}")
            
            # 调用取消订单方法
            matching_engine.cancel_order(nonexistent_order_id, "BTCUSDT")
            
            # 等待一段时间看是否有消息
            await asyncio.sleep(1.0)
            
            # 验证没有收到不存在订单的消息
            order_messages = [msg for msg in received_messages 
                            if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE" and
                               msg.get("data", {}).get("o", {}).get("i") == nonexistent_order_id]
            
            assert len(order_messages) == 0, "不应该收到不存在订单的消息"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_market_order_with_no_liquidity(self, setup_exchange, setup_mock_websocket):
        """测试无流动性时的市价单处理"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        received_messages = setup_mock_websocket["received_messages"]
        
        # 添加订单状态事件
        events["order_updates"]["market_order_NEW"] = asyncio.Event()
        events["order_updates"]["market_order_EXPIRED"] = asyncio.Event()
        events["order_updates"]["market_order_status_EXPIRED"] = asyncio.Event()
        events["final_status_key"] = "market_order_status_EXPIRED"
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            logger.info("开始测试无流动性的市价单...")
            
            # 清空所有待撮合订单，确保没有流动性
            # 这里需要实现一个清空订单簿的方法，如果matching_engine没有提供，则跳过此步骤
            # matching_engine.clear_order_book("BTCUSDT")
            
            # 创建一个市价买单，但订单簿中没有对应的卖单
            market_order = Order(
                order_id="market_order",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.1,
                price=0,  # 市价单价格为0
                user_id=user_id,
                client_order_id="client_market_order"
            )
            
            logger.info("下无流动性的市价单")
            # 下单
            matching_engine.place_order(market_order)
            
            # 等待EXPIRED状态
            await events["done"].wait()
            
            # 验证订单状态
            assert events["order_updates"]["market_order_status_EXPIRED"].is_set(), "市价单未过期"
            
            # 验证订单消息
            order_messages = [msg for msg in received_messages 
                            if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE" and
                               msg.get("data", {}).get("o", {}).get("i") == "market_order"]
            
            # 验证EXPIRED状态
            expire_msg = next((msg for msg in order_messages 
                            if msg["data"]["o"]["X"] == "EXPIRED"), None)
            assert expire_msg is not None, "未收到EXPIRED状态消息"
            
            # 验证过期原因
            assert "r" in expire_msg["data"]["o"], "过期原因字段(r)不存在"
            assert "NO_LIQUIDITY" in expire_msg["data"]["o"]["r"], "过期原因不正确"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_multiple_client_connections(self, setup_exchange):
        """测试多个客户端连接同时接收相同用户的订单更新"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        
        # 创建3个模拟WebSocket客户端连接
        mock_websockets = []
        received_messages_list = []
        event_list = []
        
        for i in range(3):
            # 创建事件标志
            events = {
                "received_update": asyncio.Event(),
                "client_index": i
            }
            event_list.append(events)
            
            # 模拟WebSocket客户端连接
            mock_websocket = MagicMock()
            mock_websocket.remote_address = (f"127.0.0.1", 12350 + i)
            mock_websockets.append(mock_websocket)
            
            # 使用列表存储收到的消息
            received_messages = []
            received_messages_list.append(received_messages)
            
            # 模拟send方法
            async def create_mock_send(client_index):
                async def mock_send(message):
                    nonlocal received_messages_list, event_list
                    logger.debug(f"客户端 {client_index} 收到消息: {message[:100]}...")
                    data = json.loads(message)
                    received_messages_list[client_index].append(data)
                    
                    # 检查订单状态更新
                    if (data.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"):
                        order_data = data.get("data", {}).get("o", {})
                        order_id = order_data.get("i")
                        if order_id == "multi_client_order":
                            event_list[client_index]["received_update"].set()
                
                return mock_send
            
            mock_websocket.send = await create_mock_send(i)
            
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
        
        try:
            logger.info("测试多客户端收到相同订单更新...")
            
            # 创建一个订单
            order = Order(
                order_id="multi_client_order",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                user_id=user_id,
                client_order_id="client_multi_client_order"
            )
            
            logger.info("下订单，应推送给多个客户端")
            # 下单
            matching_engine.place_order(order)
            
            # 等待所有客户端接收到消息
            await asyncio.gather(*[events["received_update"].wait() for events in event_list])
            
            # 验证所有客户端都接收到相同的消息
            for i, received_messages in enumerate(received_messages_list):
                order_messages = [msg for msg in received_messages 
                                if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE" and
                                   msg.get("data", {}).get("o", {}).get("i") == "multi_client_order"]
                
                assert len(order_messages) > 0, f"客户端 {i} 未收到订单消息"
            
            # 验证所有客户端收到的消息内容一致
            first_client_message = next((msg for msg in received_messages_list[0] 
                                      if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE" and
                                         msg.get("data", {}).get("o", {}).get("i") == "multi_client_order"), None)
            
            for i in range(1, len(received_messages_list)):
                client_message = next((msg for msg in received_messages_list[i] 
                                    if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE" and
                                       msg.get("data", {}).get("o", {}).get("i") == "multi_client_order"), None)
                
                # 比较消息的主要内容 (忽略可能有差异的时间戳)
                assert client_message["data"]["o"]["i"] == first_client_message["data"]["o"]["i"], "订单ID不一致"
                assert client_message["data"]["o"]["X"] == first_client_message["data"]["o"]["X"], "订单状态不一致"
                assert client_message["data"]["o"]["s"] == first_client_message["data"]["o"]["s"], "交易对不一致"
            
        finally:
            # 清理订阅和客户端
            logger.info("清理WebSocket资源")
            order_subscription_key = f"{user_id}@order"
            for mock_websocket in mock_websockets:
                if order_subscription_key in websocket_server.user_subscriptions:
                    websocket_server.user_subscriptions[order_subscription_key].discard(mock_websocket)
                
                if websocket_server.clients.get(mock_websocket):
                    del websocket_server.clients[mock_websocket] 