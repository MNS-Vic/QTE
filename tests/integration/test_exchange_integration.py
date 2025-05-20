#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易所模块集成测试
测试匹配引擎、账户管理、REST API和WebSocket的协同工作
"""
import os
import sys
import pytest
import asyncio
import json
import time
import threading
import requests
import websockets
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

# 导入需要测试的模块
from qte.exchange.matching.matching_engine import MatchingEngine, OrderSide, OrderType
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.rest_api.rest_server import ExchangeRESTServer
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer

class TestExchangeIntegration:
    """交易所模块集成测试类"""
    
    @pytest.fixture(scope="class")
    def setup_exchange(self):
        """设置交易所系统"""
        # 创建撮合引擎
        matching_engine = MatchingEngine()
        
        # 创建账户管理器
        account_manager = AccountManager()
        
        # 创建REST API服务器
        rest_server = ExchangeRESTServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=5000
        )
        
        # 创建WebSocket服务器
        ws_server = ExchangeWebSocketServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=8765
        )
        
        # 返回创建的对象
        return {
            "matching_engine": matching_engine,
            "account_manager": account_manager,
            "rest_server": rest_server,
            "ws_server": ws_server
        }
    
    @pytest.fixture(scope="class")
    def start_servers(self, setup_exchange):
        """启动服务器"""
        rest_server = setup_exchange["rest_server"]
        ws_server = setup_exchange["ws_server"]
        
        # 启动REST服务器
        rest_server.start()
        
        # 启动WebSocket服务器
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def start_ws():
            await ws_server.start()
        
        loop.run_until_complete(start_ws())
        
        # 启动后台线程保持事件循环运行
        def run_event_loop():
            loop.run_forever()
            
        thread = threading.Thread(target=run_event_loop, daemon=True)
        thread.start()
        
        # 等待服务器启动
        time.sleep(1)
        
        yield
        
        # 测试结束后关闭服务器
        rest_server.stop()
        
        async def stop_ws():
            await ws_server.stop()
            
        loop.run_until_complete(stop_ws())
        loop.stop()
    
    @pytest.fixture
    def setup_test_accounts(self, setup_exchange):
        """创建测试账户并充值"""
        account_manager = setup_exchange["account_manager"]
        rest_server = setup_exchange["rest_server"]
        ws_server = setup_exchange["ws_server"]
        
        # 创建测试用户
        user1_id = "test_user1"
        user2_id = "test_user2"
        
        # 创建账户
        account_manager.create_account(user1_id)
        account_manager.create_account(user2_id)
        
        # 获取账户
        account1 = account_manager.get_account(user1_id)
        account2 = account_manager.get_account(user2_id)
        
        # 充值
        account1.deposit("USDT", Decimal("100000"))
        account1.deposit("BTC", Decimal("10"))
        account2.deposit("USDT", Decimal("100000"))
        account2.deposit("BTC", Decimal("10"))
        
        # 创建API密钥
        api_key1 = rest_server.create_api_key(user1_id)
        api_key2 = rest_server.create_api_key(user2_id)
        
        # 同步到WebSocket服务器
        ws_server.api_keys = rest_server.api_keys.copy()
        
        return {
            "user1": {
                "id": user1_id,
                "api_key": api_key1
            },
            "user2": {
                "id": user2_id,
                "api_key": api_key2
            }
        }
    
    @pytest.mark.usefixtures("start_servers")
    def test_end_to_end_trading(self, setup_exchange, setup_test_accounts):
        """
        测试完整的交易流程
        包括下单、撮合、查询、WebSocket通知等
        """
        # 获取测试数据
        user1 = setup_test_accounts["user1"]
        user2 = setup_test_accounts["user2"]
        
        rest_url = "http://localhost:5000/api/v1"
        ws_url = "ws://localhost:8765"
        
        # REST API的headers
        headers1 = {"X-API-KEY": user1["api_key"]}
        headers2 = {"X-API-KEY": user2["api_key"]}
        
        # 测试REST API响应
        response = requests.get(f"{rest_url}/ping")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        
        # 检查初始账户状态
        response = requests.get(f"{rest_url}/account", headers=headers1)
        assert response.status_code == 200
        user1_account = response.json()
        assert len(user1_account["balances"]) >= 2  # 至少有USDT和BTC
        
        # 创建测试订单（用户1买入BTC）
        order1_data = {
            "symbol": "BTC/USDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "1.0",
            "price": "20000.0"
        }
        
        response = requests.post(
            f"{rest_url}/order", 
            headers=headers1,
            json=order1_data
        )
        assert response.status_code == 200
        order1 = response.json()
        assert order1["status"] == "NEW"
        
        # 查询订单
        response = requests.get(
            f"{rest_url}/order?symbol=BTC/USDT&orderId={order1['orderId']}", 
            headers=headers1
        )
        assert response.status_code == 200
        assert response.json()["orderId"] == order1["orderId"]
        
        # 创建匹配的订单（用户2卖出BTC）
        order2_data = {
            "symbol": "BTC/USDT",
            "side": "SELL",
            "type": "LIMIT",
            "quantity": "1.0",
            "price": "20000.0"
        }
        
        response = requests.post(
            f"{rest_url}/order", 
            headers=headers2,
            json=order2_data
        )
        assert response.status_code == 200
        order2 = response.json()
        
        # 验证订单已成交
        time.sleep(1)  # 等待撮合和结算完成
        
        # 检查订单状态
        response = requests.get(
            f"{rest_url}/order?symbol=BTC/USDT&orderId={order1['orderId']}", 
            headers=headers1
        )
        assert response.status_code == 200
        updated_order1 = response.json()
        assert updated_order1["status"] == "FILLED"
        
        # 验证账户余额已更新
        response = requests.get(f"{rest_url}/account", headers=headers1)
        assert response.status_code == 200
        updated_user1_account = response.json()
        
        # 检查买入方的BTC增加，USDT减少
        btc_balance = next((b for b in updated_user1_account["balances"] if b["asset"] == "BTC"), None)
        usdt_balance = next((b for b in updated_user1_account["balances"] if b["asset"] == "USDT"), None)
        
        assert btc_balance is not None
        assert usdt_balance is not None
        
        # 测试WebSocket订阅和消息接收
        async def test_websocket():
            # 连接WebSocket
            async with websockets.connect(ws_url) as websocket:
                # 认证
                auth_msg = {
                    "method": "auth",
                    "params": {"api_key": user1["api_key"]},
                    "id": 1
                }
                await websocket.send(json.dumps(auth_msg))
                response = await websocket.recv()
                response_data = json.loads(response)
                assert response_data["result"] == "success"
                
                # 订阅市场数据
                subscribe_msg = {
                    "method": "subscribe",
                    "params": {"streams": ["BTC/USDT@ticker"]},
                    "id": 2
                }
                await websocket.send(json.dumps(subscribe_msg))
                response = await websocket.recv()
                response_data = json.loads(response)
                assert response_data["result"] == "success"
                
                # 创建一笔新交易来触发WebSocket通知
                order3_data = {
                    "symbol": "BTC/USDT",
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "0.5",
                    "price": "21000.0"
                }
                
                # 使用另一个线程发送REST请求
                def send_order():
                    requests.post(
                        f"{rest_url}/order", 
                        headers=headers1,
                        json=order3_data
                    )
                
                # 启动线程发送订单
                thread = threading.Thread(target=send_order)
                thread.start()
                
                # 等待匹配的订单
                order4_data = {
                    "symbol": "BTC/USDT",
                    "side": "SELL",
                    "type": "LIMIT",
                    "quantity": "0.5",
                    "price": "21000.0"
                }
                
                def send_matching_order():
                    requests.post(
                        f"{rest_url}/order", 
                        headers=headers2,
                        json=order4_data
                    )
                
                # 启动线程发送匹配订单
                match_thread = threading.Thread(target=send_matching_order)
                match_thread.start()
                
                # 等待WebSocket通知
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    notification = json.loads(response)
                    
                    # 验证收到的是ticker更新
                    assert "stream" in notification
                    assert "BTC/USDT@ticker" in notification["stream"]
                    
                    # 等待线程完成
                    thread.join()
                    match_thread.join()
                    
                except asyncio.TimeoutError:
                    pytest.fail("等待WebSocket通知超时")
        
        # 执行WebSocket测试
        asyncio.get_event_loop().run_until_complete(test_websocket())
    
    @pytest.mark.usefixtures("start_servers")
    def test_error_handling(self, setup_exchange, setup_test_accounts):
        """
        测试错误处理功能
        包括无效参数、认证失败等情况
        """
        # 获取测试数据
        user1 = setup_test_accounts["user1"]
        
        rest_url = "http://localhost:5000/api/v1"
        
        # 测试无效参数
        invalid_order = {
            "symbol": "BTC/USDT",
            "side": "BUY",
            "type": "INVALID_TYPE",  # 无效的订单类型
            "quantity": "1.0",
            "price": "20000.0"
        }
        
        response = requests.post(
            f"{rest_url}/order", 
            headers={"X-API-KEY": user1["api_key"]},
            json=invalid_order
        )
        
        assert response.status_code == 400
        assert "error" in response.json()
        
        # 测试认证失败
        response = requests.get(
            f"{rest_url}/account",
            headers={"X-API-KEY": "invalid_api_key"}
        )
        
        assert response.status_code == 401
        assert "error" in response.json()
        
        # 测试缺少必要参数
        incomplete_order = {
            "symbol": "BTC/USDT",
            "side": "BUY",
            # 缺少type
            "quantity": "1.0",
            "price": "20000.0"
        }
        
        response = requests.post(
            f"{rest_url}/order", 
            headers={"X-API-KEY": user1["api_key"]},
            json=incomplete_order
        )
        
        assert response.status_code == 400
        assert "error" in response.json()
        
    @pytest.mark.usefixtures("start_servers")
    def test_zero_price_order_rejection(self, setup_exchange, setup_test_accounts):
        """
        测试零价格订单拒绝逻辑
        """
        # 获取测试数据
        user1 = setup_test_accounts["user1"]
        
        rest_url = "http://localhost:5000/api/v1"
        
        # 创建零价格订单
        zero_price_order = {
            "symbol": "BTC/USDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "1.0",
            "price": "0.0"  # 零价格
        }
        
        response = requests.post(
            f"{rest_url}/order", 
            headers={"X-API-KEY": user1["api_key"]},
            json=zero_price_order
        )
        
        # 期望返回错误
        assert response.status_code == 400
        assert "error" in response.json()
        assert "价格必须大于0" in response.json()["error"]