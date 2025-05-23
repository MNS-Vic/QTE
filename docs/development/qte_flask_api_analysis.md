# QTE Flask API (qte/exchange/rest_api/backup/rest_server.py) 与币安现货API对比分析

**最后更新**: YYYY-MM-DD (请在此处填写实际分析日期)

## 1. 概述

本文档基于对 `qte/exchange/rest_api/backup/rest_server.py` 文件的分析，旨在将QTE现有的Flask API与币安官方现货REST API进行对比，找出差异并提出适配建议，以便后续创建一个能与此模拟API交互的自定义`vnpy`网关 (`MockBinanceGateway`)。

**QTE Flask API基本情况:**
*   **实现文件**: `qte/exchange/rest_api/backup/rest_server.py`
*   **API版本前缀**: `/api/v1/`
*   **认证方式**: 通过请求头 `X-API-KEY` 传递API密钥，服务器端进行简单校验。
*   **错误响应格式**: `{"error": "message"}`
*   **时间单位**: 时间戳普遍使用毫秒。

**币安现货API基本情况:**
*   **API版本前缀**: `/api/v3/`
*   **认证方式**: 对于签名接口，使用HMAC SHA256签名。公开接口无需签名。
*   **错误响应格式**: `{"code": -xxxx, "msg": "error message"}`
*   **时间单位**: 时间戳默认为毫秒。

## 2. 端点详细对比分析

### 2.1 通用接口 (General Endpoints)

#### 2.1.1 测试服务器连通性 (Ping)
*   **币安 API**: `GET /api/v3/ping`
    *   参数: 无
    *   响应: `{}` (空对象，状态码 200表示成功)
*   **QTE API**: `GET /api/v1/ping`
    *   实现: `_ping()` 方法
    *   参数: 无
    *   响应: `{"status": "ok"}`
*   **对比与建议**:
    *   **路径**: 版本号不同。建议QTE API支持别名或调整为 `/api/v3/ping`。
    *   **响应**: 币安返回空对象，QTE返回 `{"status": "ok"}`。为严格模拟，QTE可改为空对象。但当前响应也足以判断连通性，`MockBinanceGateway` 可适配。
    *   **结论**: 基本可直接使用，`MockBinanceGateway` 稍作适配即可。

#### 2.1.2 获取服务器时间 (Server Time)
*   **币安 API**: `GET /api/v3/time`
    *   参数: 无
    *   响应: `{"serverTime": 1499827319559}` (毫秒级时间戳)
*   **QTE API**: `GET /api/v1/time`
    *   实现: `_server_time()` 方法
    *   参数: 无
    *   响应: `{"serverTime": 1628888888000}` (示例, `int(time.time() * 1000)`)
*   **对比与建议**:
    *   **路径**: 版本号不同。建议QTE API支持别名或调整为 `/api/v3/time`。
    *   **响应**: 格式和单位均与币安一致。
    *   **结论**: 高度兼容，`MockBinanceGateway` 调整路径即可。

#### 2.1.3 获取交易所交易规则和交易对信息 (Exchange Information)
*   **币安 API**: `GET /api/v3/exchangeInfo`
    *   参数: `symbol` (可选, 单个交易对), `symbols` (可选, 多个交易对的JSON数组字符串)
    *   响应: 包含时区、服务器时间、费率限制、过滤器、交易对详细信息 (symbol, status, baseAsset, quoteAsset, filters等) 的复杂JSON对象。
*   **QTE API**: **当前 `rest_server.py` 中未找到直接对应的端点。**
    *   `MatchingEngine` 类 (`self.matching_engine`) 可能包含交易对信息和规则，但未通过API暴露。
*   **对比与建议**:
    *   **缺失关键接口**: 此接口对于`vnpy`网关初始化至关重要，用于获取所有交易对的元数据（如价格精度、数量精度、最小下单量等）。
    *   **行动项**: **必须在QTE Flask API中实现此端点。**
        1.  设计API路径，建议为 `GET /api/v1/exchangeInfo` 或直接模拟币安的 `GET /api/v3/exchangeInfo`。
        2.  从 `self.matching_engine` 或相关配置中提取必要的交易对信息和交易规则。
        3.  构建与币安 `exchangeInfo` 响应结构尽可能相似的JSON对象。至少需要包含 `symbols` 数组，每个symbol对象包含 `symbol`, `status`, `baseAsset`, `quoteAsset`, `baseAssetPrecision`, `quoteAssetPrecision`, 以及关键的 `filters` (如 `PRICE_FILTER`, `LOT_SIZE`, `MIN_NOTIONAL`)。
    *   **参考**: 仔细研究币安 `GET /api/v3/exchangeInfo` 的响应结构。

