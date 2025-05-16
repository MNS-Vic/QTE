from datetime import datetime, timedelta
from typing import Optional, Union, Any  # 添加Any导入
import random # 用于模拟滑点
import logging

from qte.core.events import OrderEvent, FillEvent, EventType, MarketEvent, OrderDirection, OrderType
from qte.core.event_loop import EventLoop
from .interfaces import BrokerSimulator, CommissionModel, SlippageModel, ExecutionHandler
from qte.analysis.logger import app_logger
# 假设有一个地方可以获取当前市价，或者经纪商监听MarketEvent
# from qte_data.interfaces import DataProvider # 避免直接依赖，可改为监听市场事件

# --- 简单的佣金和滑点模型 --- #
class FixedPercentageCommission(CommissionModel):
    """一个简单的固定百分比佣金模型。"""
    def __init__(self, commission_rate: float = 0.001): # 例如 0.1%
        self.commission_rate = commission_rate

    def calculate_commission(self, symbol: str, quantity: Union[float, int], price: float, direction: OrderDirection) -> float:
        return abs(quantity * price * self.commission_rate)

class SimpleRandomSlippage(SlippageModel):
    """一个简单的随机滑点模型。"""
    def __init__(self, slippage_points: float = 0.01, slippage_chance: float = 0.5):
        self.slippage_points = slippage_points # 例如，价格的0.01个点
        self.slippage_chance = slippage_chance # 发生滑点的概率

    def calculate_fill_price_with_slippage(
        self, 
        symbol: str, 
        quantity: Union[float, int], 
        intended_price: float, 
        direction: OrderDirection, 
        market_event: Optional[MarketEvent] = None # 可以使用市场波动性等
    ) -> float:
        if random.random() < self.slippage_chance:
            slippage_amount = self.slippage_points * random.choice([-1, 1]) # 随机正向或负向滑点
            if direction == OrderDirection.BUY:
                # 买入时，滑点使价格变高 (不利)
                return intended_price + abs(slippage_amount)
            else: # SELL
                # 卖出时，滑点使价格变低 (不利)
                return intended_price - abs(slippage_amount)
        return intended_price

# --- 基础模拟经纪商 --- #
class BasicBroker(BrokerSimulator):
    """
    一个基础的模拟经纪商，处理市价订单，应用佣金和滑点。
    """
    def __init__(self, 
                 event_loop: EventLoop, 
                 commission_model: CommissionModel, 
                 slippage_model: SlippageModel,
                 data_provider: Optional[Any] = None # 实际应为 DataProvider，用于获取当前价格
                 ):
        """
        初始化基础模拟经纪商。

        参数:
            event_loop (EventLoop): 事件循环实例。
            commission_model (CommissionModel): 佣金模型实例。
            slippage_model (SlippageModel): 滑点模型实例。
            data_provider (Optional[DataProvider]): 数据提供者，用于获取市价单的当前价格。
                                                 在更高级的实现中，经纪商可以监听MarketEvents。
        """
        super().__init__(event_loop, commission_model, slippage_model)
        self.data_provider = data_provider # 用于获取当前市价
        # 也可以让Broker监听MarketEvent来维护内部的最新价格表
        # self.latest_prices: Dict[str, float] = {}
        # self.event_loop.register_handler(EventType.MARKET, self._on_market_update)
        
        app_logger.info("基础模拟经纪商已初始化。")

    # def _on_market_update(self, event: MarketEvent) -> None:
    #     """内部方法，用于更新经纪商了解的最新市场价格。"""
    #     self.latest_prices[event.symbol] = event.close_price

    def submit_order(self, order: OrderEvent) -> None:
        """
        提交订单到模拟经纪商。
        目前主要处理市价单。
        """
        app_logger.info(f"经纪商收到订单: {order.symbol} {order.direction} {order.quantity} @ {order.order_type} ID: {order.order_id}")

        if order.order_type == OrderType.MARKET.value:
            # 获取当前市价
            current_price = None
            market_event_for_slippage = None
            if self.data_provider:
                latest_bar = self.data_provider.get_latest_bar(order.symbol)
                if latest_bar and latest_bar.get('close') is not None:
                    current_price = latest_bar['close']
                    # 创建一个临时的MarketEvent给滑点模型用（如果它需要）
                    market_event_for_slippage = MarketEvent(
                        symbol=order.symbol, timestamp=latest_bar.get('datetime', order.timestamp),
                        open_price=latest_bar.get('open', current_price), high_price=latest_bar.get('high', current_price),
                        low_price=latest_bar.get('low', current_price), close_price=current_price,
                        volume=latest_bar.get('volume', 0)
                    )
                else:
                    app_logger.error(f"无法为市价单 {order.order_id} 获取合约 {order.symbol} 的当前价格。订单未执行。")
                    # TODO: 可以发送一个订单被拒绝的事件
                    return
            # elif order.symbol in self.latest_prices: # 如果经纪商自己维护价格表
            #     current_price = self.latest_prices[order.symbol]
            else:
                app_logger.error(f"经纪商未配置data_provider或内部价格表，无法执行市价单 {order.order_id}。订单未执行。")
                return

            # 计算滑点后的成交价格
            fill_price = self.slippage_model.calculate_fill_price_with_slippage(
                symbol=order.symbol,
                quantity=order.quantity,
                intended_price=current_price,
                direction=order.direction,
                market_event=market_event_for_slippage
            )

            # 计算佣金
            commission = self.commission_model.calculate_commission(
                symbol=order.symbol,
                quantity=order.quantity,
                price=fill_price, # 佣金通常基于实际成交价
                direction=order.direction
            )

            # 创建并发送 FillEvent
            fill = FillEvent(
                order_id=order.order_id or f"sim_ord_{datetime.utcnow().timestamp()}", # 如果订单没有ID，生成一个
                symbol=order.symbol,
                timestamp=order.timestamp + timedelta(microseconds=100), # 模拟微小的执行延迟
                direction=order.direction,
                quantity=order.quantity,
                fill_price=fill_price,
                commission=commission,
                slippage = fill_price - current_price if order.direction == OrderDirection.BUY else current_price - fill_price
            )
            app_logger.info(f"经纪商为订单 {order.order_id} 生成成交: {fill.quantity} {fill.symbol} @ {fill.fill_price:.2f} (佣金:{fill.commission:.2f}, 滑点:{fill.slippage:.4f})")
            self.event_loop.put_event(fill)

        elif order.order_type == OrderType.LIMIT.value:
            app_logger.warning(f"基础经纪商收到限价单 {order.order_id}，但目前未完全实现限价单逻辑。订单暂不执行。")
            # TODO: 实现限价单逻辑 (需要持续监控市价是否达到限价)
            pass
        else:
            app_logger.warning(f"经纪商收到不支持的订单类型: {order.order_type} (订单ID: {order.order_id})。订单未执行。")

