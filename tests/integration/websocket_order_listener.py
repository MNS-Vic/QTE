#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket订单监听器
为测试提供可靠的订单状态监听和验证机制
"""
import asyncio
import json
import time
import logging
from unittest.mock import MagicMock
from typing import Dict, List, Set, Optional, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketOrderListener:
    """
    WebSocket订单监听器类
    提供订单状态监听、验证和异步等待功能
    """
    
    def __init__(self, websocket_server, user_id):
        """
        初始化WebSocket订单监听器
        
        Parameters
        ----------
        websocket_server : ExchangeWebSocketServer
            WebSocket服务器实例
        user_id : str
            用户ID
        """
        self.websocket_server = websocket_server
        self.user_id = user_id
        self.mock_websocket = MagicMock()
        self.mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 监听的订单相关事件
        self.events = {
            "done": asyncio.Event(),  # 完成事件
            "order_events": {},      # 订单事件字典
        }
        
        # 接收到的消息
        self.received_messages = []
        
        # 设置模拟的send方法
        async def mock_send(message):
            logger.debug(f"收到消息: {message[:200]}...")
            data = json.loads(message)
            self.received_messages.append(data)
            
            # 检查订单状态更新
            if (data.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"):
                order_data = data.get("data", {}).get("o", {})
                order_id = order_data.get("i")
                update_type = order_data.get("x")
                status = order_data.get("X")
                
                # 记录订单状态和更新类型
                self._set_order_event(order_id, f"update_type_{update_type}")
                self._set_order_event(order_id, f"status_{status}")
                
                # 检查是否达到最终状态
                if order_id in self.events.get("final_status_keys", {}):
                    final_key = self.events["final_status_keys"][order_id]
                    if final_key == f"status_{status}":
                        self.events["done"].set()
        
        self.mock_websocket.send = mock_send
        
        # 初始化客户端信息
        self.websocket_server.clients[self.mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 模拟用户订阅订单更新
        self.subscription_key = f"{user_id}@order"
        if self.subscription_key not in self.websocket_server.user_subscriptions:
            self.websocket_server.user_subscriptions[self.subscription_key] = set()
        self.websocket_server.user_subscriptions[self.subscription_key].add(self.mock_websocket)
    
    def _set_order_event(self, order_id: str, event_key: str) -> None:
        """
        设置订单事件
        
        Parameters
        ----------
        order_id : str
            订单ID
        event_key : str
            事件键名
        """
        if order_id not in self.events["order_events"]:
            self.events["order_events"][order_id] = {}
        
        if event_key not in self.events["order_events"][order_id]:
            self.events["order_events"][order_id][event_key] = asyncio.Event()
        
        # 设置事件
        self.events["order_events"][order_id][event_key].set()
    
    def _get_order_event(self, order_id: str, event_key: str) -> Optional[asyncio.Event]:
        """
        获取订单事件
        
        Parameters
        ----------
        order_id : str
            订单ID
        event_key : str
            事件键名
            
        Returns
        -------
        Optional[asyncio.Event]
            订单事件，不存在则返回None
        """
        if order_id not in self.events["order_events"]:
            return None
        
        return self.events["order_events"][order_id].get(event_key)
    
    def watch_order_status(self, order_id: str, update_types: List[str], 
                         statuses: List[str], final_status: str) -> None:
        """
        监视订单状态
        
        Parameters
        ----------
        order_id : str
            订单ID
        update_types : List[str]
            需要监听的更新类型列表
        statuses : List[str]
            需要监听的状态列表
        final_status : str
            最终期望状态
        """
        # 初始化订单事件字典
        if order_id not in self.events["order_events"]:
            self.events["order_events"][order_id] = {}
        
        # 创建更新类型事件
        for update_type in update_types:
            key = f"update_type_{update_type}"
            if key not in self.events["order_events"][order_id]:
                self.events["order_events"][order_id][key] = asyncio.Event()
        
        # 创建状态事件
        for status in statuses:
            key = f"status_{status}"
            if key not in self.events["order_events"][order_id]:
                self.events["order_events"][order_id][key] = asyncio.Event()
        
        # 设置最终状态
        if "final_status_keys" not in self.events:
            self.events["final_status_keys"] = {}
        self.events["final_status_keys"][order_id] = f"status_{final_status}"
    
    async def wait_for_update_type(self, order_id: str, update_type: str, 
                               timeout: float = 5.0) -> bool:
        """
        等待订单更新类型
        
        Parameters
        ----------
        order_id : str
            订单ID
        update_type : str
            更新类型
        timeout : float, optional
            超时时间（秒）, by default 5.0
            
        Returns
        -------
        bool
            是否收到更新类型
        """
        event_key = f"update_type_{update_type}"
        event = self._get_order_event(order_id, event_key)
        
        if event is None:
            logger.warning(f"订单 {order_id} 未设置 {event_key} 事件")
            return False
            
        try:
            # 使用wait_for避免无限等待
            await asyncio.wait_for(event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"等待订单 {order_id} 的 {update_type} 更新类型超时")
            return False
    
    async def wait_for_status(self, order_id: str, status: str, 
                          timeout: float = 5.0) -> bool:
        """
        等待订单状态
        
        Parameters
        ----------
        order_id : str
            订单ID
        status : str
            订单状态
        timeout : float, optional
            超时时间（秒）, by default 5.0
            
        Returns
        -------
        bool
            是否收到状态
        """
        event_key = f"status_{status}"
        event = self._get_order_event(order_id, event_key)
        
        if event is None:
            logger.warning(f"订单 {order_id} 未设置 {event_key} 事件")
            return False
            
        try:
            # 使用wait_for避免无限等待
            await asyncio.wait_for(event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"等待订单 {order_id} 的 {status} 状态超时")
            return False
    
    async def wait_for_completion(self, timeout: float = 10.0) -> bool:
        """
        等待所有订单达到最终状态
        
        Parameters
        ----------
        timeout : float, optional
            超时时间（秒）, by default 10.0
            
        Returns
        -------
        bool
            是否所有订单都达到最终状态
        """
        try:
            # 创建超时任务
            async def timeout_task():
                await asyncio.sleep(timeout)
                if not self.events["done"].is_set():
                    logger.warning(f"等待完成超时，强制设置完成事件")
                    self.events["done"].set()
            
            # 启动超时任务
            timeout_future = asyncio.create_task(timeout_task())
            
            # 等待完成事件
            await self.events["done"].wait()
            
            # 取消超时任务
            timeout_future.cancel()
            
            # 检查是否由于超时而完成
            result = all(self._check_order_final_status(order_id) 
                        for order_id in self.events.get("final_status_keys", {}))
            
            return result
        except Exception as e:
            logger.error(f"等待完成时发生错误: {e}")
            return False
    
    def _check_order_final_status(self, order_id: str) -> bool:
        """
        检查订单是否达到最终状态
        
        Parameters
        ----------
        order_id : str
            订单ID
            
        Returns
        -------
        bool
            是否达到最终状态
        """
        if "final_status_keys" not in self.events or order_id not in self.events["final_status_keys"]:
            return False
            
        final_key = self.events["final_status_keys"][order_id]
        event = self._get_order_event(order_id, final_key)
        
        return event is not None and event.is_set()
    
    def cleanup(self) -> None:
        """
        清理资源
        """
        # 清理订阅
        if self.subscription_key in self.websocket_server.user_subscriptions:
            self.websocket_server.user_subscriptions[self.subscription_key].discard(self.mock_websocket)
        
        # 清理客户端
        if self.websocket_server.clients.get(self.mock_websocket):
            del self.websocket_server.clients[self.mock_websocket]
            
        logger.info("WebSocket订单监听器资源已清理")