# TDD快速参考卡片 🚀

## 🔄 TDD三步循环

```
🔴 Red → 🟢 Green → 🔵 Refactor
```

1. **🔴 Red**: 编写失败的测试
2. **🟢 Green**: 写最少代码使测试通过  
3. **🔵 Refactor**: 优化代码保持测试通过

## 📝 测试命名规范

```python
def test_[功能]_[场景]_[期望结果]():
    """测试[功能描述] - [具体场景]"""
    pass

# 示例
def test_calculate_portfolio_value_with_positions_returns_correct_total():
    """测试计算投资组合价值 - 有持仓情况 - 返回正确总值"""
```

## 🏗️ AAA测试结构

```python
def test_example():
    # Arrange（准备）- 设置测试数据
    portfolio = Portfolio(initial_capital=100000)
    
    # Act（执行）- 调用被测方法
    result = portfolio.calculate_value()
    
    # Assert（断言）- 验证结果
    assert result == 100000
```

## 🎯 常用断言

```python
# 相等断言
assert actual == expected
assert actual != unexpected

# 数值断言
assert abs(actual - expected) < 0.01  # 浮点数比较
assert 0 <= risk_value <= 1.0         # 范围检查

# 集合断言
assert item in collection
assert len(collection) == expected_size
assert set(actual) == set(expected)

# 异常断言
with pytest.raises(ValueError, match="错误信息"):
    function_that_should_raise()

# 布尔断言
assert condition is True
assert condition is False
assert condition is None
```

## 🔧 Mock使用速查

```python
from unittest.mock import Mock, patch

# 创建Mock对象
mock_obj = Mock()
mock_obj.method.return_value = "返回值"
mock_obj.method.side_effect = Exception("异常")

# 验证调用
mock_obj.method.assert_called_once()
mock_obj.method.assert_called_with(arg1, arg2)
mock_obj.method.assert_not_called()

# Patch装饰器
@patch('module.function')
def test_with_patch(mock_func):
    mock_func.return_value = "模拟返回"
    # 测试代码

# Context manager
with patch('module.function') as mock_func:
    mock_func.return_value = "模拟返回"
    # 测试代码
```

## 📊 覆盖率命令

```bash
# 运行测试并生成覆盖率
pytest tests/ --cov=qte --cov-report=html

# 检查覆盖率门禁
pytest tests/ --cov=qte --cov-fail-under=90

# 显示未覆盖行
pytest tests/ --cov=qte --cov-report=term-missing

# 分支覆盖率
pytest tests/ --cov=qte --cov-branch
```

## 🚀 常用pytest参数

```bash
# 详细输出
pytest -v

# 只运行失败的测试
pytest --lf

# 并行运行
pytest -n auto

# 运行特定标记的测试
pytest -m "not slow"

# 运行特定测试
pytest tests/test_file.py::test_function

# 停在第一个失败
pytest -x

# 显示本地变量
pytest -l --tb=short
```

## 🏷️ pytest标记

```python
import pytest

@pytest.mark.slow
def test_heavy_computation():
    """标记为慢速测试"""
    pass

@pytest.mark.integration
def test_database_integration():
    """标记为集成测试"""
    pass

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6)
])
def test_multiply_by_two(input, expected):
    """参数化测试"""
    assert multiply_by_two(input) == expected

@pytest.mark.skip(reason="功能未实现")
def test_future_feature():
    """跳过测试"""
    pass

@pytest.mark.xfail(reason="已知问题")
def test_known_issue():
    """预期失败的测试"""
    pass
```

## 🔧 Fixture速查

```python
import pytest

@pytest.fixture
def sample_data():
    """函数级fixture"""
    return {"key": "value"}

@pytest.fixture(scope="class")
def class_data():
    """类级fixture"""
    return expensive_setup()

@pytest.fixture(scope="module")
def module_data():
    """模块级fixture"""
    return very_expensive_setup()

@pytest.fixture
def cleanup_fixture():
    """带清理的fixture"""
    resource = setup_resource()
    yield resource
    cleanup_resource(resource)

# 使用fixture
def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

## 🔍 调试技巧

```python
# 在测试中设置断点
import pdb; pdb.set_trace()

# 使用pytest调试
pytest --pdb  # 失败时进入调试器
pytest --pdbcls=IPython.terminal.debugger:Pdb  # 使用IPython

# 打印调试信息
def test_debug():
    result = function_under_test()
    print(f"Debug: result = {result}")  # 使用 -s 参数显示
    assert result == expected

# 运行时显示print输出
pytest -s
```

## ⚡ 性能优化

```python
# 使用pytest-benchmark
def test_performance(benchmark):
    result = benchmark(expensive_function, arg1, arg2)
    assert result == expected

# 并行测试
pip install pytest-xdist
pytest -n auto

# 只运行修改相关的测试
pytest --testmon

# 缓存测试结果
pytest --cache-show
pytest --cache-clear
```

## 🎯 QTE项目特定

```python
# 事件循环测试
from qte.core.event_loop import EventLoop

def test_event_loop():
    event_loop = EventLoop()
    # 测试代码

# 异步测试
import pytest_asyncio

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected

# Mock数据提供者
@pytest.fixture
def mock_data_provider():
    mock = Mock()
    mock.get_latest_bar.return_value = {
        'close': 150.0,
        'symbol': 'AAPL'
    }
    return mock
```

## 📋 检查清单

### ✅ 编写测试前
- [ ] 明确测试目标
- [ ] 确定测试场景（正常、边界、异常）
- [ ] 准备测试数据
- [ ] 选择合适的断言

### ✅ 编写测试时
- [ ] 遵循AAA结构
- [ ] 使用描述性的测试名称
- [ ] 一个测试只验证一个行为
- [ ] 避免测试实现细节

### ✅ 测试完成后
- [ ] 确保测试可重复运行
- [ ] 检查测试覆盖率
- [ ] 验证测试失败时的错误信息
- [ ] 清理测试资源

### ✅ 代码提交前
- [ ] 所有测试通过
- [ ] 覆盖率达到要求（≥90%）
- [ ] 代码格式化（black, isort）
- [ ] 静态检查通过（flake8, mypy）

## 🆘 常见错误

```python
# ❌ 错误：测试依赖外部状态
def test_bad():
    # 依赖数据库或文件系统
    data = read_from_database()
    assert process(data) == expected

# ✅ 正确：使用Mock隔离依赖
def test_good(mock_database):
    mock_database.return_value = test_data
    assert process(test_data) == expected

# ❌ 错误：测试过于复杂
def test_too_complex():
    # 测试多个功能
    result1 = function1()
    result2 = function2()
    result3 = function3()
    assert all([result1, result2, result3])

# ✅ 正确：每个测试专注一个功能
def test_function1():
    assert function1() == expected1

def test_function2():
    assert function2() == expected2
```

## 📞 获取帮助

- **文档**: `docs/TDD_TRAINING_GUIDE.md`
- **示例**: `tests/unit/*/test_*_advanced.py`
- **CI/CD**: `.github/workflows/test-coverage.yml`
- **配置**: `.coveragerc`

---
**记住**: 好的测试是代码质量的保证！ 🛡️
