#!/usr/bin/env python3
"""
QTE业务指标监控模块
收集和暴露关键业务指标供Prometheus抓取
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
import psycopg2
import redis
import json


@dataclass
class TradingMetrics:
    """交易指标数据结构"""
    total_trades: int = 0
    total_volume: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    open_positions: int = 0
    portfolio_value: float = 0.0
    cash_balance: float = 0.0
    risk_exposure: float = 0.0


class BusinessMetricsCollector:
    """业务指标收集器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 数据库连接
        self.db_config = config.get('database', {})
        self.redis_config = config.get('redis', {})
        
        # Prometheus指标定义
        self._init_prometheus_metrics()
        
        # 运行状态
        self.running = False
        self.collection_thread = None
        self.collection_interval = config.get('collection_interval', 30)  # 30秒
        
    def _init_prometheus_metrics(self):
        """初始化Prometheus指标"""
        
        # 交易相关指标
        self.trades_total = Counter(
            'qte_trades_total',
            '总交易笔数',
            ['symbol', 'side', 'strategy']
        )
        
        self.trading_volume = Counter(
            'qte_trading_volume_total',
            '总交易量',
            ['symbol', 'side']
        )
        
        self.orders_total = Counter(
            'qte_orders_total',
            '总订单数',
            ['symbol', 'side', 'type', 'status']
        )
        
        self.orders_rejected = Counter(
            'qte_orders_rejected_total',
            '被拒绝的订单数',
            ['symbol', 'reason']
        )
        
        # 投资组合指标
        self.portfolio_value = Gauge(
            'qte_portfolio_total_value',
            '投资组合总价值'
        )
        
        self.portfolio_cash = Gauge(
            'qte_portfolio_cash',
            '现金余额'
        )
        
        self.portfolio_positions_value = Gauge(
            'qte_portfolio_positions_value',
            '持仓总价值'
        )
        
        self.portfolio_pnl = Gauge(
            'qte_portfolio_pnl',
            '投资组合盈亏',
            ['period']
        )
        
        self.open_positions = Gauge(
            'qte_open_positions',
            '开放持仓数量',
            ['symbol']
        )
        
        # 风险指标
        self.risk_exposure = Gauge(
            'qte_portfolio_risk_exposure',
            '投资组合风险敞口'
        )
        
        self.risk_limit = Gauge(
            'qte_portfolio_risk_limit',
            '风险限制'
        )
        
        self.drawdown = Gauge(
            'qte_portfolio_drawdown',
            '投资组合回撤',
            ['type']
        )
        
        # 策略指标
        self.strategy_pnl = Gauge(
            'qte_strategy_pnl',
            '策略盈亏',
            ['strategy_name', 'period']
        )
        
        self.strategy_sharpe_ratio = Gauge(
            'qte_strategy_sharpe_ratio',
            '策略夏普比率',
            ['strategy_name']
        )
        
        self.strategy_win_rate = Gauge(
            'qte_strategy_win_rate',
            '策略胜率',
            ['strategy_name']
        )
        
        # 市场数据指标
        self.market_data_latency = Histogram(
            'qte_market_data_latency_seconds',
            '市场数据延迟',
            ['source', 'symbol']
        )
        
        self.last_market_data_timestamp = Gauge(
            'qte_last_market_data_timestamp',
            '最后市场数据时间戳',
            ['source', 'symbol']
        )
        
        self.data_feed_connected = Gauge(
            'qte_data_feed_connected',
            '数据源连接状态',
            ['source']
        )
        
        # 系统性能指标
        self.event_processing_rate = Gauge(
            'qte_event_processing_rate',
            '事件处理速率'
        )
        
        self.event_queue_size = Gauge(
            'qte_event_queue_size',
            '事件队列大小'
        )
        
        self.memory_usage = Gauge(
            'qte_memory_usage_bytes',
            '内存使用量'
        )
        
        self.cpu_usage = Gauge(
            'qte_cpu_usage_percent',
            'CPU使用率'
        )
        
        # 错误和异常指标
        self.errors_total = Counter(
            'qte_errors_total',
            '错误总数',
            ['component', 'error_type']
        )
        
        self.exceptions_total = Counter(
            'qte_exceptions_total',
            '异常总数',
            ['component', 'exception_type']
        )
        
        # 业务质量指标
        self.price_anomalies = Counter(
            'qte_price_anomalies_total',
            '价格异常总数',
            ['symbol', 'anomaly_type']
        )
        
        self.suspicious_requests = Counter(
            'qte_suspicious_requests_total',
            '可疑请求总数',
            ['source', 'type']
        )
        
        self.auth_failures = Counter(
            'qte_auth_failures_total',
            '认证失败总数',
            ['source', 'reason']
        )
    
    def _get_db_connection(self):
        """获取数据库连接"""
        try:
            return psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'qte'),
                user=self.db_config.get('username', 'qte'),
                password=self.db_config.get('password', '')
            )
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return None
    
    def _get_redis_connection(self):
        """获取Redis连接"""
        try:
            return redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('database', 0),
                password=self.redis_config.get('password', None),
                decode_responses=True
            )
        except Exception as e:
            self.logger.error(f"Redis连接失败: {e}")
            return None
    
    def collect_trading_metrics(self) -> TradingMetrics:
        """收集交易指标"""
        metrics = TradingMetrics()
        
        db_conn = self._get_db_connection()
        if not db_conn:
            return metrics
        
        try:
            cursor = db_conn.cursor()
            
            # 查询总交易数
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(quantity * price), 0)
                FROM trades 
                WHERE created_at >= CURRENT_DATE
            """)
            daily_trades, daily_volume = cursor.fetchone()
            
            # 查询日收益
            cursor.execute("""
                SELECT COALESCE(SUM(pnl), 0)
                FROM trades 
                WHERE created_at >= CURRENT_DATE
            """)
            daily_pnl = cursor.fetchone()[0]
            
            # 查询开放持仓
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol), COALESCE(SUM(ABS(quantity)), 0)
                FROM positions 
                WHERE quantity != 0
            """)
            open_positions, total_exposure = cursor.fetchone()
            
            # 查询投资组合价值
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN quantity > 0 THEN quantity * current_price ELSE 0 END), 0) as long_value,
                    COALESCE(SUM(CASE WHEN quantity < 0 THEN ABS(quantity) * current_price ELSE 0 END), 0) as short_value,
                    (SELECT cash_balance FROM portfolio_summary ORDER BY updated_at DESC LIMIT 1) as cash
            """)
            long_value, short_value, cash_balance = cursor.fetchone()
            
            # 更新指标
            metrics.total_trades = daily_trades or 0
            metrics.total_volume = daily_volume or 0.0
            metrics.daily_pnl = daily_pnl or 0.0
            metrics.open_positions = open_positions or 0
            metrics.portfolio_value = (long_value or 0.0) + (cash_balance or 0.0)
            metrics.cash_balance = cash_balance or 0.0
            metrics.risk_exposure = total_exposure or 0.0
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"收集交易指标失败: {e}")
        finally:
            db_conn.close()
        
        return metrics
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """收集系统指标"""
        metrics = {}
        
        redis_conn = self._get_redis_connection()
        if not redis_conn:
            return metrics
        
        try:
            # 从Redis获取实时系统指标
            event_queue_size = redis_conn.get('qte:event_queue_size')
            if event_queue_size:
                metrics['event_queue_size'] = float(event_queue_size)
            
            processing_rate = redis_conn.get('qte:event_processing_rate')
            if processing_rate:
                metrics['event_processing_rate'] = float(processing_rate)
            
            memory_usage = redis_conn.get('qte:memory_usage')
            if memory_usage:
                metrics['memory_usage'] = float(memory_usage)
            
            cpu_usage = redis_conn.get('qte:cpu_usage')
            if cpu_usage:
                metrics['cpu_usage'] = float(cpu_usage)
                
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
        
        return metrics
    
    def collect_strategy_metrics(self) -> Dict[str, Dict[str, float]]:
        """收集策略指标"""
        strategy_metrics = {}
        
        db_conn = self._get_db_connection()
        if not db_conn:
            return strategy_metrics
        
        try:
            cursor = db_conn.cursor()
            
            # 查询策略表现
            cursor.execute("""
                SELECT 
                    strategy_name,
                    COALESCE(SUM(pnl), 0) as total_pnl,
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                    COALESCE(STDDEV(pnl), 0) as pnl_std
                FROM trades 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY strategy_name
            """)
            
            for row in cursor.fetchall():
                strategy_name, total_pnl, total_trades, winning_trades, pnl_std = row
                
                win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
                sharpe_ratio = (total_pnl / pnl_std) if pnl_std > 0 else 0
                
                strategy_metrics[strategy_name] = {
                    'pnl': total_pnl or 0.0,
                    'win_rate': win_rate,
                    'sharpe_ratio': sharpe_ratio,
                    'total_trades': total_trades or 0
                }
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"收集策略指标失败: {e}")
        finally:
            db_conn.close()
        
        return strategy_metrics
    
    def update_prometheus_metrics(self):
        """更新Prometheus指标"""
        try:
            # 收集交易指标
            trading_metrics = self.collect_trading_metrics()
            
            # 更新投资组合指标
            self.portfolio_value.set(trading_metrics.portfolio_value)
            self.portfolio_cash.set(trading_metrics.cash_balance)
            self.portfolio_positions_value.set(
                trading_metrics.portfolio_value - trading_metrics.cash_balance
            )
            self.portfolio_pnl.labels(period='daily').set(trading_metrics.daily_pnl)
            self.risk_exposure.set(trading_metrics.risk_exposure)
            
            # 收集系统指标
            system_metrics = self.collect_system_metrics()
            
            for metric_name, value in system_metrics.items():
                if hasattr(self, metric_name):
                    getattr(self, metric_name).set(value)
            
            # 收集策略指标
            strategy_metrics = self.collect_strategy_metrics()
            
            for strategy_name, metrics in strategy_metrics.items():
                self.strategy_pnl.labels(
                    strategy_name=strategy_name, 
                    period='30d'
                ).set(metrics['pnl'])
                
                self.strategy_win_rate.labels(
                    strategy_name=strategy_name
                ).set(metrics['win_rate'])
                
                self.strategy_sharpe_ratio.labels(
                    strategy_name=strategy_name
                ).set(metrics['sharpe_ratio'])
            
            self.logger.debug("Prometheus指标更新完成")
            
        except Exception as e:
            self.logger.error(f"更新Prometheus指标失败: {e}")
    
    def _collection_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                self.update_prometheus_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"指标收集循环错误: {e}")
                time.sleep(5)  # 错误时短暂等待
    
    def start(self, port: int = 9090):
        """启动指标收集器"""
        if self.running:
            self.logger.warning("指标收集器已在运行")
            return
        
        self.logger.info(f"启动业务指标收集器，端口: {port}")
        
        # 启动Prometheus HTTP服务器
        start_http_server(port)
        
        # 启动收集线程
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        self.logger.info("业务指标收集器启动完成")
    
    def stop(self):
        """停止指标收集器"""
        if not self.running:
            return
        
        self.logger.info("停止业务指标收集器")
        self.running = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
        
        self.logger.info("业务指标收集器已停止")


def main():
    """主函数"""
    import yaml
    import os
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    config_path = os.getenv('QTE_CONFIG_PATH', '/app/config/production.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        return
    
    # 创建并启动指标收集器
    collector = BusinessMetricsCollector(config)
    
    try:
        collector.start(port=9090)
        
        # 保持运行
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logging.info("收到停止信号")
    finally:
        collector.stop()


if __name__ == "__main__":
    main()