### 2.2 市场数据接口 (Market Data Endpoints)

#### 2.2.1 获取最新价格 (Ticker Price)
*   **币安 API**: `GET /api/v3/ticker/price`
    *   参数: `symbol` (可选, 单个交易对), `symbols` (可选, 多个交易对的JSON数组字符串 e.g. `["BTCUSDT","BNBUSDT"]`)
    *   响应 (单个symbol): `{"symbol": "BTCUSDT", "price": "40000.00000000"}`
    *   响应 (多个symbols): `[{"symbol": "BTCUSDT", "price": "40000.00"}, {"symbol": "ETHUSDT", "price": "3000.00"}]`
*   **QTE API**: `GET /api/v3/ticker/price` (也兼容 `/api/v1/ticker/price`)
    *   实现: `_ticker_price()` 方法 (lines 274-291 in `rest_server.py`)
    *   参数: `symbol` (可选, 从 `request.args.get('symbol')` 获取)
    *   响应 (单个symbol, price found): `jsonify({symbol: str(price)})` -> `{"BTCUSDT": "40000.00"}` (注意key是symbol本身)
    *   响应 (单个symbol, price not found): `_error_response("未找到指定交易对的价格", error_code=PRICE_NOT_FOUND, status_code=404)` -> `{"code": -xxxx, "msg": "未找到指定交易对的价格"}`
    *   响应 (无symbol, 获取所有): `jsonify(prices)` (prices是一个 `Dict[str, str]` 形如 `{"BTCUSDT": "40000.00", ...}`)
*   **对比与建议**:
    *   **路径**: `/v3/` 路径匹配。
    *   **参数**: 
        *   QTE支持单个 `symbol` 参数，与币安一致。
        *   QTE似乎通过不提供 `symbol` 参数来获取所有交易对价格，而币安使用 `symbols` (JSON数组字符串) 参数来获取多个特定交易对的价格。币安不传参数的行为是返回所有交易对信息。
        *   **建议**: QTE可以考虑支持 `symbols` 参数以更精确地匹配币安行为。如果QTE的无 `symbol` 参数行为是返回所有，这与币安一致。
    *   **响应结构**: 
        *   **单个 symbol**: QTE返回 `{"SYMBOL_VALUE": "PRICE_VALUE"}` (例如 `{"BTCUSDT": "40000.00"}`)，而币安返回 `{"symbol": "SYMBOL_VALUE", "price": "PRICE_VALUE"}`。**这是一个显著差异。**
        *   **多个/所有 symbols**: QTE返回一个大的 `Dict[str, str]` (例如 `{"BTCUSDT": "40000.00", "ETHUSDT": "3000.00"}`)，而币安返回一个 `List[Dict[str, str]]` (例如 `[{"symbol": "BTCUSDT", ...}, {"symbol": "ETHUSDT", ...}]`)。**这也是一个显著差异。**
    *   **行动项**: **强烈建议修改QTE的响应结构以匹配币安。**
        1.  对于单个 `symbol`，返回 `{"symbol": symbol, "price": str(price)}`。
        2.  对于无参数或 `symbols` 参数的情况，返回一个对象列表 `[{"symbol": s, "price": p}, ...]`。
        3.  需要确认 `self.matching_engine.get_all_market_prices()` 的返回类型并进行相应处理。

#### 2.2.2 24小时价格变动情况 (24hr Ticker)
*   **币安 API**: `GET /api/v3/ticker/24hr`
    *   参数: `symbol` (可选), `symbols` (可选)
    *   响应 (单个): 包含 `symbol`, `priceChange`, `priceChangePercent`, `weightedAvgPrice`, `prevClosePrice`, `lastPrice`, `lastQty`, `bidPrice`, `askPrice`, `openPrice`, `highPrice`, `lowPrice`, `volume`, `quoteVolume`, `openTime`, `closeTime`, `firstId`, `lastId`, `count` 等字段。
    *   响应 (多个): 上述对象的列表。
