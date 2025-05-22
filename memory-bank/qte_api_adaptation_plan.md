# QTE Flask API 适配与增强计划 (Phase 1.2)

**最后更新**: YYYY-MM-DD

**基于分析文档**: `memory-bank/qte_flask_api_analysis.md`

## 1. 目标

本计划旨在详细列出将 `qte/exchange/rest_api/rest_server.py` 及其依赖组件 (`MatchingEngine`, `AccountManager`, `RequestValidator`, `error_codes`) 适配至尽可能接近币安现货REST API行为所需的具体修改。

## 2. 通用修改和全局考虑

### 2.1 API路径版本统一
*   **当前**: 大部分QTE API使用 `/api/v1/` 前缀。
*   **目标**: 所有与币安对应的API端点应主要使用 `/api/v3/` 前缀。旧的 `/api/v1/` 可以暂时保留作为别名，或者在Flask蓝图/路由层面进行重定向，但新开发和测试应以 `/v3/` 为主。
*   **影响文件**: `qte/exchange/rest_api/rest_server.py` (路由注册部分)。

### 2.2 错误响应格式统一
*   **当前**: QTE使用 `_error_response(message, error_code, status_code)`，响应格式类似 `{"error": "message"}`，同时HTTP状态码可能变化。`error_code` 是QTE内部定义。
*   **目标**: 统一为币安的错误响应格式 `{"code": -xxxx, "msg": "error message"}`。HTTP状态码对于客户端错误通常是 `4xx` (例如 `400` Bad Request, `401` Unauthorized, `403` Forbidden)。
*   **影响文件**: `qte/exchange/rest_api/rest_server.py` (主要是 `_error_response` 方法的实现和所有调用它的地方), `qte/exchange/rest_api/error_codes.py`。
*   **行动**: 
    1.  修改 `error_codes.py`，使其包含与币安官方文档中对应的错误码和英文错误消息。
    2.  重构 `_error_response` 方法，使其接受币安标准的错误码和消息，并固定返回 `{"code": code, "msg": msg}` 的JSON结构，以及合适的HTTP状态码。

### 2.3 时间戳处理
*   **币安要求**: 大部分签名接口需要 `timestamp` 参数 (毫秒级Unix时间戳)，用于防止重放攻击。
*   **QTE现状**: 大部分接口不接收或处理 `timestamp`。
*   **行动 (API层面)**: 
    1.  对于所有币安对应的签名接口，QTE的Flask方法应能接收 `timestamp` 参数。
    2.  **初期可以不强制校验 `timestamp` 的时效性**，以简化 `MockBinanceGateway` 的开发 (网关仍需发送此参数)。
    3.  未来可以增加 `recvWindow` 逻辑，对时间戳进行校验。
*   **影响文件**: `qte/exchange/rest_api/rest_server.py` (所有需要签名的接口方法)。

### 2.4 认证机制 (临时适配策略)
*   **差异**: 币安使用HMAC SHA256签名，QTE使用`X-API-KEY`。
*   **临时策略**: `MockBinanceGateway` 在与QTE API交互时，将**不执行**币安标准的HMAC SHA256签名计算，而是直接在其请求头中包含一个预设的、QTE `AccountManager` 或 `RequestValidator` 能够识别的有效 `X-API-KEY`。
*   **QTE API层面**: 保持现有的 `X-API-KEY` 校验逻辑不变。未来若要追求高保真度，可为 `/api/v3/` 的签名接口实现HMAC SHA256校验逻辑。

### 2.5 数值型数据统一为字符串
*   **币安要求**: API响应中的所有价格、数量、金额等数值型数据均以字符串形式表示。
*   **QTE现状**: 部分可能直接返回数字类型。
*   **行动**: 确保所有从 `MatchingEngine` 和 `AccountManager` 获取并在API响应中出现的数值数据，在 `jsonify()` 之前都被转换为字符串。
*   **影响文件**: `qte/exchange/rest_api/rest_server.py` (所有构建响应的地方), `MatchingEngine`, `AccountManager` (其返回的数据结构也应注意此点)。

