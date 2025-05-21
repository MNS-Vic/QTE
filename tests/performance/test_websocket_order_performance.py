#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket订单更新推送性能测试
测量订单通知延迟和吞吐量
"""
import pytest
import asyncio
import json
import time
import statistics
import logging
import csv
import os
from decimal import Decimal
from typing import Dict, List, Any
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest_asyncio

from qte.exchange.matching.matching_engine import (
    MatchingEngine, Order, OrderSide, OrderType, OrderStatus, Trade
)
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestWebSocketOrderPerformance:
    """WebSocket订单更新推送性能测试"""
    
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
        account.deposit("USDT", Decimal("1000000"))  # 足够大的金额
        account.deposit("BTC", Decimal("100"))       # 足够大的金额
        
        # 创建多个对手方账户
        counter_party_ids = [f"counter_party_{i}" for i in range(5)]
        for counter_id in counter_party_ids:
            account_manager.create_account(counter_id)
            counter_account = account_manager.get_account(counter_id)
            counter_account.deposit("USDT", Decimal("1000000"))
            counter_account.deposit("BTC", Decimal("100"))
        
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
            "counter_party_ids": counter_party_ids,
            "api_key": api_key
        }
        
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
            "orders_received": {},  # 用于跟踪每个订单接收状态
            "order_latencies": {},  # 存储每个订单的延迟
            "message_count": 0      # 收到的消息总数
        }
        
        # 模拟WebSocket客户端连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 使用列表存储收到的消息
        received_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            nonlocal events
            
            receive_time = time.time()
            data = json.loads(message)
            received_messages.append(data)
            events["message_count"] += 1
            
            # 检查订单状态更新
            if (data.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"):
                order_data = data.get("data", {}).get("o", {})
                order_id = order_data.get("i")
                
                # 如果该订单被跟踪
                if order_id in events["orders_received"]:
                    # 记录收到时间，计算延迟
                    send_time = events["orders_received"][order_id]["send_time"]
                    latency = receive_time - send_time
                    
                    # 存储延迟信息
                    if order_id not in events["order_latencies"]:
                        events["order_latencies"][order_id] = []
                    events["order_latencies"][order_id].append({
                        "update_type": order_data.get("x"),
                        "status": order_data.get("X"),
                        "latency": latency
                    })
                    
                    # 如果订单最终状态是FILLED或CANCELED，标记完成
                    if order_data.get("X") in ["FILLED", "CANCELED"]:
                        events["orders_received"][order_id]["completed"] = True
                        
                        # 检查是否所有订单都完成了
                        all_completed = True
                        for order_info in events["orders_received"].values():
                            if not order_info.get("completed", False):
                                all_completed = False
                                break
                        
                        if all_completed and events.get("all_orders_sent", False):
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
    
    async def create_timeout_task(self, events, timeout_seconds=30):
        """创建超时任务"""
        async def timeout_handler():
            await asyncio.sleep(timeout_seconds)
            if not events["done"].is_set():
                logger.error(f"测试超时({timeout_seconds}秒)，强制结束测试")
                events["done"].set()
        
        return asyncio.create_task(timeout_handler())
    
    def _create_results_dir(self):
        """创建结果目录"""
        results_dir = os.path.join("results", "performance")
        os.makedirs(results_dir, exist_ok=True)
        return results_dir
    
    def _save_latency_results(self, order_latencies, test_name):
        """保存延迟测试结果到CSV文件和文本摘要"""
        results_dir = self._create_results_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(results_dir, f"{test_name}_{timestamp}.csv")
        summary_filename = os.path.join(results_dir, f"{test_name}_{timestamp}_summary.txt")
        
        # 保存原始数据到CSV
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['order_id', 'update_type', 'status', 'latency_ms']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for order_id, latencies in order_latencies.items():
                for latency_item in latencies:
                    writer.writerow({
                        'order_id': order_id,
                        'update_type': latency_item['update_type'],
                        'status': latency_item['status'],
                        'latency_ms': latency_item['latency'] * 1000
                    })
        
        # 计算并保存统计数据到文本文件
        stats = self._calculate_latency_stats(order_latencies)
        
        with open(summary_filename, 'w') as f:
            f.write(f"WebSocket订单通知延迟测试 - {test_name} - {timestamp}\n")
            f.write("="*60 + "\n\n")
            f.write(f"测试样本数: {stats['total_updates']}\n")
            f.write(f"平均延迟: {stats['mean_latency_ms']:.3f}ms\n")
            f.write(f"最小延迟: {stats['min_latency_ms']:.3f}ms\n")
            f.write(f"最大延迟: {stats['max_latency_ms']:.3f}ms\n")
            f.write(f"中位数延迟: {stats['median_latency_ms']:.3f}ms\n")
            f.write(f"95%延迟: {stats['p95_latency_ms']:.3f}ms\n")
            f.write(f"99%延迟: {stats['p99_latency_ms']:.3f}ms\n\n")
            
            f.write("按更新类型的延迟统计:\n")
            f.write("-"*40 + "\n")
            for update_type, type_stats in stats['by_update_type'].items():
                f.write(f"\n{update_type}:\n")
                f.write(f"  样本数: {type_stats['count']}\n")
                f.write(f"  平均延迟: {type_stats['mean_latency_ms']:.3f}ms\n")
                f.write(f"  最小延迟: {type_stats['min_latency_ms']:.3f}ms\n")
                f.write(f"  最大延迟: {type_stats['max_latency_ms']:.3f}ms\n")
                f.write(f"  中位数延迟: {type_stats['median_latency_ms']:.3f}ms\n")
        
        logger.info(f"延迟测试结果已保存到 {filename} 和 {summary_filename}")
        return filename
    
    def _save_throughput_results(self, throughput_data, test_name):
        """将吞吐量测试结果保存到文本文件"""
        results_dir = self._create_results_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(results_dir, f"{test_name}_{timestamp}.txt")
        
        with open(filename, 'w') as f:
            f.write(f"WebSocket订单吞吐量测试 - {test_name} - {timestamp}\n")
            f.write("="*60 + "\n\n")
            f.write(f"测试订单数: {throughput_data['total_orders']}\n")
            f.write(f"总执行时间: {throughput_data['total_time_s']:.3f}秒\n")
            f.write(f"每秒处理订单数: {throughput_data['orders_per_second']:.3f}\n\n")
            
            f.write("延迟统计:\n")
            f.write("-"*40 + "\n")
            f.write(f"平均延迟: {throughput_data['avg_latency_ms']:.3f}ms\n")
            f.write(f"95%延迟: {throughput_data['p95_latency_ms']:.3f}ms\n")
            f.write(f"99%延迟: {throughput_data['p99_latency_ms']:.3f}ms\n")
        
        logger.info(f"吞吐量测试结果已保存到 {filename}")
        return filename
    
    def _calculate_latency_stats(self, order_latencies):
        """计算延迟统计数据"""
        all_latencies = []
        latencies_by_type = {}
        
        # 收集所有延迟数据
        for order_id, latencies in order_latencies.items():
            for latency_item in latencies:
                update_type = latency_item['update_type']
                latency_ms = latency_item['latency'] * 1000  # 转换为毫秒
                
                all_latencies.append(latency_ms)
                
                if update_type not in latencies_by_type:
                    latencies_by_type[update_type] = []
                latencies_by_type[update_type].append(latency_ms)
        
        # 排序以便计算百分位数
        all_latencies.sort()
        
        # 计算总体统计数据
        total_updates = len(all_latencies)
        if total_updates == 0:
            return {
                'total_updates': 0,
                'mean_latency_ms': 0,
                'min_latency_ms': 0,
                'max_latency_ms': 0,
                'median_latency_ms': 0,
                'p95_latency_ms': 0,
                'p99_latency_ms': 0,
                'by_update_type': {}
            }
            
        result = {
            'total_updates': total_updates,
            'mean_latency_ms': sum(all_latencies) / total_updates,
            'min_latency_ms': min(all_latencies),
            'max_latency_ms': max(all_latencies),
            'median_latency_ms': self._percentile(all_latencies, 0.5),
            'p95_latency_ms': self._percentile(all_latencies, 0.95),
            'p99_latency_ms': self._percentile(all_latencies, 0.99),
            'by_update_type': {}
        }
        
        # 按更新类型计算统计数据
        for update_type, latencies in latencies_by_type.items():
            latencies.sort()
            count = len(latencies)
            result['by_update_type'][update_type] = {
                'count': count,
                'mean_latency_ms': sum(latencies) / count,
                'min_latency_ms': min(latencies),
                'max_latency_ms': max(latencies),
                'median_latency_ms': self._percentile(latencies, 0.5)
            }
        
        return result
        
    def _percentile(self, data, percentile):
        """计算百分位数"""
        n = len(data)
        if n == 0:
            return 0
        
        index = percentile * (n - 1)
        if index.is_integer():
            return data[int(index)]
        else:
            i = int(index)
            fraction = index - i
            return data[i] * (1 - fraction) + data[i + 1] * fraction
    
    @pytest.mark.asyncio
    async def test_order_notification_latency(self, setup_exchange, setup_mock_websocket):
        """测试订单通知延迟"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        counter_party_ids = setup_exchange["counter_party_ids"]
        second_user_id = counter_party_ids[0]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        
        # 创建超时任务
        timeout_task = await self.create_timeout_task(events)
        
        try:
            logger.info("开始测试订单通知延迟...")
            
            # 创建卖单以提供流动性
            counter_side_id = "sell_for_latency_test"
            counter_side_order = Order(
                order_id=counter_side_id,
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=1.0,  # 足够大的数量
                price=50000.0,
                user_id=second_user_id
            )
            
            # 放置卖单
            matching_engine.place_order(counter_side_order)
            
            # 短暂等待确保卖单进入订单簿
            await asyncio.sleep(0.1)
            
            # 创建一系列订单以测试延迟
            num_orders = 10
            orders = []
            
            for i in range(num_orders):
                order_id = f"latency_test_order_{i}"
                
                # 记录发送时间
                send_time = time.time()
                events["orders_received"][order_id] = {
                    "send_time": send_time,
                    "completed": False
                }
                
                # 创建市价买单，确保能立即成交
                order = Order(
                    order_id=order_id,
                    symbol="BTCUSDT",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=0.1,
                    user_id=user_id
                )
                
                orders.append(order)
                
                # 放置订单
                matching_engine.place_order(order)
                
                # 短暂间隔，避免过快发送
                await asyncio.sleep(0.05)
            
            # 标记所有订单已发送
            events["all_orders_sent"] = True
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 计算延迟统计数据
            latency_stats = self._calculate_latency_stats(events["order_latencies"])
            
            # 保存结果
            self._save_latency_results(events["order_latencies"], "order_notification_latency")
            
            # 输出统计数据
            logger.info(f"订单通知延迟统计:")
            logger.info(f"总消息数: {events['message_count']}")
            logger.info(f"订单数: {latency_stats['total_updates']}")
            logger.info(f"最小延迟: {latency_stats['min_latency_ms']} ms")
            logger.info(f"最大延迟: {latency_stats['max_latency_ms']} ms")
            logger.info(f"平均延迟: {latency_stats['mean_latency_ms']} ms")
            logger.info(f"P95延迟: {latency_stats['p95_latency_ms']} ms")
            logger.info(f"P99延迟: {latency_stats['p99_latency_ms']} ms")
            
            # 验证计算了所有订单的延迟
            assert len(events["order_latencies"]) == num_orders, f"应该有{num_orders}个订单的延迟数据"
            
            # 验证延迟在合理范围内
            assert latency_stats["mean_latency_ms"] > 0, "平均延迟应大于0"
            assert latency_stats["max_latency_ms"] < 1000, "最大延迟应小于1000ms（除非机器非常慢）"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_order_throughput(self, setup_exchange, setup_mock_websocket):
        """测试订单吞吐量"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        user_id = setup_exchange["user_id"]
        counter_party_ids = setup_exchange["counter_party_ids"]
        
        # 获取模拟WebSocket环境
        events = setup_mock_websocket["events"]
        
        # 创建超时任务（高吞吐量测试可能需要更长时间）
        timeout_task = await self.create_timeout_task(events, timeout_seconds=60)
        
        try:
            logger.info("开始测试订单吞吐量...")
            
            # 先在订单簿中添加足够的卖单提供流动性
            for i in range(5):
                counter_id = counter_party_ids[i % len(counter_party_ids)]
                sell_price = 50000.0 + i * 100
                
                counter_side_order = Order(
                    order_id=f"sell_for_throughput_{i}",
                    symbol="BTCUSDT",
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    quantity=10.0,  # 足够大的数量
                    price=sell_price,
                    user_id=counter_id
                )
                
                matching_engine.place_order(counter_side_order)
            
            # 短暂等待确保卖单进入订单簿
            await asyncio.sleep(0.1)
            
            # 创建大量订单以测试吞吐量
            num_orders = 50
            start_time = time.time()
            
            async def place_order(order):
                """放置订单的异步任务"""
                # 记录发送时间
                send_time = time.time()
                events["orders_received"][order.order_id] = {
                    "send_time": send_time,
                    "completed": False
                }
                
                # 放置订单
                matching_engine.place_order(order)
            
            # 创建所有订单任务
            orders = []
            tasks = []
            
            for i in range(num_orders):
                order_id = f"throughput_test_order_{i}"
                
                # 创建市价买单，确保能立即成交
                order = Order(
                    order_id=order_id,
                    symbol="BTCUSDT",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=0.05,
                    user_id=user_id
                )
                
                orders.append(order)
                tasks.append(place_order(order))
            
            # 并发执行所有订单任务
            await asyncio.gather(*tasks)
            
            # 标记所有订单已发送
            events["all_orders_sent"] = True
            
            # 等待完成或超时
            await events["done"].wait()
            
            # 计算总执行时间
            total_time = time.time() - start_time
            
            # 计算延迟统计数据
            latency_stats = self._calculate_latency_stats(events["order_latencies"])
            
            # 计算吞吐量
            orders_per_second = num_orders / total_time
            
            # 保存延迟结果
            self._save_latency_results(events["order_latencies"], "order_throughput_latency")
            
            # 保存吞吐量结果
            throughput_data = {
                'total_orders': num_orders,
                'total_time_s': round(total_time, 3),
                'orders_per_second': round(orders_per_second, 3),
                'avg_latency_ms': latency_stats['mean_latency_ms'],
                'p95_latency_ms': latency_stats['p95_latency_ms'],
                'p99_latency_ms': latency_stats['p99_latency_ms']
            }
            self._save_throughput_results(throughput_data, "order_throughput")
            
            # 输出统计数据
            logger.info(f"订单吞吐量统计:")
            logger.info(f"总订单数: {num_orders}")
            logger.info(f"总执行时间: {total_time:.3f} 秒")
            logger.info(f"每秒订单数: {orders_per_second:.3f}")
            logger.info(f"平均延迟: {latency_stats['mean_latency_ms']} ms")
            logger.info(f"P95延迟: {latency_stats['p95_latency_ms']} ms")
            logger.info(f"P99延迟: {latency_stats['p99_latency_ms']} ms")
            
            # 验证计算了所有订单的延迟
            assert len(events["order_latencies"]) == num_orders, f"应该有{num_orders}个订单的延迟数据"
            
            # 验证吞吐量在合理范围内（具体值根据硬件而定）
            assert orders_per_second > 1, "每秒订单数应大于1"
            
        finally:
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_concurrent_clients_performance(self, setup_exchange):
        """测试多客户端并发性能"""
        # 获取测试环境
        matching_engine = setup_exchange["matching_engine"]
        websocket_server = setup_exchange["websocket_server"]
        user_id = setup_exchange["user_id"]
        counter_party_ids = setup_exchange["counter_party_ids"]
        second_user_id = counter_party_ids[0]
        
        # 添加流动性
        sell_order = Order(
            order_id="sell_for_concurrent_clients",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=100.0,  # 足够大的数量
            price=50000.0,
            user_id=second_user_id
        )
        matching_engine.place_order(sell_order)
        await asyncio.sleep(0.1)
        
        try:
            logger.info("开始测试多客户端并发性能...")
            
            # 创建多个模拟客户端
            num_clients = 5
            mock_clients = []
            client_events = []
            received_messages = []
            
            # 为每个客户端创建事件跟踪器
            for i in range(num_clients):
                events = {
                    "done": asyncio.Event(),
                    "orders_received": {},
                    "order_latencies": {},
                    "message_count": 0
                }
                client_events.append(events)
                received_messages.append([])
            
            # 创建模拟客户端连接
            for i in range(num_clients):
                mock_websocket = MagicMock()
                mock_websocket.remote_address = (f"127.0.0.1", 12345 + i)
                
                # 模拟send方法
                async def create_mock_send(client_index):
                    async def mock_send(message):
                        receive_time = time.time()
                        data = json.loads(message)
                        received_messages[client_index].append(data)
                        client_events[client_index]["message_count"] += 1
                        
                        # 检查订单状态更新
                        if (data.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"):
                            order_data = data.get("data", {}).get("o", {})
                            order_id = order_data.get("i")
                            
                            # 如果该订单被跟踪
                            if order_id in client_events[client_index]["orders_received"]:
                                # 记录收到时间，计算延迟
                                send_time = client_events[client_index]["orders_received"][order_id]["send_time"]
                                latency = receive_time - send_time
                                
                                # 存储延迟信息
                                if order_id not in client_events[client_index]["order_latencies"]:
                                    client_events[client_index]["order_latencies"][order_id] = []
                                client_events[client_index]["order_latencies"][order_id].append({
                                    "update_type": order_data.get("x"),
                                    "status": order_data.get("X"),
                                    "latency": latency
                                })
                                
                                # 如果订单最终状态是FILLED或CANCELED，标记完成
                                if order_data.get("X") in ["FILLED", "CANCELED"]:
                                    client_events[client_index]["orders_received"][order_id]["completed"] = True
                                    
                                    # 检查是否所有订单都完成了
                                    all_completed = True
                                    for order_info in client_events[client_index]["orders_received"].values():
                                        if not order_info.get("completed", False):
                                            all_completed = False
                                            break
                                    
                                    if all_completed and client_events[client_index].get("all_orders_sent", False):
                                        client_events[client_index]["done"].set()
                    
                    return mock_send
                
                mock_websocket.send = await create_mock_send(i)
                mock_clients.append(mock_websocket)
                
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
            
            # 创建超时任务
            async def timeout_handler(client_events):
                await asyncio.sleep(60)
                for i, events in enumerate(client_events):
                    if not events["done"].is_set():
                        logger.error(f"客户端 {i} 测试超时(60秒)，强制结束测试")
                        events["done"].set()
            
            timeout_task = asyncio.create_task(timeout_handler(client_events))
            
            # 为每个客户端创建测试订单
            orders_per_client = 10
            start_time = time.time()
            
            # 所有客户端同时发送订单
            async def place_orders_for_client(client_index):
                client_events_obj = client_events[client_index]
                
                orders = []
                tasks = []
                
                for j in range(orders_per_client):
                    order_id = f"concurrent_client_{client_index}_order_{j}"
                    
                    # 记录发送时间
                    send_time = time.time()
                    client_events_obj["orders_received"][order_id] = {
                        "send_time": send_time,
                        "completed": False
                    }
                    
                    # 创建市价买单，确保能立即成交
                    order = Order(
                        order_id=order_id,
                        symbol="BTCUSDT",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=0.01,
                        user_id=user_id
                    )
                    
                    orders.append(order)
                    
                    async def place_order(order):
                        matching_engine.place_order(order)
                    
                    tasks.append(place_order(order))
                    await asyncio.sleep(0.01)  # 小间隔，避免完全并发
                
                # 执行该客户端的所有订单任务
                await asyncio.gather(*tasks)
                
                # 标记该客户端所有订单已发送
                client_events_obj["all_orders_sent"] = True
            
            # 并发为所有客户端下单
            await asyncio.gather(*[place_orders_for_client(i) for i in range(num_clients)])
            
            # 等待所有客户端完成
            await asyncio.gather(*[events["done"].wait() for events in client_events])
            
            # 计算总执行时间
            total_time = time.time() - start_time
            
            # 合并所有客户端的延迟数据
            all_latencies = {}
            for i, events in enumerate(client_events):
                for order_id, latencies in events["order_latencies"].items():
                    all_latencies[order_id] = latencies
            
            # 计算延迟统计数据
            latency_stats = self._calculate_latency_stats(all_latencies)
            
            # 计算总吞吐量
            total_orders = num_clients * orders_per_client
            orders_per_second = total_orders / total_time
            
            # 保存结果
            self._save_latency_results(all_latencies, "concurrent_clients_latency")
            
            throughput_data = {
                'total_orders': total_orders,
                'total_time_s': round(total_time, 3),
                'orders_per_second': round(orders_per_second, 3),
                'avg_latency_ms': latency_stats['mean_latency_ms'],
                'p95_latency_ms': latency_stats['p95_latency_ms'],
                'p99_latency_ms': latency_stats['p99_latency_ms']
            }
            self._save_throughput_results(throughput_data, "concurrent_clients_throughput")
            
            # 输出统计数据
            logger.info(f"多客户端并发性能统计:")
            logger.info(f"客户端数: {num_clients}")
            logger.info(f"每客户端订单数: {orders_per_client}")
            logger.info(f"总订单数: {total_orders}")
            logger.info(f"总执行时间: {total_time:.3f} 秒")
            logger.info(f"每秒订单数: {orders_per_second:.3f}")
            logger.info(f"平均延迟: {latency_stats['mean_latency_ms']} ms")
            logger.info(f"P95延迟: {latency_stats['p95_latency_ms']} ms")
            logger.info(f"P99延迟: {latency_stats['p99_latency_ms']} ms")
            
            # 验证数据完整性
            for i, events in enumerate(client_events):
                assert len(events["order_latencies"]) == orders_per_client, f"客户端 {i} 应该有 {orders_per_client} 个订单的延迟数据"
            
            # 验证吞吐量在合理范围内
            assert orders_per_second > 1, "每秒订单数应大于1"
            
        finally:
            # 清理资源
            for mock_websocket in mock_clients:
                if websocket_server.clients.get(mock_websocket):
                    del websocket_server.clients[mock_websocket]
                
                order_subscription_key = f"{user_id}@order"
                if order_subscription_key in websocket_server.user_subscriptions:
                    websocket_server.user_subscriptions[order_subscription_key].discard(mock_websocket)
            
            # 取消超时任务
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass 