#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟交易所单元测试
"""
import unittest
import time
import threading
from decimal import Decimal
import requests
import asyncio
import websockets
import json

from qte.exchange import MockExchange
from qte.exchange.matching.matching_engine import OrderSide, OrderType, OrderStatus


class TestMockExchange(unittest.TestCase):
    """测试模拟交易所功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试前的准备工作"""
        # 创建交易所
        cls.exchange = MockExchange(rest_port=5001, ws_port=8766)
        cls.exchange.start()
        
        # 等待服务启动
        time.sleep(1)
        
        # 注册交易对
        cls.exchange.register_symbol("BTCUSDT", "BTC", "USDT")
        
        # 创建用户
        cls.user1_id = "test_user1"
        cls.user2_id = "test_user2"
        cls.api_key1 = cls.exchange.create_user(cls.user1_id, "Test User 1")
        cls.api_key2 = cls.exchange.create_user(cls.user2_id, "Test User 2")
        
        # 为用户充值
        cls.exchange.deposit(cls.user1_id, "BTC", 1.0)
        cls.exchange.deposit(cls.user1_id, "USDT", 50000.0)
        cls.exchange.deposit(cls.user2_id, "BTC", 1.0)
        cls.exchange.deposit(cls.user2_id, "USDT", 50000.0)
        
        # REST API基本URL
        cls.base_url = "http://localhost:5001"
        cls.ws_url = "ws://localhost:8766"
    
    @classmethod
    def tearDownClass(cls):
        """测试后的清理工作"""
        # 停止交易所
        cls.exchange.stop()
    
    def test_01_rest_api_ping(self):
        """测试REST API连接"""
        response = requests.get(f"{self.base_url}/api/v1/ping")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
    
    def test_02_rest_api_server_time(self):
        """测试获取服务器时间"""
        response = requests.get(f"{self.base_url}/api/v1/time")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("serverTime", data)
    
    def test_03_rest_api_account(self):
        """测试获取账户信息"""
        headers = {"X-API-KEY": self.api_key1}
        response = requests.get(f"{self.base_url}/api/v1/account", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("balances", data)
        self.assertIsInstance(data["balances"], list)
        
        # 检查BTC余额
        btc_balance = None
        for balance in data["balances"]:
            if balance["asset"] == "BTC":
                btc_balance = balance
                break
        
        self.assertIsNotNone(btc_balance)
        self.assertEqual(float(btc_balance["free"]), 1.0)
    
    def test_04_rest_api_order_book(self):
        """测试获取订单簿"""
        response = requests.get(f"{self.base_url}/api/v1/depth?symbol=BTCUSDT")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("bids", data)
        self.assertIn("asks", data)
    
    def test_05_rest_api_place_order(self):
        """测试下单"""
        headers = {"X-API-KEY": self.api_key1}
        
        # 下限价买单
        order_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "0.01",
            "price": "20000",
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/order", 
            headers=headers, 
            json=order_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("orderId", data)
        
        # 保存订单ID用于后续测试
        self.order_id = data["orderId"]
    
    def test_06_rest_api_get_order(self):
        """测试查询订单"""
        headers = {"X-API-KEY": self.api_key1}
        
        # 确保有订单ID
        self.assertTrue(hasattr(self, "order_id"), "需要先下单再查询订单")
        
        response = requests.get(
            f"{self.base_url}/api/v1/order?symbol=BTCUSDT&orderId={self.order_id}", 
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["orderId"], self.order_id)
        self.assertEqual(data["symbol"], "BTCUSDT")
        self.assertEqual(data["side"], "BUY")
    
    def test_07_rest_api_cancel_order(self):
        """测试取消订单"""
        headers = {"X-API-KEY": self.api_key1}
        
        # 确保有订单ID
        self.assertTrue(hasattr(self, "order_id"), "需要先下单再取消订单")
        
        response = requests.delete(
            f"{self.base_url}/api/v1/order?symbol=BTCUSDT&orderId={self.order_id}", 
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["orderId"], self.order_id)
        self.assertEqual(data["status"], "CANCELED")
    
    def test_08_rest_api_open_orders(self):
        """测试查询当前挂单"""
        headers = {"X-API-KEY": self.api_key1}
        
        # 下限价买单
        order_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "0.01",
            "price": "19000",
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/order", 
            headers=headers, 
            json=order_data
        )
        
        # 查询当前挂单
        response = requests.get(
            f"{self.base_url}/api/v1/openOrders?symbol=BTCUSDT", 
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
    
    def test_09_matching_engine(self):
        """测试撮合引擎"""
        # 用户1下限价卖单
        headers1 = {"X-API-KEY": self.api_key1}
        sell_order_data = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "quantity": "0.01",
            "price": "21000",
        }
        response = requests.post(
            f"{self.base_url}/api/v1/order", 
            headers=headers1, 
            json=sell_order_data
        )
        sell_order_id = response.json()["orderId"]
        
        # 用户2下限价买单，高于卖单价格，应该立即成交
        headers2 = {"X-API-KEY": self.api_key2}
        buy_order_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "0.01",
            "price": "22000",
        }
        response = requests.post(
            f"{self.base_url}/api/v1/order", 
            headers=headers2, 
            json=buy_order_data
        )
        buy_order_id = response.json()["orderId"]
        
        # 等待撮合
        time.sleep(1)
        
        # 查询卖单状态，应该已成交
        response = requests.get(
            f"{self.base_url}/api/v1/order?symbol=BTCUSDT&orderId={sell_order_id}", 
            headers=headers1
        )
        sell_order = response.json()
        
        # 查询买单状态，应该已成交
        response = requests.get(
            f"{self.base_url}/api/v1/order?symbol=BTCUSDT&orderId={buy_order_id}", 
            headers=headers2
        )
        buy_order = response.json()
        
        # 验证订单状态
        self.assertEqual(sell_order["status"], "FILLED")
        self.assertEqual(buy_order["status"], "FILLED")
        
        # 验证成交价格，应该是卖单价格
        self.assertEqual(float(sell_order["price"]), 21000.0)
    
    def test_10_websocket_connection(self):
        """测试WebSocket连接"""
        # 由于WebSocket测试需要异步，我们使用一个简单的标志变量
        received_messages = []
        connection_success = False

        async def test_ws():
            nonlocal connection_success
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    # 请求ping
                    ping_msg = {
                        "method": "ping",
                        "id": 1
                    }
                    await websocket.send(json.dumps(ping_msg))
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    if "result" in response_data:
                        connection_success = True
                    
                    # 认证
                    auth_msg = {
                        "method": "auth",
                        "params": {"api_key": self.api_key1},
                        "id": 2
                    }
                    await websocket.send(json.dumps(auth_msg))
                    await websocket.recv()  # 认证响应
                    
                    # 订阅深度
                    subscribe_msg = {
                        "method": "subscribe",
                        "params": {"streams": ["BTCUSDT@depth"]},
                        "id": 3
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    await websocket.recv()  # 订阅响应
                    
                    # 等待数据
                    for _ in range(3):  # 尝试获取3条消息
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=2)
                            received_messages.append(response)
                        except asyncio.TimeoutError:
                            break
            except Exception as e:
                print(f"WebSocket测试出错: {e}")

        # 运行异步测试
        asyncio.run(test_ws())
        
        # 提交一些订单以触发WebSocket消息
        headers = {"X-API-KEY": self.api_key1}
        order_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "0.01",
            "price": "19500",
        }
        requests.post(f"{self.base_url}/api/v1/order", headers=headers, json=order_data)
        
        # 验证连接成功
        self.assertTrue(connection_success, "WebSocket连接失败")


if __name__ == "__main__":
    unittest.main()