# 币安API兼容性开发计划

## 一、现状分析

通过对币安API文档与当前QTE项目API实现的对比分析，发现以下关键差异：

### 1. API端点路径
- **币安**: 使用`/api/v3/`作为所有API的前缀
- **当前项目**: 使用`/api/v1/`作为API前缀
- **问题**: 需要将所有API路径更新以匹配币安标准

### 2. 错误响应格式
- **币安**: `{"code": <错误码>, "msg": "<错误消息>"}`
- **当前项目**: `{"code": <状态码>, "msg": "<错误消息>", "success": false}`
- **问题**: 移除多余的`success`字段并实现币安特定的错误码系统

### 3. 账户信息
- **币安**: 账户信息响应包含`preventSor`和`uid`字段
- **当前项目**: 未实现这些字段
- **问题**: 需要更新账户API响应格式

### 4. 订单相关字段
- **币安**: 多个API中包含`origQuoteOrderQty`、`transactTime`等字段
- **当前项目**: 未实现这些字段
- **问题**: 需要完善订单模型和相关API

### 5. 时间戳处理
- **币安**: 实现严格的时间戳验证
- **当前项目**: 缺少相应验证
- **问题**: 需要添加时间戳验证逻辑

### 6. 订单归档
- **币安**: 对90天前的零成交已取消或过期订单实现归档
- **当前项目**: 无归档机制
- **问题**: 需要实现订单归档功能

### 7. 市场订单特性
- **币安**: 特殊处理`quoteOrderQty`的市场订单
- **当前项目**: 未实现该功能
- **问题**: 需要改进市场订单逻辑

## 二、开发目标

将QTE项目的REST API和WebSocket API完全对齐币安API规范，确保:
1. API端点路径与币安保持一致
2. 响应格式与币安保持一致
3. 实现币安特有的功能特性
4. 完善错误处理机制
5. 确保完整的测试覆盖率

## 三、开发阶段

### 阶段一：基础API结构调整 (估计工作量: 3人日)

#### 1. API路径前缀更新
- 将所有API路径从`/api/v1/`更改为`/api/v3/`
- 保留原`/api/v1/`路径以维持向后兼容性

#### 2. 错误响应格式统一
- 移除`success`字段
- 实现币安错误码映射系统
- 修改所有错误响应生成逻辑

#### 3. 基础API验证调整
- 实现时间戳验证机制
- 调整`startTime`和`endTime`参数处理逻辑

### 阶段二：账户与订单API优化 (估计工作量: 5人日)

#### 1. 账户API完善
- 在账户API响应中添加`preventSor`和`uid`字段
- 更新账户模型和相关文档

#### 2. 订单API扩展
- 实现`origQuoteOrderQty`字段
- 添加`transactTime`字段到订单取消、替换等API
- 优化市场订单处理
- 实现订单归档机制

#### 3. 高级功能实现
- 添加`cancelRestrictions`参数支持
- 完善OCO订单处理

### 阶段三：WebSocket API升级 (估计工作量: 4人日)

#### 1. WebSocket基础升级
- 实现会话认证机制
- 添加心跳处理优化

#### 2. 新增WebSocket功能点
- 实现`<symbol>@avgPrice`数据流
- 支持User Data Stream相关新字段
- 处理WebSocket ID支持

#### 3. 高级优化
- 改进WebSocket断开连接处理
- 优化数据格式和序列化

### 阶段四：测试与文档 (估计工作量: 3人日)

#### 1. 全面测试套件
- 创建币安API兼容性测试套件
- 使用真实的币安API请求/响应样本进行测试
- 编写单元测试和集成测试

#### 2. 文档更新
- 更新API文档以反映币安API兼容性
- 编写迁移指南
- 更新示例代码

## 四、具体实现计划

### 1. 错误响应格式更新

```python
# qte/exchange/rest_api/rest_server.py
def _error_response(self, message: str, error_code: int = -1000, status_code: int = 400) -> Response:
    """
    生成错误响应，格式与币安API保持一致
    
    Parameters
    ----------
    message : str
        错误消息
    error_code : int, optional
        币安错误码, by default -1000
    status_code : int, optional
        HTTP状态码, by default 400
        
    Returns
    -------
    Response
        Flask响应对象
    """
    error_response = {
        "code": error_code,
        "msg": message
    }
    
    response = jsonify(error_response)
    response.status_code = status_code
    return response
```