*   **QTE API**: `GET /api/v3/ticker/24hr` (也兼容 `/api/v1/ticker/24hr`)
    *   实现: `_ticker_24hr()` 方法 (lines 293-330)
    *   参数: `symbol` (可选)
    *   逻辑: 主要依赖 `self.matching_engine.get_ticker_24hr(symbol)`。
    *   响应 (单个, 找到ticker): `jsonify(ticker_data)` (ticker_data是 `self.matching_engine.get_ticker_24hr` 的返回)
    *   响应 (未找到): `_error_response("未找到指定交易对的24小时行情数据", error_code=TICKER_NOT_FOUND, status_code=404)`
    *   响应 (无symbol, 获取所有): `jsonify(all_tickers)` (all_tickers是 `List[Dict]`, 来自 `self.matching_engine.get_all_tickers_24hr()`)
*   **对比与建议**:
    *   **路径**: 匹配。
    *   **参数**: 与 `ticker/price` 类似，QTE支持单个 `symbol`，不传 `symbol` 获取所有。币安还支持 `symbols` JSON数组。
        *   **建议**: 考虑支持 `symbols` 参数。
    *   **响应结构**: 
        *   **关键**: 需要详细对比 `self.matching_engine.get_ticker_24hr()` 和 `get_all_tickers_24hr()` 返回的字典结构与币安响应的字段是否完全一致（包括字段名、数据类型、含义）。币安的字段非常多且具体。
        *   如果QTE返回的是列表（当无symbol时），这与币安一致。
    *   **行动项**: 
        1.  **验证 `MatchingEngine` 返回的24hr ticker数据结构**，确保所有币安定义的字段都存在且正确（特别是 `openTime`, `closeTime`, `firstId`, `lastId`, `count` 等可能需要撮合引擎深度支持的字段）。
        2.  确保价格、成交量等数值以字符串形式返回，符合币安规范。

#### 2.2.3 获取深度信息 (Order Book / Depth)
*   **币安 API**: `GET /api/v3/depth`
    *   参数: `symbol` (必需), `limit` (可选, 默认100; 最大5000。不同limit值有不同权重)。
    *   响应: `{"lastUpdateId": ..., "bids": [["price", "qty"], ...], "asks": [["price", "qty"], ...]}`
*   **QTE API**: `GET /api/v3/depth` (也兼容 `/api/v1/depth`)
    *   实现: `_order_book()` 方法 (lines 332-350)
    *   参数: `symbol` (必需, 从 `request.args.get('symbol')` 获取), `limit` (可选, 从 `request.args.get('limit', default=100, type=int)` 获取)。
    *   逻辑: 调用 `self.matching_engine.get_order_book_depth(symbol, limit)`。
    *   响应 (成功): `jsonify(depth_data)` (depth_data是 `self.matching_engine.get_order_book_depth` 的返回)
    *   响应 (symbol缺失): `_error_response("缺少symbol参数", error_code=MISSING_PARAMETER, status_code=400)`
*   **对比与建议**:
    *   **路径与参数**: 匹配良好。
    *   **响应结构**: 
        *   **关键**: 需要验证 `self.matching_engine.get_order_book_depth()` 返回的数据结构是否与币安完全一致，特别是 `lastUpdateId` 字段，以及 `bids` 和 `asks` 是价格和数量字符串的列表的列表 `List[List[str]]`。
        *   币安的 `bids` 是按价格降序，`asks` 是按价格升序。
    *   **行动项**: 
        1.  **验证 `MatchingEngine` 返回的深度数据结构和排序**。确保价格和数量是字符串。
        2.  确保 `lastUpdateId` 的模拟（可以是订单簿最后更新的时间戳或一个序列号）。

#### 2.2.4 获取近期成交 (Recent Trades)
*   **币安 API**: `GET /api/v3/trades`
    *   参数: `symbol` (必需), `limit` (可选, 默认500, 最大1000)。
    *   响应: `[{"id": ..., "price": "", "qty": "", "quoteQty": "", "time": ..., "isBuyerMaker": ..., "isBestMatch": ...}, ...]`
*   **QTE API**: `GET /api/v3/trades` (也兼容 `/api/v1/trades`)
    *   实现: `_recent_trades()` 方法 (lines 352-377)
    *   参数: `symbol` (必需), `limit` (可选, 默认50, 最大500)。
    *   逻辑: 调用 `self.matching_engine.get_recent_trades(symbol, limit)`。
    *   响应 (成功): `jsonify(trades_data)` (trades_data是 `self.matching_engine.get_recent_trades` 的返回)
