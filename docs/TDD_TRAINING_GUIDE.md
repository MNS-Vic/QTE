# QTE项目TDD测试驱动开发培训指南

## 📚 目录

1. [TDD基础概念](#tdd基础概念)
2. [TDD实施流程](#tdd实施流程)
3. [QTE项目TDD最佳实践](#qte项目tdd最佳实践)
4. [测试用例编写规范](#测试用例编写规范)
5. [覆盖率管理](#覆盖率管理)
6. [CI/CD集成](#cicd集成)
7. [常见问题与解决方案](#常见问题与解决方案)
8. [实战演练](#实战演练)

## 🎯 TDD基础概念

### 什么是TDD？

测试驱动开发（Test-Driven Development，TDD）是一种软件开发方法论，遵循"测试先行"的原则：

```
Red → Green → Refactor
```

- **Red（红）**: 编写一个失败的测试
- **Green（绿）**: 编写最少的代码使测试通过
- **Refactor（重构）**: 在保持测试通过的前提下优化代码

### TDD的核心价值

1. **提高代码质量**: 确保每行代码都有测试覆盖
2. **降低缺陷率**: 在开发阶段就发现和修复问题
3. **改善设计**: 测试驱动更好的API设计
4. **增强信心**: 重构和修改代码时有安全保障
5. **文档化**: 测试用例作为代码的活文档

## 🔄 TDD实施流程

### 标准TDD循环

```python
# 1. Red阶段 - 编写失败的测试
def test_calculate_portfolio_value():
    """测试投资组合价值计算"""
    # Red: 编写失败的测试
    portfolio = Portfolio(initial_capital=100000)
    portfolio.add_position("AAPL", quantity=100, price=150.0)
    
    # 这个测试会失败，因为calculate_value方法还不存在
    assert portfolio.calculate_value() == 115000.0

# 2. Green阶段 - 实现最小可行代码
class Portfolio:
    def __init__(self, initial_capital):
        self.initial_capital = initial_capital
        self.positions = {}
        self.cash = initial_capital
    
    def add_position(self, symbol, quantity, price):
        self.positions[symbol] = {'quantity': quantity, 'price': price}
        self.cash -= quantity * price
    
    def calculate_value(self):
        # 最简单的实现使测试通过
        return self.cash + sum(pos['quantity'] * pos['price'] 
                              for pos in self.positions.values())

# 3. Refactor阶段 - 优化代码结构
class Portfolio:
    def __init__(self, initial_capital: float):
        self._initial_capital = initial_capital
        self._positions: Dict[str, Position] = {}
        self._cash = initial_capital
    
    def add_position(self, symbol: str, quantity: int, price: float) -> None:
        """添加持仓"""
        if symbol in self._positions:
            self._positions[symbol].add_quantity(quantity, price)
        else:
            self._positions[symbol] = Position(symbol, quantity, price)
        self._cash -= quantity * price
    
    def calculate_value(self) -> float:
        """计算投资组合总价值"""
        holdings_value = sum(pos.market_value for pos in self._positions.values())
        return self._cash + holdings_value
```

## 🏆 QTE项目TDD最佳实践

### 1. 测试文件组织结构

```
tests/
├── unit/                    # 单元测试
│   ├── core/               # 核心模块测试
│   │   ├── test_event_loop.py
│   │   ├── test_backtester_advanced.py
│   │   └── __init__.py
│   ├── portfolio/          # 投资组合测试
│   │   ├── test_base_portfolio_advanced.py
│   │   └── __init__.py
│   ├── strategy/           # 策略测试
│   │   ├── test_simple_moving_average_strategy_advanced.py
│   │   └── __init__.py
│   └── data/              # 数据模块测试
│       ├── test_csv_data_provider_advanced.py
│       └── __init__.py
├── integration/            # 集成测试
│   ├── test_strategy_flow.py
│   ├── test_websocket_integration.py
│   └── __init__.py
└── conftest.py            # 测试配置
```

### 2. 测试命名规范

```python
class TestBasePortfolioAdvanced:
    """BasePortfolio高级功能测试类"""
    
    def test_calculate_portfolio_value_with_positions(self):
        """测试计算投资组合价值 - 有持仓情况"""
        # 测试方法命名格式：test_[功能]_[场景]
        pass
    
    def test_calculate_portfolio_value_empty_portfolio(self):
        """测试计算投资组合价值 - 空投资组合情况"""
        pass
    
    def test_add_position_new_symbol(self):
        """测试添加持仓 - 新标的"""
        pass
    
    def test_add_position_existing_symbol(self):
        """测试添加持仓 - 已有标的"""
        pass
```

### 3. 测试用例结构（AAA模式）

```python
def test_on_fill_new_long_position(self):
    """测试处理成交事件 - 新建多头仓位"""
    # Arrange（准备）- 设置测试数据和环境
    initial_cash = self.portfolio.current_cash
    fill_event = FillEvent(
        order_id='test_order_1',
        symbol='AAPL',
        timestamp=datetime.now(timezone.utc),
        direction=OrderDirection.BUY,
        quantity=100,
        fill_price=150.0,
        commission=5.0
    )
    
    # Act（执行）- 调用被测试的方法
    self.portfolio.on_fill(fill_event)
    
    # Assert（断言）- 验证结果
    expected_cash = initial_cash - (100 * 150.0) - 5.0
    assert self.portfolio.current_cash == expected_cash
    assert 'AAPL' in self.portfolio.positions
    assert self.portfolio.positions['AAPL']['quantity'] == 100
```

### 4. Mock对象使用规范

```python
from unittest.mock import Mock, MagicMock, patch

class TestStrategy:
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_data_provider = Mock()
        self.mock_event_loop = Mock()
        
        # 配置Mock对象的返回值
        self.mock_data_provider.get_latest_bar.return_value = {
            'close': 150.0,
            'symbol': 'AAPL'
        }
    
    def test_strategy_with_mock_data(self):
        """测试策略使用Mock数据"""
        # 使用Mock对象进行隔离测试
        strategy = Strategy(
            data_provider=self.mock_data_provider,
            event_loop=self.mock_event_loop
        )
        
        # 验证Mock方法被正确调用
        strategy.process_market_data('AAPL')
        self.mock_data_provider.get_latest_bar.assert_called_once_with('AAPL')
```

## 📝 测试用例编写规范

### 1. 测试用例分类

#### 正常路径测试（Happy Path）
```python
def test_calculate_sma_normal_case(self):
    """测试计算SMA - 正常情况"""
    prices = [100, 102, 104, 106, 108]
    expected_sma = sum(prices) / len(prices)
    actual_sma = calculate_sma(prices)
    assert actual_sma == expected_sma
```

#### 边界条件测试（Edge Cases）
```python
def test_calculate_sma_minimum_data(self):
    """测试计算SMA - 最少数据"""
    prices = [100]  # 只有一个数据点
    expected_sma = 100.0
    actual_sma = calculate_sma(prices)
    assert actual_sma == expected_sma

def test_calculate_sma_empty_data(self):
    """测试计算SMA - 空数据"""
    prices = []
    with pytest.raises(ValueError, match="价格数据不能为空"):
        calculate_sma(prices)
```

#### 异常情况测试（Error Cases）
```python
def test_calculate_sma_invalid_data_type(self):
    """测试计算SMA - 无效数据类型"""
    prices = "invalid_data"
    with pytest.raises(TypeError, match="价格数据必须是数字列表"):
        calculate_sma(prices)

def test_calculate_sma_negative_prices(self):
    """测试计算SMA - 负价格"""
    prices = [100, -50, 150]
    with pytest.raises(ValueError, match="价格不能为负数"):
        calculate_sma(prices)
```

### 2. 断言最佳实践

```python
# ✅ 好的断言 - 具体且有意义
assert portfolio.current_cash == 95000.0
assert len(portfolio.positions) == 2
assert 'AAPL' in portfolio.positions
assert portfolio.positions['AAPL']['quantity'] == 100

# ❌ 不好的断言 - 过于宽泛
assert portfolio.current_cash > 0
assert portfolio.positions
assert portfolio.is_valid()

# ✅ 浮点数比较
assert abs(calculated_value - expected_value) < 0.01

# ✅ 异常断言
with pytest.raises(ValueError, match="订单数量必须大于0"):
    portfolio.add_order(symbol="AAPL", quantity=0)

# ✅ 集合断言
assert set(portfolio.symbols) == {"AAPL", "GOOGL", "MSFT"}
```

## 📊 覆盖率管理

### 1. 覆盖率目标设定

```python
# .coveragerc 配置
[report]
fail_under = 90  # 总体覆盖率门禁
show_missing = True
precision = 1

# 核心模块覆盖率要求
# - qte/core/: >= 95%
# - qte/portfolio/: >= 90%
# - qte/strategy/: >= 90%
# - qte/exchange/: >= 85%
# - qte/data/: >= 80%
```

### 2. 覆盖率监控命令

```bash
# 运行测试并生成覆盖率报告
pytest tests/unit/ --cov=qte --cov-report=html --cov-report=term-missing --cov-branch

# 检查特定模块覆盖率
pytest tests/unit/portfolio/ --cov=qte.portfolio --cov-report=term-missing

# 覆盖率门禁检查
pytest tests/unit/ --cov=qte --cov-fail-under=90
```

### 3. 覆盖率分析

```python
# 分析覆盖率报告
import json

def analyze_coverage_report():
    with open('coverage.json', 'r') as f:
        data = json.load(f)
    
    # 找出覆盖率低的模块
    low_coverage_files = []
    for file_path, file_data in data['files'].items():
        coverage = file_data['summary']['percent_covered']
        if coverage < 80 and file_path.startswith('qte/'):
            low_coverage_files.append((file_path, coverage))
    
    # 按覆盖率排序
    low_coverage_files.sort(key=lambda x: x[1])
    
    print("需要改进的模块:")
    for file_path, coverage in low_coverage_files:
        print(f"{file_path}: {coverage:.1f}%")
```

## 🚀 CI/CD集成

### 1. GitHub Actions配置

我们已经创建了完整的CI/CD流水线，包括：

- **测试覆盖率检查**: 自动运行测试并检查覆盖率门禁
- **安全扫描**: 使用Bandit进行安全漏洞扫描
- **代码质量检查**: Black、isort、Flake8、MyPy
- **性能测试**: 基准性能测试
- **覆盖率徽章**: 自动更新覆盖率徽章

### 2. 本地开发工作流

```bash
# 1. 开发前运行测试
pytest tests/unit/ -v

# 2. 编写新功能的测试（TDD Red阶段）
# 创建 tests/unit/new_module/test_new_feature.py

# 3. 运行新测试（应该失败）
pytest tests/unit/new_module/test_new_feature.py -v

# 4. 实现功能代码（TDD Green阶段）
# 编写 qte/new_module/new_feature.py

# 5. 再次运行测试（应该通过）
pytest tests/unit/new_module/test_new_feature.py -v

# 6. 检查覆盖率
pytest tests/unit/ --cov=qte.new_module --cov-report=term-missing

# 7. 重构优化（TDD Refactor阶段）
# 优化代码结构，确保测试仍然通过

# 8. 提交代码
git add .
git commit -m "feat: 添加新功能及其测试用例"
git push
```

## ❓ 常见问题与解决方案

### 1. 测试运行缓慢

**问题**: 测试执行时间过长
**解决方案**:
```python
# 使用pytest-xdist并行运行测试
pip install pytest-xdist
pytest tests/ -n auto

# 使用pytest标记分类测试
@pytest.mark.slow
def test_heavy_computation():
    pass

# 只运行快速测试
pytest tests/ -m "not slow"
```

### 2. Mock对象配置复杂

**问题**: Mock对象设置复杂，测试难以维护
**解决方案**:
```python
# 使用fixture简化Mock配置
@pytest.fixture
def mock_data_provider():
    mock = Mock()
    mock.get_latest_bar.return_value = {'close': 150.0}
    mock.stream_market_data.return_value = []
    return mock

# 使用patch装饰器
@patch('qte.module.external_service')
def test_with_patched_service(mock_service):
    mock_service.return_value = "mocked_result"
    # 测试代码
```

### 3. 异步代码测试

**问题**: 异步代码测试复杂
**解决方案**:
```python
import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    result = await async_function()
    assert result == expected_value

@pytest_asyncio.fixture
async def async_setup():
    """异步fixture"""
    async_resource = await create_async_resource()
    yield async_resource
    await cleanup_async_resource(async_resource)
```

## 🎯 实战演练

### 练习1：为新功能编写TDD测试

**任务**: 为投资组合添加风险计算功能

```python
# 1. Red阶段 - 编写失败的测试
def test_calculate_portfolio_risk_normal_case():
    """测试计算投资组合风险 - 正常情况"""
    portfolio = Portfolio(initial_capital=100000)
    portfolio.add_position("AAPL", 100, 150.0)
    portfolio.add_position("GOOGL", 50, 2500.0)
    
    # 这个测试会失败，因为calculate_risk方法还不存在
    risk = portfolio.calculate_risk()
    assert 0.0 <= risk <= 1.0

# 2. Green阶段 - 实现最小功能
def calculate_risk(self):
    """计算投资组合风险"""
    # 最简单的实现
    return 0.5

# 3. Refactor阶段 - 完善实现
def calculate_risk(self):
    """计算投资组合风险（基于持仓集中度）"""
    if not self.positions:
        return 0.0
    
    total_value = self.calculate_value()
    if total_value == 0:
        return 0.0
    
    # 计算持仓集中度风险
    max_position_weight = max(
        pos['quantity'] * pos['price'] / total_value 
        for pos in self.positions.values()
    )
    
    return min(max_position_weight, 1.0)
```

### 练习2：重构现有代码

**任务**: 重构订单处理逻辑，保持测试通过

```python
# 原始实现
def process_order(self, order):
    if order.direction == "BUY":
        self.cash -= order.quantity * order.price
        if order.symbol in self.positions:
            self.positions[order.symbol] += order.quantity
        else:
            self.positions[order.symbol] = order.quantity
    # ... 更多逻辑

# 重构后的实现
def process_order(self, order: Order) -> None:
    """处理订单"""
    self._validate_order(order)
    
    if order.direction == OrderDirection.BUY:
        self._process_buy_order(order)
    elif order.direction == OrderDirection.SELL:
        self._process_sell_order(order)
    
    self._update_portfolio_metrics()

def _process_buy_order(self, order: Order) -> None:
    """处理买单"""
    cost = order.quantity * order.price
    self._update_cash(-cost)
    self._update_position(order.symbol, order.quantity)

def _validate_order(self, order: Order) -> None:
    """验证订单"""
    if order.quantity <= 0:
        raise ValueError("订单数量必须大于0")
    if order.price <= 0:
        raise ValueError("订单价格必须大于0")
```

## 📚 推荐资源

### 书籍
- 《测试驱动开发》- Kent Beck
- 《重构：改善既有代码的设计》- Martin Fowler
- 《代码整洁之道》- Robert C. Martin

### 在线资源
- [pytest官方文档](https://docs.pytest.org/)
- [Python Mock库文档](https://docs.python.org/3/library/unittest.mock.html)
- [TDD最佳实践](https://testdriven.io/)

### QTE项目相关
- [项目测试覆盖率报告](./htmlcov/index.html)
- [CI/CD流水线状态](../.github/workflows/test-coverage.yml)
- [代码质量指标](./coverage.json)

---

**记住**: TDD不仅仅是一种测试方法，更是一种设计思维。通过测试驱动开发，我们能够编写出更加健壮、可维护和高质量的代码。

**开始你的TDD之旅吧！** 🚀
