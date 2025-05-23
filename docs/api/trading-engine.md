# QTE模拟交易所API指南

本文档介绍了QTE框架中模拟交易所的API使用方法，包括REST API和WebSocket接口。这些接口模拟了真实交易所的API设计，使策略开发者能够更接近真实环境地进行回测。

## 整体架构

QTE模拟交易所由以下核心组件组成：

1. **撮合引擎（Matching Engine）**：处理订单匹配和成交
2. **账户管理（Account Manager）**：管理用户账户、资金和持仓
3. **REST API接口**：提供HTTP API接口
4. **WebSocket接口**：提供实时数据和交易更新

## 快速开始

### 初始化模拟交易所

```python
from qte.exchange import MockExchange

# 创建模拟交易所实例
exchange = MockExchange(rest_host="localhost", rest_port=5000, 
                        ws_host="localhost", ws_port=8765)

# 启动交易所服务
exchange.start()

# 注册交易对
exchange.register_symbol("BTCUSDT", "BTC", "USDT")

# 创建用户并获取API密钥
api_key = exchange.create_user("user1", "User One")

# 为用户充值
exchange.deposit("user1", "BTC", 1.0)
exchange.deposit("user1", "USDT", 50000.0)
```

## REST API接口

REST API接口支持以下主要功能：

### 市场数据API

- **GET /api/v1/ping**: 测试连接
- **GET /api/v1/time**: 获取服务器时间
- **GET /api/v1/ticker/price**: 获取最新价格
- **GET /api/v1/ticker/24hr**: 获取24小时价格变动统计
- **GET /api/v1/depth**: 获取订单簿
- **GET /api/v1/trades**: 获取最近成交
- **GET /api/v1/klines**: 获取K线数据

### 交易API

- **POST /api/v1/order**: 创建订单
- **DELETE /api/v1/order**: 取消订单
- **GET /api/v1/order**: 查询订单
- **GET /api/v1/openOrders**: 查询当前挂单
- **GET /api/v1/allOrders**: 查询所有订单

### 账户API

- **GET /api/v1/account**: 查询账户信息
- **GET /api/v1/myTrades**: 查询用户交易历史

### 示例：使用requests库访问REST API

```python
import requests

# API基本URL
base_url = "http://localhost:5000"

# API密钥（通过exchange.create_user获取）
api_key = "your_api_key_here"

# 设置请求头
headers = {
    "X-API-KEY": api_key
}

# 查询账户信息
response = requests.get(f"{base_url}/api/v1/account", headers=headers)
account_info = response.json()
print(account_info)

# 下单示例（限价买单）
order_data = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "LIMIT",
    "quantity": "0.01",
    "price": "20000",
    "newClientOrderId": "my_order_id_123"
}
response = requests.post(f"{base_url}/api/v1/order", headers=headers, json=order_data)
order_result = response.json()
print(order_result)
```

## WebSocket接口

WebSocket接口支持以下订阅流：

### 市场数据流

- **{symbol}@ticker**: 价格变动
- **{symbol}@depth**: 订单簿深度变动
- **{symbol}@trade**: 实时成交
- **{symbol}@kline**: K线更新

### 用户数据流

- **{userId}@account**: 账户信息更新
- **{userId}@order**: 订单状态更新
- **{userId}@trade**: 用户成交更新

### 示例：使用websockets库连接WebSocket

```python
import asyncio
import json
import websockets

async def connect_to_websocket():
    # WebSocket URL
    ws_url = "ws://localhost:8765"
    
    # 连接WebSocket
    async with websockets.connect(ws_url) as websocket:
        # 认证
        auth_msg = {
            "method": "auth",
            "params": {
                "api_key": "your_api_key_here"
            },
            "id": 1
        }
        await websocket.send(json.dumps(auth_msg))
        response = await websocket.recv()
        print(f"认证响应: {response}")
        
        # 订阅市场数据
        subscribe_msg = {
            "method": "subscribe",
            "params": {
                "streams": ["BTCUSDT@trade", "BTCUSDT@depth"]
            },
            "id": 2
        }
        await websocket.send(json.dumps(subscribe_msg))
        response = await websocket.recv()
        print(f"订阅响应: {response}")
        
        # 订阅用户数据
        subscribe_user_msg = {
            "method": "subscribe",
            "params": {
                "streams": ["user1@account", "user1@order"]
            },
            "id": 3
        }
        await websocket.send(json.dumps(subscribe_user_msg))
        response = await websocket.recv()
        print(f"用户订阅响应: {response}")
        
        # 接收消息
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"收到消息: {data}")

# 运行示例
asyncio.run(connect_to_websocket())
```

## 在策略中使用模拟交易所

为了将策略与模拟交易所集成，建议使用以下方法：

1. 在回测环境中启动模拟交易所
2. 策略通过REST API和WebSocket与交易所交互，而不是直接调用内部函数
3. 这样可以更好地模拟实盘环境，减少从回测到实盘的转换成本

### 策略示例

