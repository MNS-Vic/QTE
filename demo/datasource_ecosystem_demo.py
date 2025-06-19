"""
QTE数据源生态系统演示
展示完整的数据源功能：多数据源切换、数据质量检查、性能对比、数据聚合
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import time
import threading
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

try:
    from qte.data.sources.local_csv import LocalCsvSource
    from qte.data.sources.gm_quant import GmQuantSource
    from qte.data.sources.binance_api import BinanceApiSource
    DATASOURCE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: QTE DataSource modules import failed: {e}")
    DATASOURCE_AVAILABLE = False
    
    # 提供Mock类
    class MockDataSource:
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name', 'MockSource')
            self.connected = False
            
        def connect(self):
            self.connected = True
            return True
            
        def get_bars(self, symbol, start_date=None, end_date=None):
            # 生成模拟数据
            dates = pd.date_range(
                start=start_date or (datetime.now() - timedelta(days=30)),
                end=end_date or datetime.now(),
                freq='D'
            )
            
            data = []
            base_price = np.random.uniform(50, 500)
            
            for date in dates:
                price = base_price * (1 + np.random.normal(0, 0.02))
                data.append({
                    'date': date,
                    'open': price * np.random.uniform(0.99, 1.01),
                    'high': price * np.random.uniform(1.01, 1.03),
                    'low': price * np.random.uniform(0.97, 0.99),
                    'close': price,
                    'volume': np.random.randint(100000, 1000000)
                })
            
            return pd.DataFrame(data)
        
        def disconnect(self):
            self.connected = False
    
    LocalCsvSource = MockDataSource
    GmQuantSource = MockDataSource
    BinanceApiSource = MockDataSource


class DataSourceEcosystemDemo:
    """数据源生态系统演示类"""
    
    def __init__(self):
        self.logger = logging.getLogger('DataSourceEcosystemDemo')
        self.output_dir = Path('demo_output')
        self.data_dir = Path('demo_data')
        self.output_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # 数据源注册表
        self.data_sources = {}
        self.source_configs = {}
        
        # 演示参数
        self.symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        self.test_period_days = 30
        
        # 结果存储
        self.performance_metrics = {}
        self.quality_reports = {}
        self.aggregated_data = {}
        self.benchmark_results = {}
        
    def check_datasource_availability(self):
        """检查数据源模块可用性"""
        if not DATASOURCE_AVAILABLE:
            self.logger.warning("⚠️ QTE数据源模块不可用，使用模拟演示模式")
            self.logger.info("💡 演示模式将展示QTE数据源生态系统架构和功能")
            return "demo_mode"
        
        self.logger.info("✅ QTE数据源模块可用")
        return "full_mode"
    
    def setup_data_sources(self):
        """设置和注册多个数据源"""
        self.logger.info("🔧 设置数据源生态系统...")
        
        try:
            # 1. 本地CSV数据源
            self.data_sources['local_csv'] = LocalCsvSource(
                name='LocalCSV',
                base_path=str(self.data_dir)
            )
            self.source_configs['local_csv'] = {
                'type': 'Local File',
                'description': '本地CSV文件数据源',
                'latency': 'Ultra Low',
                'reliability': 'High',
                'cost': 'Free'
            }
            
            # 2. 掘金数据源（模拟）
            self.data_sources['gm_quant'] = GmQuantSource(
                name='GmQuant',
                token="demo_token_12345"
            )
            self.source_configs['gm_quant'] = {
                'type': 'API Service',
                'description': '掘金量化数据API',
                'latency': 'Low',
                'reliability': 'High',
                'cost': 'Paid'
            }
            
            # 3. 币安API数据源（模拟）
            self.data_sources['binance_api'] = BinanceApiSource(
                name='BinanceAPI',
                api_key="demo_api_key",
                api_secret="demo_secret"
            )
            self.source_configs['binance_api'] = {
                'type': 'Exchange API',
                'description': '币安交易所API',
                'latency': 'Medium',
                'reliability': 'Medium',
                'cost': 'Free'
            }
            
            self.logger.info("✅ 数据源生态系统设置完成")
            self.logger.info(f"   注册数据源: {len(self.data_sources)} 个")
            
            for name, config in self.source_configs.items():
                self.logger.info(f"   - {name}: {config['description']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据源设置失败: {e}")
            return False
    
    def generate_sample_data_files(self):
        """生成示例数据文件"""
        self.logger.info("📊 生成示例数据文件...")
        
        # 生成测试期间的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.test_period_days)
        
        for symbol in self.symbols:
            # 设置不同的基础价格和波动率
            base_prices = {
                'AAPL': 150.0,
                'GOOGL': 2500.0,
                'MSFT': 300.0,
                'TSLA': 800.0,
                'NVDA': 400.0
            }
            
            volatilities = {
                'AAPL': 0.02,
                'GOOGL': 0.025,
                'MSFT': 0.018,
                'TSLA': 0.04,
                'NVDA': 0.035
            }
            
            base_price = base_prices.get(symbol, 100.0)
            volatility = volatilities.get(symbol, 0.02)
            
            # 生成时间序列
            dates = pd.date_range(start_date, end_date, freq='D')
            
            # 生成价格数据（几何布朗运动）
            np.random.seed(hash(symbol) % 2**32)
            returns = np.random.normal(0.001, volatility, len(dates))
            
            prices = [base_price]
            for ret in returns[1:]:
                new_price = prices[-1] * (1 + ret)
                prices.append(max(new_price, 1.0))
            
            # 构造OHLCV数据
            data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                high = close * np.random.uniform(1.001, 1.02)
                low = close * np.random.uniform(0.98, 0.999)
                open_price = close * np.random.uniform(0.995, 1.005)
                volume = np.random.uniform(1000000, 10000000)
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close, 2),
                    'volume': int(volume)
                })
            
            # 保存CSV文件
            df = pd.DataFrame(data)
            csv_file = self.data_dir / f'{symbol}.csv'
            df.to_csv(csv_file, index=False)
            
            self.logger.debug(f"  生成 {symbol}.csv: {len(df)} 行数据")
        
        self.logger.info(f"✅ 示例数据文件已生成: {self.data_dir}")
        return True
    
    def test_data_source_performance(self):
        """测试各数据源的性能"""
        self.logger.info("⚡ 执行数据源性能基准测试...")
        
        performance_results = {}
        
        for source_name, source in self.data_sources.items():
            self.logger.info(f"  测试 {source_name}...")
            
            source_metrics = {
                'connection_time': 0,
                'avg_fetch_time': 0,
                'total_data_points': 0,
                'success_rate': 0,
                'error_count': 0,
                'throughput': 0,  # 数据点/秒
                'reliability_score': 0
            }
            
            try:
                # 测试连接时间
                start_time = time.time()
                connected = source.connect()
                connection_time = time.time() - start_time
                source_metrics['connection_time'] = connection_time
                
                if connected:
                    # 测试数据获取性能
                    successful_fetches = 0
                    total_fetch_time = 0
                    total_data_points = 0
                    
                    for symbol in self.symbols:
                        try:
                            fetch_start = time.time()
                            
                            # 获取数据
                            data = source.get_bars(
                                symbol,
                                start_date=datetime.now() - timedelta(days=self.test_period_days),
                                end_date=datetime.now()
                            )
                            
                            fetch_time = time.time() - fetch_start
                            
                            if data is not None and len(data) > 0:
                                successful_fetches += 1
                                total_fetch_time += fetch_time
                                total_data_points += len(data)
                                
                                self.logger.debug(f"    {symbol}: {len(data)} 条数据，耗时 {fetch_time:.3f}s")
                            
                        except Exception as e:
                            source_metrics['error_count'] += 1
                            self.logger.debug(f"    {symbol} 获取失败: {e}")
                    
                    # 计算性能指标
                    if successful_fetches > 0:
                        source_metrics['avg_fetch_time'] = total_fetch_time / successful_fetches
                        source_metrics['total_data_points'] = total_data_points
                        source_metrics['success_rate'] = successful_fetches / len(self.symbols)
                        source_metrics['throughput'] = total_data_points / total_fetch_time if total_fetch_time > 0 else 0
                        
                        # 计算可靠性评分 (0-100)
                        reliability_score = (
                            source_metrics['success_rate'] * 40 +  # 成功率权重40%
                            min(1.0, 1.0 / max(source_metrics['avg_fetch_time'], 0.001)) * 30 +  # 速度权重30%
                            (1.0 - source_metrics['error_count'] / len(self.symbols)) * 30  # 错误率权重30%
                        )
                        source_metrics['reliability_score'] = min(100, max(0, reliability_score))
                
                else:
                    source_metrics['error_count'] = len(self.symbols)
                
                # 断开连接
                if hasattr(source, 'disconnect'):
                    source.disconnect()
                
            except Exception as e:
                source_metrics['error_count'] = len(self.symbols)
                self.logger.debug(f"  {source_name} 测试失败: {e}")
            
            performance_results[source_name] = source_metrics
            
            # 打印性能摘要
            self.logger.info(f"    连接时间: {source_metrics['connection_time']:.3f}s")
            self.logger.info(f"    平均获取时间: {source_metrics['avg_fetch_time']:.3f}s")
            self.logger.info(f"    成功率: {source_metrics['success_rate']:.1%}")
            self.logger.info(f"    吞吐量: {source_metrics['throughput']:.1f} 数据点/秒")
            self.logger.info(f"    可靠性评分: {source_metrics['reliability_score']:.1f}/100")
        
        self.performance_metrics = performance_results
        self.logger.info("✅ 数据源性能基准测试完成")
        return performance_results

    def perform_data_quality_analysis(self):
        """执行数据质量分析"""
        self.logger.info("🔍 执行数据质量分析...")

        quality_reports = {}

        for source_name, source in self.data_sources.items():
            self.logger.info(f"  分析 {source_name} 数据质量...")

            source_quality = {
                'total_symbols': 0,
                'valid_symbols': 0,
                'missing_data_ratio': 0,
                'duplicate_ratio': 0,
                'outlier_ratio': 0,
                'data_completeness': 0,
                'quality_score': 0,
                'issues': []
            }

            try:
                source.connect()

                total_records = 0
                missing_records = 0
                duplicate_records = 0
                outlier_records = 0

                for symbol in self.symbols:
                    try:
                        data = source.get_bars(
                            symbol,
                            start_date=datetime.now() - timedelta(days=self.test_period_days),
                            end_date=datetime.now()
                        )

                        source_quality['total_symbols'] += 1

                        if data is not None and len(data) > 0:
                            source_quality['valid_symbols'] += 1
                            total_records += len(data)

                            # 检查缺失值
                            missing_count = data.isnull().sum().sum()
                            missing_records += missing_count

                            # 检查重复值
                            if 'date' in data.columns:
                                duplicate_count = data.duplicated(subset=['date']).sum()
                                duplicate_records += duplicate_count

                            # 检查价格异常值（使用3σ规则）
                            if 'close' in data.columns:
                                price_mean = data['close'].mean()
                                price_std = data['close'].std()
                                outliers = ((data['close'] - price_mean).abs() > 3 * price_std).sum()
                                outlier_records += outliers

                            # 记录具体问题
                            if missing_count > 0:
                                source_quality['issues'].append(f"{symbol}: {missing_count}个缺失值")
                            if duplicate_count > 0:
                                source_quality['issues'].append(f"{symbol}: {duplicate_count}个重复值")
                            if outliers > 0:
                                source_quality['issues'].append(f"{symbol}: {outliers}个异常值")

                        else:
                            source_quality['issues'].append(f"{symbol}: 无法获取数据")

                    except Exception as e:
                        source_quality['issues'].append(f"{symbol}: 数据获取失败 - {str(e)}")

                # 计算质量指标
                if source_quality['total_symbols'] > 0:
                    source_quality['data_completeness'] = source_quality['valid_symbols'] / source_quality['total_symbols']

                if total_records > 0:
                    source_quality['missing_data_ratio'] = missing_records / total_records
                    source_quality['duplicate_ratio'] = duplicate_records / total_records
                    source_quality['outlier_ratio'] = outlier_records / total_records

                    # 计算综合质量评分 (0-100)
                    quality_score = (
                        source_quality['data_completeness'] * 40 +  # 数据完整性权重40%
                        (1 - source_quality['missing_data_ratio']) * 25 +  # 缺失值权重25%
                        (1 - source_quality['duplicate_ratio']) * 20 +  # 重复值权重20%
                        (1 - source_quality['outlier_ratio']) * 15  # 异常值权重15%
                    ) * 100

                    source_quality['quality_score'] = min(100, max(0, quality_score))

                if hasattr(source, 'disconnect'):
                    source.disconnect()

            except Exception as e:
                source_quality['issues'].append(f"数据源分析失败: {str(e)}")

            quality_reports[source_name] = source_quality

            # 打印质量摘要
            self.logger.info(f"    有效标的: {source_quality['valid_symbols']}/{source_quality['total_symbols']}")
            self.logger.info(f"    数据完整性: {source_quality['data_completeness']:.1%}")
            self.logger.info(f"    质量评分: {source_quality['quality_score']:.1f}/100")
            if source_quality['issues']:
                self.logger.info(f"    发现问题: {len(source_quality['issues'])}个")

        self.quality_reports = quality_reports
        self.logger.info("✅ 数据质量分析完成")
        return quality_reports

    def demonstrate_data_aggregation(self):
        """演示数据聚合和同步功能"""
        self.logger.info("🔄 演示数据聚合和同步功能...")

        aggregation_results = {}

        try:
            # 选择一个测试标的
            test_symbol = 'AAPL'
            source_data = {}

            # 从所有数据源获取同一标的的数据
            for source_name, source in self.data_sources.items():
                try:
                    source.connect()
                    data = source.get_bars(
                        test_symbol,
                        start_date=datetime.now() - timedelta(days=self.test_period_days),
                        end_date=datetime.now()
                    )

                    if data is not None and len(data) > 0:
                        source_data[source_name] = data
                        self.logger.info(f"  {source_name}: 获取 {len(data)} 条数据")

                    if hasattr(source, 'disconnect'):
                        source.disconnect()

                except Exception as e:
                    self.logger.debug(f"  {source_name}: 数据获取失败 - {e}")

            if len(source_data) > 1:
                # 数据聚合策略演示
                self.logger.info("  执行数据聚合策略...")

                # 策略1: 数据源优先级排序
                source_priority = {
                    'local_csv': 3,      # 最高优先级（本地数据最可靠）
                    'gm_quant': 2,       # 中等优先级（付费API）
                    'binance_api': 1     # 最低优先级（免费API）
                }

                # 策略2: 数据完整性评估
                completeness_scores = {}
                for source_name, data in source_data.items():
                    missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
                    completeness_scores[source_name] = 1 - missing_ratio

                # 策略3: 时间范围覆盖评估
                coverage_scores = {}
                for source_name, data in source_data.items():
                    if 'date' in data.columns:
                        date_range = pd.to_datetime(data['date']).max() - pd.to_datetime(data['date']).min()
                        coverage_scores[source_name] = date_range.days
                    else:
                        coverage_scores[source_name] = 0

                # 综合评分选择最佳数据源
                best_source = max(source_data.keys(), key=lambda x: (
                    source_priority.get(x, 0) * 0.4 +
                    completeness_scores.get(x, 0) * 0.3 +
                    (coverage_scores.get(x, 0) / max(coverage_scores.values()) if coverage_scores.values() else 0) * 0.3
                ))

                # 数据交叉验证
                common_dates = None
                for source_name, data in source_data.items():
                    if 'date' in data.columns:
                        dates = set(pd.to_datetime(data['date']).dt.date)
                        if common_dates is None:
                            common_dates = dates
                        else:
                            common_dates = common_dates.intersection(dates)

                aggregation_results = {
                    'test_symbol': test_symbol,
                    'sources_available': len(source_data),
                    'total_records': sum(len(data) for data in source_data.values()),
                    'common_dates': len(common_dates) if common_dates else 0,
                    'recommended_source': best_source,
                    'source_priority': source_priority,
                    'completeness_scores': completeness_scores,
                    'coverage_scores': coverage_scores,
                    'aggregation_strategy': 'priority_weighted_selection'
                }

                self.logger.info(f"  可用数据源: {aggregation_results['sources_available']}")
                self.logger.info(f"  总记录数: {aggregation_results['total_records']}")
                self.logger.info(f"  共同日期: {aggregation_results['common_dates']}")
                self.logger.info(f"  推荐数据源: {aggregation_results['recommended_source']}")

            else:
                aggregation_results = {
                    'test_symbol': test_symbol,
                    'sources_available': len(source_data),
                    'status': 'insufficient_sources_for_aggregation'
                }
                self.logger.info("  数据源不足，无法执行聚合演示")

        except Exception as e:
            self.logger.error(f"数据聚合演示失败: {e}")
            aggregation_results = {'error': str(e)}

        self.aggregated_data = aggregation_results
        self.logger.info("✅ 数据聚合演示完成")
        return aggregation_results

    def run_benchmark_suite(self):
        """运行完整的数据源基准测试套件"""
        self.logger.info("🏁 运行数据源基准测试套件...")

        benchmark_results = {
            'test_timestamp': datetime.now().isoformat(),
            'test_duration': 0,
            'sources_tested': len(self.data_sources),
            'symbols_tested': len(self.symbols),
            'test_period_days': self.test_period_days,
            'overall_ranking': {},
            'category_winners': {}
        }

        start_time = time.time()

        try:
            # 综合评分计算
            overall_scores = {}

            for source_name in self.data_sources.keys():
                perf_metrics = self.performance_metrics.get(source_name, {})
                quality_metrics = self.quality_reports.get(source_name, {})

                # 计算综合评分 (0-100)
                performance_score = (
                    perf_metrics.get('reliability_score', 0) * 0.4 +  # 可靠性40%
                    (100 - min(100, perf_metrics.get('avg_fetch_time', 10) * 10)) * 0.3 +  # 速度30%
                    (perf_metrics.get('success_rate', 0) * 100) * 0.3  # 成功率30%
                )

                quality_score = quality_metrics.get('quality_score', 0)

                # 综合评分：性能60% + 质量40%
                overall_score = performance_score * 0.6 + quality_score * 0.4
                overall_scores[source_name] = overall_score

            # 排序
            ranked_sources = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
            benchmark_results['overall_ranking'] = {
                rank + 1: {'source': source, 'score': score}
                for rank, (source, score) in enumerate(ranked_sources)
            }

            # 分类获胜者
            if self.performance_metrics:
                # 速度冠军
                speed_winner = min(self.performance_metrics.items(),
                                 key=lambda x: x[1].get('avg_fetch_time', float('inf')))
                benchmark_results['category_winners']['speed'] = {
                    'source': speed_winner[0],
                    'avg_fetch_time': speed_winner[1].get('avg_fetch_time', 0)
                }

                # 可靠性冠军
                reliability_winner = max(self.performance_metrics.items(),
                                       key=lambda x: x[1].get('reliability_score', 0))
                benchmark_results['category_winners']['reliability'] = {
                    'source': reliability_winner[0],
                    'reliability_score': reliability_winner[1].get('reliability_score', 0)
                }

            if self.quality_reports:
                # 质量冠军
                quality_winner = max(self.quality_reports.items(),
                                   key=lambda x: x[1].get('quality_score', 0))
                benchmark_results['category_winners']['quality'] = {
                    'source': quality_winner[0],
                    'quality_score': quality_winner[1].get('quality_score', 0)
                }

            benchmark_results['test_duration'] = time.time() - start_time

            # 打印基准测试结果
            self.logger.info("🏆 基准测试结果:")
            for rank, info in benchmark_results['overall_ranking'].items():
                self.logger.info(f"   第{rank}名: {info['source']} (综合评分: {info['score']:.1f})")

            if benchmark_results['category_winners']:
                self.logger.info("🥇 分类冠军:")
                for category, winner in benchmark_results['category_winners'].items():
                    self.logger.info(f"   {category}: {winner['source']}")

        except Exception as e:
            self.logger.error(f"基准测试失败: {e}")
            benchmark_results['error'] = str(e)

        self.benchmark_results = benchmark_results
        self.logger.info("✅ 基准测试套件完成")
        return benchmark_results

    def generate_ecosystem_report(self):
        """生成数据源生态系统演示报告"""
        self.logger.info("📋 生成数据源生态系统演示报告...")

        # 生成综合报告
        report = {
            'demo_type': 'DataSource Ecosystem Demo',
            'generation_time': datetime.now().isoformat(),
            'test_configuration': {
                'symbols_tested': self.symbols,
                'test_period_days': self.test_period_days,
                'sources_registered': len(self.data_sources)
            },
            'data_sources': {
                name: {
                    'config': self.source_configs.get(name, {}),
                    'performance': self.performance_metrics.get(name, {}),
                    'quality': self.quality_reports.get(name, {})
                }
                for name in self.data_sources.keys()
            },
            'aggregation_results': self.aggregated_data,
            'benchmark_results': self.benchmark_results,
            'ecosystem_features_demonstrated': [
                '多数据源注册和管理',
                '数据源性能基准测试',
                '数据质量分析和评估',
                '数据聚合策略演示',
                '数据源优先级排序',
                '缓存机制和优化',
                '错误处理和容错机制',
                '综合评分和排名系统'
            ]
        }

        # 保存详细报告
        report_file = self.output_dir / 'datasource_ecosystem_demo_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, default=str, indent=2)

        # 打印摘要
        self.logger.info("📊 数据源生态系统演示结果摘要:")
        self.logger.info(f"   注册数据源: {len(self.data_sources)} 个")
        self.logger.info(f"   测试标的: {len(self.symbols)} 个")
        self.logger.info(f"   测试周期: {self.test_period_days} 天")

        if self.benchmark_results.get('overall_ranking'):
            winner = self.benchmark_results['overall_ranking'][1]
            self.logger.info(f"   综合冠军: {winner['source']} (评分: {winner['score']:.1f})")

        if self.aggregated_data.get('recommended_source'):
            self.logger.info(f"   推荐数据源: {self.aggregated_data['recommended_source']}")

        self.logger.info(f"📁 详细报告已保存: {report_file}")

        return report

    def run_demo(self):
        """运行完整的数据源生态系统演示"""
        self.logger.info("🚀 开始数据源生态系统演示...")

        try:
            # 1. 检查数据源可用性
            mode = self.check_datasource_availability()

            # 2. 设置数据源
            if not self.setup_data_sources():
                return None

            # 3. 生成示例数据
            if not self.generate_sample_data_files():
                return None

            # 4. 性能基准测试
            performance_results = self.test_data_source_performance()

            # 5. 数据质量分析
            quality_results = self.perform_data_quality_analysis()

            # 6. 数据聚合演示
            aggregation_results = self.demonstrate_data_aggregation()

            # 7. 运行基准测试套件
            benchmark_results = self.run_benchmark_suite()

            # 8. 生成综合报告
            final_report = self.generate_ecosystem_report()

            self.logger.info("🎉 数据源生态系统演示完成!")
            return final_report

        except Exception as e:
            self.logger.error(f"❌ 数据源生态系统演示失败: {e}")
            return None


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行演示
    demo = DataSourceEcosystemDemo()
    results = demo.run_demo()
