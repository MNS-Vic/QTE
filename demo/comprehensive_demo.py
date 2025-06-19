"""
QTE综合演示模式
依次运行所有演示模式，生成统一的综合报告
"""

import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback


class ComprehensiveDemo:
    """QTE综合演示类"""
    
    def __init__(self):
        self.logger = logging.getLogger('ComprehensiveDemo')
        self.output_dir = Path('demo_output')
        self.reports_dir = Path('demo_reports')
        self.output_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # 演示模式配置
        self.demo_modes = [
            {
                'name': 'simple',
                'display_name': '简单演示',
                'description': '基础量化交易演示',
                'module': 'run_qte_demo',
                'function': 'run_simple_demo',
                'estimated_time': 5
            },
            {
                'name': 'advanced',
                'display_name': '高级演示',
                'description': '高级事件驱动演示',
                'module': 'run_qte_demo',
                'function': 'run_advanced_demo',
                'estimated_time': 10
            },
            {
                'name': 'exchange',
                'display_name': '虚拟交易所',
                'description': '虚拟交易所完整功能演示',
                'module': 'demo.virtual_exchange_demo',
                'class': 'VirtualExchangeDemo',
                'estimated_time': 15
            },
            {
                'name': 'ml',
                'display_name': '机器学习',
                'description': '机器学习交易策略演示',
                'module': 'demo.ml_trading_demo',
                'class': 'MLTradingDemo',
                'estimated_time': 20
            },
            {
                'name': 'vnpy',
                'display_name': 'vnpy集成',
                'description': 'vnpy集成架构演示',
                'module': 'demo.vnpy_integration_demo',
                'class': 'VnpyIntegrationDemo',
                'estimated_time': 8
            },
            {
                'name': 'datasource',
                'display_name': '数据源生态系统',
                'description': '数据源生态系统演示',
                'module': 'demo.datasource_ecosystem_demo',
                'class': 'DataSourceEcosystemDemo',
                'estimated_time': 12
            },
            {
                'name': 'report',
                'display_name': '可视化报告',
                'description': '可视化报告演示',
                'module': 'demo.visualization_report_demo',
                'class': 'VisualizationReportDemo',
                'estimated_time': 6
            }
        ]
        
        # 结果存储
        self.demo_results = {}
        self.execution_stats = {}
        self.comprehensive_report = {}
        
    def display_welcome_banner(self):
        """显示欢迎横幅"""
        total_estimated_time = sum(demo['estimated_time'] for demo in self.demo_modes)
        
        self.logger.info("=" * 80)
        self.logger.info("🚀 QTE量化交易引擎 - 综合演示模式")
        self.logger.info("=" * 80)
        self.logger.info(f"📋 将依次运行 {len(self.demo_modes)} 个演示模式")
        self.logger.info(f"⏱️ 预计总耗时: {total_estimated_time} 秒")
        self.logger.info(f"📊 演示功能: 数据源 → 策略执行 → 交易所 → 分析报告")
        self.logger.info("=" * 80)
        
        # 显示演示列表
        for i, demo in enumerate(self.demo_modes, 1):
            self.logger.info(f"  {i}. {demo['display_name']} - {demo['description']}")
        
        self.logger.info("=" * 80)
    
    def run_single_demo(self, demo_config: Dict, demo_index: int) -> Dict:
        """运行单个演示模式"""
        demo_name = demo_config['name']
        display_name = demo_config['display_name']
        total_demos = len(self.demo_modes)
        
        self.logger.info(f"🎬 [{demo_index}/{total_demos}] 开始运行: {display_name}")
        self.logger.info(f"📝 描述: {demo_config['description']}")
        
        start_time = time.time()
        demo_result = {
            'name': demo_name,
            'display_name': display_name,
            'description': demo_config['description'],
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'duration': 0,
            'error': None,
            'result_data': None
        }
        
        try:
            # 检查是否是函数调用还是类调用
            if 'function' in demo_config:
                # 函数调用方式
                module_name = demo_config['module']
                function_name = demo_config['function']

                self.logger.info(f"📦 导入模块: {module_name}.{function_name}")

                # 导入模块
                module = __import__(module_name, fromlist=[function_name])
                demo_function = getattr(module, function_name)

                # 运行演示函数
                self.logger.info(f"▶️ 执行演示...")
                if demo_name == 'advanced':
                    # 高级演示需要配置文件参数
                    result = demo_function(config_file=None)
                else:
                    result = demo_function()
            else:
                # 类调用方式
                module_name = demo_config['module']
                class_name = demo_config['class']

                self.logger.info(f"📦 导入模块: {module_name}.{class_name}")

                # 导入模块
                module = __import__(module_name, fromlist=[class_name])
                demo_class = getattr(module, class_name)

                # 创建演示实例
                if demo_name == 'advanced':
                    # 高级演示需要配置文件参数
                    demo_instance = demo_class(config_file=None)
                else:
                    demo_instance = demo_class()

                # 运行演示
                self.logger.info(f"▶️ 执行演示...")
                result = demo_instance.run_demo()
            
            # 记录成功结果
            demo_result['status'] = 'success'
            demo_result['result_data'] = result
            
            duration = time.time() - start_time
            demo_result['duration'] = duration
            
            self.logger.info(f"✅ [{demo_index}/{total_demos}] {display_name} 完成 (耗时: {duration:.2f}s)")
            
        except Exception as e:
            # 记录错误但继续执行其他演示
            duration = time.time() - start_time
            demo_result['status'] = 'failed'
            demo_result['duration'] = duration
            demo_result['error'] = str(e)
            demo_result['traceback'] = traceback.format_exc()
            
            self.logger.error(f"❌ [{demo_index}/{total_demos}] {display_name} 失败 (耗时: {duration:.2f}s)")
            self.logger.error(f"错误信息: {str(e)}")
            self.logger.debug(f"详细错误: {traceback.format_exc()}")
        
        demo_result['end_time'] = datetime.now().isoformat()
        return demo_result
    
    def calculate_execution_statistics(self):
        """计算执行统计信息"""
        total_demos = len(self.demo_results)
        successful_demos = sum(1 for result in self.demo_results.values() if result['status'] == 'success')
        failed_demos = total_demos - successful_demos
        
        total_duration = sum(result['duration'] for result in self.demo_results.values())
        avg_duration = total_duration / total_demos if total_demos > 0 else 0
        
        # 按状态分组
        success_list = [name for name, result in self.demo_results.items() if result['status'] == 'success']
        failed_list = [name for name, result in self.demo_results.items() if result['status'] == 'failed']
        
        self.execution_stats = {
            'total_demos': total_demos,
            'successful_demos': successful_demos,
            'failed_demos': failed_demos,
            'success_rate': successful_demos / total_demos if total_demos > 0 else 0,
            'total_duration': total_duration,
            'average_duration': avg_duration,
            'success_list': success_list,
            'failed_list': failed_list
        }
        
        return self.execution_stats
    
    def aggregate_demo_results(self):
        """聚合所有演示结果"""
        aggregated_data = {
            'trading_statistics': {
                'total_trades': 0,
                'total_pnl': 0,
                'total_symbols': 0,
                'total_strategies': 0
            },
            'technical_capabilities': {
                'ml_models_trained': 0,
                'data_sources_tested': 0,
                'vnpy_events_processed': 0,
                'charts_generated': 0
            },
            'performance_metrics': {
                'best_return': 0,
                'total_market_data_points': 0,
                'total_features_generated': 0
            }
        }
        
        # 从各个演示结果中提取关键指标
        for demo_name, demo_result in self.demo_results.items():
            if demo_result['status'] != 'success' or not demo_result['result_data']:
                continue
            
            result_data = demo_result['result_data']
            
            try:
                # 简单演示和高级演示的交易统计
                if demo_name in ['simple', 'advanced']:
                    if 'total_trades' in result_data:
                        aggregated_data['trading_statistics']['total_trades'] += result_data['total_trades']
                    if 'total_pnl' in result_data:
                        aggregated_data['trading_statistics']['total_pnl'] += result_data['total_pnl']
                
                # 机器学习演示
                elif demo_name == 'ml':
                    if 'models_trained' in result_data:
                        aggregated_data['technical_capabilities']['ml_models_trained'] = result_data['models_trained']
                    if 'features_generated' in result_data:
                        aggregated_data['performance_metrics']['total_features_generated'] = result_data['features_generated']
                    if 'backtest_results' in result_data:
                        backtest = result_data['backtest_results']
                        if 'total_return' in backtest:
                            aggregated_data['performance_metrics']['best_return'] = max(
                                aggregated_data['performance_metrics']['best_return'],
                                backtest['total_return']
                            )
                
                # vnpy集成演示
                elif demo_name == 'vnpy':
                    if 'trading_statistics' in result_data:
                        stats = result_data['trading_statistics']
                        if 'total_events' in stats:
                            aggregated_data['technical_capabilities']['vnpy_events_processed'] = stats['total_events']
                
                # 数据源演示
                elif demo_name == 'datasource':
                    if 'test_configuration' in result_data:
                        config = result_data['test_configuration']
                        if 'sources_registered' in config:
                            aggregated_data['technical_capabilities']['data_sources_tested'] = config['sources_registered']
                
                # 可视化报告演示
                elif demo_name == 'report':
                    if 'charts_created' in result_data:
                        aggregated_data['technical_capabilities']['charts_generated'] = result_data['charts_created']
                
                # 虚拟交易所演示
                elif demo_name == 'exchange':
                    if 'exchange_statistics' in result_data:
                        stats = result_data['exchange_statistics']
                        if 'market_data_points' in stats:
                            aggregated_data['performance_metrics']['total_market_data_points'] = stats['market_data_points']
                        if 'total_trades' in stats:
                            aggregated_data['trading_statistics']['total_trades'] += stats['total_trades']
            
            except Exception as e:
                self.logger.debug(f"聚合 {demo_name} 结果时出错: {e}")
        
        return aggregated_data

    def generate_comprehensive_report(self):
        """生成综合演示报告"""
        self.logger.info("📋 生成综合演示报告...")

        # 计算统计信息
        stats = self.calculate_execution_statistics()
        aggregated_data = self.aggregate_demo_results()

        # 生成综合报告
        self.comprehensive_report = {
            'report_type': 'QTE Comprehensive Demo Report',
            'generation_time': datetime.now().isoformat(),
            'execution_summary': {
                'total_demos_run': stats['total_demos'],
                'successful_demos': stats['successful_demos'],
                'failed_demos': stats['failed_demos'],
                'success_rate': stats['success_rate'],
                'total_duration_seconds': stats['total_duration'],
                'average_duration_seconds': stats['average_duration']
            },
            'demo_results': self.demo_results,
            'aggregated_metrics': aggregated_data,
            'system_capabilities_demonstrated': [
                '基础量化交易策略执行',
                '高级事件驱动架构',
                '虚拟交易所完整功能',
                '机器学习特征工程和模型训练',
                'vnpy框架集成和兼容性',
                '多数据源生态系统管理',
                '专业级可视化报告生成',
                '端到端量化交易流程'
            ],
            'technical_stack_coverage': {
                'data_layer': 'datasource' in stats['success_list'],
                'strategy_layer': 'ml' in stats['success_list'],
                'execution_layer': 'vnpy' in stats['success_list'],
                'exchange_layer': 'exchange' in stats['success_list'],
                'analysis_layer': 'report' in stats['success_list']
            }
        }

        # 保存详细报告
        report_file = self.output_dir / 'comprehensive_demo_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.comprehensive_report, f, default=str, indent=2)

        self.logger.info(f"📁 综合报告已保存: {report_file}")
        return self.comprehensive_report

    def display_final_summary(self):
        """显示最终摘要"""
        stats = self.execution_stats
        aggregated = self.comprehensive_report.get('aggregated_metrics', {})

        self.logger.info("=" * 80)
        self.logger.info("🎉 QTE综合演示完成!")
        self.logger.info("=" * 80)

        # 执行统计
        self.logger.info("📊 执行统计:")
        self.logger.info(f"   总演示数: {stats['total_demos']}")
        self.logger.info(f"   成功演示: {stats['successful_demos']}")
        self.logger.info(f"   失败演示: {stats['failed_demos']}")
        self.logger.info(f"   成功率: {stats['success_rate']:.1%}")
        self.logger.info(f"   总耗时: {stats['total_duration']:.2f}秒")
        self.logger.info(f"   平均耗时: {stats['average_duration']:.2f}秒")

        # 成功的演示
        if stats['success_list']:
            self.logger.info("✅ 成功运行的演示:")
            for demo_name in stats['success_list']:
                demo_info = next(d for d in self.demo_modes if d['name'] == demo_name)
                duration = self.demo_results[demo_name]['duration']
                self.logger.info(f"   - {demo_info['display_name']} ({duration:.2f}s)")

        # 失败的演示
        if stats['failed_list']:
            self.logger.info("❌ 失败的演示:")
            for demo_name in stats['failed_list']:
                demo_info = next(d for d in self.demo_modes if d['name'] == demo_name)
                error = self.demo_results[demo_name]['error']
                self.logger.info(f"   - {demo_info['display_name']}: {error}")

        # 聚合指标
        self.logger.info("📈 聚合指标:")
        trading_stats = aggregated.get('trading_statistics', {})
        tech_caps = aggregated.get('technical_capabilities', {})
        perf_metrics = aggregated.get('performance_metrics', {})

        if trading_stats.get('total_trades', 0) > 0:
            self.logger.info(f"   总交易数: {trading_stats['total_trades']}")
        if trading_stats.get('total_pnl', 0) != 0:
            self.logger.info(f"   总盈亏: ${trading_stats['total_pnl']:,.2f}")
        if tech_caps.get('ml_models_trained', 0) > 0:
            self.logger.info(f"   ML模型训练: {tech_caps['ml_models_trained']}个")
        if tech_caps.get('data_sources_tested', 0) > 0:
            self.logger.info(f"   数据源测试: {tech_caps['data_sources_tested']}个")
        if tech_caps.get('vnpy_events_processed', 0) > 0:
            self.logger.info(f"   vnpy事件处理: {tech_caps['vnpy_events_processed']}个")
        if perf_metrics.get('best_return', 0) > 0:
            self.logger.info(f"   最佳收益率: {perf_metrics['best_return']:.2%}")

        # 技术栈覆盖
        tech_coverage = self.comprehensive_report.get('technical_stack_coverage', {})
        self.logger.info("🏗️ 技术栈覆盖:")
        layers = [
            ('data_layer', '数据层'),
            ('strategy_layer', '策略层'),
            ('execution_layer', '执行层'),
            ('exchange_layer', '交易所层'),
            ('analysis_layer', '分析层')
        ]

        for layer_key, layer_name in layers:
            status = "✅" if tech_coverage.get(layer_key, False) else "❌"
            self.logger.info(f"   {status} {layer_name}")

        self.logger.info("=" * 80)
        self.logger.info("🎯 QTE量化交易引擎演示系统展示了完整的技术栈能力!")
        self.logger.info("📁 详细报告: demo_output/comprehensive_demo_report.json")
        self.logger.info("=" * 80)

    def run_demo(self):
        """运行综合演示"""
        self.logger.info("🚀 开始QTE综合演示...")

        # 显示欢迎横幅
        self.display_welcome_banner()

        overall_start_time = time.time()

        try:
            # 依次运行所有演示模式
            for i, demo_config in enumerate(self.demo_modes, 1):
                demo_result = self.run_single_demo(demo_config, i)
                self.demo_results[demo_config['name']] = demo_result

                # 短暂暂停，让用户看到进度
                time.sleep(0.5)

            # 计算总体统计
            self.calculate_execution_statistics()

            # 生成综合报告
            comprehensive_report = self.generate_comprehensive_report()

            # 显示最终摘要
            self.display_final_summary()

            overall_duration = time.time() - overall_start_time
            self.logger.info(f"⏱️ 综合演示总耗时: {overall_duration:.2f}秒")

            return comprehensive_report

        except Exception as e:
            self.logger.error(f"❌ 综合演示失败: {e}")
            self.logger.debug(f"详细错误: {traceback.format_exc()}")
            return None


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行综合演示
    demo = ComprehensiveDemo()
    results = demo.run_demo()