## 3. `rest_server.py` 端点修改清单

以下将针对 `memory-bank/qte_flask_api_analysis.md` 中分析的每个端点及其对应的QTE内部方法列出修改要点。

### 3.1 通用接口 (General Endpoints)

#### 3.1.1 `_ping()` (对应 `GET /api/v3/ping`)
*   **路径**: 确保注册到 `/api/v3/ping`。
*   **响应**: 修改为返回空JSON对象 `{}`。

#### 3.1.2 `_server_time()` (对应 `GET /api/v3/time`)
*   **路径**: 确保注册到 `/api/v3/time`。
*   **响应**: 保持 `{"serverTime": <timestamp_ms>}` 结构，确保时间戳为毫秒级整数。

#### 3.1.3 新增 `_exchange_info()` (对应 `GET /api/v3/exchangeInfo`)
*   **路径**: 实现并注册到 `GET /api/v3/exchangeInfo`。
*   **参数**: 应该能接收可选的 `symbol` 和 `symbols` (JSON数组字符串) 参数，并相应地过滤返回结果。
*   **逻辑**: 
    1.  从 `MatchingEngine` 获取所有或指定的交易对信息。
    2.  构建与币安 `exchangeInfo` 响应高度相似的JSON结构。至少包含 `timezone`, `serverTime`, `rateLimits` (可模拟), `exchangeFilters` (可为空), 和 `symbols` 数组。
    3.  `symbols` 数组中每个对象需包含: `symbol`, `status`, `baseAsset`, `quoteAsset`, `baseAssetPrecision`, `quoteAssetPrecision`, `baseCommissionPrecision`, `quoteCommissionPrecision`, `orderTypes` (支持的订单类型列表), `icebergAllowed`, `ocoAllowed`, `quoteOrderQtyMarketAllowed`, `allowTrailingStop`, `cancelReplaceAllowed`, `isSpotTradingAllowed`, `isMarginTradingAllowed`, 和关键的 `filters` 数组。
    4.  `filters` 数组至少应模拟: 
        *   `PRICE_FILTER`: `minPrice`, `maxPrice`, `tickSize`
        *   `LOT_SIZE` (或 `MARKET_LOT_SIZE`): `minQty`, `maxQty`, `stepSize`
        *   `MIN_NOTIONAL`: `minNotional`, `applyToMarket`
        *   其他如 `PERCENT_PRICE`, `MAX_NUM_ORDERS`, `MAX_NUM_ALGO_ORDERS` 等可逐步添加或用默认值模拟。
*   **`MatchingEngine` 依赖**: 需要 `MatchingEngine` 提供获取交易对详细规格（精度、过滤器规则等）的方法。

### 3.2 市场数据接口 (Market Data Endpoints)

#### 3.2.1 `_ticker_price()` (对应 `GET /api/v3/ticker/price`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **参数**: 支持可选的 `symbol` 和 `symbols` (JSON数组字符串) 参数。
*   **响应结构**: 
    *   单个 `symbol`: `{"symbol": "SYMBOL_VALUE", "price": "PRICE_VALUE"}`。
    *   多个/所有 `symbols`: `[{"symbol": "S1", "price": "P1"}, {"symbol": "S2", "price": "P2"}, ...]`。
*   **`MatchingEngine` 依赖**: `get_current_price(symbol)` 和 `get_all_market_prices()` 返回的结构需要适配，确保价格是字符串。

