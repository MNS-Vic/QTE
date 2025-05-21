# QTE 交易所 WebSocket 单元测试

本目录包含QTE交易所WebSocket模块的单元测试，主要测试WebSocket服务器的各个功能单元。

## 测试文件

- `test_order_update_format.py`: 测试WebSocket订单更新消息的格式是否符合币安API标准

## 测试范围

1. **消息格式**:
   - 测试订单创建、成交、部分成交、取消等状态的消息格式
   - 验证所有必要字段和可选字段的存在和格式
   - 验证消息符合币安API格式标准

2. **特殊状态**:
   - 测试EXPIRED_IN_MATCH状态的消息格式
   - 测试自成交预防触发时的消息格式
   - 测试拒绝订单的消息格式

## 测试方法

单元测试使用以下方法:

1. **模拟对象**:
   - 使用`unittest.mock`模块创建模拟对象
   - 模拟WebSocket客户端连接和消息传递

2. **隔离测试**:
   - 测试专注于消息格式而非功能流程
   - 使用预设的订单对象和状态

3. **断言**:
   - 验证消息结构是否符合预期
   - 检查关键字段的数据类型和格式
   - 检查字段间的逻辑关系

## 运行测试

可以使用以下命令运行所有WebSocket单元测试:

```bash
pytest tests/unit/exchange/websocket
```

或者运行特定的测试文件:

```bash
pytest tests/unit/exchange/websocket/test_order_update_format.py
```

## 扩展测试

未来可以添加的单元测试:

1. WebSocket连接管理单元测试
2. 消息处理逻辑单元测试
3. 订阅管理单元测试
4. 安全验证单元测试

## 测试覆盖率

可以使用`pytest-cov`插件检查测试覆盖率:

```bash
pytest --cov=qte.exchange.websocket tests/unit/exchange/websocket
``` 