*   **对比与建议**:
    *   **路径与参数**: 匹配，但QTE的 `limit` 默认值和最大值与币安不同。
        *   **建议**: 考虑将QTE的 `limit` 默认值和最大值调整为与币安一致 (默认500, 最大1000)，但这取决于 `MatchingEngine` 的能力。
    *   **响应结构**: 
        *   **关键**: 需要验证 `self.matching_engine.get_recent_trades()` 返回的列表内字典结构是否与币安完全一致。币安包含 `id` (成交ID), `quoteQty` (成交额), `time` (毫秒时间戳), `isBuyerMaker` (boolean), `isBestMatch` (boolean)。
    *   **行动项**: 
        1.  **验证 `MatchingEngine` 返回的成交数据结构**，确保所有币安字段存在且类型正确（价格、数量、成交额为字符串，时间戳为毫秒，布尔值为布尔型）。

#### 2.2.5 获取K线数据 (Klines)
*   **币安 API**: `GET /api/v3/klines`
    *   参数: `symbol` (必需), `interval` (必需, e.g., 1m, 5m, 1h, 1d), `startTime` (可选, 毫秒), `endTime` (可选, 毫秒), `limit` (可选, 默认500, 最大1000)。
    *   响应: `[[openTime, open, high, low, close, volume, closeTime, quoteAssetVolume, numberOfTrades, takerBuyBaseAssetVolume, takerBuyQuoteAssetVolume, ignore], ...]` (每个元素都是一个数组，数值型数据通常为字符串)
*   **QTE API**: `GET /api/v3/klines` (也兼容 `/api/v1/klines`)
    *   实现: `_klines()` 方法 (lines 379-434)
    *   参数: `symbol` (必需), `interval` (必需), `startTime` (可选), `endTime` (可选), `limit` (可选, 默认500)。
    *   逻辑: 参数校验后调用 `self.matching_engine.get_klines(symbol, interval, startTime, endTime, limit)`。
    *   响应 (成功): `jsonify(klines_data)` (klines_data是 `self.matching_engine.get_klines` 的返回)
*   **对比与建议**:
    *   **路径与参数**: 匹配良好。
    *   **响应结构**: 
        *   **关键**: 需要验证 `self.matching_engine.get_klines()` 返回的数据结构是否为列表的列表，并且内部列表的12个元素的顺序、含义和数据类型（特别是数值是否为字符串）是否与币安完全一致。
    *   **行动项**: 
        1.  **验证 `MatchingEngine` 返回的K线数据结构和内容**。确保所有12个字段都按币安顺序提供，数值型数据为字符串。

#### 2.2.6 获取平均价格 (Average Price)
*   **币安 API**: `GET /api/v3/avgPrice`
    *   参数: `symbol` (必需)
    *   响应: `{"mins": 5, "price": "9300.00000"}` (mins是计算平均价的分钟数)
*   **QTE API**: `GET /api/v3/avgPrice`
    *   实现: `_avg_price()` 方法 (lines 898-929 in `rest_server.py` outline)
    *   参数: `symbol` (必需)
    *   逻辑: 调用 `self.matching_engine.get_average_price(symbol)`。
    *   响应 (成功): `jsonify(avg_price_data)` (avg_price_data 结构未知，需查看实现)
    *   响应 (symbol缺失/错误): 包含错误处理。
*   **对比与建议**:
    *   **路径与参数**: 匹配。
    *   **响应结构**: 
        *   **关键**: 需要验证 `self.matching_engine.get_average_price()` 返回的数据结构。币安返回 `{"mins": ..., "price": "..."}`。QTE的实现需要确认是否包含 `mins` 字段以及其含义（币安的是指过去5分钟均价）。
    *   **行动项**: 
        1.  **检查 `_avg_price` 方法和 `MatchingEngine.get_average_price` 的实现**，确认返回结构和 `mins` 字段的逻辑。若要严格模拟币安，`mins` 字段应该存在且有意义（例如，如果QTE计算的是特定周期的均价，可以用该周期表示）。

### 2.3 账户接口 (Account Endpoints)

所有账户相关的接口通常需要签名认证。

