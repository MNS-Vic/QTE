#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
REST API服务器 - 模拟交易所REST API接口
"""
import logging
import json
import uuid
import time
import threading
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union, Tuple
from flask import Flask, request, jsonify, Response
from werkzeug.serving import make_server

# 导入匹配引擎和账户管理器
from qte.exchange.matching.matching_engine import MatchingEngine, Order, OrderSide, OrderType, OrderStatus
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.rest_api.request_validator import RequestValidator

logger = logging.getLogger("RESTServer")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ExchangeRESTServer:
    """交易所REST API服务器"""
    
    def __init__(self, matching_engine: MatchingEngine, account_manager: AccountManager, 
                host: str = "localhost", port: int = 5000):
        """
        初始化REST API服务器
        
        Parameters
        ----------
        matching_engine : MatchingEngine
            撮合引擎
        account_manager : AccountManager
            账户管理器
        host : str, optional
            主机地址, by default "localhost"
        port : int, optional
            端口, by default 5000
        """
        self.matching_engine = matching_engine
        self.account_manager = account_manager
        self.host = host
        self.port = port
        
        # 创建Flask应用
        self.app = Flask(__name__)
        self.server = None
        self.server_thread = None
        
        # API密钥管理
        self.api_keys: Dict[str, str] = {}  # API密钥 -> 用户ID
        
        # 注册路由
        self._register_routes()
        
        logger.info(f"REST API服务器已初始化: {host}:{port}")
    
    def _register_routes(self) -> None:
        """注册API路由"""
        # 市场数据接口
        self.app.route('/api/v1/ping', methods=['GET'])(self._ping)
        self.app.route('/api/v1/time', methods=['GET'])(self._server_time)
        self.app.route('/api/v1/ticker/price', methods=['GET'])(self._ticker_price)
        self.app.route('/api/v1/ticker/24hr', methods=['GET'])(self._ticker_24hr)
        self.app.route('/api/v1/depth', methods=['GET'])(self._order_book)
        self.app.route('/api/v1/trades', methods=['GET'])(self._recent_trades)
        self.app.route('/api/v1/klines', methods=['GET'])(self._klines)
        
        # 交易接口
        self.app.route('/api/v1/order', methods=['POST'])(self._create_order)
        self.app.route('/api/v1/order', methods=['DELETE'])(self._cancel_order)
        self.app.route('/api/v1/order', methods=['GET'])(self._get_order)
        self.app.route('/api/v1/openOrders', methods=['GET'])(self._get_open_orders)
        self.app.route('/api/v1/allOrders', methods=['GET'])(self._get_all_orders)
        
        # 账户接口
        self.app.route('/api/v1/account', methods=['GET'])(self._get_account)
        self.app.route('/api/v1/myTrades', methods=['GET'])(self._get_my_trades)
        
        # 测试接口
        self.app.route('/api/v1/deposit', methods=['POST'])(self._deposit)
        self.app.route('/api/v1/withdraw', methods=['POST'])(self._withdraw)
    
    def start(self) -> bool:
        """
        启动服务器
        
        Returns
        -------
        bool
            是否成功启动
        """
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("服务器已经运行")
            return False
            
        try:
            self.server = make_server(self.host, self.port, self.app)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"REST API服务器已启动: http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"启动服务器失败: {e}")
            return False
    
    def stop(self) -> bool:
        """
        停止服务器
        
        Returns
        -------
        bool
            是否成功停止
        """
        if not self.server:
            logger.warning("服务器未运行")
            return False
            
        try:
            self.server.shutdown()
            if self.server_thread:
                self.server_thread.join(timeout=5)
            
            logger.info("REST API服务器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止服务器失败: {e}")
            return False
    
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
    
    def _authenticate(self, api_key=None) -> Optional[str]:
        """
        验证API密钥并返回用户ID
        
        Parameters
        ----------
        api_key : str, optional
            API密钥，如不提供则从请求头获取, by default None
            
        Returns
        -------
        Optional[str]
            用户ID，认证失败返回None
        """
        api_key = api_key or request.headers.get('X-API-KEY')
        if not api_key:
            logger.warning("认证失败: 缺少X-API-KEY请求头")
            return None
            
        user_id = self.get_user_id_from_api_key(api_key)
        if not user_id:
            logger.warning(f"认证失败: 无效的API密钥 {api_key}")
            return None
            
        logger.debug(f"认证成功: 用户 {user_id}")
        return user_id
    
    def _error_response(self, message: str, status_code: int = 400) -> Response:
        """
        生成错误响应
        
        Parameters
        ----------
        message : str
            错误信息
        status_code : int, optional
            HTTP状态码, by default 400
            
        Returns
        -------
        Response
            错误响应
        """
        # 定义标准错误消息
        error_messages = {
            401: "未提供API密钥",
            403: "无权访问该资源",
            404: "请求的资源不存在",
            400: "请求参数无效"
        }
        
        # 如果是标准状态码且没有自定义消息，使用标准消息
        if status_code in error_messages and message is None:
            message = error_messages[status_code]
            
        return jsonify({"error": message}), status_code
    
    # 市场数据接口实现
    def _ping(self) -> Response:
        """测试连接"""
        return jsonify({"status": "ok"})
    
    def _server_time(self) -> Response:
        """获取服务器时间"""
        return jsonify({"serverTime": int(time.time() * 1000)})
    
    def _ticker_price(self) -> Response:
        """获取最新价格"""
        symbol = request.args.get('symbol')
        
        if symbol:
            # 获取单个交易对价格
            price = self.matching_engine.get_market_price(symbol)
            if price is None:
                return self._error_response(f"交易对 {symbol} 无价格数据", 404)
            return jsonify({"symbol": symbol, "price": str(price)})
        else:
            # 获取所有交易对价格
            result = []
            for symbol in self.matching_engine.order_books.keys():
                price = self.matching_engine.get_market_price(symbol)
                if price is not None:
                    result.append({"symbol": symbol, "price": str(price)})
            return jsonify(result)
    
    def _ticker_24hr(self) -> Response:
        """获取24小时价格变动统计"""
        symbol = request.args.get('symbol')
        
        # 实际项目中应该有更复杂的统计逻辑
        # 这里简化实现，返回一些基本数据
        
        if symbol:
            # 获取单个交易对统计
            order_book = self.matching_engine.get_order_book(symbol)
            last_price = self.matching_engine.get_market_price(symbol) or 0
            
            stats = {
                "symbol": symbol,
                "lastPrice": str(last_price),
                "volume": "0",  # 简化实现，应该累计24小时成交量
                "highPrice": "0",  # 简化实现，应该计算24小时最高价
                "lowPrice": "0",  # 简化实现，应该计算24小时最低价
                "priceChange": "0",  # 简化实现，应该计算24小时价格变动
                "priceChangePercent": "0"  # 简化实现，应该计算24小时价格变动百分比
            }
            return jsonify(stats)
        else:
            # 获取所有交易对统计
            result = []
            for symbol in self.matching_engine.order_books.keys():
                last_price = self.matching_engine.get_market_price(symbol) or 0
                stats = {
                    "symbol": symbol,
                    "lastPrice": str(last_price),
                    "volume": "0",
                    "highPrice": "0",
                    "lowPrice": "0",
                    "priceChange": "0",
                    "priceChangePercent": "0"
                }
                result.append(stats)
            return jsonify(result)
    
    def _order_book(self) -> Response:
        """获取订单簿"""
        symbol = request.args.get('symbol')
        limit = int(request.args.get('limit', 10))
        
        if not symbol:
            return self._error_response("必须指定交易对")
            
        order_book = self.matching_engine.get_order_book(symbol)
        depth = order_book.get_depth(limit)
        
        # 转换为字符串格式
        result = {
            "symbol": symbol,
            "bids": [[str(price), str(qty)] for price, qty in depth["bids"]],
            "asks": [[str(price), str(qty)] for price, qty in depth["asks"]]
        }
        
        return jsonify(result)
    
    def _recent_trades(self) -> Response:
        """获取最近成交"""
        symbol = request.args.get('symbol')
        limit = int(request.args.get('limit', 500))
        
        if not symbol:
            return self._error_response("必须指定交易对")
            
        # 获取最近的成交记录
        trades = []
        count = 0
        
        for trade in reversed(self.matching_engine.trades):
            if trade.symbol == symbol:
                trades.append({
                    "id": trade.trade_id,
                    "price": str(trade.price),
                    "qty": str(trade.quantity),
                    "time": int(trade.timestamp * 1000),
                    "isBuyerMaker": False  # 简化实现，应该根据订单方向判断
                })
                count += 1
                if count >= limit:
                    break
                    
        return jsonify(trades)
    
    def _klines(self) -> Response:
        """获取K线数据"""
        symbol = request.args.get('symbol')
        interval = request.args.get('interval', '1m')
        
        if not symbol:
            return self._error_response("必须指定交易对")
            
        # 实际项目中应该有K线数据生成逻辑
        # 这里返回简化的示例数据
        
        return jsonify([
            [
                1499040000000,      # 开盘时间
                "0.01634790",       # 开盘价
                "0.01640000",       # 最高价
                "0.01630000",       # 最低价
                "0.01639990",       # 收盘价
                "148976.11427815",  # 成交量
                1499644799999,      # 收盘时间
                "2434.19055334",    # 成交额
                308,                # 成交笔数
                "1756.87402397",    # 主动买入成交量
                "28.46694368",      # 主动买入成交额
                "0"                 # 忽略
            ]
        ])
    
    # 交易接口实现
    def _create_order(self) -> Response:
        """创建订单"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        # 获取请求参数
        data = request.json
        if not data:
            return self._error_response("无效的请求数据")
            
        symbol = data.get('symbol')
        side = data.get('side')
        type = data.get('type')
        quantity = data.get('quantity')
        price = data.get('price')
        client_order_id = data.get('newClientOrderId')
        
        # 使用请求验证器进行参数验证
        is_valid, error_msg = RequestValidator.validate_order_request(data)
        if not is_valid:
            return self._error_response(error_msg)
            
        try:
            # 转换参数
            quantity = Decimal(str(quantity))
            price = Decimal(str(price)) if price else None
                
            # 锁定资金
            if not self.account_manager.lock_funds_for_order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                amount=quantity,
                price=price
            ):
                return self._error_response("资金不足")
                
            try:
                # 创建订单
                order = Order(
                    order_id=str(uuid.uuid4()),
                    symbol=symbol,
                    side=OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL,
                    order_type=OrderType.LIMIT if type.upper() == 'LIMIT' else OrderType.MARKET,
                    quantity=float(quantity),
                    price=float(price) if price else None,
                    user_id=user_id,
                    client_order_id=client_order_id
                )
                
                # 提交订单到撮合引擎
                trades = self.matching_engine.place_order(order)
                
                # 处理成交
                for trade in trades:
                    # 获取买卖双方订单
                    buy_order = self.matching_engine.get_order_book(symbol).get_order(trade.buy_order_id) or order
                    sell_order = self.matching_engine.get_order_book(symbol).get_order(trade.sell_order_id) or order
                    
                    # 结算买方账户
                    if buy_order.user_id:
                        self.account_manager.settle_trade(
                            user_id=buy_order.user_id,
                            symbol=symbol,
                            side="BUY",
                            amount=Decimal(str(trade.quantity)),
                            price=Decimal(str(trade.price))
                        )
                        
                    # 结算卖方账户
                    if sell_order.user_id:
                        self.account_manager.settle_trade(
                            user_id=sell_order.user_id,
                            symbol=symbol,
                            side="SELL",
                            amount=Decimal(str(trade.quantity)),
                            price=Decimal(str(trade.price))
                        )
                
                # 构建响应
                result = {
                    "symbol": symbol,
                    "orderId": order.order_id,
                    "clientOrderId": client_order_id,
                    "transactTime": int(time.time() * 1000),
                    "price": str(price) if price else "0",
                    "origQty": str(quantity),
                    "executedQty": str(order.filled_quantity),
                    "status": order.status.value,
                    "type": type.upper(),
                    "side": side.upper()
                }
                
                return jsonify(result)
                
            except Exception as e:
                # 发生异常时，解锁已锁定的资金
                try:
                    self.account_manager.unlock_funds_for_order(
                        user_id=user_id,
                        symbol=symbol,
                        side=side,
                        amount=quantity,
                        price=price
                    )
                except Exception as unlock_e:
                    logger.error("解锁资金失败")
                    logger.error(f"解锁资金异常详情: {unlock_e}")
                
                # 重新抛出原始异常让外层catch处理
                raise
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            return self._error_response(f"创建订单失败: {str(e)}")
    
    def _cancel_order(self) -> Response:
        """取消订单"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        # 获取请求参数
        request_data = {
            'symbol': request.args.get('symbol'),
            'orderId': request.args.get('orderId'),
            'origClientOrderId': request.args.get('origClientOrderId')
        }
        
        # 使用请求验证器进行参数验证
        is_valid, error_msg = RequestValidator.validate_cancel_request(request_data)
        if not is_valid:
            return self._error_response(error_msg)
            
        symbol = request_data['symbol']
        order_id = request_data.get('orderId')
        client_order_id = request_data.get('origClientOrderId')
            
        # 获取订单簿
        order_book = self.matching_engine.get_order_book(symbol)
        
        # 查找订单
        order = None
        if order_id:
            order = order_book.get_order(order_id)
        elif client_order_id:
            # 搜索具有指定客户端ID的订单
            for o in order_book.order_map.values():
                if o.client_order_id == client_order_id and o.user_id == user_id:
                    order = o
                    break
                    
        if not order:
            return self._error_response("订单不存在", 404)
            
        # 验证所有权
        if order.user_id != user_id:
            return self._error_response("无权操作此订单", 403)
            
        # 解锁资金
        self.account_manager.unlock_funds_for_order(
            user_id=user_id,
            symbol=symbol,
            side="BUY" if order.side == OrderSide.BUY else "SELL",
            amount=Decimal(str(order.remaining_quantity)),
            price=Decimal(str(order.price)) if order.price else None
        )
        
        # 取消订单
        success = self.matching_engine.cancel_order(order.order_id, symbol)
        
        if success:
            result = {
                "symbol": symbol,
                "orderId": order.order_id,
                "clientOrderId": order.client_order_id,
                "status": "CANCELED"
            }
            return jsonify(result)
        else:
            return self._error_response("取消订单失败")
    
    def _get_order(self) -> Response:
        """查询订单"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        # 获取请求参数
        request_data = {
            'symbol': request.args.get('symbol'),
            'orderId': request.args.get('orderId'),
            'origClientOrderId': request.args.get('origClientOrderId')
        }
        
        # 使用请求验证器进行参数验证
        is_valid, error_msg = RequestValidator.validate_query_request(request_data)
        if not is_valid:
            return self._error_response(error_msg)
            
        symbol = request_data['symbol']
        order_id = request_data.get('orderId')
        client_order_id = request_data.get('origClientOrderId')
            
        # 获取订单簿
        order_book = self.matching_engine.get_order_book(symbol)
        
        # 查找订单
        order = None
        if order_id:
            order = order_book.get_order(order_id)
        elif client_order_id:
            # 搜索具有指定客户端ID的订单
            for o in order_book.order_map.values():
                if o.client_order_id == client_order_id and o.user_id == user_id:
                    order = o
                    break
                    
        if not order:
            return self._error_response("订单不存在", 404)
            
        # 验证所有权
        if order.user_id != user_id:
            return self._error_response("无权查看此订单", 403)
            
        # 构建响应
        result = {
            "symbol": order.symbol,
            "orderId": order.order_id,
            "clientOrderId": order.client_order_id,
            "price": str(order.price) if order.price else "0",
            "origQty": str(order.quantity),
            "executedQty": str(order.filled_quantity),
            "status": order.status.value,
            "type": order.order_type.value,
            "side": order.side.value,
            "time": int(order.timestamp * 1000)
        }
        
        return jsonify(result)
    
    def _get_open_orders(self) -> Response:
        """查询当前挂单"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        symbol = request.args.get('symbol')
        
        result = []
        
        # 如果指定了交易对，只查询该交易对
        if symbol:
            order_books = [self.matching_engine.get_order_book(symbol)]
        else:
            # 否则查询所有交易对
            order_books = self.matching_engine.order_books.values()
            
        # 从所有相关订单簿中查找用户的挂单
        for order_book in order_books:
            for order in order_book.order_map.values():
                if order.user_id == user_id and order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]:
                    result.append({
                        "symbol": order.symbol,
                        "orderId": order.order_id,
                        "clientOrderId": order.client_order_id,
                        "price": str(order.price) if order.price else "0",
                        "origQty": str(order.quantity),
                        "executedQty": str(order.filled_quantity),
                        "status": order.status.value,
                        "type": order.order_type.value,
                        "side": order.side.value,
                        "time": int(order.timestamp * 1000)
                    })
                    
        return jsonify(result)
    
    def _get_all_orders(self) -> Response:
        """查询所有订单"""
        # 实际项目中应该有订单历史记录存储
        # 这里简化返回当前挂单
        return self._get_open_orders()
    
    # 账户接口实现
    def _get_account(self) -> Response:
        """查询账户信息"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        account = self.account_manager.get_account(user_id)
        if not account:
            return self._error_response("账户不存在", 404)
            
        # 构建响应
        balances = []
        for asset, balance in account.balances.items():
            balances.append({
                "asset": asset,
                "free": str(balance.free),
                "locked": str(balance.locked)
            })
            
        result = {
            "accountId": user_id,
            "balances": balances
        }
        
        return jsonify(result)
    
    def _get_my_trades(self) -> Response:
        """查询用户交易历史"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        symbol = request.args.get('symbol')
        limit = int(request.args.get('limit', 500))
        
        if not symbol:
            return self._error_response("必须指定交易对")
            
        # 查找用户在指定交易对上的所有交易
        trades = []
        count = 0
        
        for trade in reversed(self.matching_engine.trades):
            if trade.symbol == symbol and (trade.buyer_user_id == user_id or trade.seller_user_id == user_id):
                trades.append({
                    "id": trade.trade_id,
                    "orderId": trade.buy_order_id if trade.buyer_user_id == user_id else trade.sell_order_id,
                    "price": str(trade.price),
                    "qty": str(trade.quantity),
                    "quoteQty": str(float(trade.price) * float(trade.quantity)),
                    "time": int(trade.timestamp * 1000),
                    "isBuyer": trade.buyer_user_id == user_id,
                    "isMaker": False  # 简化实现，应该根据订单类型判断
                })
                count += 1
                if count >= limit:
                    break
                    
        return jsonify(trades)
    
    # 测试接口实现
    def _deposit(self) -> Response:
        """充值（测试用）"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        data = request.json
        if not data:
            return self._error_response("无效的请求数据")
            
        asset = data.get('asset')
        amount = data.get('amount')
        
        if not asset or not amount:
            return self._error_response("缺少必要参数")
            
        try:
            amount = Decimal(str(amount))
            
            account = self.account_manager.get_account(user_id)
            if not account:
                return self._error_response("账户不存在", 404)
                
            success = account.deposit(asset, amount)
            
            if success:
                return jsonify({"status": "ok", "message": f"成功充值 {amount} {asset}"})
            else:
                return self._error_response("充值失败")
                
        except Exception as e:
            logger.error(f"充值失败: {e}")
            return self._error_response(f"充值失败: {str(e)}")
    
    def _withdraw(self) -> Response:
        """提现（测试用）"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("未认证", 401)
            
        data = request.json
        if not data:
            return self._error_response("无效的请求数据")
            
        asset = data.get('asset')
        amount = data.get('amount')
        
        if not asset or not amount:
            return self._error_response("缺少必要参数")
            
        try:
            amount = Decimal(str(amount))
            
            account = self.account_manager.get_account(user_id)
            if not account:
                return self._error_response("账户不存在", 404)
                
            success = account.withdraw(asset, amount)
            
            if success:
                return jsonify({"status": "ok", "message": f"成功提现 {amount} {asset}"})
            else:
                return self._error_response("提现失败，余额不足")
                
        except Exception as e:
            logger.error(f"提现失败: {e}")
            return self._error_response(f"提现失败: {str(e)}")