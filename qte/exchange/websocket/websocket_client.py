#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket客户端 - 用于连接交易所WebSocket接口
"""
import json
import logging
import asyncio
import time
from typing import Dict, List, Set, Any, Optional, Callable, Awaitable
import websockets

logger = logging.getLogger("WebSocketClient")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ExchangeWebSocketClient:
    """交易所WebSocket客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 8765, api_key: Optional[str] = None):
        """
        初始化WebSocket客户端
        
        Parameters
        ----------
        host : str, optional
            主机地址, by default "localhost"
        port : int, optional
            端口, by default 8765
        api_key : Optional[str], optional
            API密钥, by default None
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.ws_url = f"ws://{host}:{port}"
        
        # 连接状态
        self.connection = None
        self.connected = False
        self.user_id = None
        
        # 订阅和回调
        self.subscriptions: Set[str] = set()
        self.message_callbacks: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        
        # 请求ID和响应
        self.request_id = 0
        self.responses: Dict[str, Any] = {}
        self.response_events: Dict[str, asyncio.Event] = {}
        
        logger.info(f"WebSocket客户端已初始化: {self.ws_url}")
    
    async def connect(self) -> bool:
        """
        连接到WebSocket服务器
        
        Returns
        -------
        bool
            是否成功连接
        """
        if self.connected:
            logger.warning("已经连接到WebSocket服务器")
            return True
            
        try:
            self.connection = await websockets.connect(self.ws_url)
            self.connected = True
            
            # 启动消息处理任务
            asyncio.create_task(self._message_handler())
            
            logger.info(f"已连接到WebSocket服务器: {self.ws_url}")
            
            # 如果提供了API密钥，自动认证
            if self.api_key:
                auth_success = await self.authenticate(self.api_key)
                if not auth_success:
                    logger.error("自动认证失败")
                    await self.disconnect()
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"连接到WebSocket服务器失败: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """
        断开与WebSocket服务器的连接
        
        Returns
        -------
        bool
            是否成功断开
        """
        if not self.connected or not self.connection:
            logger.warning("未连接到WebSocket服务器")
            return True
            
        try:
            await self.connection.close()
            self.connected = False
            self.connection = None
            self.subscriptions.clear()
            
            logger.info("已断开与WebSocket服务器的连接")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    async def authenticate(self, api_key: str) -> bool:
        """
        认证
        
        Parameters
        ----------
        api_key : str
            API密钥
            
        Returns
        -------
        bool
            是否认证成功
        """
        if not self.connected:
            logger.error("未连接到WebSocket服务器")
            return False
            
        request_id = self._get_next_request_id()
        auth_request = {
            "method": "auth",
            "params": {"api_key": api_key},
            "id": request_id
        }
        
        # 创建响应事件
        response_event = asyncio.Event()
        self.response_events[request_id] = response_event
        
        # 发送认证请求
        await self.connection.send(json.dumps(auth_request))
        
        # 等待响应
        await response_event.wait()
        
        # 处理响应
        response = self.responses.get(request_id)
        success = response and "result" in response and response["result"] == "success"
        
        if success:
            self.user_id = response.get("user_id")
            self.api_key = api_key
            logger.info(f"认证成功，用户ID: {self.user_id}")
        else:
            error_msg = response.get("error") if response else "未知错误"
            logger.error(f"认证失败: {error_msg}")
            
        # 清理
        del self.response_events[request_id]
        if request_id in self.responses:
            del self.responses[request_id]
            
        return success
    
    async def subscribe(self, streams: List[str]) -> bool:
        """
        订阅数据流
        
        Parameters
        ----------
        streams : List[str]
            数据流列表，格式如：["BTCUSDT@trade", "user123@account"]
            
        Returns
        -------
        bool
            是否订阅成功
        """
        if not self.connected:
            logger.error("未连接到WebSocket服务器")
            return False
            
        request_id = self._get_next_request_id()
        subscribe_request = {
            "method": "subscribe",
            "params": {"streams": streams},
            "id": request_id
        }
        
        # 创建响应事件
        response_event = asyncio.Event()
        self.response_events[request_id] = response_event
        
        # 发送订阅请求
        await self.connection.send(json.dumps(subscribe_request))
        
        # 等待响应
        await response_event.wait()
        
        # 处理响应
        response = self.responses.get(request_id)
        success = response and "result" in response and response["result"] == "success"
        
        if success:
            subscribed_streams = response.get("streams", [])
            self.subscriptions.update(subscribed_streams)
            logger.info(f"订阅成功: {subscribed_streams}")
        else:
            error_msg = response.get("error") if response else "未知错误"
            logger.error(f"订阅失败: {error_msg}")
            
        # 清理
        del self.response_events[request_id]
        if request_id in self.responses:
            del self.responses[request_id]
            
        return success
    
    async def unsubscribe(self, streams: Optional[List[str]] = None) -> bool:
        """
        取消订阅数据流
        
        Parameters
        ----------
        streams : Optional[List[str]], optional
            数据流列表，如果为None则取消所有订阅, by default None
            
        Returns
        -------
        bool
            是否取消订阅成功
        """
        if not self.connected:
            logger.error("未连接到WebSocket服务器")
            return False
            
        request_id = self._get_next_request_id()
        unsubscribe_request = {
            "method": "unsubscribe",
            "id": request_id
        }
        
        if streams:
            unsubscribe_request["params"] = {"streams": streams}
            
        # 创建响应事件
        response_event = asyncio.Event()
        self.response_events[request_id] = response_event
        
        # 发送取消订阅请求
        await self.connection.send(json.dumps(unsubscribe_request))
        
        # 等待响应
        await response_event.wait()
        
        # 处理响应
        response = self.responses.get(request_id)
        success = response and "result" in response and response["result"] == "success"
        
        if success:
            if streams:
                for stream in streams:
                    if stream in self.subscriptions:
                        self.subscriptions.remove(stream)
                logger.info(f"已取消订阅: {streams}")
            else:
                self.subscriptions.clear()
                logger.info("已取消所有订阅")
        else:
            error_msg = response.get("error") if response else "未知错误"
            logger.error(f"取消订阅失败: {error_msg}")
            
        # 清理
        del self.response_events[request_id]
        if request_id in self.responses:
            del self.responses[request_id]
            
        return success
    
    def add_message_callback(self, stream: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        添加消息回调
        
        Parameters
        ----------
        stream : str
            数据流，如："BTCUSDT@trade"
        callback : Callable[[Dict[str, Any]], None]
            回调函数，接受消息数据作为参数
        """
        if stream not in self.message_callbacks:
            self.message_callbacks[stream] = []
        self.message_callbacks[stream].append(callback)
        logger.info(f"已添加{stream}的消息回调")
    
    def remove_message_callback(self, stream: str, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        移除消息回调
        
        Parameters
        ----------
        stream : str
            数据流
        callback : Callable[[Dict[str, Any]], None]
            回调函数
            
        Returns
        -------
        bool
            是否成功移除
        """
        if stream in self.message_callbacks and callback in self.message_callbacks[stream]:
            self.message_callbacks[stream].remove(callback)
            logger.info(f"已移除{stream}的消息回调")
            return True
        return False
    
    async def _message_handler(self) -> None:
        """
        消息处理循环
        """
        if not self.connected or not self.connection:
            logger.error("未连接到WebSocket服务器")
            return
            
        try:
            async for message in self.connection:
                await self._process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("与WebSocket服务器的连接已关闭")
            self.connected = False
            self.connection = None
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            
    async def _process_message(self, message: str) -> None:
        """
        处理接收到的消息
        
        Parameters
        ----------
        message : str
            消息内容
        """
        try:
            data = json.loads(message)
            
            # 处理响应消息
            if "id" in data:
                request_id = data["id"]
                self.responses[request_id] = data
                
                if request_id in self.response_events:
                    self.response_events[request_id].set()
                return
                
            # 处理数据流消息
            if "stream" in data:
                stream = data["stream"]
                stream_data = data.get("data", {})
                
                # 调用回调
                if stream in self.message_callbacks:
                    for callback in self.message_callbacks[stream]:
                        try:
                            callback(stream_data)
                        except Exception as e:
                            logger.error(f"执行{stream}的回调时出错: {e}")
                            
        except json.JSONDecodeError:
            logger.error(f"解析消息失败: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
    
    def _get_next_request_id(self) -> str:
        """
        获取下一个请求ID
        
        Returns
        -------
        str
            请求ID
        """
        self.request_id += 1
        return f"req_{self.request_id}" 