#### 2.3.1 查询账户信息 (Account Information)
*   **币安 API**: `GET /api/v3/account`
    *   **签名**: 是 (HMAC SHA256)
    *   **参数**: `timestamp` (必需), `recvWindow` (可选), `omitZeroBalances` (可选, 2024-04-02新增)
    *   **响应**: 包含 `makerCommission`, `takerCommission`, `buyerCommission`, `sellerCommission`, `canTrade`, `canWithdraw`, `canDeposit`, `updateTime`, `accountType`, `balances` (一个包含 `asset`, `free`, `locked` 的对象列表), `permissions` (e.g., `["SPOT"]`), `uid` (2023-07-11 新增), `preventSor` (2023-07-11 新增) 等众多字段。
*   **QTE API**: `GET /api/v1/account` (在 `rest_server.py` 中通过 `_get_account_info` 实现, lines 608-631)
    *   **签名**: QTE使用 `X-API-KEY` 进行简单认证，没有复杂的签名过程。
    *   **参数**: 无显式参数，依赖请求头中的 `X-API-KEY`。
    *   **逻辑**: 
        *   通过 `self.validator.validate_request(request)` 校验API Key。
        *   调用 `self.account_manager.get_account_info(api_key)` 获取账户数据。
    *   **响应 (成功)**: `jsonify(account_info)` (其中 `account_info` 的结构示例为 `{"userId": "user1", "canTrade": True, "balances": [{"asset": "BTC", "free": "10.0", "locked": "0.5"}, ...]}`)
    *   **响应 (API Key无效/未找到账户)**: `_error_response`
*   **对比与建议**:
    *   **路径**: QTE为 `/api/v1/account`，币安为 `/api/v3/account`。
        *   **建议**: QTE可以考虑添加 `/api/v3/account` 别名或迁移。 `MockBinanceGateway` 需要适配此路径。
    *   **认证**: **重大差异**。
        *   币安使用HMAC SHA256签名。QTE使用简单的API Key头传递。
        *   **行动项**: 为了让 `vnpy` 官方币安网关或其修改版能直接与QTE模拟盘交互，QTE的 `MockBinanceGateway` 必须处理这种差异。有两个主要方向：
            1.  **`MockBinanceGateway` 内部不做签名**: `MockBinanceGateway` 在向QTE API发送请求时，不执行币安标准的签名流程，而是直接传递预设的 `X-API-KEY`。这是最简单的实现方式。
            2.  **QTE API 实现签名校验 (复杂，但更逼真)**: 修改QTE的 `/api/v3/account` (及其他需签名接口) 以支持HMAC SHA256签名校验。这需要QTE端存储 `api_secret` 并实现校验逻辑。如果走这条路，`MockBinanceGateway` 就可以使用标准的签名流程。
        *   **初步建议**: 先采用方案1，在 `MockBinanceGateway` 中简化认证逻辑，确保能快速打通。未来如果追求更高保真度，可以考虑方案2。
    *   **参数**: 
        *   币安需要 `timestamp`。QTE不需要。`MockBinanceGateway` 在调用QTE时可以不传 `timestamp`。
        *   币安有可选的 `recvWindow` 和 `omitZeroBalances`。QTE目前不支持。
        *   **建议**: QTE的 `AccountManager.get_account_info` 可以考虑未来支持 `omitZeroBalances` 逻辑。
    *   **响应结构**: 
        *   QTE的示例响应 `{"userId": ..., "canTrade": ..., "balances": [...]}` 只包含了币安响应中的一部分核心字段。
        *   币安的 `balances` 列表内对象包含 `asset`, `free`, `locked`。QTE的示例与之匹配。
        *   币安还包含 `makerCommission`, `takerCommission`, `canWithdraw`, `canDeposit`, `updateTime`, `accountType`, `permissions`, `uid`, `preventSor` 等。这些在QTE的示例中缺失。
        *   **行动项**: 
            1.  **大幅增强 `AccountManager.get_account_info` 返回的数据结构**，使其包含币安响应中的绝大部分关键字段，即使某些字段在QTE中只是模拟值或固定值（例如 `canWithdraw`, `canDeposit`, `accountType`, `permissions` 可以是预设的模拟值）。
            2.  特别注意 `updateTime` (账户最后更新时间的毫秒时间戳) 和 `permissions` 字段的模拟。
            3.  确保 `balances` 中的 `free` 和 `locked` 是字符串。

