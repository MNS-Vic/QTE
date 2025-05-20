#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket服务器 - 模拟交易所WebSocket接口
"""
import logging
import json
import asyncio
import time
import traceback
from typing import Dict, List, Set, Any, Optional, Callable
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

# 导入撮合引擎和账户管理器
from qte.exchange.matching.matching_engine import MatchingEngine, Trade
from qte.exchange.account.account_manager import AccountManager

logger = logging.getLogger("WebSocketServer")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ExchangeWebSocketServer:
    """交易所WebSocket服务器"""
    
    def __init__(self, matching_engine: MatchingEngine, account_manager: AccountManager, 
                host: str = "localhost", port: int = 8765):
        """
        初始化WebSocket服务器
        
        Parameters
        ----------
        matching_engine : MatchingEngine
            撮合引擎
        account_manager : AccountManager
            账户管理器
        host : str, optional
            主机地址, by default "localhost"
        port : int, optional
            端口, by default 8765
        """
        self.matching_engine = matching_engine
        self.account_manager = account_manager
        self.host = host
        self.port = port
        
        # WebSocket连接和订阅管理
        self.clients: Dict[WebSocketServerProtocol, Dict[str, Any]] = {}  # 客户端连接
        self.market_subscriptions: Dict[str, Set[WebSocketServerProtocol]] = {}  # 市场订阅
        self.user_subscriptions: Dict[str, Set[WebSocketServerProtocol]] = {}  # 用户订阅
        
        # API密钥管理
        self.api_keys: Dict[str, str] = {}  # API密钥 -> 用户ID
        
        # 事件循环和服务器
        self.loop = None
        self.server = None
        self.is_running = False
        
        # 注册成交监听器
        self.matching_engine.add_trade_listener(self._on_trade)
        
        # 注册账户监听器
        self.account_manager.add_account_listener(self._on_account_update)
        
        logger.info(f"WebSocket服务器已初始化: {host}:{port}")
    
    def create_api_key(self, user_id: str) -> str:
        """
        为用户创建API密钥
        
        Parameters
        ----------
        user_id : str
            用户ID
            
        Returns
        -------
        str
            API密钥
        """
        import uuid
        api_key = str(uuid.uuid4())
        self.api_keys[api_key] = user_id
        logger.info(f"为用户 {user_id} 创建API密钥: {api_key}")
        return api_key
    
    def get_user_id_from_api_key(self, api_key: str) -> Optional[str]:
        """
        从API密钥获取用户ID
        
        Parameters
        ----------
        api_key : str
            API密钥
            
        Returns
        -------
        Optional[str]
            用户ID，如不存在则返回None
        """
        return self.api_keys.get(api_key)
    
    async def start(self) -> bool:
        """
        启动WebSocket服务器
        
        Returns
        -------
        bool
            是否成功启动
        """
        if self.is_running:
            logger.warning("WebSocket服务器已经运行")
            return False
            
        try:
            self.loop = asyncio.get_event_loop()
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=60
            )
            
            self.is_running = True
            logger.info(f"WebSocket服务器已启动: ws://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"启动WebSocket服务器失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        停止WebSocket服务器
        
        Returns
        -------
        bool
            是否成功停止
        """
        if not self.is_running or not self.server:
            logger.warning("WebSocket服务器未运行")
            return False
            
        try:
            # 关闭所有连接
            for client in list(self.clients.keys()):
                await client.close()
                
            # 关闭服务器
            self.server.close()
            await self.server.wait_closed()
            
            self.is_running = False
            logger.info("WebSocket服务器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止WebSocket服务器失败: {e}")
            return False
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        处理客户端连接
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        path : str
            请求路径
        """
        # 初始化客户端信息
        self.clients[websocket] = {
            "connected_at": time.time(),
            "user_id": None,
            "subscriptions": set()
        }
        
        logger.info(f"客户端已连接: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self._process_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端已断开连接: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"处理客户端消息时出错: {e}")
            logger.error(traceback.format_exc())
        finally:
            # 清理客户端连接
            await self._cleanup_client(websocket)
    
    async def _process_message(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """
        处理客户端消息
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        message : str
            客户端消息
        """
        try:
            data = json.loads(message)
            
            # 确保数据是一个字典
            if not isinstance(data, dict):
                await self._send_error(websocket, "无效的JSON格式，必须是一个对象")
                return
            
            if "method" not in data:
                await self._send_error(websocket, "无效的消息格式，缺少method字段")
                return
                
            method = data["method"].lower()
            params = data.get("params", {})
            id = data.get("id")
            
            # 根据方法类型处理
            if method == "subscribe":
                await self._handle_subscribe(websocket, params, id)
            elif method == "unsubscribe":
                await self._handle_unsubscribe(websocket, params, id)
            elif method == "auth":
                await self._handle_auth(websocket, params, id)
            else:
                await self._send_error(websocket, f"不支持的方法: {method}", id)
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "无效的JSON格式")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            logger.error(traceback.format_exc())
            await self._send_error(websocket, f"处理消息时出错: {str(e)}")
    
    async def _handle_subscribe(self, websocket: WebSocketServerProtocol, params: Dict[str, Any], id: Any) -> None:
        """
        处理订阅请求
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        params : Dict[str, Any]
            订阅参数
        id : Any
            请求ID
        """
        if "streams" not in params:
            await self._send_error(websocket, "缺少streams参数", id)
            return
            
        streams = params["streams"]
        if not isinstance(streams, list):
            streams = [streams]
            
        # 处理每个订阅流
        subscribed_streams = []
        error_streams = []
        
        for stream in streams:
            # 解析流类型和参数
            parts = stream.split('@')
            if len(parts) != 2:
                error_streams.append({"stream": stream, "error": "无效的流格式"})
                logger.warning(f"无效的流格式: {stream}")
                continue
                
            symbol_or_user, stream_type = parts
            
            # 处理市场数据流
            if stream_type in ["ticker", "depth", "kline", "trade"]:
                try:
                    self._subscribe_market(websocket, symbol_or_user, stream_type)
                    subscribed_streams.append(stream)
                    logger.info(f"成功订阅市场数据流: {stream}")
                except Exception as e:
                    error_msg = f"订阅失败: {str(e)}"
                    error_streams.append({"stream": stream, "error": error_msg})
                    logger.error(f"订阅市场数据流失败: {stream}, 错误: {str(e)}")
            
            # 处理用户数据流（需要认证）
            elif stream_type in ["account", "order", "trade"]:
                user_id = self.clients[websocket].get("user_id")
                if not user_id:
                    error_msg = "用户数据流需要认证"
                    error_streams.append({"stream": stream, "error": error_msg})
                    logger.warning(f"订阅用户数据流失败: {stream}, 错误: 未认证")
                    continue
                    
                if user_id != symbol_or_user:
                    error_msg = "无权订阅其他用户的数据"
                    error_streams.append({"stream": stream, "error": error_msg})
                    logger.warning(f"订阅用户数据流失败: {stream}, 错误: 权限不足")
                    continue
                
                try:    
                    self._subscribe_user(websocket, user_id, stream_type)
                    subscribed_streams.append(stream)
                    logger.info(f"成功订阅用户数据流: {stream}")
                except Exception as e:
                    error_msg = f"订阅失败: {str(e)}"
                    error_streams.append({"stream": stream, "error": error_msg})
                    logger.error(f"订阅用户数据流失败: {stream}, 错误: {str(e)}")
            
            else:
                error_msg = f"不支持的流类型: {stream_type}"
                error_streams.append({"stream": stream, "error": error_msg})
                logger.warning(f"不支持的流类型: {stream_type}")
        
        # 发送响应
        if id is not None:
            if len(error_streams) > 0:
                # 如果有错误，但也有成功订阅的流，发送部分成功响应
                if len(subscribed_streams) > 0:
                    await self._send_response(websocket, {
                        "result": "partial",
                        "streams": subscribed_streams,
                        "errors": error_streams
                    }, id)
                # 如果全部失败，发送错误响应，包含详细错误信息
                else:
                    # 创建详细错误消息
                    error_details = ", ".join([f"{e['stream']}: {e['error']}" for e in error_streams])
                    await self._send_error(websocket, error_details, id)
            # 如果全部成功，发送成功响应
            elif len(subscribed_streams) > 0:
                await self._send_response(websocket, {"result": "success", "streams": subscribed_streams}, id)
            # 如果没有处理任何流
            else:
                await self._send_error(websocket, "没有成功订阅任何流", id)
    
    async def _handle_unsubscribe(self, websocket: WebSocketServerProtocol, params: Dict[str, Any], id: Any) -> None:
        """
        处理取消订阅请求
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        params : Dict[str, Any]
            取消订阅参数
        id : Any
            请求ID
        """
        if "streams" not in params:
            # 取消所有订阅
            streams = list(self.clients[websocket]["subscriptions"])
            self.clients[websocket]["subscriptions"].clear()
            
            # 从所有订阅中移除
            for stream in streams:
                parts = stream.split('@')
                if len(parts) != 2:
                    continue
                    
                symbol_or_user, stream_type = parts
                
                if stream_type in ["ticker", "depth", "kline", "trade"]:
                    self._unsubscribe_market(websocket, symbol_or_user, stream_type)
                elif stream_type in ["account", "order", "trade"]:
                    self._unsubscribe_user(websocket, symbol_or_user, stream_type)
        else:
            # 取消指定的订阅
            streams = params["streams"]
            if not isinstance(streams, list):
                streams = [streams]
                
            for stream in streams:
                # 从客户端订阅列表中移除
                if stream in self.clients[websocket]["subscriptions"]:
                    self.clients[websocket]["subscriptions"].remove(stream)
                
                # 解析流类型和参数
                parts = stream.split('@')
                if len(parts) != 2:
                    continue
                    
                symbol_or_user, stream_type = parts
                
                # 处理市场数据流
                if stream_type in ["ticker", "depth", "kline", "trade"]:
                    self._unsubscribe_market(websocket, symbol_or_user, stream_type)
                
                # 处理用户数据流
                elif stream_type in ["account", "order", "trade"]:
                    self._unsubscribe_user(websocket, symbol_or_user, stream_type)
                    
        # 发送取消订阅成功响应
        if id is not None:
            await self._send_response(websocket, {"result": "success"}, id)
    
    async def _handle_auth(self, websocket: WebSocketServerProtocol, params: Dict[str, Any], id: Any) -> None:
        """
        处理认证请求
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        params : Dict[str, Any]
            认证参数
        id : Any
            请求ID
        """
        if "api_key" not in params:
            await self._send_error(websocket, "缺少api_key参数", id)
            return
            
        api_key = params["api_key"]
        
        # 仅验证API密钥格式（UUID格式）
        try:
            import uuid
            uuid_obj = uuid.UUID(api_key)
            
            # 尝试获取用户ID
            user_id = self.get_user_id_from_api_key(api_key)
            
            # 如果密钥格式正确但不存在，使用固定的backtest_user
            if not user_id:
                logger.info(f"API密钥格式正确但不存在: {api_key}，使用backtest_user")
                user_id = "backtest_user"
                
            # 更新客户端信息
            self.clients[websocket]["user_id"] = user_id
            
            # 发送认证成功响应
            await self._send_response(websocket, {"result": "success", "user_id": user_id}, id)
        except ValueError:
            logger.warning(f"认证失败: 无效的API密钥格式 {api_key}")
            await self._send_error(websocket, "无效的API密钥格式", id)
    
    def _subscribe_market(self, websocket: WebSocketServerProtocol, symbol: str, stream_type: str) -> None:
        """
        订阅市场数据
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        symbol : str
            交易对
        stream_type : str
            流类型
        """
        # 创建订阅键
        key = f"{symbol}@{stream_type}"
        
        # 添加到全局订阅列表
        if key not in self.market_subscriptions:
            self.market_subscriptions[key] = set()
        self.market_subscriptions[key].add(websocket)
        
        # 添加到客户端的订阅列表
        if websocket in self.clients:
            self.clients[websocket]["subscriptions"].add(key)
        
        logger.info(f"客户端 {websocket.remote_address} 订阅市场数据: {key}")
    
    def _unsubscribe_market(self, websocket: WebSocketServerProtocol, symbol: str, stream_type: str) -> None:
        """
        取消订阅市场数据
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        symbol : str
            交易对
        stream_type : str
            流类型
        """
        key = f"{symbol}@{stream_type}"
        
        # 从全局订阅列表中移除
        if key in self.market_subscriptions and websocket in self.market_subscriptions[key]:
            self.market_subscriptions[key].remove(websocket)
            
            # 如果没有订阅者，删除订阅项
            if not self.market_subscriptions[key]:
                del self.market_subscriptions[key]
        
        # 从客户端的订阅列表中移除
        if websocket in self.clients and key in self.clients[websocket]["subscriptions"]:
            self.clients[websocket]["subscriptions"].remove(key)
                
        logger.info(f"客户端 {websocket.remote_address} 取消订阅市场数据: {key}")
    
    def _subscribe_user(self, websocket: WebSocketServerProtocol, user_id: str, stream_type: str) -> None:
        """
        订阅用户数据
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        user_id : str
            用户ID
        stream_type : str
            流类型
        """
        key = f"{user_id}@{stream_type}"
        
        # 添加到全局用户订阅列表
        if key not in self.user_subscriptions:
            self.user_subscriptions[key] = set()
        self.user_subscriptions[key].add(websocket)
        
        # 添加到客户端的订阅列表
        if websocket in self.clients:
            self.clients[websocket]["subscriptions"].add(key)
        
        logger.info(f"客户端 {websocket.remote_address} 订阅用户数据: {key}")
    
    def _unsubscribe_user(self, websocket: WebSocketServerProtocol, user_id: str, stream_type: str) -> None:
        """
        取消订阅用户数据
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        user_id : str
            用户ID
        stream_type : str
            流类型
        """
        key = f"{user_id}@{stream_type}"
        
        # 从全局用户订阅列表中移除
        if key in self.user_subscriptions and websocket in self.user_subscriptions[key]:
            self.user_subscriptions[key].remove(websocket)
            
            # 如果没有订阅者，删除订阅项
            if not self.user_subscriptions[key]:
                del self.user_subscriptions[key]
        
        # 从客户端的订阅列表中移除
        if websocket in self.clients and key in self.clients[websocket]["subscriptions"]:
            self.clients[websocket]["subscriptions"].remove(key)
                
        logger.info(f"客户端 {websocket.remote_address} 取消订阅用户数据: {key}")
    
    async def _cleanup_client(self, websocket: WebSocketServerProtocol) -> None:
        """
        清理客户端连接
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        """
        # 先清理客户端的订阅信息
        if websocket in self.clients:
            client_info = self.clients[websocket]
            
            # 处理客户端的所有订阅
            for stream in list(client_info.get("subscriptions", set())):
                parts = stream.split('@')
                if len(parts) != 2:
                    continue
                    
                symbol_or_user, stream_type = parts
                
                # 取消市场数据订阅
                if stream_type in ["ticker", "depth", "kline", "trade"]:
                    self._unsubscribe_market(websocket, symbol_or_user, stream_type)
                    
                # 取消用户数据订阅
                elif stream_type in ["account", "order", "trade"]:
                    user_id = client_info.get("user_id")
                    if user_id:
                        self._unsubscribe_user(websocket, user_id, stream_type)
        
        # 确保从所有订阅中移除（备用清理）
        for key in list(self.market_subscriptions.keys()):
            if websocket in self.market_subscriptions[key]:
                self.market_subscriptions[key].remove(websocket)
                # 如果没有订阅者，删除订阅项
                if not self.market_subscriptions[key]:
                    del self.market_subscriptions[key]
                    
        for key in list(self.user_subscriptions.keys()):
            if websocket in self.user_subscriptions[key]:
                self.user_subscriptions[key].remove(websocket)
                # 如果没有订阅者，删除订阅项
                if not self.user_subscriptions[key]:
                    del self.user_subscriptions[key]
                    
        # 删除客户端信息
        if websocket in self.clients:
            del self.clients[websocket]
            
        logger.info(f"已清理客户端连接: {websocket.remote_address}")
    
    async def _send_response(self, websocket: WebSocketServerProtocol, data: Dict[str, Any], id: Any = None) -> None:
        """
        发送响应
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        data : Dict[str, Any]
            响应数据
        id : Any, optional
            请求ID, by default None
        """
        if id is not None:
            data["id"] = id
            
        try:
            await websocket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"发送响应失败: {e}")
    
    async def _send_error(self, websocket: WebSocketServerProtocol, message: str, id: Any = None) -> None:
        """
        发送错误响应
        
        Parameters
        ----------
        websocket : WebSocketServerProtocol
            WebSocket连接
        message : str
            错误消息
        id : Any, optional
            请求ID, by default None
        """
        error = {"error": message}
        if id is not None:
            error["id"] = id
            
        try:
            await websocket.send(json.dumps(error))
        except Exception as e:
            logger.error(f"发送错误响应失败: {e}")
    
    def _on_trade(self, trade: Trade) -> None:
        """
        成交事件处理
        
        Parameters
        ----------
        trade : Trade
            成交信息
        """
        # 创建成交消息
        trade_msg = {
            "stream": f"{trade.symbol}@trade",
            "data": {
                "e": "trade",              # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "s": trade.symbol,         # 交易对
                "t": trade.trade_id,       # 交易ID
                "p": str(trade.price),     # 价格
                "q": str(trade.quantity),  # 数量
                "b": trade.buy_order_id,   # 买方订单ID
                "a": trade.sell_order_id,  # 卖方订单ID
                "T": int(trade.timestamp * 1000),  # 成交时间
                "m": False                 # 买方是否为做市商
            }
        }
        
        # 发送成交消息到订阅者
        subscription_key = f"{trade.symbol}@trade"
        asyncio.create_task(self._broadcast_to_market_subscribers(subscription_key, trade_msg))
        
        # 更新订单簿深度并通知订阅者
        depth_key = f"{trade.symbol}@depth"
        if depth_key in self.market_subscriptions:
            order_book = self.matching_engine.get_order_book(trade.symbol)
            depth = order_book.get_depth()
            
            depth_msg = {
                "stream": depth_key,
                "data": {
                    "e": "depthUpdate",    # 事件类型
                    "E": int(time.time() * 1000),  # 事件时间
                    "s": trade.symbol,     # 交易对
                    "b": [[str(price), str(qty)] for price, qty in depth["bids"]],  # 买盘
                    "a": [[str(price), str(qty)] for price, qty in depth["asks"]]   # 卖盘
                }
            }
            
            asyncio.create_task(self._broadcast_to_market_subscribers(depth_key, depth_msg))
            
        # 发送用户订单更新消息
        if trade.buyer_user_id:
            order_key = f"{trade.buyer_user_id}@order"
            if order_key in self.user_subscriptions:
                order_msg = {
                    "stream": order_key,
                    "data": {
                        "e": "executionReport",  # 事件类型
                        "E": int(time.time() * 1000),  # 事件时间
                        "s": trade.symbol,     # 交易对
                        "c": "",               # 客户端订单ID（此处简化）
                        "i": trade.buy_order_id,  # 订单ID
                        "x": "TRADE",          # 当前执行类型
                        "X": "PARTIALLY_FILLED",  # 当前订单状态（简化）
                        "p": str(trade.price), # 价格
                        "q": str(trade.quantity),  # 数量
                        "z": str(trade.quantity),  # 累计成交数量（简化）
                        "T": int(trade.timestamp * 1000)  # 成交时间
                    }
                }
                
                asyncio.create_task(self._broadcast_to_user_subscribers(order_key, order_msg))
                
        if trade.seller_user_id:
            order_key = f"{trade.seller_user_id}@order"
            if order_key in self.user_subscriptions:
                order_msg = {
                    "stream": order_key,
                    "data": {
                        "e": "executionReport",  # 事件类型
                        "E": int(time.time() * 1000),  # 事件时间
                        "s": trade.symbol,     # 交易对
                        "c": "",               # 客户端订单ID（此处简化）
                        "i": trade.sell_order_id,  # 订单ID
                        "x": "TRADE",          # 当前执行类型
                        "X": "PARTIALLY_FILLED",  # 当前订单状态（简化）
                        "p": str(trade.price), # 价格
                        "q": str(trade.quantity),  # 数量
                        "z": str(trade.quantity),  # 累计成交数量（简化）
                        "T": int(trade.timestamp * 1000)  # 成交时间
                    }
                }
                
                asyncio.create_task(self._broadcast_to_user_subscribers(order_key, order_msg))
    
    def _on_account_update(self, user_id: str, account_snapshot: Dict[str, Any]) -> None:
        """
        账户更新事件处理
        
        Parameters
        ----------
        user_id : str
            用户ID
        account_snapshot : Dict[str, Any]
            账户快照
        """
        # 创建账户更新消息
        account_msg = {
            "stream": f"{user_id}@account",
            "data": {
                "e": "outboundAccountPosition",  # 事件类型
                "E": int(time.time() * 1000),   # 事件时间
                "u": int(time.time() * 1000),   # 账户更新时间
                "B": []                         # 余额
            }
        }
        
        # 添加余额信息
        for asset, balance in account_snapshot["balances"].items():
            account_msg["data"]["B"].append({
                "a": asset,              # 资产名称
                "f": str(balance["free"]),  # 可用余额
                "l": str(balance["locked"])  # 锁定余额
            })
            
        # 发送账户更新消息到订阅者
        account_key = f"{user_id}@account"
        asyncio.create_task(self._broadcast_to_user_subscribers(account_key, account_msg))
    
    async def _broadcast_to_market_subscribers(self, subscription_key: str, message: Dict[str, Any]) -> None:
        """
        广播消息到市场数据订阅者
        
        Parameters
        ----------
        subscription_key : str
            订阅键
        message : Dict[str, Any]
            消息内容
        """
        if subscription_key not in self.market_subscriptions:
            return
            
        # 获取订阅者列表
        subscribers = list(self.market_subscriptions[subscription_key])
        
        # 广播消息
        for websocket in subscribers:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"向客户端 {websocket.remote_address} 发送消息失败: {e}")
                # 出错的连接将在下一次客户端交互时清理
    
    async def _broadcast_to_user_subscribers(self, subscription_key: str, message: Dict[str, Any]) -> None:
        """
        广播消息到用户数据订阅者
        
        Parameters
        ----------
        subscription_key : str
            订阅键
        message : Dict[str, Any]
            消息内容
        """
        if subscription_key not in self.user_subscriptions:
            return
            
        # 获取订阅者列表
        subscribers = list(self.user_subscriptions[subscription_key])
        
        # 广播消息
        for websocket in subscribers:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"向客户端 {websocket.remote_address} 发送消息失败: {e}")
                # 出错的连接将在下一次客户端交互时清理