# 示例用法
if __name__ == '__main__':
    from qte.core.event_loop import EventLoop
    from qte.core.events import OrderDirection, OrderType, EventType
    from datetime import datetime, timedelta

    # 1. 设置组件
    test_loop = EventLoop()
    commission_model_test = FixedPercentageCommission(0.0005) # 0.05% 佣金
    slippage_model_test = SimpleRandomSlippage(0.02, 0.8) # 0.02价格点滑点，80%概率发生

    # 模拟一个DataProvider
    class MockDataProviderBrokerTest:
        _prices = {"TEST_STOCK": 100.0}
        def get_latest_bar(self, symbol: str) -> Optional[dict]:
            if symbol in self._prices:
                price = self._prices[symbol]
                self._prices[symbol] += random.uniform(-0.1, 0.1) # 价格小幅波动
                return {"datetime": datetime.utcnow(), "symbol": symbol, "close": price, "open":price, "high":price, "low":price, "volume":100}
            return None

    mock_dp_broker = MockDataProviderBrokerTest()
    broker = BasicBroker(test_loop, commission_model_test, slippage_model_test, data_provider=mock_dp_broker)

    # 模拟一个成交处理器
    def fill_event_handler(event: FillEvent):
        app_logger.info(f"[Test Fill Handler] 收到成交: ID={event.order_id}, {event.direction} {event.quantity} {event.symbol} @ {event.fill_price:.2f}, Comm: {event.commission:.2f}, Slippage: {event.slippage:.4f}")

    test_loop.register_handler(EventType.FILL, fill_event_handler)

    app_logger.info("\n--- 经纪商测试开始 ---")

    # 2. 创建并提交市价买单
    order1_id = "order_buy_1"
    market_order_buy = OrderEvent(
        order_id=order1_id,
        symbol="TEST_STOCK",
        order_type=OrderType.MARKET,
        direction=OrderDirection.BUY,
        quantity=10,
        timestamp=datetime.utcnow()
    )
    broker.submit_order(market_order_buy)

    # 3. 创建并提交市价卖单
    order2_id = "order_sell_1"
    market_order_sell = OrderEvent(
        order_id=order2_id,
        symbol="TEST_STOCK",
        order_type=OrderType.MARKET,
        direction=OrderDirection.SELL,
        quantity=5,
        timestamp=datetime.utcnow() + timedelta(seconds=1)
    )
    broker.submit_order(market_order_sell)
    
    # 4. 提交一个限价单 (预期会收到警告)
    order3_id = "order_limit_buy_1"
    limit_order_buy = OrderEvent(
        order_id=order3_id,
        symbol="TEST_STOCK",
        order_type=OrderType.LIMIT,
        direction=OrderDirection.BUY,
        quantity=2,
        limit_price=95.0, # 设置一个较低的限价
        timestamp=datetime.utcnow() + timedelta(seconds=2)
    )
    broker.submit_order(limit_order_buy)

    # 5. 模拟事件循环处理 (在简单测试中，我们没有启动事件循环线程)
    # 在真实回测中，事件循环会驱动这些事件的处理
    # 这里我们手动检查一下队列 (如果需要的话，但Fill会直接发给已注册的handler)
    # print("事件队列内容 (部分，仅用于调试，真实循环会处理):")
    # temp_queue_view = list(test_loop.event_queue)
    # for i, evt in enumerate(temp_queue_view):
    #     if i < 5 : print(evt)
    #     else: print(f"... and {len(temp_queue_view) - i} more events ..."); break

    app_logger.info("\n--- 经纪商测试结束 (请查看日志中的[Test Fill Handler]输出) ---") 