```python
import requests
import json
import time
import threading
import websockets
import asyncio

class TradingStrategy:
    def __init__(self, api_key, rest_url="http://localhost:5000", ws_url="ws://localhost:8765"):
        self.api_key = api_key
        self.rest_url = rest_url
        self.ws_url = ws_url
        self.headers = {"X-API-KEY": api_key}
        self.ws_client = None
        self.ws_thread = None
        self.running = False
        
    def start(self):
        # 启动WebSocket连接线程
        self.running = True
        self.ws_thread = threading.Thread(target=self.start_ws_client)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # 开始交易逻辑
        while self.running:
            try:
                # 获取市场数据
                ticker = self.get_ticker("BTCUSDT")
                depth = self.get_order_book("BTCUSDT")
                
                # 交易逻辑
                # ...
                
                # 下单示例
                # self.place_order("BTCUSDT", "BUY", "LIMIT", 0.01, 20000)
                
                time.sleep(5)  # 每5秒执行一次
            except Exception as e:
                print(f"策略执行错误: {e}")
                time.sleep(5)
    
    def stop(self):
        self.running = False
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
    
    def start_ws_client(self):
        asyncio.run(self.ws_client_loop())
    
    async def ws_client_loop(self):
        async with websockets.connect(self.ws_url) as websocket:
            # 认证
            await websocket.send(json.dumps({
                "method": "auth",
                "params": {"api_key": self.api_key},
                "id": 1
            }))
            
            # 订阅
            await websocket.send(json.dumps({
                "method": "subscribe",
                "params": {"streams": ["BTCUSDT@ticker", "BTCUSDT@depth"]},
                "id": 2
            }))
            
            # 接收消息
            while self.running:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    self.process_ws_message(data)
                except Exception as e:
                    print(f"WebSocket错误: {e}")
                    break
    
    def process_ws_message(self, data):
        # 处理WebSocket消息
        print(f"WS消息: {data}")
    
    def get_ticker(self, symbol):
        """获取最新价格"""
        response = requests.get(f"{self.rest_url}/api/v1/ticker/price?symbol={symbol}", headers=self.headers)
        return response.json()
    
    def get_order_book(self, symbol, limit=10):
        """获取订单簿"""
        response = requests.get(f"{self.rest_url}/api/v1/depth?symbol={symbol}&limit={limit}", headers=self.headers)
        return response.json()
    
    def place_order(self, symbol, side, order_type, quantity, price=None):
        """下单"""
        data = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity)
        }
        if price:
            data["price"] = str(price)
            
        response = requests.post(f"{self.rest_url}/api/v1/order", headers=self.headers, json=data)
        return response.json()
    
    def cancel_order(self, symbol, order_id):
        """取消订单"""
        params = f"symbol={symbol}&orderId={order_id}"
        response = requests.delete(f"{self.rest_url}/api/v1/order?{params}", headers=self.headers)
        return response.json()
    
    def get_account(self):
        """获取账户信息"""
        response = requests.get(f"{self.rest_url}/api/v1/account", headers=self.headers)
        return response.json()

# 使用示例
if __name__ == "__main__":
    # 获取API密钥（假设已经创建）
    api_key = "your_api_key_here"
    
    # 创建并启动策略
    strategy = TradingStrategy(api_key)
    try:
        strategy.start()
    except KeyboardInterrupt:
        strategy.stop()
        print("策略已停止")
```

## 高级用法

### 扩展模拟交易所功能

你可以通过继承基类来扩展模拟交易所的功能，例如：

- 增加更多订单类型
- 实现更高级的撮合算法
- 添加风险控制和交易限制
- 增加交易对支持

### 模拟交易所与QTE回测引擎的集成

模拟交易所可以与QTE回测引擎集成，以提供更真实的回测环境：

```python
from qte.exchange import MockExchange
from qte.core import EngineManager
import threading
import time

# 创建并启动模拟交易所
exchange = MockExchange()
exchange.start()
exchange.register_symbol("BTCUSDT", "BTC", "USDT")
api_key = exchange.create_user("strategy1", "Strategy One")
exchange.deposit("strategy1", "BTC", 1.0)
exchange.deposit("strategy1", "USDT", 50000.0)

# 创建并配置回测引擎
engine_manager = EngineManager()
# 配置数据源等...

# 启动回测
engine_manager.start()

# 等待回测完成
time.sleep(10)  # 或者使用事件等待回测完成

# 停止服务
engine_manager.stop()
exchange.stop()
```

## 注意事项与最佳实践

1. **性能考虑**：模拟交易所在本地运行，性能与真实交易所会有差异
2. **API兼容性**：尽管模拟了主流交易所API，但仍存在部分差异
3. **数据存储**：交易数据当前仅保存在内存中，重启后会丢失
4. **多用户**：支持模拟多个用户账户的交互
5. **安全性**：本地模拟环境不需要实现复杂的安全措施

## 常见问题解答

**Q: 如何调整订单撮合的速度？**
A: 目前撮合引擎是实时处理的，没有刻意的延迟。如需模拟延迟，可以在撮合引擎中添加延时逻辑。

**Q: 模拟交易所支持哪些订单类型？**
A: 当前支持限价单(LIMIT)和市价单(MARKET)，未来会增加止损单等高级类型。

**Q: 如何处理WebSocket连接断开？**
A: 在策略实现中，应该包含重连逻辑，监测连接状态并在断开时尝试重新连接。

**Q: 如何同时模拟多个交易所？**
A: 可以创建多个MockExchange实例，使用不同的端口运行。

## 扩展资源

- [QTE框架文档](../index.md)
- [策略开发指南](../development/strategy_development.md)
- [回测系统架构](../architecture/backtest_architecture.md)