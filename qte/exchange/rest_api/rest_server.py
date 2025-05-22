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
# 导入所有错误码
from qte.exchange.rest_api.error_codes import *

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
        # 市场数据接口 - 公共API，无需认证
        # v3 API路由
        self.app.route('/api/v3/ping', methods=['GET'])(self._ping)
        self.app.route('/api/v3/time', methods=['GET'])(self._server_time)
        self.app.route('/api/v3/ticker/price', methods=['GET'])(self._ticker_price)
        self.app.route('/api/v3/ticker/24hr', methods=['GET'])(self._ticker_24hr)
        self.app.route('/api/v3/ticker/tradingDay', methods=['GET'])(self._trading_day)
        self.app.route('/api/v3/depth', methods=['GET'])(self._order_book)
        self.app.route('/api/v3/trades', methods=['GET'])(self._recent_trades)
        self.app.route('/api/v3/klines', methods=['GET'])(self._klines)
        self.app.route('/api/v3/avgPrice', methods=['GET'])(self._avg_price)
        
        # 交易接口 - 需要认证
        self.app.route('/api/v3/order', methods=['POST'])(self._create_order)
        self.app.route('/api/v3/order/test', methods=['POST'])(self._test_order)
        self.app.route('/api/v3/order', methods=['DELETE'])(self._cancel_order)
        self.app.route('/api/v3/order', methods=['GET'])(self._get_order)
        self.app.route('/api/v3/openOrders', methods=['GET'])(self._get_open_orders)
        self.app.route('/api/v3/allOrders', methods=['GET'])(self._get_all_orders)
        
        # 账户接口 - 需要认证
        self.app.route('/api/v3/account', methods=['GET'])(self._get_account)
        self.app.route('/api/v3/myTrades', methods=['GET'])(self._get_my_trades)
        self.app.route('/api/v3/account/commission', methods=['GET'])(self._get_commission)
        
        # 测试接口 - 需要认证
        self.app.route('/api/v3/deposit', methods=['POST'])(self._deposit)
        self.app.route('/api/v3/withdraw', methods=['POST'])(self._withdraw)
        
        # 保持向后兼容性的v1 API路由
        self.app.route('/api/v1/ping', methods=['GET'])(self._ping)
        self.app.route('/api/v1/time', methods=['GET'])(self._server_time)
        self.app.route('/api/v1/ticker/price', methods=['GET'])(self._ticker_price)
        self.app.route('/api/v1/ticker/24hr', methods=['GET'])(self._ticker_24hr)
        self.app.route('/api/v1/depth', methods=['GET'])(self._order_book)
        self.app.route('/api/v1/trades', methods=['GET'])(self._recent_trades)
        self.app.route('/api/v1/klines', methods=['GET'])(self._klines)
        
        self.app.route('/api/v1/order', methods=['POST'])(self._create_order)
        self.app.route('/api/v1/order', methods=['DELETE'])(self._cancel_order)
        self.app.route('/api/v1/order', methods=['GET'])(self._get_order)
        self.app.route('/api/v1/openOrders', methods=['GET'])(self._get_open_orders)
        self.app.route('/api/v1/allOrders', methods=['GET'])(self._get_all_orders)
        
        self.app.route('/api/v1/account', methods=['GET'])(self._get_account)
        self.app.route('/api/v1/myTrades', methods=['GET'])(self._get_my_trades)
        
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
        API认证
        
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
            logger.warning("认证失败: 未提供API密钥")
            return None
            
        # 验证API密钥
        try:
            user_id = self.get_user_id_from_api_key(api_key)
            if not user_id:
                logger.warning(f"认证失败: 无效的API密钥 {api_key[:8]}...")
                return None
                
            logger.debug(f"认证成功: 用户 {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"认证过程出错: {e}")
            return None
    
    def _error_response(self, message: str, error_code: int, status_code: int = 400):
        """统一的错误响应处理"""
        logger.error(f"Error response: msg='{message}', code={error_code}, http_status={status_code}")
        # 确保符合币安的错误响应格式: {"code": error_code_value, "msg": message_string}
        response = jsonify({"code": error_code, "msg": message})
        response.status_code = status_code
        return response
    
    # 市场数据接口实现
    def _ping(self):
        # return jsonify({"status": "ok"})
        # 按照币安API规范，ping成功应返回空对象 {}
        return jsonify({})
    
    def _server_time(self) -> Response:
        """获取服务器时间"""
        return jsonify({"serverTime": int(time.time() * 1000)})
    
    def _ticker_price(self) -> Response:
        """获取最新价格 (单个/多个/全部) - Binance compliant"""
        requested_symbol_param = request.args.get('symbol')
        requested_symbols_param = request.args.get('symbols')

        symbols_to_fetch = []
        # Determines if the final jsonify output should be a single object or an array.
        # True if 'symbol' param is used, False otherwise (for 'symbols' param or getting all tickers).
        return_single_object_for_output = False

        if requested_symbols_param is not None:  # Prioritize 'symbols' over 'symbol'
            try:
                parsed_symbols = json.loads(requested_symbols_param)
                if not isinstance(parsed_symbols, list):
                    return self._error_response("Parameter 'symbols' must be a JSON array.", INVALID_PARAM, 400)
                if not parsed_symbols:  # Empty list, e.g. symbols=[]
                    return self._error_response("Parameter 'symbols' cannot be an empty list.", INVALID_PARAM, 400)
                
                for s_idx, s_val in enumerate(parsed_symbols):
                    if not isinstance(s_val, str):
                        return self._error_response(f"All symbols in 'symbols' list must be strings. Found type '{type(s_val).__name__}' at index {s_idx}.", INVALID_PARAM, 400)
                
                symbols_to_fetch = parsed_symbols
                return_single_object_for_output = False # Output is an array for 'symbols' param
            except json.JSONDecodeError:
                return self._error_response("Parameter 'symbols' is malformed. Expected a JSON array string.", INVALID_PARAM, 400)
        
        elif requested_symbol_param is not None:
            # request.args.get always gives string, so no explicit type check needed for requested_symbol_param itself
            symbols_to_fetch = [requested_symbol_param]
            return_single_object_for_output = True # Output is a single object for 'symbol' param
        
        else:  # Neither 'symbol' nor 'symbols' provided, return all available symbols
            symbols_to_fetch = list(self.matching_engine.order_books.keys())
            return_single_object_for_output = False # Output is an array for all symbols

        collected_tickers = []
        # If symbols_to_fetch is empty at this point (e.g., from order_books.keys() and there are no books),
        # collected_tickers will remain empty, and an empty list [] will be returned if not return_single_object_for_output,
        # which is correct for "all symbols" if none exist.
        
        for sym_name in symbols_to_fetch:
            price = self.matching_engine.get_market_price(sym_name)
            if price is None:
                # If the symbol was explicitly requested (i.e., not part of a "get all available symbols"),
                # then it's an error according to Binance behavior.
                if requested_symbols_param is not None or requested_symbol_param is not None:
                    # UNKNOWN_SYMBOL should be -1121 as per Binance for "Invalid symbol"
                    return self._error_response(f"Invalid symbol: {sym_name}", UNKNOWN_SYMBOL, 400)
                else:
                    # For "get all available symbols", if a symbol from matching_engine.order_books.keys()
                    # somehow has no price (e.g., engine initialized it but no trades/quotes yet), we should skip it.
                    logger.warning(f"Symbol '{sym_name}' from all available symbols has no market price, skipping.")
                    continue
            collected_tickers.append({"symbol": sym_name, "price": str(price)})
        
        if return_single_object_for_output:
            # This path is for when 'symbol' param was used.
            # symbols_to_fetch should have contained exactly one symbol.
            if not collected_tickers:
                # This implies the single requested symbol was invalid and the error for UNKNOWN_SYMBOL
                # should have been raised within the loop. This is a fallback / defensive check.
                # The symbols_to_fetch list would contain the original invalid symbol name.
                return self._error_response(f"Invalid symbol: {symbols_to_fetch[0]}", UNKNOWN_SYMBOL, 400)
            return jsonify(collected_tickers[0])
        else:
            # This path is for 'symbols' param or "get all". Output is an array.
            # If "get all" was requested and no symbols with prices exist, an empty array is correctly returned.
            return jsonify(collected_tickers)
    
    def _ticker_24hr(self) -> Response:
        """获取24小时价格变动统计 (单个/多个/全部) - Binance compliant"""
        requested_symbol_param = request.args.get('symbol')
        requested_symbols_param = request.args.get('symbols')

        symbols_to_fetch = []
        return_single_object_for_output = False

        if requested_symbols_param is not None:
            try:
                parsed_symbols = json.loads(requested_symbols_param)
                if not isinstance(parsed_symbols, list):
                    return self._error_response("Parameter 'symbols' must be a JSON array.", INVALID_PARAM, 400)
                if not parsed_symbols:
                     return self._error_response("Parameter 'symbols' cannot be an empty list.", INVALID_PARAM, 400)
                for s_idx, s_val in enumerate(parsed_symbols):
                    if not isinstance(s_val, str):
                        return self._error_response(f"All symbols in 'symbols' list must be strings. Found type '{type(s_val).__name__}' at index {s_idx}.", INVALID_PARAM, 400)
                symbols_to_fetch = parsed_symbols
                return_single_object_for_output = False
            except json.JSONDecodeError:
                return self._error_response("Parameter 'symbols' is malformed. Expected a JSON array string.", INVALID_PARAM, 400)
        elif requested_symbol_param is not None:
            symbols_to_fetch = [requested_symbol_param]
            return_single_object_for_output = True
        else:
            symbols_to_fetch = list(self.matching_engine.order_books.keys())
            return_single_object_for_output = False

        collected_stats = []
        current_time_ms = int(time.time() * 1000)
        open_time_ms = current_time_ms - (24 * 60 * 60 * 1000) # 24 hours ago

        for sym_name in symbols_to_fetch:
            # Ensure symbol exists in the matching engine, otherwise it's an invalid symbol if explicitly requested.
            if sym_name not in self.matching_engine.order_books:
                if requested_symbols_param is not None or requested_symbol_param is not None:
                    return self._error_response(f"Invalid symbol: {sym_name}", UNKNOWN_SYMBOL, 400)
                else:
                    # If getting all symbols, skip unknown ones that might be in keys but not fully initialized
                    logger.warning(f"Symbol '{sym_name}' from all available symbols not found in order books, skipping for 24hr ticker.")
                    continue
            
            last_price = self.matching_engine.get_market_price(sym_name) or Decimal("0")
            # Placeholder values for other fields, to be fully implemented later.
            # The structure must match Binance's response.
            stats = {
                "symbol": sym_name,
                "priceChange": "0", # Placeholder
                "priceChangePercent": "0.000", # Placeholder, e.g., "-0.792"
                "weightedAvgPrice": str(last_price), # Simplified, should be volume-weighted
                "prevClosePrice": str(last_price), # Simplified, should be price 24h ago
                "lastPrice": str(last_price),
                "lastQty": "0", # Placeholder, quantity of last trade
                "bidPrice": str(self.matching_engine.get_best_bid(sym_name) or "0"),
                "bidQty": "0", # Placeholder, quantity of best bid
                "askPrice": str(self.matching_engine.get_best_ask(sym_name) or "0"),
                "askQty": "0", # Placeholder, quantity of best ask
                "openPrice": str(last_price), # Simplified, should be price at openTime
                "highPrice": str(last_price), # Simplified
                "lowPrice": str(last_price),  # Simplified
                "volume": "0", # Placeholder, total traded base asset volume
                "quoteVolume": "0", # Placeholder, total traded quote asset volume
                "openTime": open_time_ms,
                "closeTime": current_time_ms,
                "firstId": 0,  # Placeholder, first tradeId
                "lastId": 0,   # Placeholder, last tradeId
                "count": 0     # Placeholder, total number of trades
            }
            collected_stats.append(stats)

        if return_single_object_for_output:
            if not collected_stats:
                # Should have been caught by UNKNOWN_SYMBOL check inside loop for single requested symbol
                return self._error_response(f"Invalid symbol: {symbols_to_fetch[0]}", UNKNOWN_SYMBOL, 400)
            return jsonify(collected_stats[0])
        else:
            return jsonify(collected_stats)
    
    def _order_book(self) -> Response:
        """获取订单簿 - Binance compliant"""
        symbol = request.args.get('symbol')
        limit_str = request.args.get('limit')

        if not symbol:
            # Binance error: {"code":-1102,"msg":"Mandatory 'symbol' was not sent, was empty/null, or malformed."}
            return self._error_response("Mandatory 'symbol' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED , 400)
        
        # Validate symbol existence
        if symbol not in self.matching_engine.order_books:
            return self._error_response(f"Invalid symbol: {symbol}", UNKNOWN_SYMBOL, 400)

        allowed_limits = [5, 10, 20, 50, 100, 500, 1000, 5000]
        limit = 100 # Default Binance limit

        if limit_str is not None:
            try:
                limit_val = int(limit_str)
                if limit_val not in allowed_limits:
                    # Binance error: {"code":-1100,"msg":"Illegal characters found in parameter 'limit'; legal range is '5, 10, 20, 50, 100, 500, 1000, 5000'"}
                    # Or sometimes: {"code":-1128,"msg":"KEEPALIVED_TRADE_SERVICE_ERR_PARAM:limit:not in selection"} if using ws
                    return self._error_response(f"Illegal characters found in parameter 'limit'; legal values are '{allowed_limits}'", ILLEGAL_CHARS, 400) # Using general ILLEGAL_CHARS for now
                limit = limit_val
            except ValueError:
                 # Binance error: {"code":-1100,"msg":"Illegal characters found in parameter 'limit'; legal range is '5, 10, 20, 50, 100, 500, 1000, 5000'"}
                return self._error_response(f"Illegal characters found in parameter 'limit'. Expected an integer.", ILLEGAL_CHARS, 400)
            
        order_book = self.matching_engine.get_order_book(symbol)
        depth = order_book.get_depth(limit) # Matching engine's get_depth should handle the limit
        
        # Simulate lastUpdateId. In a real system, this would be tracked.
        # Using the timestamp of the latest trade for the symbol, or current time if no trades.
        last_trade_for_symbol = next((t for t in reversed(self.matching_engine.trades) if t.symbol == symbol), None)
        last_update_id = int(last_trade_for_symbol.timestamp * 1000) if last_trade_for_symbol else int(time.time() * 1000)

        result = {
            "lastUpdateId": last_update_id,
            "symbol": symbol, # Though not in Binance REST response for single symbol, it helps for consistency if we ever use it internally
            "bids": [[str(price), str(qty)] for price, qty in depth["bids"]],
            "asks": [[str(price), str(qty)] for price, qty in depth["asks"]]
        }
        # Binance REST API for depth does NOT include the symbol in the top-level dict if symbol is in query.
        # It does for websocket @depth streams. For consistency with REST, we might remove it here.
        # However, the plan states "Symbol (string, e.g. BTCUSDT) - QTE includes it, Binance does not for REST single symbol query",
        # implying we can keep it if it aligns with internal or broader QTE needs.
        # For strict Binance REST /api/v3/depth compliance, remove "symbol" key from result.
        # Let's stick to the plan and keep it for now, but note the discrepancy.
        # Decision: Remove for stricter compliance with Binance REST spec for this endpoint.
        if "symbol" in result: # Removing it as per strict Binance REST API for GET /api/v3/depth?symbol=X
            del result["symbol"]

        return jsonify(result)
    
    def _recent_trades(self) -> Response:
        """获取最近成交 - Binance compliant"""
        symbol = request.args.get('symbol')
        limit_str = request.args.get('limit')

        if not symbol:
            return self._error_response("Mandatory 'symbol' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        
        if symbol not in self.matching_engine.order_books:
            return self._error_response(f"Invalid symbol: {symbol}", UNKNOWN_SYMBOL, 400)

        limit = 500 # Default Binance limit for recent trades
        max_limit = 1000

        if limit_str is not None:
            try:
                limit_val = int(limit_str)
                if not (1 <= limit_val <= max_limit):
                    # Binance error for trades: {"code":-1100,"msg":"Illegal characters found in parameter 'limit'; legal range is '1-1000'"}
                    return self._error_response(f"Parameter 'limit' is out of bounds. Must be between 1 and {max_limit}.", ILLEGAL_CHARS, 400)
                limit = limit_val
            except ValueError:
                return self._error_response("Illegal characters found in parameter 'limit'. Expected an integer.", ILLEGAL_CHARS, 400)
            
        trades_data = []
        # Trades in matching_engine.trades are expected to be stored chronologically (oldest first)
        # So, we iterate in reverse to get the most recent ones.
        # The trade objects in self.matching_engine.trades should ideally have a unique integer ID.
        # For now, if trade.trade_id is not an int, we might need to assign one or handle it.

        count = 0
        for trade in reversed(self.matching_engine.trades):
            if trade.symbol == symbol:
                # Assuming trade.trade_id is an integer or can be converted/mapped to one.
                # If trade.trade_id is a UUID string, Binance expects an int. This might need adjustment in Trade object or here.
                # For now, let's assume it can be a string if it uniquely identifies, though Binance uses int.
                # To be closer to Binance, we might use a simple counter or hash if trade.trade_id isn't an int.
                # Let's use a placeholder for trade.id if it's not an integer, as Binance expects int for trade IDs.
                trade_id_to_report = trade.trade_id
                if not isinstance(trade.trade_id, int):
                    # Fallback: use a hash of the string trade_id, then take a part of it to make it int-like
                    # This is a mock, a proper system would assign sequential integer IDs.
                    try:
                        trade_id_to_report = int(str(uuid.UUID(trade.trade_id).int)[:10]) # Example, may not be ideal
                    except ValueError: # if trade.trade_id is not even a valid UUID string
                        trade_id_to_report = count + 1 # Simplest mock ID

                trades_data.append({
                    "id": trade_id_to_report, # Binance expects integer trade ID
                    "price": str(trade.price),
                    "qty": str(trade.quantity),
                    "quoteQty": str(trade.price * trade.quantity), # Calculate quoteQty
                    "time": int(trade.timestamp * 1000),
                    # isBuyerMaker: True if the buyer was the maker. This requires knowing which order was resting.
                    # Simplified: assume taker for now. This needs more info from matching engine.
                    "isBuyerMaker": False, 
                    "isBestMatch": True # Simplified, assume all are best match for public trades
                })
                count += 1
                if count >= limit:
                    break
                    
        return jsonify(trades_data)
    
    def _klines(self) -> Response:
        """获取K线数据 - Binance compliant"""
        symbol = request.args.get('symbol')
        interval = request.args.get('interval')
        start_time_str = request.args.get('startTime')
        end_time_str = request.args.get('endTime')
        limit_str = request.args.get('limit')
        time_zone_str = request.args.get('timeZone') # Default UTC (0 offset) in Binance

        if not symbol:
            return self._error_response("Mandatory 'symbol' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        if not interval:
            return self._error_response("Mandatory 'interval' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)

        if symbol not in self.matching_engine.order_books:
             return self._error_response(f"Invalid symbol: {symbol}", UNKNOWN_SYMBOL, 400)

        # Validate interval
        # Full list from Binance: 1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        # Adding 's' for seconds as per some API docs, though Spot often starts with 'm'
        allowed_intervals = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        if interval not in allowed_intervals:
            return self._error_response(f"Invalid interval: {interval}. Allowed intervals: {allowed_intervals}", INVALID_PARAM, 400) # Or a more specific error code if available

        limit = 500 # Default Binance limit
        max_limit = 1000
        if limit_str is not None:
            try:
                limit_val = int(limit_str)
                if not (1 <= limit_val <= max_limit):
                    return self._error_response(f"Parameter 'limit' is out of bounds. Must be between 1 and {max_limit}.", ILLEGAL_CHARS, 400)
                limit = limit_val
            except ValueError:
                return self._error_response("Illegal characters found in parameter 'limit'. Expected an integer.", ILLEGAL_CHARS, 400)

        # Timezone handling (simplified, primarily for parameter validation/acknowledgment)
        # Binance default is UTC (0 offset). Example: "Etc/GMT+5" would be -5 hours from UTC.
        # For now, we accept it but don't deeply implement timezone-based kline generation logic.
        # The actual `time_zone_offsets` dictionary already exists from previous commit, focusing on named zones.
        # Binance allows RFC822 style, e.g. +0800 or Z for UTC. Our current list is simplified.
        # Let's keep the existing timeZone validation and offset calculation for now.
        time_zone = time_zone_str or 'UTC'
        allowed_time_zones = ['UTC', 'China', 'JST', 'KST', 'SGT'] # From existing code
        if time_zone not in allowed_time_zones:
             # This error path was in previous code, let's ensure it uses standard error codes.
            return self._error_response(f"Invalid timeZone: {time_zone}. Allowed values: {allowed_time_zones}", INVALID_PARAM, 400)
        
        time_zone_offsets = {'UTC': 0, 'China': 8, 'JST': 9, 'KST': 9, 'SGT': 8}
        offset_hours = time_zone_offsets.get(time_zone, 0)
        offset_ms = offset_hours * 3600 * 1000

        # startTime and endTime parsing (optional)
        start_time_ms = None
        if start_time_str:
            try:
                start_time_ms = int(start_time_str)
            except ValueError:
                return self._error_response("Illegal characters found in parameter 'startTime'. Expected an integer timestamp.", ILLEGAL_CHARS, 400)
        
        end_time_ms = None
        if end_time_str:
            try:
                end_time_ms = int(end_time_str)
            except ValueError:
                return self._error_response("Illegal characters found in parameter 'endTime'. Expected an integer timestamp.", ILLEGAL_CHARS, 400)
        
        # TODO: Implement actual kline generation based on trades in matching_engine, 
        # respecting interval, startTime, endTime, limit, and timezone.
        # For now, returning mock klines that match the structure.

        klines_data = []
        # Generate 'limit' number of mock klines for demonstration.
        # A real implementation would query historical data.
        current_kline_open_time = int(time.time() * 1000) - (limit * 60 * 1000) # Mock start time for a 1m interval series
        
        # Adjust mock times by the conceptual offset. Note: Binance applies timezone primarily for day-aligned requests.
        # For millisecond timestamps, the absolute time is usually clear. This is a simplified application.
        current_kline_open_time += offset_ms 

        # Get a price for the mock klines, default to 0 if no market price
        mock_price_decimal = self.matching_engine.get_market_price(symbol) or Decimal("0.0")
        mock_price_str = str(mock_price_decimal)
        mock_high_str = str(mock_price_decimal * Decimal("1.01")) # Mock high 1% above
        mock_low_str = str(mock_price_decimal * Decimal("0.99"))  # Mock low 1% below

        interval_ms_map = { # Simplified mapping for mock close time calculation
            "1s": 1000, "1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000, "30m": 1800000,
            "1h": 3600000, "2h": 7200000, "4h": 14400000, "6h": 21600000, "8h": 28800000, "12h": 43200000,
            "1d": 86400000, "3d": 259200000, "1w": 604800000, "1M": 2592000000 # Approx 30 days for 1M
        }
        current_interval_ms = interval_ms_map.get(interval, 60000) # Default to 1m if somehow interval is bad (should be caught)

        for i in range(limit):
            open_t = current_kline_open_time + (i * current_interval_ms)
            close_t = open_t + current_interval_ms -1 # Close time is end of interval
            
            # Mock data for a single kline
            kline = [
                open_t,                     # 0 Open time
                mock_price_str,             # 1 Open
                mock_high_str,              # 2 High
                mock_low_str,               # 3 Low
                mock_price_str,             # 4 Close
                "100",                      # 5 Volume (mock)
                close_t,                    # 6 Close time
                str(mock_price_decimal * Decimal("100")), # 7 Quote asset volume (mock)
                10,                         # 8 Number of trades (mock)
                "50",                       # 9 Taker buy base asset volume (mock)
                str(mock_price_decimal * Decimal("50")),  # 10 Taker buy quote asset volume (mock)
                "0"                         # 11 Ignore
            ]
            klines_data.append(kline)
        
        # If startTime and endTime are provided, a real implementation would filter/generate klines for that range.
        # Our current mock simply returns 'limit' klines ending roughly now.

        return jsonify(klines_data)
    
    # 交易接口实现
    def _create_order(self) -> Response:
        """创建订单 - Binance compliant"""
        # Simplified API Key authentication for now
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return self._error_response("API-key required for this endpoint.", INVALID_API_KEY_ORDER, 401)
        user_id = self.get_user_id_from_api_key(api_key)
        if not user_id:
            return self._error_response("Invalid API-key.", INVALID_API_KEY_ORDER, 401)
            
        data = {}
        if request.content_type == 'application/json' and request.json:
            data = request.json
        elif request.form:
            data = request.form.to_dict()
        elif request.args: # Binance also supports query params for POST /api/v3/order
            data = request.args.to_dict()
        
        if not data:
            return self._error_response("Missing request data", error_code=INVALID_PARAM, status_code=400)
        
        # Timestamp is mandatory for signed endpoints
        timestamp_str = data.get('timestamp')
        if not timestamp_str:
            return self._error_response("Mandatory parameter 'timestamp' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        is_valid_ts, ts_err_msg, ts_err_code = RequestValidator.validate_timestamp(timestamp_str)
        if not is_valid_ts:
            return self._error_response(ts_err_msg, ts_err_code, 400)
        
        transact_time = int(time.time() * 1000) # Record transaction time early

        # Validate other parameters using RequestValidator (needs expansion for new fields)
        # is_valid, error_msg, error_code_from_validator = RequestValidator.validate_order_request(data)
        # if not is_valid:
        #     return self._error_response(error_msg or "Invalid request parameters", error_code_from_validator or INVALID_PARAM, 400)

        # Manual validation for key parameters for now, to be integrated into RequestValidator
        symbol = data.get('symbol')
        side = data.get('side')
        order_type = data.get('type') # Renamed from 'type' to 'order_type' to avoid conflict with python type

        if not symbol:
            return self._error_response("Mandatory parameter 'symbol' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        if symbol not in self.matching_engine.order_books:
            return self._error_response(f"Invalid symbol: {symbol}", UNKNOWN_SYMBOL, 400)
        if not side or side.upper() not in ['BUY', 'SELL']:
            return self._error_response("Mandatory parameter 'side' was not sent or is invalid.", INVALID_PARAM, 400)
        
        allowed_order_types = ['LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER']
        if not order_type or order_type.upper() not in allowed_order_types:
            return self._error_response(f"Mandatory parameter 'type' was not sent or is invalid. Supported types: {allowed_order_types}", INVALID_PARAM, 400)
        order_type_upper = order_type.upper()

        quantity_str = data.get('quantity')
        quote_order_qty_str = data.get('quoteOrderQty')
        price_str = data.get('price')

        time_in_force = data.get('timeInForce')
        allowed_tif = ['GTC', 'IOC', 'FOK']
        if order_type_upper == 'LIMIT' or order_type_upper == 'STOP_LOSS_LIMIT' or order_type_upper == 'TAKE_PROFIT_LIMIT' or order_type_upper == 'LIMIT_MAKER':
            if not time_in_force or time_in_force.upper() not in allowed_tif:
                # For LIMIT_MAKER, only GTC might be implicitly allowed by some exchanges, but Binance allows GTC, IOC, FOK for LIMIT_MAKER too.
                return self._error_response(f"Parameter 'timeInForce' is mandatory for order type {order_type_upper} and must be one of {allowed_tif}.", INVALID_PARAM, 400)
            time_in_force = time_in_force.upper()
        elif time_in_force: # Provided for an order type that does not use it (e.g. MARKET)
             return self._error_response(f"Parameter 'timeInForce' is not applicable for order type {order_type_upper}.", INVALID_PARAM, 400)
        else: # For MARKET orders, TIF is not used/sent, can be considered None internally
            time_in_force = None 

        if order_type_upper == 'LIMIT_MAKER' and time_in_force not in ['GTC', 'IOC', 'FOK']:
             # Redundant if covered above, but explicit check as per some API notes. Binance doc implies LIMIT_MAKER follows LIMIT TIF rules.
             # If LIMIT_MAKER could only be GTC, this check would be: if time_in_force != 'GTC': error
             pass # Covered by the general TIF check for LIMIT types

        # Price is required for limit-based orders
        if order_type_upper in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER']:
            if not price_str:
                return self._error_response(f"Parameter 'price' is mandatory for order type {order_type_upper}.", INVALID_PARAM, 400)
        
        # Quantity or quoteOrderQty logic
        if not quantity_str and not quote_order_qty_str:
            return self._error_response("Either 'quantity' or 'quoteOrderQty' is required.", INVALID_PARAM, 400)
        if quantity_str and quote_order_qty_str and order_type_upper == 'MARKET': # For market, only one should be provided
            return self._error_response("For MARKET orders, either 'quantity' or 'quoteOrderQty' should be sent, but not both.", INVALID_PARAM, 400)
        if quote_order_qty_str and order_type_upper != 'MARKET':
            return self._error_response("'quoteOrderQty' is only supported for MARKET orders.", INVALID_PARAM, 400)
        
        # Stop Price validation
        stop_price_str = data.get('stopPrice')
        if order_type_upper in ['STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT'] and not stop_price_str:
            return self._error_response(f"Parameter 'stopPrice' is mandatory for order type {order_type_upper}.", INVALID_PARAM, 400)
        
        # Iceberg quantity for LIMIT or LIMIT_MAKER and TIF must be GTC
        iceberg_qty_str = data.get('icebergQty')
        if iceberg_qty_str and order_type_upper not in ['LIMIT', 'LIMIT_MAKER']:
            return self._error_response("'icebergQty' is only supported for LIMIT or LIMIT_MAKER orders.", INVALID_PARAM, 400)
        if iceberg_qty_str and time_in_force != 'GTC': # As per docs: iceberg TIF must be GTC
             return self._error_response("For iceberg orders, 'timeInForce' must be GTC.", INVALID_PARAM, 400)

        # Response type
        new_order_resp_type = data.get('newOrderRespType', 'FULL').upper()
        if new_order_resp_type not in ['ACK', 'RESULT', 'FULL']:
            return self._error_response("Invalid 'newOrderRespType'. Must be ACK, RESULT, or FULL.", INVALID_PARAM, 400)

        client_order_id = data.get('newClientOrderId') # Optional
        self_trade_prevention_mode = data.get('selfTradePreventionMode', 'NONE').upper()
        if self_trade_prevention_mode not in ['NONE', 'EXPIRE_TAKER', 'EXPIRE_MAKER', 'EXPIRE_BOTH']:
            return self._error_response("Invalid 'selfTradePreventionMode'.", INVALID_PARAM, 400)

        # Convert numeric strings to Decimal, handling potential errors
        try:
            quantity = Decimal(quantity_str) if quantity_str else None
            price = Decimal(price_str) if price_str else None
            quote_order_qty = Decimal(quote_order_qty_str) if quote_order_qty_str else None
            stop_price = Decimal(stop_price_str) if stop_price_str else None
            iceberg_qty = Decimal(iceberg_qty_str) if iceberg_qty_str else None
        except Exception as e:
            logger.error(f"Error converting numeric order parameters: {e}")
            return self._error_response("Invalid number format for quantity, price, quoteOrderQty, stopPrice, or icebergQty.", INVALID_PARAM, 400)
        
        # TODO: Further validation for stopPrice conditions (e.g. > market for STOP_LOSS BUY)
        # TODO: Logic for locking funds needs to be robust for all order types and quoteOrderQty

        # For now, existing fund locking might be too simple for complex orders.
        # This needs careful review based on order type and parameters.
        # Simplified fund locking attempt, to be refined:
        lock_amount_for_fund_check = quantity
        is_quote_order_for_fund_check = False
        if order_type_upper == 'MARKET' and side.upper() == 'BUY' and quote_order_qty:
            lock_amount_for_fund_check = quote_order_qty
            is_quote_order_for_fund_check = True
            price_for_fund_check = None # For market quote buy, price is not used for locking quote asset
        else:
            price_for_fund_check = price # or stop_price or market_price depending on order type

        if not self.account_manager.lock_funds_for_order(
            user_id=user_id, symbol=symbol, side=side.upper(),
            amount=lock_amount_for_fund_check, price=price_for_fund_check, 
            is_quote_order=is_quote_order_for_fund_check 
        ):
            return self._error_response("Insufficient balance.", INSUFFICIENT_BALANCE, 400) # Use specific error code for balance

        internal_order_id = str(uuid.uuid4())
        order_to_place = Order(
            order_id=internal_order_id, # Use internal UUID, clientOrderId is separate
            symbol=symbol,
            side=OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL,
            order_type=OrderType[order_type_upper], # Assumes OrderType enum matches Binance string
            quantity=quantity if quantity else Decimal('0'),
            price=price,
            timestamp=time.time(), # Order creation timestamp on server
            user_id=user_id,
            client_order_id=client_order_id,
            time_in_force=time_in_force, # Store TIF
            stop_price=stop_price, # Store stopPrice
            iceberg_qty=iceberg_qty, # Store icebergQty
            quote_order_qty=quote_order_qty, 
            self_trade_prevention_mode=self_trade_prevention_mode,
            # price_match was in previous Order object, it's not a standard Binance param for /v3/order POST
            # It might be an internal QTE concept. For now, let's default or remove if not used.
            price_match='NONE' # Defaulting, as it's not a direct Binance param here.
        )

        try:
            success = self.matching_engine.place_order(order_to_place)
            # After placing, the order object in matching_engine (order_to_place might be a copy)
            # will have its status, executed_quantity, etc. updated.
            # We need to retrieve the definitive state of the order from the matching engine.
            
            # Fetch the order from matching engine to get its final state after processing
            # This is crucial as its status, executedQty etc. might have changed.
            # The `place_order` could return the updated order object or its ID for refetching.
            # For now, let's assume `place_order` updates `order_to_place` in-place or we refetch it.
            # If matching_engine.place_order does not update the passed order object by reference, 
            # we must fetch it by order_id.
            processed_order = self.matching_engine.get_order(internal_order_id) 
            if not processed_order: # Should not happen if place_order was successful and ID is correct
                # This is an internal error state if success was true but order not found
                logger.error(f"Order {internal_order_id} placed but not found in matching engine!")
                # Unlock funds as a safety measure if we can determine what was locked.
                self.account_manager.unlock_funds_for_order(user_id=user_id, symbol=symbol, side=side.upper(),amount=lock_amount_for_fund_check, price=price_for_fund_check, is_quote_order=is_quote_order_for_fund_check)
                return self._error_response("Order processing error after placement.", INTERNAL_SERVER_ERROR, 500)

            if not success: # If matching engine explicitly rejected it (e.g. FOK not fillable)
                self.account_manager.unlock_funds_for_order(user_id=user_id, symbol=symbol, side=side.upper(),amount=lock_amount_for_fund_check, price=price_for_fund_check, is_quote_order=is_quote_order_for_fund_check)
                # Error message might come from matching engine or be generic here.
                # TODO: Get specific error from matching engine if possible.
                return self._error_response("Order placement failed by matching engine.", ORDER_PLACEMENT_FAILED, 400) # Example code

            # Construct response based on newOrderRespType
            response_data = {
                "symbol": processed_order.symbol,
                "orderId": processed_order.order_id, # This is our internal_order_id
                "orderListId": -1, # Not supporting OCO/OTO orders yet
                "clientOrderId": processed_order.client_order_id or "", # Return empty string if None, Binance does this
                "transactTime": transact_time
            }

            if new_order_resp_type == 'RESULT' or new_order_resp_type == 'FULL':
                response_data.update({
                    "price": str(processed_order.price or "0"), # Price might be null for MARKET orders until filled
                    "origQty": str(processed_order.quantity),
                    "executedQty": str(processed_order.executed_quantity),
                    "cummulativeQuoteQty": str(processed_order.cummulative_quote_qty), # Needs to be calculated by ME
                    "status": processed_order.status.name, # Assuming OrderStatus enum has .name attribute
                    "timeInForce": processed_order.time_in_force or "", # Ensure TIF is in response
                    "type": processed_order.order_type.name, # Assuming OrderType enum has .name
                    "side": processed_order.side.name, # Assuming OrderSide enum has .name
                    "workingTime": transact_time, # Placeholder, time order is on book. Can be same as transactTime for immediate.
                    "selfTradePreventionMode": processed_order.self_trade_prevention_mode or "NONE",
                    "origQuoteOrderQty": str(processed_order.quote_order_qty or "0.000000") # Add origQuoteOrderQty
                })
            
            if new_order_resp_type == 'FULL':
                fills = []
                # Find trades related to this order_id from matching_engine.trades
                # Trade object should have price, quantity, trade_id, and potentially commission info.
                for trade_info in self.matching_engine.trades: # This list might grow large
                    if trade_info.buy_order_id == processed_order.order_id or trade_info.sell_order_id == processed_order.order_id:
                        # TODO: Commission and commissionAsset need to be calculated/retrieved.
                        # Mocking commission for now.
                        commission_asset = processed_order.symbol[-4:] if processed_order.symbol.endswith(("USDT", "BUSD", "TUSD")) else processed_order.symbol[:3]
                        fills.append({
                            "price": str(trade_info.price),
                            "qty": str(trade_info.quantity),
                            "commission": "0.0", # Mock
                            "commissionAsset": commission_asset, # Mock: base or quote
                            "tradeId": trade_info.trade_id # Assuming trade_id is an int
                        })
                response_data["fills"] = fills
            
            return jsonify(response_data)

        except Exception as e:
            # Unlock funds on any unexpected error during placement or response construction
            logger.error(f"Error during order creation or processing: {e}", exc_info=True)
            try:
                self.account_manager.unlock_funds_for_order(user_id=user_id, symbol=symbol, side=side.upper(),amount=lock_amount_for_fund_check, price=price_for_fund_check, is_quote_order=is_quote_order_for_fund_check)
            except Exception as unlock_e:
                logger.error(f"Failed to unlock funds during exception handling: {unlock_e}")
            return self._error_response(f"Order creation failed due to an internal error: {str(e)}", INTERNAL_SERVER_ERROR, 500)
    
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
    
    def _avg_price(self) -> Response:
        """
        获取当前平均价格
        
        Returns
        -------
        Response
            当前平均价格响应
        """
        symbol = request.args.get('symbol')
        
        if not symbol:
            # Binance error: {"code":-1102,"msg":"Mandatory 'symbol' was not sent, was empty/null, or malformed."}
            # Or for avgPrice specifically: {"code":-1105,"msg":"Parameter 'symbol' was empty."} - Let's use this if defined, else general mandatory.
            # Using MANDATORY_PARAM_EMPTY_OR_MALFORMED as a general one for now.
            return self._error_response("Parameter 'symbol' was empty.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400) # -1105 is more specific if available
            
        # 获取当前价格
        price = self.matching_engine.get_market_price(symbol)
        if price is None:
            # Binance error for invalid symbol in avgPrice: {"code":-1121,"msg":"Invalid symbol."} which is UNKNOWN_SYMBOL
            return self._error_response(f"Invalid symbol: {symbol}", UNKNOWN_SYMBOL, 400)
            
        # 币安API中closeTime表示最后交易时间，这里简化为当前时间
        current_time_ms = int(time.time() * 1000)
        
        result = {
            "mins": 5,  # Binance avgPrice is typically for 5 minutes
            "price": str(price),
            "closeTime": current_time_ms  # Added as per Binance API update 2023-12-04
        }
        
        return jsonify(result)
    
    def _get_commission(self) -> Response:
        """获取账户佣金费率"""
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("API-key required", error_code=INVALID_API_KEY, status_code=401)
        
        # 固定费率，实际项目中应根据用户等级、交易量等计算
        maker_commission = "0.001" # 0.1%
        taker_commission = "0.001" # 0.1%
        
        result = {
            "makerCommission": maker_commission,
            "takerCommission": taker_commission,
            "buyerCommission": "0",
            "sellerCommission": "0"
        }
        
        return jsonify(result)
    
    def _trading_day(self) -> Response:
        """
        获取当前交易日信息
        根据币安API: /api/v3/ticker/tradingDay
        """
        # 获取当前时间
        now = time.time()
        
        # 计算交易日开始时间和结束时间
        # 币安以UTC 0点作为交易日分界
        now_dt = time.gmtime(now)
        
        # 当前交易日开始时间（UTC 0点）
        start_time = time.mktime(time.struct_time((
            now_dt.tm_year, now_dt.tm_mon, now_dt.tm_mday,
            0, 0, 0, now_dt.tm_wday, now_dt.tm_yday, now_dt.tm_isdst
        )))
        
        # 下一交易日开始时间
        end_time = start_time + 86400  # 一天的秒数
        
        result = {
            "timezone": "UTC",
            "serverTime": int(now * 1000),
            "tradingDayStart": int(start_time * 1000),
            "tradingDayEnd": int(end_time * 1000)
        }
        
        return jsonify(result)
    
    def _test_order(self) -> Response:
        """
        测试下单接口，与_create_order逻辑相同但不实际下单
        根据币安API: POST /api/v3/order/test
        """
        user_id = self._authenticate()
        if not user_id:
            return self._error_response("API-key required", error_code=INVALID_API_KEY_ORDER, status_code=401)
            
        # 获取请求参数 - 支持不同的内容类型
        data = {}
        if request.content_type == 'application/json' and request.json:
            data = request.json
        elif request.form:
            data = request.form.to_dict()
        elif request.args:
            data = request.args.to_dict()
        
        if not data:
            return self._error_response("Missing request data", error_code=INVALID_PARAM, status_code=400)
        
        # 验证时间戳参数
        timestamp = data.get('timestamp')
        if timestamp:
            is_valid, error_msg, error_code = RequestValidator.validate_timestamp(timestamp)
            if not is_valid:
                return self._error_response(error_msg, error_code=error_code, status_code=400)
        
        # 使用请求验证器进行参数验证
        is_valid, error_msg = RequestValidator.validate_order_request(data)
        if not is_valid:
            # 返回400状态码和错误信息
            return self._error_response(error_msg or "Invalid request parameters", error_code=INVALID_PARAM, status_code=400)
        
        # 成功通过验证，返回空对象表示成功
        return jsonify({})

    # 新增: 获取交易所信息
    def _exchange_info(self):
        # TODO: 从 MatchingEngine 获取真实的或模拟的交易所信息
        # 以下为模拟数据结构，需要严格按照币安文档填充
        exchange_info_data = {
            "timezone": "UTC",
            "serverTime": int(time.time() * 1000),
            "rateLimits": [
                {
                    "rateLimitType": "REQUEST_WEIGHT",
                    "interval": "MINUTE",
                    "intervalNum": 1,
                    "limit": 1200
                },
                {
                    "rateLimitType": "ORDERS",
                    "interval": "SECOND",
                    "intervalNum": 10,
                    "limit": 50
                },
                {
                    "rateLimitType": "ORDERS",
                    "interval": "DAY",
                    "intervalNum": 1,
                    "limit": 160000
                }
            ],
            "exchangeFilters": [],
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "baseAssetPrecision": 8,
                    "quoteAsset": "USDT",
                    "quotePrecision": 8,
                    "quoteAssetPrecision": 8, # 币安文档中有 quoteAssetPrecision 和 quotePrecision
                    "baseCommissionPrecision": 8,
                    "quoteCommissionPrecision": 8,
                    "orderTypes": ["LIMIT", "LIMIT_MAKER", "MARKET", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT"],
                    "icebergAllowed": True,
                    "ocoAllowed": True,
                    "quoteOrderQtyMarketAllowed": True,
                    "allowTrailingStop": True, # 币安实际为 allowTrailingStop
                    "cancelReplaceAllowed": True, # 币安新增字段
                    "isSpotTradingAllowed": True,
                    "isMarginTradingAllowed": False, # QTE模拟盘暂不考虑杠杆
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01",
                            "maxPrice": "1000000.00",
                            "tickSize": "0.01"
                        },
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.00001",
                            "maxQty": "9000.00",
                            "stepSize": "0.00001"
                        },
                        {
                            "filterType": "MIN_NOTIONAL",
                            "minNotional": "10.0",
                            "applyToMarket": True,
                            "avgPriceMins": 5
                        }
                    ],
                    "permissions": [["SPOT"]] # 币安新格式
                }
                # TODO: 添加更多模拟交易对
            ]
        }
        return jsonify(exchange_info_data)

    # 市场数据接口的Flask路由
    def register_market_data_routes(self, app_or_blueprint):
        # Ping
        app_or_blueprint.add_url_rule("/api/v1/ping", view_func=self._ping, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/ping", view_func=self._ping, methods=["GET"])
        # Server Time
        app_or_blueprint.add_url_rule("/api/v1/time", view_func=self._server_time, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/time", view_func=self._server_time, methods=["GET"])
        # Exchange Info
        app_or_blueprint.add_url_rule("/api/v3/exchangeInfo", view_func=self._exchange_info, methods=["GET"])
        # 保持v1的兼容性，如果vnpy某些旧版或者自定义网关可能访问
        app_or_blueprint.add_url_rule("/api/v1/exchangeInfo", view_func=self._exchange_info, methods=["GET"])

        # Ticker Price
        app_or_blueprint.add_url_rule("/api/v1/ticker/price", view_func=self._ticker_price, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/ticker/price", view_func=self._ticker_price, methods=["GET"])
        # Ticker 24hr
        app_or_blueprint.add_url_rule("/api/v1/ticker/24hr", view_func=self._ticker_24hr, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/ticker/24hr", view_func=self._ticker_24hr, methods=["GET"])
        # Ticker tradingDay
        app_or_blueprint.add_url_rule("/api/v1/ticker/tradingDay", view_func=self._trading_day, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/ticker/tradingDay", view_func=self._trading_day, methods=["GET"])
        # Depth
        app_or_blueprint.add_url_rule("/api/v1/depth", view_func=self._order_book, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/depth", view_func=self._order_book, methods=["GET"])
        # Recent trades
        app_or_blueprint.add_url_rule("/api/v1/trades", view_func=self._recent_trades, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/trades", view_func=self._recent_trades, methods=["GET"])
        # Klines
        app_or_blueprint.add_url_rule("/api/v1/klines", view_func=self._klines, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/klines", view_func=self._klines, methods=["GET"])
        # Avg price
        app_or_blueprint.add_url_rule("/api/v1/avgPrice", view_func=self._avg_price, methods=["GET"])
        app_or_blueprint.add_url_rule("/api/v3/avgPrice", view_func=self._avg_price, methods=["GET"])

    def _cancel_order(self) -> Response:
        """取消订单 - Binance compliant"""
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return self._error_response("API-key required for this endpoint.", INVALID_API_KEY_ORDER, 401)
        user_id = self.get_user_id_from_api_key(api_key)
        if not user_id:
            return self._error_response("Invalid API-key.", INVALID_API_KEY_ORDER, 401)

        # Parameters can be in request body (form-data) or query string for DELETE
        data = {}
        if request.form:
            data = request.form.to_dict()
        elif request.args:
            data = request.args.to_dict()
        # No explicit JSON body for DELETE in typical REST, but Flask might allow it.
        # Binance docs specify query string or application/x-www-form-urlencoded for DELETE.

        timestamp_str = data.get('timestamp')
        if not timestamp_str:
            return self._error_response("Mandatory parameter 'timestamp' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        is_valid_ts, ts_err_msg, ts_err_code = RequestValidator.validate_timestamp(timestamp_str)
        if not is_valid_ts:
            return self._error_response(ts_err_msg, ts_err_code, 400)
        
        transact_time = int(time.time() * 1000)

        symbol = data.get('symbol')
        order_id = data.get('orderId')
        orig_client_order_id = data.get('origClientOrderId')
        # new_client_order_id_for_cancel = data.get('newClientOrderId') # Not a standard Binance param for cancel response, but used by some exchanges.
                                                                     # Binance returns the original clientOrderId.

        cancel_restrictions = data.get('cancelRestrictions')

        if not symbol:
            return self._error_response("Mandatory parameter 'symbol' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
            
        if not (order_id or orig_client_order_id):
            return self._error_response("Either 'orderId' or 'origClientOrderId' is required.", INVALID_PARAM, 400)
            
        if cancel_restrictions and cancel_restrictions.upper() not in ["ONLY_NEW", "ONLY_PARTIALLY_FILLED"]:
            return self._error_response("Invalid 'cancelRestrictions'. Must be ONLY_NEW or ONLY_PARTIALLY_FILLED.", INVALID_PARAM, 400)
        
        # Fetch the order to be cancelled
        order_to_cancel = None
        if order_id:
            # Assuming get_order can find an order by its internal ID across all users if needed,
            # but for cancellation, it should be user-specific. 
            # The MatchingEngine.get_order(order_id) might need user_id for security.
            # Let's assume get_order(order_id) is sufficient if order_id is globally unique.
            order_to_cancel = self.matching_engine.get_order(order_id)
        elif orig_client_order_id:
            # This needs to search by user_id and client_order_id.
            order_to_cancel = self.matching_engine.get_order_by_client_id(user_id, orig_client_order_id)
            
        if not order_to_cancel:
            # Binance error: {"code":-2013,"msg":"Order does not exist."} or specific for archived.
            # Check if it might be an archived order (simplified check here)
            # A full check would query a separate archive / check timestamps etc.
            # For now, we just use ORDER_NOT_FOUND.
            return self._error_response("Order does not exist.", ORDER_NOT_FOUND, 404) 
            
        if order_to_cancel.user_id != user_id:
            # This should ideally not happen if get_order_by_client_id is scoped by user_id
            # And if get_order(order_id) also implies user ownership or is globally unique & then checked
            return self._error_response("Order does not belong to the current user or API key.", UNAUTHORIZED, 401) # Or ORDER_NOT_FOUND

        if order_to_cancel.symbol != symbol:
             return self._error_response(f"Order {order_to_cancel.order_id} symbol {order_to_cancel.symbol} does not match requested symbol {symbol}.", INVALID_PARAM, 400)

        # Check cancel restrictions
        if cancel_restrictions:
            current_status_str = order_to_cancel.status.name.upper()
            if cancel_restrictions.upper() == "ONLY_NEW" and current_status_str != OrderStatus.NEW.name.upper():
                return self._error_response("Order was not canceled due to cancel restrictions (ONLY_NEW).", CANCEL_REJECTED, 400) # -2011
            if cancel_restrictions.upper() == "ONLY_PARTIALLY_FILLED" and current_status_str != OrderStatus.PARTIALLY_FILLED.name.upper():
                return self._error_response("Order was not canceled due to cancel restrictions (ONLY_PARTIALLY_FILLED).", CANCEL_REJECTED, 400) # -2011
        
        # Check if order is already in a final state
        if order_to_cancel.status in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            # Binance might return the current state of the order if already cancelled/filled, or an error like "Order already in final state"
            # For simplicity, let's return an error indicating it cannot be cancelled.
            # Example Binance error: {"code":-2011,"msg":"CANCEL_REJECTED"} if already cancelled/filled.
            return self._error_response(f"Order is already in a final state ({order_to_cancel.status.name}) and cannot be canceled.", CANCEL_REJECTED, 400)

        # Attempt to cancel in matching engine
        # The matching_engine.cancel_order should handle fund unlocking internally.
        # If not, we have to do it here based on remaining_quantity.
        cancel_success = self.matching_engine.cancel_order(order_to_cancel.order_id)
        
        if not cancel_success:
            # This implies an issue within the matching engine if it passed previous checks.
            # Or, the ME itself might have its own restrictions (e.g. mid-match)
            return self._error_response("Failed to cancel order in matching engine.", INTERNAL_SERVER_ERROR, 500) # Or a more specific ME error
        
        # Fetch the order again to get its updated state (should be CANCELED)
        cancelled_order = self.matching_engine.get_order(order_to_cancel.order_id)
        if not cancelled_order or cancelled_order.status != OrderStatus.CANCELED:
            logger.error(f"Order {order_to_cancel.order_id} cancel reported success but status is not CANCELED. Current: {cancelled_order.status if cancelled_order else 'Not Found'}")
            # Fallback response or error, though ideally ME guarantees status update.
            # For now, we'll proceed assuming it is CANCELED based on cancel_success.
            # If ME doesn't update status properly, this needs fixing in ME.
            # Let's use the original order_to_cancel and manually set status for response if needed, but that's not ideal.
            # Best is to rely on cancelled_order being accurate.
            if not cancelled_order:
                 return self._error_response("Error fetching cancelled order details.", INTERNAL_SERVER_ERROR, 500)
            # If status isn't CANCELED, this is an inconsistency.

        # Construct response similar to a FULL order response but with status CANCELED.
        response_data = {
            "symbol": cancelled_order.symbol,
            "orderId": cancelled_order.order_id,
            "orderListId": -1, 
            "clientOrderId": cancelled_order.client_order_id or "",
            "transactTime": transact_time, # Time of cancel transaction
            "price": str(cancelled_order.price or "0"),
            "origQty": str(cancelled_order.quantity),
            "executedQty": str(cancelled_order.executed_quantity),
            "cummulativeQuoteQty": str(cancelled_order.cummulative_quote_qty),
            "status": cancelled_order.status.name, # Should be CANCELED
            "timeInForce": cancelled_order.time_in_force or "",
            "type": cancelled_order.order_type.name,
            "side": cancelled_order.side.name,
            "selfTradePreventionMode": cancelled_order.self_trade_prevention_mode or "NONE"
            # Binance response for cancel also includes 'origClientOrderId' directly, which is same as clientOrderId for non-OCO
            # "origClientOrderId": cancelled_order.client_order_id or "", # This is redundant if clientOrderId is already populated
        }
        # Add `origClientOrderId` field specifically if it's different from how `clientOrderId` is handled or if Binance always includes it
        # The parameter was `origClientOrderId`, so the response field with the same name should reflect the input if used for lookup.
        if orig_client_order_id: # If lookup was by origClientOrderId
            response_data["origClientOrderId"] = orig_client_order_id
        elif cancelled_order.client_order_id: # If lookup by orderId but clientOrderId existed
             response_data["origClientOrderId"] = cancelled_order.client_order_id
        else: # Default if no client ID involved
            response_data["origClientOrderId"] = ""

        # Note: Binance cancel response does not typically include 'fills'.
        # It also may or may not include 'workingTime'. Let's omit it for cancel.
        
        return jsonify(response_data)
    
    def _get_order(self) -> Response:
        """查询订单 - Binance compliant"""
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return self._error_response("API-key required for this endpoint.", INVALID_API_KEY_ORDER, 401)
        user_id = self.get_user_id_from_api_key(api_key)
        if not user_id:
            return self._error_response("Invalid API-key.", INVALID_API_KEY_ORDER, 401)

        data = request.args.to_dict() # GET requests use query parameters

        timestamp_str = data.get('timestamp')
        if not timestamp_str:
            return self._error_response("Mandatory parameter 'timestamp' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        is_valid_ts, ts_err_msg, ts_err_code = RequestValidator.validate_timestamp(timestamp_str)
        if not is_valid_ts:
            return self._error_response(ts_err_msg, ts_err_code, 400)

        symbol = data.get('symbol')
        order_id_str = data.get('orderId')
        orig_client_order_id = data.get('origClientOrderId')

        if not symbol:
            return self._error_response("Mandatory parameter 'symbol' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
            
        if not (order_id_str or orig_client_order_id):
            return self._error_response("Either 'orderId' or 'origClientOrderId' is required.", INVALID_PARAM, 400)

        order_to_query = None
        if order_id_str:
            try:
                # order_id_val = int(order_id_str) # Binance orderId is long (int)
                # Our internal order_id is UUID string. For querying by 'orderId', we use our internal ID.
                order_to_query = self.matching_engine.get_order(order_id_str)
            except ValueError:
                return self._error_response("Invalid format for 'orderId'.", INVALID_PARAM, 400)
        elif orig_client_order_id:
            order_to_query = self.matching_engine.get_order_by_client_id(user_id, orig_client_order_id)
            
        if not order_to_query:
            # Check if it is an archived order (not implemented yet, so just return not found)
            # Binance: {"code":-2013, "msg":"Order does not exist."} 
            # Or {"code":-2026, "msg":"Order was canceled or expired with no executed qty over 90 days ago and has been archived."}            
            return self._error_response("Order does not exist.", ORDER_NOT_FOUND, 404)
            
        if order_to_query.user_id != user_id:
            return self._error_response("Order does not belong to the current user.", UNAUTHORIZED, 401) # Or ORDER_NOT_FOUND

        if order_to_query.symbol != symbol:
             return self._error_response(f"Order symbol mismatch. Requested for {symbol} but order is for {order_to_query.symbol}.", INVALID_PARAM, 400)

        # Determine isWorking status
        is_working = order_to_query.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]
        
        # updateTime: last modification time of the order. Can be same as creation if no updates.
        # For simplicity, using order.timestamp (creation) if no specific update_time field exists on Order object.
        # A more accurate system would track last_update_timestamp on the Order object.
        update_time_ms = int((order_to_query.update_timestamp if hasattr(order_to_query, 'update_timestamp') and order_to_query.update_timestamp else order_to_query.timestamp) * 1000)

        response_data = {
            "symbol": order_to_query.symbol,
            "orderId": order_to_query.order_id,
            "orderListId": -1, 
            "clientOrderId": order_to_query.client_order_id or "",
            "price": str(order_to_query.price or "0"),
            "origQty": str(order_to_query.quantity),
            "executedQty": str(order_to_query.executed_quantity),
            "cummulativeQuoteQty": str(order_to_query.cummulative_quote_qty),
            "status": order_to_query.status.name, 
            "timeInForce": order_to_query.time_in_force or "",
            "type": order_to_query.order_type.name,
            "side": order_to_query.side.name,
            "stopPrice": str(order_to_query.stop_price or "0"), # Include if present
            "icebergQty": str(order_to_query.iceberg_qty or "0"), # Include if present
            "time": int(order_to_query.timestamp * 1000), # This is transactTime (creation time for order)
            "updateTime": update_time_ms, # Last update time
            "isWorking": is_working,
            "origQuoteOrderQty": str(order_to_query.quote_order_qty or "0.000000"),
            "selfTradePreventionMode": order_to_query.self_trade_prevention_mode or "NONE"
        }
        # Binance specific: if orderId was used for query, origClientOrderId might not be in response unless it exists on order.
        # If origClientOrderId was used for query, it should be in response.
        # Our logic ensures clientOrderId from order object is always used for that field.
        # To include origClientOrderId in response if it was used as a query param:
        if orig_client_order_id:
            response_data['origClientOrderId'] = orig_client_order_id
        # else, if not queried by origClientOrderId, Binance response doesn't explicitly have an 'origClientOrderId' field
        # unless it's the same as clientOrderId (which is already there).

        return jsonify(response_data)
    
    def _get_open_orders(self) -> Response:
        """查询当前挂单 - Binance compliant"""
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return self._error_response("API-key required for this endpoint.", INVALID_API_KEY_ORDER, 401)
        user_id = self.get_user_id_from_api_key(api_key)
        if not user_id:
            return self._error_response("Invalid API-key.", INVALID_API_KEY_ORDER, 401)

        data = request.args.to_dict()
        timestamp_str = data.get('timestamp')
        if not timestamp_str:
            return self._error_response("Mandatory parameter 'timestamp' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        is_valid_ts, ts_err_msg, ts_err_code = RequestValidator.validate_timestamp(timestamp_str)
        if not is_valid_ts:
            return self._error_response(ts_err_msg, ts_err_code, 400)

        symbol_param = data.get('symbol') # Optional
        
        open_orders_response = []
        
        # Determine which order books to iterate through
        order_books_to_check = []
        if symbol_param:
            if symbol_param not in self.matching_engine.order_books:
                # If a symbol is specified and it's invalid/unknown, Binance returns an empty array for openOrders.
                # Not an error, just no open orders for that (invalid) symbol.
                return jsonify([]) 
            order_books_to_check = [self.matching_engine.get_order_book(symbol_param)]
        else:
            order_books_to_check = self.matching_engine.order_books.values()
            
        for order_book in order_books_to_check:
            if not order_book: continue # Should not happen if get_order_book returns None for invalid symbol_param
            # Iterate through all orders in this book (both bids and asks sides)
            # The order_map in OrderBook should contain all orders for that symbol.
            for order_id_in_book, order_in_book in order_book.order_map.items():
                if order_in_book.user_id == user_id and order_in_book.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]:
                    update_time_ms = int((order_in_book.update_timestamp if hasattr(order_in_book, 'update_timestamp') and order_in_book.update_timestamp else order_in_book.timestamp) * 1000)
                    is_working = True # By definition, as we are checking NEW and PARTIALLY_FILLED

                    order_data = {
                        "symbol": order_in_book.symbol,
                        "orderId": order_in_book.order_id,
                        "orderListId": -1,
                        "clientOrderId": order_in_book.client_order_id or "",
                        "price": str(order_in_book.price or "0"),
                        "origQty": str(order_in_book.quantity),
                        "executedQty": str(order_in_book.executed_quantity),
                        "cummulativeQuoteQty": str(order_in_book.cummulative_quote_qty),
                        "status": order_in_book.status.name,
                        "timeInForce": order_in_book.time_in_force or "",
                        "type": order_in_book.order_type.name,
                        "side": order_in_book.side.name,
                        "stopPrice": str(order_in_book.stop_price or "0"),
                        "icebergQty": str(order_in_book.iceberg_qty or "0"),
                        "time": int(order_in_book.timestamp * 1000), # Creation time
                        "updateTime": update_time_ms, # Last update time
                        "isWorking": is_working,
                        "origQuoteOrderQty": str(order_in_book.quote_order_qty or "0.000000"),
                        "selfTradePreventionMode": order_in_book.self_trade_prevention_mode or "NONE"
                    }
                    open_orders_response.append(order_data)
                    
        return jsonify(open_orders_response)
    
    def _get_all_orders(self) -> Response:
        """获取所有订单 - Binance compliant"""
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return self._error_response("API-key required for this endpoint.", INVALID_API_KEY_ORDER, 401)
        user_id = self.get_user_id_from_api_key(api_key)
        if not user_id:
            return self._error_response("Invalid API-key.", INVALID_API_KEY_ORDER, 401)

        # Parameters can be in request body (form-data) or query string for GET
        data = {}
        if request.form:
            data = request.form.to_dict()
        elif request.args:
            data = request.args.to_dict()
        # No explicit JSON body for GET in typical REST, but Flask might allow it.
        # Binance docs specify query string or application/x-www-form-urlencoded for GET.

        symbol = data.get('symbol')
        limit_str = data.get('limit')

        if not symbol:
            return self._error_response("Mandatory parameter 'symbol' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        
        if not limit_str:
            return self._error_response("Mandatory parameter 'limit' was not sent, was empty/null, or malformed.", MANDATORY_PARAM_EMPTY_OR_MALFORMED, 400)
        
        try:
            limit = int(limit_str)
            if limit <= 0:
                return self._error_response("Invalid 'limit' format. Must be a positive integer.", INVALID_PARAM, 400)
        except ValueError:
            return self._error_response("Invalid 'limit' format. Expected an integer.", INVALID_PARAM, 400)

        all_orders = []
        # Trades in matching_engine.trades are expected to be stored chronologically (oldest first)
        # So, we iterate in reverse to get the most recent ones.
        # The trade objects in self.matching_engine.trades should ideally have a unique integer ID.
        # For now, if trade.trade_id is not an int, we might need to assign one or handle it.

        count = 0
        for trade in reversed(self.matching_engine.trades):
            if trade.symbol == symbol:
                # Assuming trade.trade_id is an integer or can be converted/mapped to one.
                # If trade.trade_id is a UUID string, Binance expects an int. This might need adjustment in Trade object or here.
                # For now, let's assume it can be a string if it uniquely identifies, though Binance uses int.
                # To be closer to Binance, we might use a simple counter or hash if trade.trade_id isn't an int.
                # Let's use a placeholder for trade.id if it's not an integer, as Binance expects int for trade IDs.
                trade_id_to_report = trade.trade_id
                if not isinstance(trade.trade_id, int):
                    # Fallback: use a hash of the string trade_id, then take a part of it to make it int-like
                    # This is a mock, a proper system would assign sequential integer IDs.
                    try:
                        trade_id_to_report = int(str(uuid.UUID(trade.trade_id).int)[:10]) # Example, may not be ideal
                    except ValueError: # if trade.trade_id is not even a valid UUID string
                        trade_id_to_report = count + 1 # Simplest mock ID

                all_orders.append({
                    "id": trade_id_to_report, # Binance expects integer trade ID
                    "price": str(trade.price),
                    "qty": str(trade.quantity),
                    "quoteQty": str(trade.price * trade.quantity), # Calculate quoteQty
                    "time": int(trade.timestamp * 1000),
                    # isBuyerMaker: True if the buyer was the maker. This requires knowing which order was resting.
                    # Simplified: assume taker for now. This needs more info from matching engine.
                    "isBuyerMaker": False, 
                    "isBestMatch": True # Simplified, assume all are best match for public trades
                })
                count += 1
                if count >= limit:
                    break

        return jsonify(all_orders)