#### 3.2.2 `_ticker_24hr()` (对应 `GET /api/v3/ticker/24hr`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **参数**: 支持可选的 `symbol` 和 `symbols` (JSON数组字符串) 参数。
*   **响应结构**: 
    *   单个/多个: 确保返回对象/对象列表，每个对象包含币安定义的所有字段 (e.g., `symbol`, `priceChange`, `priceChangePercent`, `weightedAvgPrice`, `prevClosePrice`, `lastPrice`, `lastQty`, `bidPrice`, `askPrice`, `openPrice`, `highPrice`, `lowPrice`, `volume`, `quoteVolume`, `openTime`, `closeTime`, `firstId`, `lastId`, `count`)。所有数值型数据为字符串。
*   **`MatchingEngine` 依赖**: `get_ticker_24hr(symbol)` 和 `get_all_tickers_24hr()` 需返回包含所有上述字段的字典/字典列表。

#### 3.2.3 `_order_book()` (对应 `GET /api/v3/depth`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **参数**: `symbol` (必需), `limit` (可选, 默认调整为100，最大值考虑与币安对齐，如500或1000，取决于`MatchingEngine`能力)。
*   **响应结构**: 确保为 `{"lastUpdateId": ..., "bids": [["price_str", "qty_str"], ...], "asks": [["price_str", "qty_str"], ...]}`。 `bids` 降序，`asks` 升序。
*   **`MatchingEngine` 依赖**: `get_order_book_depth(symbol, limit)` 需返回此结构，并包含 `lastUpdateId` (可以是模拟的序列号或时间戳)。

#### 3.2.4 `_recent_trades()` (对应 `GET /api/v3/trades`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **参数**: `symbol` (必需), `limit` (可选, 默认调整为500，最大1000，取决于`MatchingEngine`能力)。
*   **响应结构**: 返回对象列表，每个对象包含币安定义的字段 (`id`, `price`, `qty`, `quoteQty`, `time`, `isBuyerMaker`, `isBestMatch`)。数值为字符串。
*   **`MatchingEngine` 依赖**: `get_recent_trades(symbol, limit)` 需返回此结构。

#### 3.2.5 `_klines()` (对应 `GET /api/v3/klines`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **参数**: `symbol`, `interval` (必需)。`startTime`, `endTime`, `limit` (可选, `limit` 默认500，最大1000)。
*   **响应结构**: 返回列表的列表 `[[openTime, open, high, low, close, volume, closeTime, quoteAssetVolume, numberOfTrades, takerBuyBaseAssetVolume, takerBuyQuoteAssetVolume, ignore], ...]`。所有内部元素按顺序，数值型为字符串。
*   **`MatchingEngine` 依赖**: `get_klines(...)` 需返回此结构。

#### 3.2.6 `_avg_price()` (对应 `GET /api/v3/avgPrice`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **参数**: `symbol` (必需)。
*   **响应结构**: `{"mins": simulated_mins, "price": "PRICE_VALUE"}`。`simulated_mins` 可以是固定值（如5）或基于 `MatchingEngine` 计算逻辑。
*   **`MatchingEngine` 依赖**: `get_average_price(symbol)` 应能支持返回这种结构或提供计算所需数据。

### 3.3 账户接口 (Account Endpoints)

#### 3.3.1 `_get_account_info()` (对应 `GET /api/v3/account`)
*   **路径**: 确保注册到 `/api/v3/account` (也处理 `/api/v1/account` 的兼容)。
*   **认证**: 保持 `X-API-KEY`，但方法应接收 `timestamp` (初期可不校验), `recvWindow` (可选), `omitZeroBalances` (可选) 参数。
*   **响应结构**: 大幅增强。需包含 `makerCommission`, `takerCommission`, `buyerCommission`, `sellerCommission`, `canTrade`, `canWithdraw`, `canDeposit`, `updateTime`, `accountType`, `balances` (每个含 `asset`, `free`, `locked` - 字符串), `permissions` (e.g., `["SPOT"]`), `uid`, `preventSor`。许多字段可以是模拟的固定值。
*   **`AccountManager` 依赖**: `get_account_info(api_key, omitZeroBalances_flag)` 需返回包含所有上述字段的字典。