### 2. 币安错误码映射表

```python
# qte/exchange/rest_api/error_codes.py
"""
币安API错误码映射

此模块定义了与币安API兼容的错误码
"""

# 服务器或网络错误 (-1xxx)
SERVER_ERROR = -1000  # 未知错误
DISCONNECTED = -1001  # 与服务器断开连接
UNAUTHORIZED = -1002  # 未授权
TOO_MANY_REQUESTS = -1003  # 请求过多
SERVER_BUSY = -1004  # 服务器繁忙
TIMEOUT = -1005  # 超时
UNKNOWN_ORDER_COMPOSITION = -1006  # 未知的订单组合
UNEXPECTED_RESP = -1007  # 系统异常

# 请求错误 (-3xxx)
BAD_API_KEY_FMT = -3000  # 错误的API Key格式
INVALID_API_KEY = -3001  # 无效的API Key
INVALID_SIGNED_MSG = -3002  # 无效的签名
MALFORMED_MSG = -3003  # 格式错误

# 订单错误 (-2xxx)
UNAUTHORIZED_EXECUTION = -2010  # 新订单被拒绝
CANCEL_REJECTED = -2011  # 取消订单被拒绝
CANCEL_ALL_FAIL = -2012  # 无法取消所有订单
NO_SUCH_ORDER = -2013  # 订单不存在
ORDER_ARCHIVED = -2026  # 订单已归档
```

### 3. 实现时间戳验证

```python
# qte/exchange/rest_api/request_validator.py
def validate_timestamp(timestamp: int) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    验证时间戳是否在有效范围内
    
    Parameters
    ----------
    timestamp : int
        毫秒时间戳
        
    Returns
    -------
    Tuple[bool, Optional[str], Optional[int]]
        (是否有效, 错误信息, 错误码)
    """
    # 2017年1月1日时间戳（毫秒）
    min_timestamp = 1483228800000
    # 当前时间 + 10秒
    max_timestamp = int(time.time() * 1000) + 10000
    
    if timestamp < min_timestamp:
        return False, f"Timestamp is too early. Minimum allowed: {min_timestamp}", -1021
    
    if timestamp > max_timestamp:
        return False, f"Timestamp is too far in the future", -1021
    
    return True, None, None
```

### 4. 更新账户信息API

```python
# qte/exchange/rest_api/rest_server.py
def _get_account(self) -> Response:
    """
    获取账户信息，格式与币安API保持一致
    
    Returns
    -------
    Response
        账户信息响应
    """
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return self._error_response("API-key is required", -2015, 401)
            
    user_id = self._authenticate(api_key)
    if not user_id:
        return self._error_response("Invalid API-key, IP, or permissions", -2008, 401)
            
    # 获取账户
    account = self.account_manager.get_account(user_id)
    if not account:
        return self._error_response("Account not found", -2013, 404)
            
    # 获取账户快照
    snapshot = account.get_account_snapshot()
    
    # 构建响应 - 兼容币安格式
    result = {
        "makerCommission": 10,
        "takerCommission": 10,
        "buyerCommission": 0,
        "sellerCommission": 0,
        "canTrade": True,
        "canWithdraw": True,
        "canDeposit": True,
        "brokered": False,
        "requireSelfTradePrevention": False,
        "preventSor": False,  # 按照2023-07-11更新
        "uid": user_id,       # 按照2023-07-11更新
        "updateTime": int(time.time() * 1000),
        "accountType": "SPOT",
        "balances": [],
        "permissions": ["SPOT"]
    }
    
    # 添加余额 - 格式与币安一致
    for asset, balance in snapshot["balances"].items():
        result["balances"].append({
            "asset": asset,
            "free": str(balance["free"]),
            "locked": str(balance["locked"])
        })
            
    return jsonify(result)
```

### 5. 更新订单模型

