#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复WebSocket服务器测试问题

这个文件分析并解决WebSocket服务器测试中的两个失败案例:
1. test_subscribe_user_data_without_auth
2. test_subscribe_other_user_data

问题描述:
在这两个测试中，期望WebSocket服务器在处理非法订阅请求时发送两条消息:
1. 一条错误消息
2. 一条成功消息（即使实际上订阅失败）

但实际实现中，服务器只发送了一条消息（错误消息），导致测试失败。

根本原因分析:
检查websocket_server.py中的_handle_subscribe方法，发现在处理非法的用户数据流订阅时,
服务器会发送错误消息并继续处理下一个流，而不会在错误情况下发送成功响应。

这与测试的期望不符，但实际上服务器的行为是正确的 - 它不应该在订阅失败时发送成功消息。

解决方案:
有两种可能的解决方案:

1. 修改测试用例以适应服务器的实际行为:
   - 修改测试断言，期望只有一条错误消息，而不是两条消息
   - 这是更好的解决方案，因为服务器行为是合理的

2. 修改服务器实现以适应测试期望:
   - 在_handle_subscribe方法中，即使流订阅失败，也总是发送成功响应
   - 不推荐这种方法，因为它会导致服务器发送混淆的消息

下面是修改测试的示例代码:
```python
# test_subscribe_user_data_without_auth中的修改
# 验证响应 - 只发送错误消息
assert mock_websocket.send.call_count == 1
error_response = json.loads(mock_websocket.send.call_args[0][0])
assert error_response["id"] == subscribe_id
assert "error" in error_response
assert "用户数据流需要认证" in error_response["error"]

# test_subscribe_other_user_data中的修改
# 验证响应 - 只发送错误消息
assert mock_websocket.send.call_count == 1
error_response = json.loads(mock_websocket.send.call_args[0][0])
assert error_response["id"] == subscribe_id
assert "error" in error_response
assert "无权订阅其他用户的数据" in error_response["error"]
```

注意事项:
1. 测试应该验证实际的服务器行为，而不是强制服务器满足不合理的期望
2. 在这种情况下，服务器在错误情况下只发送错误消息是合理的行为
3. 测试用例应该修改为适应这种行为，而不是要求服务器发送混淆的响应
"""

# 不需要执行代码，这个文件只是分析问题并提供解决方案 