### 3.4 交易接口 (Trading Endpoints)

#### 3.4.1 `_place_order()` (对应 `POST /api/v3/order`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **认证**: `X-API-KEY`。方法需接收币安标准下单参数，特别是 `symbol`, `side`, `type`, `timestamp` (必需)。条件必需/可选参数如 `timeInForce`, `quantity`, `quoteOrderQty`, `price`, `stopPrice`, `newClientOrderId` (替換 `client_order_id`), `newOrderRespType`。
*   **参数处理**: 
    *   在方法内部，基于 `type` 处理不同订单类型的逻辑和所需参数。
    *   支持 `LIMIT`, `MARKET`。逐步考虑 `STOP_LOSS`, `TAKE_PROFIT` 系列 (如果 `MatchingEngine` 支持)。
    *   支持 `timeInForce` (GTC, IOC, FOK for LIMIT)。
    *   支持 `newOrderRespType` (ACK, RESULT, FULL)，这会影响返回的响应结构。
*   **响应结构 (基于 `newOrderRespType`, 默认FULL)**: 包含 `symbol`, `orderId`, `orderListId` (-1 if not OCO), `clientOrderId`, `transactTime`, `price`, `origQty`, `executedQty`, `cummulativeQuoteQty`, `status`, `timeInForce`, `type`, `side`, `fills` (成交列表，每个fill包含 `price`, `qty`, `commission`, `commissionAsset`, `tradeId`)。
*   **`MatchingEngine` 依赖**: `place_order()` 需接收更丰富的参数，并返回包含上述所有字段的详细订单信息或确认信息。

#### 3.4.2 `_get_order_status()` (对应 `GET /api/v3/order`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **认证**: `X-API-KEY`。接收参数 `symbol` (必需), `orderId` 或 `origClientOrderId`, `timestamp`。
*   **逻辑**: 支持通过 `orderId` 或 `origClientOrderId` 查询。
*   **响应结构**: 与 `POST /api/v3/order` 的 `FULL` 响应结构一致。
*   **`MatchingEngine` 依赖**: `get_order_status(identifier, id_type, symbol)` 需返回包含所有上述字段的订单详情。

#### 3.4.3 `_cancel_order()` (对应 `DELETE /api/v3/order`)
*   **路径**: 确保 `/v3/` 路径正确。
*   **参数获取**: 从 `request.args` 或路径参数获取，而不是 `request.form`。
*   **认证**: `X-API-KEY`。接收参数 `symbol` (必需), `orderId` 或 `origClientOrderId`, `newClientOrderId` (可选的撤单自定义ID), `timestamp`。
*   **响应结构**: 与查询订单类似，返回被撤销订单的详细信息，状态为 `CANCELED`。
*   **`MatchingEngine` 依赖**: `cancel_order(identifier, id_type, symbol)` 需返回被撤销订单的详细信息。

#### 3.4.4 `_get_open_orders()` (对应 `GET /api/v3/openOrders`)
*   **路径**: 注册为 `/api/v3/openOrders` (原 `/api/v1/open_orders` 可兼容)。
*   **认证**: `X-API-KEY`。接收参数 `symbol` (可选), `timestamp`。
*   **响应结构**: 返回订单对象列表，每个对象结构与 `GET /api/v3/order` 的 `FULL` 响应一致。
*   **`AccountManager` 依赖**: `get_open_orders(api_key, symbol)` 返回的列表内订单对象需符合该结构。

#### 3.4.5 `_get_all_orders()` (方法已存在，需绑定到 `GET /api/v3/allOrders`)
*   **路径**: 绑定到 `GET /api/v3/allOrders`。
*   **认证**: `X-API-KEY`。接收参数 `symbol` (必需), `orderId` (可选, 查询起始ID), `startTime`, `endTime`, `limit` (可选), `timestamp`。
*   **参数名统一**: `start_time` -> `startTime`, `end_time` -> `endTime`。
*   **响应结构**: 返回订单对象列表，每个对象结构与 `GET /api/v3/order` 的 `FULL` 响应一致。
*   **`AccountManager` 依赖**: `get_all_orders(api_key, symbol, startTime, endTime, limit, from_order_id)` 返回的列表内订单对象需符合该结构。