### 2.4 交易接口 (Trading Endpoints)

交易接口均需要认证，且与币安API的认证方式差异同2.3.1所述。

#### 2.4.1 下新订单 (New Order)
*   **币安 API**: `POST /api/v3/order` (HMAC SHA256签名)
    *   **参数**: 
        *   必需: `symbol`, `side` (BUY/SELL), `type` (LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER), `timestamp`。
        *   条件必需 (取决于`type`): `timeInForce` (GTC, IOC, FOK - for LIMIT), `quantity`, `quoteOrderQty` (for MARKET), `price` (for LIMIT, STOP_LOSS_LIMIT, TAKE_PROFIT_LIMIT), `stopPrice` (for STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT)。
        *   可选: `newClientOrderId` (自定义订单ID), `strategyId`, `strategyType`, `icebergQty`, `newOrderRespType` (ACK, RESULT, FULL - 默认FULL)。
    *   **响应 (FULL)**: 包含 `symbol`, `orderId`, `orderListId`, `clientOrderId`, `transactTime`, `price`, `origQty`, `executedQty`, `cummulativeQuoteQty`, `status`, `timeInForce`, `type`, `side`, `fills` (成交列表) 等非常详细的订单信息。
*   **QTE API**: `POST /api/v1/order` (通过 `_place_order` 实现, lines 436-522)
    *   **认证**: `X-API-KEY`。
    *   **参数 (从 `request.form` 获取)**:
        *   必需: `symbol`, `side`, `type`, `quantity`。
        *   可选: `price` (如果类型不是MARKET), `client_order_id` (对应 `newClientOrderId`)。
    *   **逻辑**: 
        *   参数校验 (包括 `symbol` 是否存在, `type` 是否支持, `side` 是否有效, `quantity` 和 `price` 的有效性)。
        *   调用 `self.matching_engine.place_order()`。
        *   根据 `place_order` 的结果 (成功/失败，订单状态) 构建响应。
    *   **响应 (成功示例)**: `{"orderId": "some-uuid", "clientOrderId": "custom-id", "symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT", "quantity": "1.0", "price": "30000.0", "status": "NEW"}`。
    *   **响应 (失败)**: `_error_response` (包含具体错误信息，如余额不足、无效参数等)。
*   **对比与建议**:
    *   **路径与方法**: QTE为 `/api/v1/order` (POST)，币安为 `/api/v3/order` (POST)。建议QTE适配路径。
    *   **认证**: 同2.3.1，存在显著差异。`MockBinanceGateway` 需要适配。
    *   **参数**: 
        *   QTE的参数集是币安的子集。QTE目前只显式支持 `LIMIT` 和 `MARKET` 类型 (从代码逻辑看，其他类型可能未处理或报错)。
        *   币安的 `type` 支持更多高级订单类型 (STOP_LOSS, TAKE_PROFIT 系列)。
        *   币安有 `timeInForce`, `quoteOrderQty`, `stopPrice`, `newOrderRespType`, `icebergQty` 等QTE缺失的重要参数。
        *   QTE使用 `client_order_id`，币安是 `newClientOrderId`。
        *   币安必需 `timestamp`。
        *   **行动项**:
            1.  QTE应在 `_place_order` 中明确支持币安定义的各种 `type`，如果 `MatchingEngine` 不支持，API层应返回标准错误。
            2.  **考虑在QTE中逐步支持 `timeInForce` (至少GTC, IOC, FOK for LIMIT orders) 和 `quoteOrderQty` (for MARKET orders)。**
            3.  `newOrderRespType` 对 `vnpy` 很重要，`vnpy` 通常期望 `ACK` 或 `RESULT` 以快速响应。QTE当前行为类似 `RESULT` 或 `FULL`。可以考虑支持此参数，如果 `MatchingEngine` 能提供不同阶段的订单确认信息。
            4.  参数名 `client_order_id` -> `newClientOrderId`。
    *   **响应结构**: 
        *   QTE的成功响应字段远少于币安的 `FULL` 响应。币安的响应包含 `orderId`, `orderListId`, `transactTime`, `origQty`, `executedQty`, `cummulativeQuoteQty`, `status`, `timeInForce`, `type`, `side`, 甚至 `fills`。
        *   **行动项**: **大幅增强 `_place_order` 的成功响应结构**，以匹配币安的 `FULL` 响应。这需要 `MatchingEngine.place_order()` 返回更丰富的订单信息，特别是 `orderId`, `transactTime`, `status` (初始状态，如NEW)，以及在发生撮合时的 `executedQty`, `cummulativeQuoteQty`, `fills`。对于未立即成交的订单，`fills` 可以为空数组。

