"""
回测器服务 - 负责执行策略回测
"""

import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class BacktestResult:
    """回测结果类"""
    
    def __init__(self):
        self.initial_capital = 0.0
        self.final_equity = 0.0
        self.total_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.equity_curve = []
        self.transactions = []
        self.metrics = {}
        self.outputs = {}
    
    def calculate_metrics(self):
        """计算回测指标"""
        if self.initial_capital <= 0:
            return
        
        # 基本指标
        total_return = (self.final_equity - self.initial_capital) / self.initial_capital
        
        # 年化收益率 (假设30天数据)
        days = 30  # 可以从equity_curve计算实际天数
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown()
        
        # 夏普比率 (简化计算)
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # 胜率
        win_rate = self.winning_trades / max(self.total_trades, 1)
        
        # 盈亏比
        avg_profit_loss_ratio = self._calculate_avg_profit_loss_ratio()
        
        self.metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trade_count': self.total_trades,
            'win_rate': win_rate,
            'avg_profit_loss_ratio': avg_profit_loss_ratio,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades
        }
    
    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.equity_curve:
            return 0.0
        
        equity_values = [point['equity'] for point in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0.0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_sharpe_ratio(self) -> float:
        """计算夏普比率"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        # 计算日收益率
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1]['equity']
            curr_equity = self.equity_curve[i]['equity']
            if prev_equity > 0:
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        # 计算夏普比率
        mean_return = sum(returns) / len(returns)
        if len(returns) < 2:
            return 0.0
        
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_return = variance ** 0.5
        
        if std_return == 0:
            return 0.0
        
        # 年化夏普比率 (假设无风险利率为0)
        sharpe = (mean_return / std_return) * (252 ** 0.5)  # 252个交易日
        return sharpe
    
    def _calculate_avg_profit_loss_ratio(self) -> float:
        """计算平均盈亏比"""
        if not self.transactions:
            return 0.0
        
        profits = [t['pnl'] for t in self.transactions if t['pnl'] > 0]
        losses = [abs(t['pnl']) for t in self.transactions if t['pnl'] < 0]
        
        if not profits or not losses:
            return 0.0
        
        avg_profit = sum(profits) / len(profits)
        avg_loss = sum(losses) / len(losses)
        
        return avg_profit / avg_loss if avg_loss > 0 else 0.0


class BacktesterService:
    """回测器服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化回测器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger('BacktesterService')
        
        # 回测参数
        self.initial_capital = config.get('initial_capital', 100000.0)
        self.commission = config.get('commission', 0.001)
        self.slippage = config.get('slippage', 0.0001)
        
        self.logger.info(f"📊 回测器初始化: 初始资金=${self.initial_capital:,.2f}")
    
    def run_backtest(self, 
                    data: Dict[str, Any], 
                    strategy: Any,
                    initial_capital: Optional[float] = None) -> BacktestResult:
        """
        运行回测
        
        Args:
            data: 市场数据
            strategy: 交易策略
            initial_capital: 初始资金
            
        Returns:
            回测结果
        """
        initial_capital = initial_capital or self.initial_capital
        
        self.logger.info("🔄 开始回测...")
        
        # 初始化回测结果
        result = BacktestResult()
        result.initial_capital = initial_capital
        
        # 回测状态
        current_capital = initial_capital
        positions = {}  # symbol -> quantity
        
        # 处理市场数据
        total_trades = 0
        
        # 获取所有数据点并按时间排序
        all_data_points = self._prepare_data_for_backtest(data)
        
        # 初始化权益曲线
        result.equity_curve.append({
            'timestamp': all_data_points[0]['timestamp'] if all_data_points else datetime.now().isoformat(),
            'equity': current_capital,
            'cash': current_capital,
            'positions_value': 0.0,
            'drawdown': 0.0
        })
        
        # 逐个处理数据点
        for data_point in all_data_points:
            # 创建市场事件
            market_event = {
                'symbol': data_point['symbol'],
                'timestamp': data_point['timestamp'],
                'open_price': data_point['open'],
                'high_price': data_point['high'],
                'low_price': data_point['low'],
                'close_price': data_point['close'],
                'volume': data_point['volume']
            }
            
            # 策略处理
            signal = strategy.process_market_data(market_event)
            
            if signal:
                # 执行交易
                trade_result = self._execute_trade(
                    signal, market_event, current_capital, positions
                )
                
                if trade_result:
                    # 更新资金和持仓
                    current_capital = trade_result['new_capital']
                    positions = trade_result['new_positions']
                    total_trades += 1
                    
                    # 记录交易
                    result.transactions.append(trade_result['transaction'])
                    
                    # 更新策略持仓
                    strategy.update_position(signal['symbol'], signal['direction'])
                    
                    self.logger.debug(f"📈 执行交易: {signal['symbol']} {signal['signal_type']}")
            
            # 更新权益曲线
            positions_value = self._calculate_positions_value(positions, data)
            total_equity = current_capital + positions_value
            
            result.equity_curve.append({
                'timestamp': data_point['timestamp'],
                'equity': total_equity,
                'cash': current_capital,
                'positions_value': positions_value,
                'drawdown': 0.0  # 将在后面计算
            })
        
        # 计算最终结果
        result.final_equity = result.equity_curve[-1]['equity'] if result.equity_curve else initial_capital
        result.total_pnl = result.final_equity - result.initial_capital
        result.total_trades = total_trades
        
        # 统计盈亏交易
        for transaction in result.transactions:
            if transaction['pnl'] > 0:
                result.winning_trades += 1
            elif transaction['pnl'] < 0:
                result.losing_trades += 1
        
        # 计算回撤
        self._calculate_drawdowns(result.equity_curve)
        
        # 计算指标
        result.calculate_metrics()
        
        # 生成输出
        result.outputs = {
            'equity_curve_df': pd.DataFrame(result.equity_curve),
            'transactions_df': pd.DataFrame(result.transactions) if result.transactions else pd.DataFrame(),
            'summary': {
                'initial_capital': result.initial_capital,
                'final_equity': result.final_equity,
                'total_pnl': result.total_pnl,
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades
            }
        }
        
        self.logger.info(f"✅ 回测完成，总交易次数: {total_trades}")
        return result
    
    def _prepare_data_for_backtest(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """准备回测数据"""
        all_points = []
        
        if 'data' in data:
            # 新格式：data是包含各个标的数据的字典
            for symbol, symbol_data in data['data'].items():
                if 'data' in symbol_data:
                    for point in symbol_data['data']:
                        point_copy = point.copy()
                        point_copy['symbol'] = symbol
                        all_points.append(point_copy)
        else:
            # 旧格式：直接是数据字典
            for symbol, symbol_data in data.items():
                if isinstance(symbol_data, dict) and 'data' in symbol_data:
                    for point in symbol_data['data']:
                        point_copy = point.copy()
                        point_copy['symbol'] = symbol
                        all_points.append(point_copy)
        
        # 按时间排序
        all_points.sort(key=lambda x: x['timestamp'])
        return all_points
    
    def _execute_trade(self, signal: Dict[str, Any], market_event: Dict[str, Any], 
                      current_capital: float, positions: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """执行交易"""
        symbol = signal['symbol']
        direction = signal['direction']
        price = market_event['close_price']
        
        # 计算交易数量 (简化：固定金额)
        trade_amount = min(current_capital * 0.1, 10000)  # 10%资金或最多1万
        quantity = int(trade_amount / price) if price > 0 else 0
        
        if quantity <= 0:
            return None
        
        # 计算交易成本
        trade_value = quantity * price
        commission_cost = trade_value * self.commission
        slippage_cost = trade_value * self.slippage
        total_cost = commission_cost + slippage_cost
        
        # 检查资金是否足够
        if direction > 0:  # 买入
            total_required = trade_value + total_cost
            if total_required > current_capital:
                return None
            
            new_capital = current_capital - total_required
            new_positions = positions.copy()
            new_positions[symbol] = new_positions.get(symbol, 0) + quantity
            
        else:  # 卖出
            current_position = positions.get(symbol, 0)
            if current_position < quantity:
                quantity = current_position
                if quantity <= 0:
                    return None
                trade_value = quantity * price
            
            new_capital = current_capital + trade_value - total_cost
            new_positions = positions.copy()
            new_positions[symbol] = new_positions.get(symbol, 0) - quantity
        
        # 计算盈亏 (简化计算)
        pnl = trade_value * direction - total_cost
        
        transaction = {
            'timestamp': market_event['timestamp'],
            'symbol': symbol,
            'direction': 'BUY' if direction > 0 else 'SELL',
            'quantity': quantity,
            'price': price,
            'trade_value': trade_value,
            'commission': commission_cost,
            'slippage': slippage_cost,
            'pnl': pnl
        }
        
        return {
            'new_capital': new_capital,
            'new_positions': new_positions,
            'transaction': transaction
        }
    
    def _calculate_positions_value(self, positions: Dict[str, int], data: Dict[str, Any]) -> float:
        """计算持仓价值 (简化实现)"""
        # 这里简化处理，实际应该用最新价格计算
        return 0.0
    
    def _calculate_drawdowns(self, equity_curve: List[Dict[str, Any]]):
        """计算回撤"""
        if not equity_curve:
            return
        
        peak = equity_curve[0]['equity']
        
        for point in equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak if peak > 0 else 0.0
            point['drawdown'] = drawdown