## 4. `MatchingEngine` 修改建议

*   **交易对规格**: 提供方法获取交易对的详细规格信息，包括精度 (baseAsset, quoteAsset, baseCommission, quoteCommission), 订单类型支持, 状态, 以及所有过滤器 (`PRICE_FILTER`, `LOT_SIZE`, `MIN_NOTIONAL` 等) 的参数。供 `_exchange_info()` 使用。
*   **24hr Ticker**: `get_ticker_24hr()` 和 `get_all_tickers_24hr()` 返回的字典需包含币安定义的所有字段，所有数值型数据（价格、量）为字符串。
*   **Order Book**: `get_order_book_depth()` 需返回 `lastUpdateId`，bids/asks 为 `price_str`, `qty_str` 的列表的列表。
*   **Recent Trades**: `get_recent_trades()` 返回的字典列表需包含 `id`, `quoteQty`, `time`, `isBuyerMaker`, `isBestMatch`。数值为字符串。
*   **Klines**: `get_klines()` 返回的内部列表需严格按币安12元素顺序，数值为字符串。
*   **Average Price**: `get_average_price()` 考虑返回 `{"mins": ..., "price": "..."}` 或相关数据。
*   **Place Order**: `place_order()` 方法需：
    *   接收更多参数以支持不同订单类型 (`type`), `timeInForce`, `quoteOrderQty`, `stopPrice`, `newClientOrderId`, `newOrderRespType`。
    *   返回更详细的订单信息对象或确认对象，包含 `orderId`, `orderListId`, `clientOrderId`, `transactTime`, `price`, `origQty`, `executedQty`, `cummulativeQuoteQty`, `status`, `timeInForce`, `type`, `side`, `fills`。
*   **Order Status/Cancel**: `get_order_status()` 和 `cancel_order()` 需支持通过 `symbol` 和 `origClientOrderId` (除了 `orderId`) 定位订单，并返回完整的订单信息对象。
*   **数据类型**: 确保所有返回给API层并最终进入JSON响应的价格、数量等数值都已是字符串形式或可以轻易被API层转换为字符串。

## 5. `AccountManager` 修改建议

*   **Account Info**: `get_account_info()` 需返回更完整的账户信息字典，包含币安定义的多个字段（佣金费率、权限、`updateTime` 等），即使部分是模拟值。`balances` 内数值为字符串。考虑 `omitZeroBalances` 参数。
*   **Open/All Orders**: `get_open_orders()` 和 `get_all_orders()` 返回的订单对象列表，其内部订单结构需与币安 `FULL` 订单响应一致。考虑 `get_all_orders` 支持 `from_order_id` 参数。

## 6. `RequestValidator` 和 `error_codes.py` 修改建议

*   **`error_codes.py`**: 全面替换为币安的错误码和对应的英文错误消息。定义一个映射或直接使用币安的 `-xxxx` 编码。
*   **`RequestValidator.validate_request()`**: 保持 `X-API-KEY` 校验。如果未来QTE API要支持真正的签名校验，这里将是主要修改点。
*   **参数校验逻辑**: `rest_server.py` 中的各个API方法内部的参数校验逻辑需要增强，以匹配币安对各参数的要求（如类型、范围、依赖关系）。

## 7. 下一步

将此计划作为 Phase 1.3 及后续实施阶段的指导蓝图。优先修改API路径、错误响应格式、以及 `_exchange_info` 端点的实现，因为这些是 `vnpy` 网关能与QTE API初步对接的基础。 