#### 2.4.2 查询订单状态 (Query Order)
*   **币安 API**: `GET /api/v3/order` (HMAC SHA256签名)
    *   **参数**: `symbol` (必需), `orderId` 或 `origClientOrderId` (两者至少一个), `timestamp` (必需)。
    *   **响应**: 与 `POST /api/v3/order` 的 `FULL` 响应结构类似，包含订单的当前完整信息。
*   **QTE API**: `GET /api/v1/order` (通过 `_get_order_status` 实现, lines 524-553)
    *   **认证**: `X-API-KEY`。
    *   **参数**: `order_id` (从 `request.args.get('order_id')` 获取，必需)。QTE似乎不支持通过 `client_order_id` 查询。
    *   **逻辑**: 调用 `self.matching_engine.get_order_status(order_id)`。
    *   **响应 (成功示例)**: `{"orderId": "some-uuid", ..., "status": "FILLED"}` (假设返回完整订单信息)。
*   **对比与建议**:
    *   **路径与方法**: QTE为 `/api/v1/order` (GET)，币安为 `/api/v3/order` (GET)。建议QTE适配路径。
    *   **认证**: 同上。
    *   **参数**: 
        *   币安必需 `symbol` 和 `timestamp`。QTE不需要。
        *   币安支持 `orderId` 或 `origClientOrderId`。QTE目前只支持 `order_id`。
        *   **行动项**: 
            1.  QTE的 `_get_order_status` 需要能够接收并处理 `symbol` 参数（即使 `MatchingEngine` 的查询可能不需要它，API层也应接收以保持一致性）。
            2.  QTE应考虑支持通过 `origClientOrderId` 查询订单，这需要 `MatchingEngine` 的支持。
            3.  `MockBinanceGateway` 调用QTE时需要处理 `timestamp` 的缺失。
    *   **响应结构**: 
        *   **关键**: 需要确保 `self.matching_engine.get_order_status()` 返回的订单信息结构与币安 `FULL` 响应一致。
        *   **行动项**: **验证并调整 `MatchingEngine.get_order_status` 的返回结构**，使其包含币安要求的所有字段 (e.g., `orderListId`, `price`, `origQty`, `executedQty`, `cummulativeQuoteQty`, `status`, `timeInForce`, `type`, `side`, `time` (下单时间), `updateTime` (最后更新时间), `fills` 如果有)。

#### 2.4.3 撤销订单 (Cancel Order)
*   **币安 API**: `DELETE /api/v3/order` (HMAC SHA256签名)
    *   **参数**: `symbol` (必需), `orderId` 或 `origClientOrderId` (两者至少一个), `newClientOrderId` (可选, 用户自定义的撤单操作ID), `timestamp` (必需)。
    *   **响应**: 包含 `symbol`, `orderId`, `origClientOrderId`, `orderListId`, `clientOrderId` (即请求中的 `newClientOrderId`), `price`, `origQty`, `executedQty`, `cummulativeQuoteQty`, `status` (通常为CANCELED), `timeInForce`, `type`, `side` 等被撤销订单的信息。
*   **QTE API**: `DELETE /api/v1/order` (通过 `_cancel_order` 实现, lines 555-583)
    *   **认证**: `X-API-KEY`。
    *   **参数**: `order_id` (从 `request.form.get('order_id')` 获取，必需 - 注意这里用了`request.form`，对于DELETE应该是`args`或路径参数，或者vnpy中 DELETE 请求也可能带body)。
    *   **逻辑**: 调用 `self.matching_engine.cancel_order(order_id)`。
    *   **响应 (成功示例)**: `{"orderId": "some-uuid", "status": "CANCELLED"}`。
