#!/usr/bin/env python3
"""
QTE性能监控和基准测试脚本
定期执行性能测试，检测性能回归
"""

import time
import json
import logging
import statistics
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests
import psutil
import threading


@dataclass
class PerformanceBenchmark:
    """性能基准数据结构"""
    test_name: str
    timestamp: str
    duration_seconds: float
    throughput_ops_per_sec: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    error_count: int
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 基准配置
        self.baseline_file = config.get('baseline_file', '/opt/qte/performance_baseline.json')
        self.regression_threshold = config.get('regression_threshold', 0.2)  # 20%性能下降阈值
        self.test_interval = config.get('test_interval', 3600)  # 1小时
        
        # QTE服务配置
        self.qte_host = config.get('qte_host', 'localhost')
        self.qte_port = config.get('qte_port', 8080)
        self.qte_admin_port = config.get('qte_admin_port', 8081)
        
        # 告警配置
        self.webhook_url = config.get('webhook_url')
        
        # 运行状态
        self.running = False
        self.monitor_thread = None
        
        # 历史数据
        self.performance_history: List[PerformanceBenchmark] = []
        self.baseline_metrics: Optional[Dict[str, float]] = None
        
        self._load_baseline()
    
    def _load_baseline(self):
        """加载性能基准"""
        try:
            with open(self.baseline_file, 'r') as f:
                self.baseline_metrics = json.load(f)
            self.logger.info(f"已加载性能基准: {self.baseline_file}")
        except FileNotFoundError:
            self.logger.warning("未找到性能基准文件，将创建新基准")
            self.baseline_metrics = None
        except Exception as e:
            self.logger.error(f"加载性能基准失败: {e}")
            self.baseline_metrics = None
    
    def _save_baseline(self, metrics: Dict[str, float]):
        """保存性能基准"""
        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            self.logger.info(f"已保存性能基准: {self.baseline_file}")
        except Exception as e:
            self.logger.error(f"保存性能基准失败: {e}")
    
    def test_api_performance(self) -> PerformanceBenchmark:
        """测试API性能"""
        test_name = "api_performance"
        start_time = time.time()
        
        # 性能指标
        latencies = []
        errors = 0
        total_requests = 100
        
        # 系统资源监控
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = []
        
        self.logger.info(f"开始API性能测试，请求数: {total_requests}")
        
        # 执行性能测试
        for i in range(total_requests):
            request_start = time.time()
            
            try:
                # 测试健康检查端点
                response = requests.get(
                    f"http://{self.qte_host}:{self.qte_port}/health",
                    timeout=10
                )
                
                if response.status_code == 200:
                    latency = (time.time() - request_start) * 1000  # ms
                    latencies.append(latency)
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                self.logger.debug(f"请求失败: {e}")
            
            # 监控CPU使用率
            if i % 10 == 0:
                cpu_percent.append(psutil.cpu_percent())
            
            # 控制请求频率
            time.sleep(0.01)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 计算最终内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = final_memory - initial_memory
        
        # 计算性能指标
        success_rate = (total_requests - errors) / total_requests
        throughput = total_requests / duration
        
        if latencies:
            p50_latency = statistics.median(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        else:
            p50_latency = p95_latency = p99_latency = 0
        
        avg_cpu = statistics.mean(cpu_percent) if cpu_percent else 0
        
        benchmark = PerformanceBenchmark(
            test_name=test_name,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration,
            throughput_ops_per_sec=throughput,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=avg_cpu,
            success_rate=success_rate,
            error_count=errors,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency
        )
        
        self.logger.info(f"API性能测试完成: 吞吐量={throughput:.1f}ops/s, "
                        f"成功率={success_rate:.2%}, P95延迟={p95_latency:.1f}ms")
        
        return benchmark
    
    def test_event_processing_performance(self) -> PerformanceBenchmark:
        """测试事件处理性能"""
        test_name = "event_processing"
        start_time = time.time()
        
        # 通过管理接口获取事件处理指标
        try:
            response = requests.get(
                f"http://{self.qte_host}:{self.qte_admin_port}/metrics",
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"无法获取指标: {response.status_code}")
            
            # 解析Prometheus指标
            metrics_text = response.text
            
            # 提取关键指标
            event_rate = self._extract_metric(metrics_text, 'qte_event_processing_rate')
            queue_size = self._extract_metric(metrics_text, 'qte_event_queue_size')
            memory_usage = self._extract_metric(metrics_text, 'qte_memory_usage_bytes')
            
            duration = time.time() - start_time
            
            benchmark = PerformanceBenchmark(
                test_name=test_name,
                timestamp=datetime.now().isoformat(),
                duration_seconds=duration,
                throughput_ops_per_sec=event_rate or 0,
                memory_usage_mb=(memory_usage or 0) / 1024 / 1024,
                cpu_usage_percent=psutil.cpu_percent(),
                success_rate=1.0 if event_rate else 0.0,
                error_count=0,
                p50_latency_ms=0,  # 事件处理延迟需要专门测量
                p95_latency_ms=0,
                p99_latency_ms=0
            )
            
            self.logger.info(f"事件处理性能测试完成: 处理速率={event_rate:.1f}events/s, "
                           f"队列大小={queue_size}")
            
        except Exception as e:
            self.logger.error(f"事件处理性能测试失败: {e}")
            
            benchmark = PerformanceBenchmark(
                test_name=test_name,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                throughput_ops_per_sec=0,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                success_rate=0,
                error_count=1,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0
            )
        
        return benchmark
    
    def test_database_performance(self) -> PerformanceBenchmark:
        """测试数据库性能"""
        test_name = "database_performance"
        start_time = time.time()
        
        try:
            # 执行数据库性能测试
            result = subprocess.run([
                'python', '-c', '''
import psycopg2
import time
import statistics

# 连接数据库
conn = psycopg2.connect(
    host="postgres",
    port=5432,
    database="qte",
    user="qte",
    password="password"
)

cursor = conn.cursor()
latencies = []

# 执行查询测试
for i in range(50):
    start = time.time()
    cursor.execute("SELECT COUNT(*) FROM trades WHERE created_at >= CURRENT_DATE")
    cursor.fetchone()
    latencies.append((time.time() - start) * 1000)

cursor.close()
conn.close()

print(f"avg_latency:{statistics.mean(latencies):.2f}")
print(f"p95_latency:{statistics.quantiles(latencies, n=20)[18]:.2f}")
print(f"success_rate:1.0")
                '''
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # 解析结果
                output_lines = result.stdout.strip().split('\n')
                metrics = {}
                for line in output_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metrics[key] = float(value)
                
                duration = time.time() - start_time
                
                benchmark = PerformanceBenchmark(
                    test_name=test_name,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=duration,
                    throughput_ops_per_sec=50 / duration,  # 50个查询
                    memory_usage_mb=0,  # 数据库内存使用由数据库监控
                    cpu_usage_percent=0,
                    success_rate=metrics.get('success_rate', 0),
                    error_count=0,
                    p50_latency_ms=metrics.get('avg_latency', 0),
                    p95_latency_ms=metrics.get('p95_latency', 0),
                    p99_latency_ms=0
                )
                
                self.logger.info(f"数据库性能测试完成: 平均延迟={metrics.get('avg_latency', 0):.1f}ms")
                
            else:
                raise Exception(f"数据库测试失败: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"数据库性能测试失败: {e}")
            
            benchmark = PerformanceBenchmark(
                test_name=test_name,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                throughput_ops_per_sec=0,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                success_rate=0,
                error_count=1,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0
            )
        
        return benchmark
    
    def _extract_metric(self, metrics_text: str, metric_name: str) -> Optional[float]:
        """从Prometheus指标文本中提取指标值"""
        for line in metrics_text.split('\n'):
            if line.startswith(metric_name) and not line.startswith('#'):
                try:
                    value = float(line.split()[-1])
                    return value
                except (ValueError, IndexError):
                    continue
        return None
    
    def run_performance_tests(self) -> List[PerformanceBenchmark]:
        """运行所有性能测试"""
        self.logger.info("开始执行性能测试套件")
        
        tests = [
            self.test_api_performance,
            self.test_event_processing_performance,
            self.test_database_performance
        ]
        
        results = []
        
        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
                self.performance_history.append(result)
            except Exception as e:
                self.logger.error(f"性能测试失败 {test_func.__name__}: {e}")
        
        # 保留最近100次测试结果
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        self.logger.info(f"性能测试完成，共执行 {len(results)} 个测试")
        
        return results
    
    def detect_performance_regression(self, current_results: List[PerformanceBenchmark]) -> List[Dict[str, Any]]:
        """检测性能回归"""
        regressions = []
        
        if not self.baseline_metrics:
            self.logger.warning("未设置性能基准，无法检测回归")
            return regressions
        
        for result in current_results:
            test_name = result.test_name
            baseline_key = f"{test_name}_throughput"
            
            if baseline_key in self.baseline_metrics:
                baseline_throughput = self.baseline_metrics[baseline_key]
                current_throughput = result.throughput_ops_per_sec
                
                if baseline_throughput > 0:
                    regression_ratio = (baseline_throughput - current_throughput) / baseline_throughput
                    
                    if regression_ratio > self.regression_threshold:
                        regression = {
                            'test_name': test_name,
                            'metric': 'throughput',
                            'baseline_value': baseline_throughput,
                            'current_value': current_throughput,
                            'regression_percent': regression_ratio * 100,
                            'threshold_percent': self.regression_threshold * 100,
                            'timestamp': result.timestamp
                        }
                        regressions.append(regression)
                        
                        self.logger.warning(f"检测到性能回归: {test_name} 吞吐量下降 {regression_ratio:.1%}")
        
        return regressions
    
    def send_regression_alert(self, regressions: List[Dict[str, Any]]):
        """发送性能回归告警"""
        if not regressions or not self.webhook_url:
            return
        
        alert_data = {
            'alert_type': 'performance_regression',
            'timestamp': datetime.now().isoformat(),
            'regressions': regressions,
            'severity': 'warning'
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"已发送性能回归告警，回归数量: {len(regressions)}")
            else:
                self.logger.error(f"发送告警失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"发送告警异常: {e}")
    
    def update_baseline(self, results: List[PerformanceBenchmark]):
        """更新性能基准"""
        if not results:
            return
        
        new_baseline = {}
        
        for result in results:
            if result.success_rate > 0.9:  # 只有成功率>90%的测试才更新基准
                test_name = result.test_name
                new_baseline[f"{test_name}_throughput"] = result.throughput_ops_per_sec
                new_baseline[f"{test_name}_p95_latency"] = result.p95_latency_ms
                new_baseline[f"{test_name}_memory_usage"] = result.memory_usage_mb
        
        if new_baseline:
            self.baseline_metrics = new_baseline
            self._save_baseline(new_baseline)
            self.logger.info("已更新性能基准")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 执行性能测试
                results = self.run_performance_tests()
                
                # 检测性能回归
                regressions = self.detect_performance_regression(results)
                
                if regressions:
                    self.send_regression_alert(regressions)
                
                # 如果没有基准或者测试结果良好，更新基准
                if not self.baseline_metrics or all(r.success_rate > 0.95 for r in results):
                    self.update_baseline(results)
                
                # 等待下次测试
                time.sleep(self.test_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(60)  # 错误时等待1分钟
    
    def start(self):
        """启动性能监控"""
        if self.running:
            self.logger.warning("性能监控已在运行")
            return
        
        self.logger.info("启动性能监控")
        self.running = True
        
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info("性能监控启动完成")
    
    def stop(self):
        """停止性能监控"""
        if not self.running:
            return
        
        self.logger.info("停止性能监控")
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("性能监控已停止")


def main():
    """主函数"""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description='QTE性能监控')
    parser.add_argument('--config', default='/app/config/production.yaml', help='配置文件路径')
    parser.add_argument('--test-only', action='store_true', help='仅执行一次测试')
    parser.add_argument('--update-baseline', action='store_true', help='更新性能基准')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"加载配置失败: {e}")
        return
    
    # 创建性能监控器
    monitor_config = config.get('performance_monitoring', {})
    monitor = PerformanceMonitor(monitor_config)
    
    if args.test_only:
        # 仅执行一次测试
        results = monitor.run_performance_tests()
        
        if args.update_baseline:
            monitor.update_baseline(results)
        
        # 输出结果
        for result in results:
            print(json.dumps(asdict(result), indent=2))
    else:
        # 启动持续监控
        try:
            monitor.start()
            
            # 保持运行
            while True:
                time.sleep(60)
                
        except KeyboardInterrupt:
            logging.info("收到停止信号")
        finally:
            monitor.stop()


if __name__ == "__main__":
    main()
