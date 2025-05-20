#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速启动QTE模拟交易所
"""
from qte.exchange import MockExchange
import logging
import signal
import sys
import time

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QTE模拟交易所")

def main():
    """主函数，启动模拟交易所"""
    # 创建模拟交易所实例
    exchange = MockExchange(
        rest_host="localhost",
        rest_port=5000,
        ws_host="localhost",
        ws_port=8765
    )
    
    # 设置信号处理，以便在Ctrl+C时优雅退出
    def signal_handler(sig, frame):
        logger.info("收到中断信号，正在停止服务...")
        exchange.stop()
        logger.info("服务已停止，退出程序")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动交易所服务
        logger.info("正在启动交易所服务...")
        exchange.start()
        
        # 注册一些常用交易对
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        for symbol in symbols:
            # 简单解析交易对获取基础和计价资产
            base_asset = symbol[:3]
            quote_asset = symbol[3:]
            
            logger.info(f"注册交易对: {symbol}")
            exchange.register_symbol(symbol, base_asset, quote_asset)
        
        # 创建演示账户
        user_id = "demo_user"
        api_key = exchange.create_user(user_id, "Demo User")
        
        # 为账户充值
        for symbol in symbols:
            base_asset = symbol[:3]
            quote_asset = symbol[3:]
            
            # 充值基础资产和计价资产
            exchange.deposit(user_id, base_asset, 1.0)
            exchange.deposit(user_id, quote_asset, 100000.0)
            
            logger.info(f"为账户 {user_id} 充值资产: {base_asset}=1.0, {quote_asset}=100000.0")
        
        logger.info(f"演示账户已创建，用户ID: {user_id}, API密钥: {api_key}")
        logger.info("请保存此API密钥用于API认证")
        
        # 显示访问信息
        logger.info("\n" + "-" * 50)
        logger.info("模拟交易所服务已启动!")
        logger.info(f"REST API: http://localhost:5000")
        logger.info(f"WebSocket: ws://localhost:8765")
        logger.info("-" * 50)
        logger.info("支持的API接口：")
        logger.info("  - 市场数据: /api/v1/ping, /api/v1/time, /api/v1/ticker/price, /api/v1/depth 等")
        logger.info("  - 交易接口: /api/v1/order, /api/v1/openOrders, /api/v1/myTrades 等")
        logger.info("  - 账户管理: /api/v1/account")
        logger.info("-" * 50)
        logger.info("使用Ctrl+C终止服务")
        
        # 保持服务运行
        while True:
            time.sleep(1)
    
    except Exception as e:
        logger.error(f"启动服务时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()