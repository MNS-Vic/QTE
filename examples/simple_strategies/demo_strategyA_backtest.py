#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
移动平均线交叉策略回测演示

此脚本演示如何使用掘金数据提供者和移动平均线交叉策略进行回测
"""

import sys
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入策略和回测器
try:
    from test.test_ma_cross_strategy import run_backtest
    from strategy.strategyA.ma_cross_strategy import MACrossStrategy
    from qte_data.gm_data_provider import GmDataProvider
    from qte_core.event_loop import EventLoop
except ImportError as e:
    logger.error(f"导入模块出错: {e}")
    logger.error("请确保当前目录是项目根目录，并且已安装所有依赖")
    sys.exit(1)


def main():
    """主函数"""
    logger.info("===== 移动平均线交叉策略回测演示 =====")
    
    # 定义回测参数
    symbol = "SHSE.000001"  # 上证指数
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    short_window = 5  # 短期均线周期
    long_window = 20  # 长期均线周期
    initial_capital = 100000.0  # 初始资金
    
    logger.info("回测参数:")
    logger.info(f"交易品种: {symbol}")
    logger.info(f"回测周期: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"短期均线: {short_window}日")
    logger.info(f"长期均线: {long_window}日")
    logger.info(f"初始资金: {initial_capital:.2f}")
    
    try:
        # 运行回测
        results = run_backtest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            short_window=short_window,
            long_window=long_window,
            initial_capital=initial_capital
        )
        
        if results:
            logger.info("\n===== 回测结果 =====")
            logger.info(f"总收益率: {results['total_return']:.2%}")
            logger.info(f"年化收益率: {results['annual_return']:.2%}")
            logger.info(f"最大回撤: {results['max_drawdown']:.2%}")
            logger.info(f"夏普比率: {results['sharpe_ratio']:.2f}")
            
            # 交易统计
            if not isinstance(results['trades'], list) and not results['trades'].empty:
                buy_trades = results['trades'][results['trades']['action'] == 'BUY']
                sell_trades = results['trades'][results['trades']['action'] == 'SELL']
                close_trades = results['trades'][results['trades']['action'] == 'CLOSE']
                
                logger.info(f"交易次数: {len(results['trades'])}")
                logger.info(f"买入次数: {len(buy_trades)}")
                logger.info(f"卖出次数: {len(sell_trades)}")
                logger.info(f"平仓次数: {len(close_trades)}")
        else:
            logger.warning("回测未返回结果")
    
    except Exception as e:
        logger.error(f"回测过程出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    logger.info("\n演示完成")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 