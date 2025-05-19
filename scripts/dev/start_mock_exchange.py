#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动模拟交易所服务脚本
"""
import argparse
import logging
import signal
import sys
import time
from typing import Dict, List, Optional, Any

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MockExchangeService")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="启动QTE模拟交易所服务")
    
    parser.add_argument("--rest-host", type=str, default="localhost",
                        help="REST API主机地址 (默认: localhost)")
    parser.add_argument("--rest-port", type=int, default=5000,
                        help="REST API端口 (默认: 5000)")
    parser.add_argument("--ws-host", type=str, default="localhost",
                        help="WebSocket主机地址 (默认: localhost)")
    parser.add_argument("--ws-port", type=int, default=8765,
                        help="WebSocket端口 (默认: 8765)")
    parser.add_argument("--symbols", type=str, nargs="+", default=["BTCUSDT"],
                        help="交易对列表，空格分隔 (默认: BTCUSDT)")
    parser.add_argument("--demo-account", action="store_true",
                        help="是否创建演示账户")
    parser.add_argument("--demo-balance", type=float, default=10000.0,
                        help="演示账户初始余额 (默认: 10000.0)")
    
    return parser.parse_args()

def setup_signal_handlers(exchange):
    """设置信号处理器，以便在Ctrl+C时优雅退出"""
    def signal_handler(sig, frame):
        logger.info("收到中断信号，正在停止服务...")
        exchange.stop()
        logger.info("服务已停止，退出程序")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """主函数"""
    args = parse_args()
    
    try:
        # 导入模拟交易所
        from qte.exchange import MockExchange
        
        # 创建模拟交易所实例
        logger.info(f"正在创建模拟交易所实例 (REST: {args.rest_host}:{args.rest_port}, WS: {args.ws_host}:{args.ws_port})...")
        exchange = MockExchange(
            rest_host=args.rest_host,
            rest_port=args.rest_port,
            ws_host=args.ws_host,
            ws_port=args.ws_port
        )
        
        # 设置信号处理
        setup_signal_handlers(exchange)
        
        # 启动交易所服务
        logger.info("正在启动交易所服务...")
        exchange.start()
        
        # 注册交易对
        for symbol in args.symbols:
            logger.info(f"注册交易对: {symbol}")
            # 简单解析交易对获取基础和计价资产
            if '/' in symbol:
                base_asset, quote_asset = symbol.split('/')
            else:
                # 尝试按常见格式拆分，如BTCUSDT -> BTC, USDT
                base_asset = symbol[:3]
                quote_asset = symbol[3:]
            
            exchange.register_symbol(symbol, base_asset, quote_asset)
        
        # 创建演示账户
        if args.demo_account:
            user_id = "demo_user"
            logger.info(f"创建演示账户: {user_id}")
            api_key = exchange.create_user(user_id, "Demo User")
            
            # 为账户充值
            for symbol in args.symbols:
                if '/' in symbol:
                    base_asset, quote_asset = symbol.split('/')
                else:
                    base_asset = symbol[:3]
                    quote_asset = symbol[3:]
                
                # 充值基础资产和计价资产
                exchange.deposit(user_id, base_asset, args.demo_balance * 0.01)  # 基础资产充少一点
                exchange.deposit(user_id, quote_asset, args.demo_balance)        # 计价资产充多一点
                
                logger.info(f"为账户 {user_id} 充值资产: {base_asset}={args.demo_balance * 0.01}, {quote_asset}={args.demo_balance}")
            
            logger.info(f"演示账户API密钥: {api_key}")
            logger.info("请保存此API密钥用于API认证")
        
        # 显示服务信息
        logger.info(f"模拟交易所服务已启动")
        logger.info(f"REST API: http://{args.rest_host}:{args.rest_port}")
        logger.info(f"WebSocket: ws://{args.ws_host}:{args.ws_port}")
        logger.info("使用Ctrl+C终止服务")
        
        # 保持服务运行
        while True:
            time.sleep(1)
            
    except ImportError:
        logger.error("导入模块失败，请确保已安装QTE库")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动服务时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()