# QTE 交易所集成测试

本目录包含QTE交易所的集成测试，用于测试各组件之间的交互以及完整的功能流程。

## WebSocket订单推送测试

WebSocket订单推送测试验证交易所能够通过WebSocket协议实时推送订单状态更新，符合币安API的标准格式和行为。

### 测试文件

- `test_websocket_order_updates.py`: 基本订单生命周期测试，验证订单状态变化的通知
- `test_websocket_order_scenarios.py`: 高级订单场景测试，包括不同的价格匹配模式和自成交预防功能
- `test_websocket_order_edge_cases.py`: 边界情况和错误处理测试，验证异常情况下的行为
- `test_websocket_connection_management.py`: 连接管理测试，验证连接建立、断开、订阅等功能
- `test_websocket_security.py`: 安全性测试，验证API密钥验证、权限检查、操作限制等安全机制

### 测试范围

1. **基本功能**:
   - 订单创建、部分成交、完全成交、取消的通知
   - 订单更新消息格式符合币安API标准
   - 支持价格匹配模式和自成交预防

2. **边界情况**:
   - 余额不足时的订单处理
   - 无效价格和数量的处理
   - 取消不存在的订单
   - 无流动性时的市价单处理

3. **连接管理**:
   - WebSocket连接的建立和断开
   - 用户认证和会话管理
   - 主题订阅和取消订阅
   - 多客户端并发连接

4. **安全性**:
   - API密钥验证
   - 跨账户操作拦截
   - 未认证操作拦截
   - 输入验证和防止恶意请求

## 运行测试

可以使用以下命令运行所有集成测试:

```bash
pytest tests/integration
```

或者运行特定的测试文件:

```bash
pytest tests/integration/test_websocket_order_updates.py
```

或者运行特定的测试:

```bash
pytest tests/integration/test_websocket_order_updates.py::TestWebSocketOrderUpdatesIntegration::test_order_lifecycle_updates
```

## 测试数据

测试使用模拟的交易对和账户，无需连接真实的交易环境。所有测试都会创建必要的测试数据并在测试完成后清理。 