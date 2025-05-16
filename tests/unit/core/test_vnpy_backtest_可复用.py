#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于vnpy风格的事件驱动回测测试脚本
特点：事件引擎、模块化设计、全市场支持
"""
import os
import datetime
import time
from enum import Enum
from collections import defaultdict
from queue import Queue, Empty
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 常量定义
EMPTY_STRING = ""
EMPTY_FLOAT = 0.0
EMPTY_INT = 0

# 方向常量
DIRECTION_LONG = "多"
DIRECTION_SHORT = "空"
DIRECTION_NET = "净"

# 开平常量
OFFSET_OPEN = "开"
OFFSET_CLOSE = "平"
OFFSET_CLOSETODAY = "平今"
OFFSET_CLOSEYESTERDAY = "平昨"

# 状态常量
STATUS_SUBMITTING = "提交中"
STATUS_NOTTRADED = "未成交"
STATUS_PARTTRADED = "部分成交"
STATUS_ALLTRADED = "全部成交"
STATUS_CANCELLED = "已撤销"
STATUS_REJECTED = "拒单"

# 订单类型
ORDER_MARKET = "市价单"
ORDER_LIMIT = "限价单"
ORDER_STOP = "停止单"

# 事件类型
class EventType(Enum):
    """事件类型枚举"""
    EVENT_TICK = "事件_TICK行情"
    EVENT_BAR = "事件_K线"
    EVENT_ORDER = "事件_订单"
    EVENT_TRADE = "事件_成交"
    EVENT_POSITION = "事件_持仓"
    EVENT_ACCOUNT = "事件_账户"
    EVENT_CONTRACT = "事件_合约"
    EVENT_TIMER = "事件_计时器"

# 基础事件类
class Event:
    """事件对象"""
    def __init__(self, type=None):
        self.type = type
        self.dict = {}

# 事件引擎类
class EventEngine:
    """事件引擎"""
    def __init__(self):
        """初始化事件引擎"""
        # 事件队列
        self.queue = Queue()
        
        # 事件处理线程是否在运行
        self.active = False
        
        # 事件处理函数字典，key:事件类型，value:处理函数列表
        self.handlers = defaultdict(list)
        
        # 计时器，用于触发计时器事件
        self.timer = None
        self.timer_active = False
        self.timer_count = 0
        self.timer_interval = 1  # 默认1秒

    def register(self, type_, handler):
        """注册事件处理函数"""
        handler_list = self.handlers[type_]
        if handler not in handler_list:
            handler_list.append(handler)
    
    def unregister(self, type_, handler):
        """注销事件处理函数"""
        handler_list = self.handlers[type_]
        if handler in handler_list:
            handler_list.remove(handler)
        
        if not handler_list:
            del self.handlers[type_]
            
    def put(self, event):
        """向事件队列中存入事件"""
        self.queue.put(event)

    def start(self):
        """启动事件处理"""
        self.active = True
        
    def stop(self):
        """停止事件处理"""
        self.active = False
        
        if self.timer:
            self.timer_active = False
            self.timer = None
    
    def process(self):
        """处理事件"""
        while self.active:
            try:
                event = self.queue.get(block=False)
                if event.type in self.handlers:
                    for handler in self.handlers[event.type]:
                        handler(event)
            except Empty:
                break

# 数据类
class VtBarData:
    """K线数据类"""
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING        # 代码
        self.exchange = EMPTY_STRING      # 交易所
        self.vtSymbol = EMPTY_STRING      # 合约在vt系统中的唯一代码
        
        self.open = EMPTY_FLOAT           # OHLC
        self.high = EMPTY_FLOAT
        self.low = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        
        self.date = EMPTY_STRING          # 日期
        self.time = EMPTY_STRING          # 时间
        self.datetime = None              # python的datetime时间对象
        
        self.volume = EMPTY_INT           # 成交量
        self.openInterest = EMPTY_INT     # 持仓量

class VtOrderData:
    """订单数据类"""
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码
        
        self.orderID = EMPTY_STRING             # 订单编号
        self.vtOrderID = EMPTY_STRING           # 订单在vt系统中的唯一编号
        
        self.direction = EMPTY_STRING           # 方向
        self.offset = EMPTY_STRING              # 开平
        self.price = EMPTY_FLOAT                # 价格
        self.totalVolume = EMPTY_INT            # 数量
        self.tradedVolume = EMPTY_INT           # 成交数量
        self.status = EMPTY_STRING              # 订单状态
        
        self.orderTime = EMPTY_STRING           # 下单时间
        self.cancelTime = EMPTY_STRING          # 撤单时间
        
        self.frontID = EMPTY_INT                # 前置机编号
        self.sessionID = EMPTY_INT              # 会话编号

class VtTradeData:
    """成交数据类"""
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码
        
        self.tradeID = EMPTY_STRING             # 成交编号
        self.vtTradeID = EMPTY_STRING           # 成交在vt系统中的唯一编号
        
        self.orderID = EMPTY_STRING             # 订单编号
        self.vtOrderID = EMPTY_STRING           # 订单在vt系统中的唯一编号
        
        self.direction = EMPTY_STRING           # 方向
        self.offset = EMPTY_STRING              # 开平
        self.price = EMPTY_FLOAT                # 价格
        self.volume = EMPTY_INT                 # 数量
        self.tradeTime = EMPTY_STRING           # 成交时间

class VtPositionData:
    """持仓数据类"""
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码
        
        self.direction = EMPTY_STRING           # 持仓方向
        self.position = EMPTY_INT               # 持仓量
        self.frozen = EMPTY_INT                 # 冻结数量
        self.price = EMPTY_FLOAT                # 持仓均价
        self.vtPositionName = EMPTY_STRING      # 持仓在vt系统中的唯一代码

class VtAccountData:
    """账户数据类"""
    def __init__(self):
        """Constructor"""
        self.accountID = EMPTY_STRING           # 账户代码
        self.vtAccountID = EMPTY_STRING         # 账户在vt中的唯一代码
        
        self.preBalance = EMPTY_FLOAT           # 昨日账户结算净值
        self.balance = EMPTY_FLOAT              # 账户净值
        self.available = EMPTY_FLOAT            # 可用资金
        self.commission = EMPTY_FLOAT           # 今日手续费
        self.margin = EMPTY_FLOAT               # 保证金占用
        self.closeProfit = EMPTY_FLOAT          # 平仓盈亏
        self.positionProfit = EMPTY_FLOAT       # 持仓盈亏

# 策略基类
class CtaTemplate:
    """CTA策略模板"""
    className = 'CtaTemplate'
    author = 'vnpy'
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                'className',
                'author',
                'vtSymbol']
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
              'trading',
              'pos']
    
    def __init__(self, ctaEngine=None, setting=None):
        """Constructor"""
        self.ctaEngine = ctaEngine
        
        # 策略的基本变量，由引擎管理
        self.inited = False                    # 策略初始化标记
        self.trading = False                   # 策略交易开关
        
        self.vtSymbol = EMPTY_STRING           # 交易的合约vt系统代码    
        self.pos = 0                           # 持仓量
        
        # 参数和变量设置
        if setting:
            self.setParams(setting)
    
    def setParams(self, setting):
        """设置参数"""
        for name in self.paramList:
            if name in setting:
                setattr(self, name, setting[name])
    
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        raise NotImplementedError

    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    def buy(self, price, volume, stop=False):
        """买开"""
        return self.sendOrder(DIRECTION_LONG, OFFSET_OPEN, price, volume, stop)
    
    def sell(self, price, volume, stop=False):
        """卖平"""
        return self.sendOrder(DIRECTION_SHORT, OFFSET_CLOSE, price, volume, stop)
    
    def short(self, price, volume, stop=False):
        """卖开"""
        return self.sendOrder(DIRECTION_SHORT, OFFSET_OPEN, price, volume, stop)
    
    def cover(self, price, volume, stop=False):
        """买平"""
        return self.sendOrder(DIRECTION_LONG, OFFSET_CLOSE, price, volume, stop)
    
    def sendOrder(self, direction, offset, price, volume, stop=False):
        """发送委托"""
        if self.trading:
            # 如果具有ctaEngine属性，使用ctaEngine发单
            if self.ctaEngine:
                if stop:
                    vtOrderID = self.ctaEngine.sendStopOrder(self.vtSymbol, direction, offset, price, volume)
                else:
                    vtOrderID = self.ctaEngine.sendOrder(self.vtSymbol, direction, offset, price, volume)
                return vtOrderID
            # 否则，返回空字符串
            else:
                return ''
        else:
            return ''
        
    def cancelOrder(self, vtOrderID):
        """撤单"""
        if self.trading:
            if self.ctaEngine:
                self.ctaEngine.cancelOrder(vtOrderID)

# 双均线策略
class DoubleMaStrategy(CtaTemplate):
    """双均线交易策略"""
    className = 'DoubleMaStrategy'
    author = 'vnpy'
    
    # 策略参数
    fastPeriod = 10     # 快速移动平均线周期
    slowPeriod = 30     # 慢速移动平均线周期
    initBars = 30       # 初始化需要的数据
    
    # 策略变量
    fastMa = 0          # 快速均线数值
    slowMa = 0          # 慢速均线数值
    
    # 参数列表
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastPeriod',
                 'slowPeriod']
    
    # 变量列表
    varList = ['inited',
               'trading',
               'pos',
               'fastMa',
               'slowMa']
    
    def __init__(self, ctaEngine=None, setting=None):
        """Constructor"""
        super(DoubleMaStrategy, self).__init__(ctaEngine, setting)
        
        # 指标数据
        self.barList = []
        
        # 创建指标变量
        self.fastMa = 0
        self.slowMa = 0
    
    def onInit(self):
        """初始化策略"""
        self.writeLog('双均线策略初始化')
        
        # 初始化指标
        self.barList = []
        self.fastMa = 0
        self.slowMa = 0
        
        # 加载历史数据用于初始化指标
        initData = self.loadBar(self.initBars)
        for bar in initData:
            self.barList.append(bar)
        
        self.inited = True
        self.writeLog('双均线策略初始化完成')
    
    def onStart(self):
        """启动策略"""
        self.writeLog('双均线策略启动')
        self.trading = True
    
    def onStop(self):
        """停止策略"""
        self.writeLog('双均线策略停止')
        self.trading = False
    
    def onBar(self, bar):
        """收到K线推送"""
        # 记录最新数据
        self.barList.append(bar)
        if len(self.barList) > self.slowPeriod:
            self.barList.pop(0)
        
        # 计算快速和慢速均线
        closePrices = [bar.close for bar in self.barList]
        
        if len(closePrices) >= self.fastPeriod:
            self.fastMa = sum(closePrices[-self.fastPeriod:]) / self.fastPeriod
        
        if len(closePrices) >= self.slowPeriod:
            self.slowMa = sum(closePrices[-self.slowPeriod:]) / self.slowPeriod
        
        # 交易逻辑
        # 当快速均线上穿慢速均线时，做多（买入）；当快速均线下穿慢速均线时，平仓（卖出）
        crossOver = self.fastMa > self.slowMa and self.fastMa <= self.slowMa
        crossBelow = self.fastMa < self.slowMa and self.fastMa >= self.slowMa
        
        if crossOver:  # 金叉
            # 如果当前持有空头，先平仓
            if self.pos < 0:
                self.cover(bar.close, abs(self.pos))
            # 开多仓
            if self.pos == 0:
                self.buy(bar.close, 1)
            
        elif crossBelow:  # 死叉
            # 如果当前持有多头，平仓
            if self.pos > 0:
                self.sell(bar.close, abs(self.pos))
            # 如果策略支持做空
            # if self.pos == 0:
            #     self.short(bar.close, 1)
    
    def writeLog(self, content):
        """输出日志"""
        print(f"{datetime.datetime.now()}: {content}")
    
    def loadBar(self, days):
        """加载历史数据"""
        if self.ctaEngine:
            return self.ctaEngine.loadBar(self.vtSymbol, days)
        return []

# 回测引擎基类
class BacktestingEngine:
    """回测引擎基类"""
    def __init__(self):
        """Constructor"""
        # 事件引擎
        self.eventEngine = EventEngine()
        
        # 策略字典
        self.strategyDict = {}
        
        # 数据字典
        self.barDict = {}
        
        # 持仓字典
        self.posDict = {}
        
        # 账户
        self.account = VtAccountData()
        self.account.balance = 100000.0  # 初始资金
        self.account.available = 100000.0
        
        # 回测结果
        self.result = {}
        self.resultDaily = {}
        
        # 交易记录
        self.tradeList = []
        
        # 日期
        self.startDate = None
        self.endDate = None
        self.currentDate = None
    
    def loadHistoryData(self, symbol, startDate, endDate, filePath=None):
        """加载历史数据"""
        if filePath and os.path.exists(filePath):
            # 读取CSV文件
            df = pd.read_csv(filePath, index_col=0, parse_dates=True)
            df = df.rename(columns={c: c.lower() for c in df.columns})
            
            # 根据日期过滤
            mask = (df.index >= startDate) & (df.index <= endDate)
            df = df.loc[mask]
            
            # 确保必要的列存在
            columns = ['open', 'high', 'low', 'close', 'volume']
            for col in columns:
                if col not in df.columns:
                    if col == 'volume':
                        df[col] = 0
                    else:
                        # 使用close填充缺失价格列
                        df[col] = df['close'] if 'close' in df.columns else 0
            
            # 转换为K线对象列表
            barList = []
            for index, row in df.iterrows():
                bar = VtBarData()
                bar.vtSymbol = symbol
                bar.symbol = symbol
                bar.open = row['open']
                bar.high = row['high']
                bar.low = row['low']
                bar.close = row['close']
                bar.volume = row['volume']
                bar.datetime = index
                bar.date = index.strftime('%Y-%m-%d')
                bar.time = index.strftime('%H:%M:%S')
                barList.append(bar)
            
            return barList
        
        else:
            print(f"无法找到文件: {filePath}，生成模拟数据")
            
            # 生成模拟数据
            start = pd.to_datetime(startDate)
            end = pd.to_datetime(endDate)
            dates = pd.date_range(start=start, end=end, freq='D')
            dates = dates[dates.dayofweek < 5]  # 只保留工作日
            
            barList = []
            price = 100.0
            
            # 设置随机种子以确保可重复性
            np.random.seed(42)
            
            for i, date in enumerate(dates):
                bar = VtBarData()
                bar.vtSymbol = symbol
                bar.symbol = symbol
                
                # 生成价格
                if i > 0:
                    price = price * (1 + np.random.normal(0, 0.01))
                
                bar.close = price
                bar.open = price * (1 + np.random.normal(0, 0.005))
                bar.high = max(bar.open, bar.close) * (1 + abs(np.random.normal(0, 0.003)))
                bar.low = min(bar.open, bar.close) * (1 - abs(np.random.normal(0, 0.003)))
                bar.volume = np.random.randint(10000, 100000)
                
                bar.datetime = date
                bar.date = date.strftime('%Y-%m-%d')
                bar.time = "00:00:00"
                
                barList.append(bar)
            
            return barList
    
    def addStrategy(self, strategyClass, setting=None):
        """添加策略"""
        strategy = strategyClass(self, setting)
        self.strategyDict[strategy.className] = strategy
        return strategy
    
    def loadBar(self, vtSymbol, days=0):
        """加载最近N天的历史数据"""
        if vtSymbol in self.barDict:
            bars = self.barDict[vtSymbol]
            if days > 0:
                return bars[-days:]
            else:
                return bars
        return []
    
    def initStrategy(self, strategyClassName):
        """初始化策略"""
        if strategyClassName in self.strategyDict:
            strategy = self.strategyDict[strategyClassName]
            strategy.onInit()
            return True
        return False
    
    def startStrategy(self, strategyClassName):
        """启动策略"""
        if strategyClassName in self.strategyDict:
            strategy = self.strategyDict[strategyClassName]
            strategy.onStart()
            return True
        return False
    
    def stopStrategy(self, strategyClassName):
        """停止策略"""
        if strategyClassName in self.strategyDict:
            strategy = self.strategyDict[strategyClassName]
            strategy.onStop()
            return True
        return False
    
    def processBarForStrategy(self, strategyClassName, bar):
        """处理单个K线给策略推送"""
        if strategyClassName in self.strategyDict:
            strategy = self.strategyDict[strategyClassName]
            if strategy.inited and strategy.trading:
                strategy.onBar(bar)
    
    def sendOrder(self, vtSymbol, direction, offset, price, volume):
        """发送委托"""
        # 创建订单
        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.price = price
        order.totalVolume = volume
        order.direction = direction
        order.offset = offset
        
        # 生成订单ID
        orderID = f"O-{int(time.time()*1000000)}"
        order.orderID = orderID
        order.vtOrderID = orderID
        
        # 更新持仓
        if vtSymbol not in self.posDict:
            self.posDict[vtSymbol] = 0
        
        # 处理订单
        if direction == DIRECTION_LONG and offset == OFFSET_OPEN:
            # 买开，加仓
            cost = price * volume
            if self.account.available >= cost:
                self.posDict[vtSymbol] += volume
                self.account.available -= cost
                
                # 记录交易
                trade = VtTradeData()
                trade.vtSymbol = vtSymbol
                trade.direction = direction
                trade.offset = offset
                trade.price = price
                trade.volume = volume
                trade.tradeTime = time.strftime('%H:%M:%S', time.localtime())
                
                self.tradeList.append(trade)
        
        elif direction == DIRECTION_SHORT and offset == OFFSET_CLOSE:
            # 卖平，减仓
            if self.posDict[vtSymbol] >= volume:
                self.posDict[vtSymbol] -= volume
                self.account.available += price * volume
                
                # 记录交易
                trade = VtTradeData()
                trade.vtSymbol = vtSymbol
                trade.direction = direction
                trade.offset = offset
                trade.price = price
                trade.volume = volume
                trade.tradeTime = time.strftime('%H:%M:%S', time.localtime())
                
                self.tradeList.append(trade)
        
        return orderID
    
    def calculateResult(self):
        """计算回测结果"""
        if not self.tradeList:
            self.result = {}
            return
        
        # 计算每日盈亏
        datePnl = {}  # 日期: 盈亏
        dateBalance = {}  # 日期: 账户结余
        lastBalance = self.account.balance
        
        # 逐笔交易对每日盈亏的贡献
        for trade in self.tradeList:
            tradeDate = trade.tradeTime.split(' ')[0]
            
            # 针对当前交易，计算每日盈亏
            if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_OPEN:
                # 买开，当天没有盈亏
                pass
            
            elif trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_CLOSE:
                # 卖平，计算盈亏
                openTrades = [t for t in self.tradeList if t.direction == DIRECTION_LONG and t.offset == OFFSET_OPEN and t.volume > 0]
                if openTrades:
                    openTrade = openTrades[0]  # 简化处理，假设先开先平
                    pnl = (trade.price - openTrade.price) * trade.volume
                    
                    if tradeDate in datePnl:
                        datePnl[tradeDate] += pnl
                    else:
                        datePnl[tradeDate] = pnl
        
        # 计算每日账户结余
        dates = sorted(datePnl.keys())
        for date in dates:
            pnl = datePnl[date]
            lastBalance += pnl
            dateBalance[date] = lastBalance
        
        # 计算回测结果
        self.result = {
            'startDate': self.startDate,
            'endDate': self.endDate,
            'totalDays': (pd.to_datetime(self.endDate) - pd.to_datetime(self.startDate)).days,
            'initialCapital': self.account.balance,
            'endCapital': lastBalance,
            'totalReturn': lastBalance / self.account.balance - 1,
            'annualReturn': (lastBalance / self.account.balance) ** (365 / max(1, (pd.to_datetime(self.endDate) - pd.to_datetime(self.startDate)).days)) - 1,
            'maxDrawdown': self.calculateMaxDrawdown(dateBalance),
            'dailyPnl': datePnl,
            'dailyBalance': dateBalance
        }
        
        # 计算夏普比率
        returns = []
        dates = sorted(dateBalance.keys())
        prevBalance = self.account.balance
        
        for date in dates:
            balance = dateBalance[date]
            dailyReturn = balance / prevBalance - 1
            returns.append(dailyReturn)
            prevBalance = balance
        
        if returns:
            mean = np.mean(returns)
            std = np.std(returns)
            sharpeRatio = mean / std * np.sqrt(252) if std > 0 else 0
            self.result['sharpeRatio'] = sharpeRatio
        else:
            self.result['sharpeRatio'] = 0
    
    def calculateMaxDrawdown(self, balanceDict):
        """计算最大回撤"""
        if not balanceDict:
            return 0
        
        # 转换为pandas Series
        balance = pd.Series(balanceDict)
        
        # 计算累计最大值
        cummax = balance.cummax()
        
        # 计算回撤
        drawdown = (cummax - balance) / cummax
        
        # 返回最大回撤
        return drawdown.max()
    
    def showResult(self):
        """显示回测结果"""
        if not self.result:
            print("没有回测结果可显示")
            return
        
        # 打印基本回测结果
        print("\n============== 回测结果 ==============")
        print(f"开始日期: {self.result['startDate']}")
        print(f"结束日期: {self.result['endDate']}")
        print(f"总交易日: {self.result['totalDays']}")
        print(f"初始资金: {self.result['initialCapital']:.2f}")
        print(f"结束资金: {self.result['endCapital']:.2f}")
        print(f"总收益率: {self.result['totalReturn']:.2%}")
        print(f"年化收益率: {self.result['annualReturn']:.2%}")
        print(f"最大回撤: {self.result['maxDrawdown']:.2%}")
        print(f"夏普比率: {self.result['sharpeRatio']:.4f}")
        
        # 绘制资金曲线
        if 'dailyBalance' in self.result and self.result['dailyBalance']:
            dates = sorted(self.result['dailyBalance'].keys())
            balance = [self.result['dailyBalance'][date] for date in dates]
            
            plt.figure(figsize=(12, 6))
            plt.plot(dates, balance)
            plt.title('账户资金曲线')
            plt.xlabel('日期')
            plt.ylabel('资金')
            plt.grid(True)
            plt.savefig('vnpy_backtest_balance.png', dpi=300)
            plt.show()
    
    def runBacktesting(self, startDate, endDate):
        """运行回测"""
        self.startDate = startDate
        self.endDate = endDate
        
        # 加载历史数据
        for symbol in self.strategyDict.values():
            vtSymbol = symbol.vtSymbol
            if vtSymbol:
                # 尝试从文件加载，或生成模拟数据
                filePath = f"../data/backtest_data/daily/SHSE/{vtSymbol}/price.csv"
                bars = self.loadHistoryData(vtSymbol, startDate, endDate, filePath)
                self.barDict[vtSymbol] = bars
        
        # 初始化策略
        for strategyClassName in self.strategyDict:
            self.initStrategy(strategyClassName)
            self.startStrategy(strategyClassName)
        
        # 推送K线数据
        for symbol in self.barDict:
            bars = self.barDict[symbol]
            for bar in bars:
                for strategyClassName in self.strategyDict:
                    self.processBarForStrategy(strategyClassName, bar)
        
        # 计算回测结果
        self.calculateResult()
        
        # 停止策略
        for strategyClassName in self.strategyDict:
            self.stopStrategy(strategyClassName)

# 主函数
def main():
    """主函数"""
    print("============= vnpy风格回测引擎 - 双均线交叉策略 =============")
    
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置策略参数
    setting = {
        'fastPeriod': 10,
        'slowPeriod': 30,
        'vtSymbol': '000001',
    }
    
    # 添加策略
    strategy = engine.addStrategy(DoubleMaStrategy, setting)
    
    # 设置回测参数
    startDate = '2020-01-01'
    endDate = '2022-12-31'
    
    # 运行回测
    start_time = time.time()
    print(f"开始回测 {startDate} 至 {endDate}...")
    engine.runBacktesting(startDate, endDate)
    
    # 显示回测结果
    engine.showResult()
    
    # 输出回测性能
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n回测用时: {duration:.2f} 秒")
    print(f"交易次数: {len(engine.tradeList)}")
    
    # 计算胜率
    if engine.tradeList:
        winTrades = [t for t in engine.tradeList if t.direction == DIRECTION_SHORT and t.offset == OFFSET_CLOSE]
        winCount = 0
        for trade in winTrades:
            openTrades = [t for t in engine.tradeList if t.direction == DIRECTION_LONG and t.offset == OFFSET_OPEN]
            if openTrades:
                openTrade = openTrades[0]  # 简化处理
                if trade.price > openTrade.price:
                    winCount += 1
        winRate = winCount / len(winTrades) if winTrades else 0
        print(f"胜率: {winRate:.2%}")
    
    print("注: vnpy框架的核心优势在于事件驱动架构和全市场支持")

if __name__ == "__main__":
    main() 