```python
# qte/exchange/matching/order.py
class Order:
    """
    订单类，兼容币安订单模型
    """
    def __init__(self, ..., quote_order_qty: Optional[Decimal] = None, ...):
        # 现有代码
        ...
        self.quote_order_qty = quote_order_qty  # 报价资产数量，用于市价单
        self.transact_time = int(time.time() * 1000)  # 交易时间
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典，格式与币安保持一致
        
        Returns
        -------
        Dict[str, Any]
            订单字典表示
        """
        result = {
            "symbol": self.symbol,
            "orderId": self.order_id,
            "orderListId": -1,  # 默认不是OCO的一部分
            "clientOrderId": self.client_order_id or "",
            "price": str(self.price) if self.price else "0.00000000",
            "origQty": str(self.quantity),
            "executedQty": str(self.filled_quantity),
            "cummulativeQuoteQty": str(self.filled_quote_quantity),
            "status": self.status.value,
            "timeInForce": self.time_in_force.value if hasattr(self, 'time_in_force') else "GTC",
            "type": self.order_type.value,
            "side": self.side.value,
            "stopPrice": "0.00000000",  # 默认无止损价
            "icebergQty": "0.00000000",  # 默认非冰山订单
            "time": int(self.timestamp * 1000),
            "updateTime": int(self.update_time * 1000) if hasattr(self, 'update_time') else int(self.timestamp * 1000),
            "isWorking": True,
            "origQuoteOrderQty": str(self.quote_order_qty) if self.quote_order_qty else "0.00000000"  # 新字段
        }
        return result
```

### 6. 实现订单归档机制

```python
# qte/exchange/matching/matching_engine.py
class MatchingEngine:
    # 现有代码
    ...
    
    def get_order(self, symbol: str, order_id: str) -> Optional[Order]:
        """
        获取订单信息
        
        Parameters
        ----------
        symbol : str
            交易对
        order_id : str
            订单ID
            
        Returns
        -------
        Optional[Order]
            订单对象，如不存在则返回None
        """
        order_book = self.get_order_book(symbol)
        order = order_book.get_order(order_id)
        
        if not order:
            # 检查归档订单
            order = self._get_archived_order(symbol, order_id)
            
        return order
    
    def _get_archived_order(self, symbol: str, order_id: str) -> Optional[Order]:
        """
        获取归档订单
        
        Parameters
        ----------
        symbol : str
            交易对
        order_id : str
            订单ID
            
        Returns
        -------
        Optional[Order]
            归档订单对象，如不存在则返回None
        """
        # 实现订单归档逻辑
        # 注意：此处简化实现，实际应当连接数据库查询
        return None
        
    def archive_old_orders(self) -> None:
        """
        归档90天前的零成交已取消或过期订单
        """
        ninety_days_ago = time.time() - (90 * 24 * 60 * 60)
        
        for symbol, order_book in self.order_books.items():
            for order_id, order in list(order_book.completed_orders.items()):
                if (order.status in [OrderStatus.CANCELED, OrderStatus.EXPIRED] and 
                    order.filled_quantity == Decimal('0') and 
                    order.update_time < ninety_days_ago):
                    # 归档订单
                    self._archive_order(order)
                    # 从完成订单列表中移除
                    order_book.completed_orders.pop(order_id, None)
    
    def _archive_order(self, order: Order) -> None:
        """
        归档订单
        
        Parameters
        ----------
        order : Order
            要归档的订单
        """
        # 实现订单归档逻辑
        # 注意：此处简化实现，实际应当存储到数据库
        pass
```

## 五、测试策略

### 1. 单元测试
- 为每个修改的API端点编写单元测试
- 测试错误码和响应格式
- 测试特殊情况和边界条件

### 2. 集成测试
- 测试API端点之间的交互
- 模拟真实交易场景测试

### 3. 兼容性测试
- 使用真实的币安API请求/响应样本进行测试
- 验证响应格式与币安保持一致

### 4. 回归测试
- 确保现有功能不受影响
- 验证向后兼容性

## 六、风险与缓解措施

### 1. 兼容性风险
- **风险**: 修改API格式可能破坏现有客户端
- **缓解**: 保留原API路径，添加版本控制，发布迁移指南

### 2. 性能风险
- **风险**: 新增功能可能影响系统性能
- **缓解**: 进行性能测试，确保系统在高负载下仍能正常运行

### 3. 测试覆盖不足
- **风险**: 测试可能未覆盖所有币安API特性
- **缓解**: 创建全面的测试套件，使用币安API文档作为参考

## 七、时间规划

- **阶段一**: 2周
- **阶段二**: 3周
- **阶段三**: 2周
- **阶段四**: 1周

**总估计时间**: 8周

## 八、验收标准

1. 所有API端点与币安API规范保持一致
2. 响应格式与币安保持一致
3. 测试覆盖率达到95%以上
4. 文档完善，包含所有API变更
5. 与真实币安API的兼容性测试通过 