*   **对比与建议**:
    *   **路径与方法**: QTE为 `/api/v1/order` (DELETE)，币安为 `/api/v3/order` (DELETE)。建议QTE适配路径。
    *   **认证**: 同上。
    *   **参数**: 
        *   币安必需 `symbol` 和 `timestamp`。QTE不需要。
        *   币安支持 `orderId` 或 `origClientOrderId`，以及可选的撤单ID `newClientOrderId`。QTE仅支持 `order_id`。
        *   QTE从 `request.form` 获取 `order_id`，对于DELETE请求，更常见的是从查询参数 `request.args` 或路径中获取。
        *   **行动项**: 
            1.  QTE的 `_cancel_order` 应从 `request.args` (或路径) 获取参数。
            2.  需要接收并处理 `symbol`。
            3.  考虑支持通过 `origClientOrderId` 撤单。
            4.  考虑支持 `newClientOrderId` (撤单操作ID)。
    *   **响应结构**: 
        *   QTE的响应远比币安简单。
        *   **行动项**: **大幅增强 `_cancel_order` 的成功响应结构**，以匹配币安的撤单响应。这需要 `MatchingEngine.cancel_order()` 返回被撤销订单的详细信息。

#### 2.4.4 查询当前挂单 (Current Open Orders)
*   **币安 API**: `GET /api/v3/openOrders` (HMAC SHA256签名)
    *   **参数**: `symbol` (可选, 不提供则查所有), `timestamp` (必需)。
    *   **响应**: 一个订单对象列表，每个对象的结构与查询单个订单的响应类似。
*   **QTE API**: `GET /api/v1/open_orders` (通过 `_get_open_orders` 实现, lines 585-606)
    *   **认证**: `X-API-KEY`。
    *   **参数**: `symbol` (可选, 从 `request.args.get('symbol')` 获取)。
    *   **逻辑**: 调用 `self.account_manager.get_open_orders(api_key, symbol)`。
    *   **响应 (成功示例)**: `[{"orderId": "uuid1", ...}, {"orderId": "uuid2", ...}]`。
*   **对比与建议**:
    *   **路径**: QTE为 `/api/v1/open_orders`，币安为 `/api/v3/openOrders`。建议QTE适配。
    *   **认证**: 同上。
    *   **参数**: 
        *   币安必需 `timestamp`。QTE不需要。
        *   参数 `symbol` 的行为一致。
    *   **响应结构**: 
        *   **关键**: 需要确保 `self.account_manager.get_open_orders()` 返回的列表内订单对象结构与币安的订单结构完全一致。
        *   **行动项**: **验证并调整 `AccountManager.get_open_orders` 的返回结构**。参考2.4.2查询订单的响应字段要求。

#### 2.4.5 查询所有订单 (All Orders - 包括历史订单)
*   **币安 API**: `GET /api/v3/allOrders` (HMAC SHA256签名)
    *   **参数**: `symbol` (必需), `orderId` (可选, 从此ID开始获取), `startTime` (可选), `endTime` (可选), `limit` (可选, 默认500, 最大1000), `timestamp` (必需)。
    *   **响应**: 一个订单对象列表，结构同上。
*   **QTE API**: **当前 `rest_server.py` 中未找到直接对应的端点 (`_get_all_orders` 方法存在但未被路由绑定 lines 751-775)**。
    *   `_get_all_orders` 方法定义: `def _get_all_orders(self): api_key = self.validator.validate_request(request)...orders = self.account_manager.get_all_orders(api_key, symbol, start_time, end_time, limit)...`
    *   参数: `symbol`, `start_time`, `end_time`, `limit` (从 `request.args` 获取)。
*   **对比与建议**:
    *   **缺失API路由**: QTE有实现逻辑但未暴露为API端点。
    *   **行动项**: 
        1.  **为 `_get_all_orders` 方法绑定API路由**，建议为 `GET /api/v3/allOrders`。
        2.  **认证**: 添加 `X-API-KEY` 认证逻辑（或未来适配签名）。
        3.  **参数**: 
            *   QTE的 `_get_all_orders` 逻辑需要 `symbol` 是必需的，与币安一致。
            *   币安还支持 `orderId` (作为查询起点)。QTE可考虑添加。
            *   币安需要 `timestamp`。
            *   QTE的 `start_time`, `end_time`, `limit` 命名与币安 `startTime`, `endTime`, `limit` 略有不同但含义一致。建议统一为驼峰式。
        4.  **响应结构**: 确保 `self.account_manager.get_all_orders()` 返回的列表内订单对象结构与币安的订单结构完全一致。

--- 
*API接口分析初步完成，后续需要根据这些分析点进行QTE代码的修改和`MockBinanceGateway`的设计。* 