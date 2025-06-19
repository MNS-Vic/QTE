"""
QTE演示系统测试套件
验证演示系统的功能完整性和稳定性
"""

import logging
import unittest
import tempfile
import shutil
from pathlib import Path
import json
import sys
import os

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from demo.simple_trading_demo import SimpleTradeDemo
from demo.advanced_trading_demo import AdvancedTradeDemo

class DemoTestSuite:
    """演示测试套件"""
    
    def __init__(self):
        self.logger = logging.getLogger('DemoTestSuite')
        self.temp_dir = None
        self.original_output_dir = None
        
    def setup_test_environment(self):
        """设置测试环境"""
        self.logger.info("🧪 设置测试环境...")
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix='qte_demo_test_')
        self.original_output_dir = os.environ.get('QTE_DEMO_OUTPUT_DIR', 'demo_output')
        os.environ['QTE_DEMO_OUTPUT_DIR'] = self.temp_dir
        
        self.logger.info(f"📁 临时测试目录: {self.temp_dir}")
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        self.logger.info("🧹 清理测试环境...")
        
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        if self.original_output_dir:
            os.environ['QTE_DEMO_OUTPUT_DIR'] = self.original_output_dir
    
    def test_simple_demo(self):
        """测试简单演示"""
        self.logger.info("🧪 测试简单演示...")
        
        try:
            demo = SimpleTradeDemo()
            results = demo.run()
            
            # 验证结果
            assert results is not None, "简单演示应该返回结果"
            assert 'total_trades' in results, "结果应该包含交易次数"
            assert 'final_equity' in results, "结果应该包含最终权益"
            assert results['total_trades'] >= 0, "交易次数应该非负"
            assert results['final_equity'] > 0, "最终权益应该为正"
            
            # 验证输出文件
            output_dir = Path(demo.output_dir)
            assert output_dir.exists(), "输出目录应该存在"
            
            data_file = output_dir / 'sample_market_data.json'
            assert data_file.exists(), "市场数据文件应该存在"
            
            report_file = output_dir / 'simple_demo_report.json'
            assert report_file.exists(), "报告文件应该存在"
            
            # 验证报告内容
            with open(report_file, 'r') as f:
                report_data = json.load(f)
                assert 'total_trades' in report_data, "报告应该包含交易次数"
                assert 'metrics' in report_data, "报告应该包含指标"
            
            self.logger.info("✅ 简单演示测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 简单演示测试失败: {e}")
            return False
    
    def test_advanced_demo(self):
        """测试高级演示"""
        self.logger.info("🧪 测试高级演示...")
        
        try:
            demo = AdvancedTradeDemo()
            results = demo.run()
            
            # 验证结果
            assert results is not None, "高级演示应该返回结果"
            assert 'backtest_summary' in results, "结果应该包含回测摘要"
            assert 'performance_metrics' in results, "结果应该包含性能指标"
            
            summary = results['backtest_summary']
            assert 'total_signals' in summary, "摘要应该包含信号总数"
            assert 'total_orders' in summary, "摘要应该包含订单总数"
            assert summary['total_signals'] >= 0, "信号总数应该非负"
            assert summary['total_orders'] >= 0, "订单总数应该非负"
            
            # 验证输出文件
            output_dir = Path(demo.output_dir)
            assert output_dir.exists(), "输出目录应该存在"
            
            data_file = output_dir / 'advanced_market_data.json'
            assert data_file.exists(), "高级市场数据文件应该存在"
            
            report_file = output_dir / 'advanced_demo_report.json'
            assert report_file.exists(), "高级报告文件应该存在"
            
            self.logger.info("✅ 高级演示测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 高级演示测试失败: {e}")
            return False
    
    def test_data_generation(self):
        """测试数据生成功能"""
        self.logger.info("🧪 测试数据生成...")
        
        try:
            # 测试简单数据生成
            simple_demo = SimpleTradeDemo()
            market_data = simple_demo.generate_sample_data()
            
            assert market_data is not None, "应该生成市场数据"
            assert len(market_data) > 0, "市场数据不应为空"
            
            for symbol, data in market_data.items():
                assert len(data) > 0, f"符号{symbol}的数据不应为空"
                for data_point in data[:5]:  # 检查前5个数据点
                    required_fields = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
                    for field in required_fields:
                        assert field in data_point, f"数据点应该包含字段{field}"
                    
                    # 验证价格逻辑
                    assert data_point['high'] >= data_point['low'], "最高价应该大于等于最低价"
                    assert data_point['high'] >= data_point['open'], "最高价应该大于等于开盘价"
                    assert data_point['high'] >= data_point['close'], "最高价应该大于等于收盘价"
                    assert data_point['low'] <= data_point['open'], "最低价应该小于等于开盘价"
                    assert data_point['low'] <= data_point['close'], "最低价应该小于等于收盘价"
                    assert data_point['volume'] > 0, "成交量应该为正"
            
            self.logger.info("✅ 数据生成测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据生成测试失败: {e}")
            return False
    
    def test_strategy_functionality(self):
        """测试策略功能"""
        self.logger.info("🧪 测试策略功能...")
        
        try:
            from qte.core.events import MarketEvent
            from datetime import datetime
            
            # 测试简单移动平均策略
            simple_demo = SimpleTradeDemo()
            strategy = simple_demo.create_simple_strategy()
            
            # 创建测试市场事件
            test_prices = [100, 101, 102, 103, 104, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96]
            signals = []
            
            for i, price in enumerate(test_prices):
                market_event = MarketEvent(
                    symbol='TEST',
                    timestamp=datetime.now(),
                    open_price=price,
                    high_price=price * 1.01,
                    low_price=price * 0.99,
                    close_price=price,
                    volume=1000000
                )
                
                signal = strategy.process_market_data(market_event)
                if signal:
                    signals.append(signal)
            
            # 验证策略生成了信号
            assert len(signals) > 0, "策略应该生成交易信号"
            
            for signal in signals:
                assert hasattr(signal, 'symbol'), "信号应该有symbol属性"
                assert hasattr(signal, 'direction'), "信号应该有direction属性"
                assert signal.direction in [-1, 1], "信号方向应该是1或-1"
            
            self.logger.info("✅ 策略功能测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 策略功能测试失败: {e}")
            return False
    
    def test_risk_management(self):
        """测试风险管理功能"""
        self.logger.info("🧪 测试风险管理...")
        
        try:
            from demo.advanced_trading_demo import RiskManager
            
            # 创建风险管理器
            risk_config = {
                'max_position_size': 0.1,
                'max_daily_loss': 0.02,
                'max_drawdown': 0.15
            }
            
            risk_manager = RiskManager(risk_config)
            
            # 测试风险检查
            test_portfolio = {'AAPL': {'quantity': 100, 'avg_price': 150.0}}
            
            # 创建测试信号
            from qte.core.events import SignalEvent
            from datetime import datetime
            
            test_signal = SignalEvent(
                symbol='AAPL',
                timestamp=datetime.now(),
                signal_type='LONG',
                direction=1,
                strength=1.0
            )
            
            # 风险检查应该返回布尔值
            risk_check_result = risk_manager.check_signal(test_signal, test_portfolio)
            assert isinstance(risk_check_result, bool), "风险检查应该返回布尔值"
            
            # 生成风险报告
            risk_report = risk_manager.generate_risk_report(test_portfolio)
            assert isinstance(risk_report, dict), "风险报告应该是字典"
            
            self.logger.info("✅ 风险管理测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 风险管理测试失败: {e}")
            return False
    
    def test_configuration_loading(self):
        """测试配置加载功能"""
        self.logger.info("🧪 测试配置加载...")
        
        try:
            # 测试默认配置
            demo = AdvancedTradeDemo()
            config = demo.config
            
            assert 'initial_capital' in config, "配置应该包含初始资金"
            assert 'symbols' in config, "配置应该包含交易符号"
            assert 'strategies' in config, "配置应该包含策略配置"
            assert 'risk' in config, "配置应该包含风险配置"
            
            assert config['initial_capital'] > 0, "初始资金应该为正"
            assert len(config['symbols']) > 0, "应该有交易符号"
            
            self.logger.info("✅ 配置加载测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置加载测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🧪 开始运行演示系统测试套件...")
        
        # 设置测试环境
        self.setup_test_environment()
        
        test_results = {}
        
        try:
            # 运行各项测试
            tests = [
                ('数据生成测试', self.test_data_generation),
                ('策略功能测试', self.test_strategy_functionality),
                ('风险管理测试', self.test_risk_management),
                ('配置加载测试', self.test_configuration_loading),
                ('简单演示测试', self.test_simple_demo),
                ('高级演示测试', self.test_advanced_demo),
            ]
            
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                self.logger.info(f"🔄 运行: {test_name}")
                try:
                    result = test_func()
                    test_results[test_name] = result
                    if result:
                        passed += 1
                        self.logger.info(f"✅ {test_name} 通过")
                    else:
                        self.logger.error(f"❌ {test_name} 失败")
                except Exception as e:
                    test_results[test_name] = False
                    self.logger.error(f"❌ {test_name} 异常: {e}")
            
            # 打印测试摘要
            self.logger.info("📊 测试结果摘要:")
            self.logger.info(f"   总测试数: {total}")
            self.logger.info(f"   通过数: {passed}")
            self.logger.info(f"   失败数: {total - passed}")
            self.logger.info(f"   通过率: {passed/total*100:.1f}%")
            
            if passed == total:
                self.logger.info("🎉 所有测试通过!")
            else:
                self.logger.warning(f"⚠️  {total - passed} 个测试失败")
            
            return {
                'total_tests': total,
                'passed_tests': passed,
                'failed_tests': total - passed,
                'pass_rate': passed / total,
                'test_details': test_results
            }
            
        finally:
            # 清理测试环境
            self.cleanup_test_environment()


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    test_suite = DemoTestSuite()
    results = test_suite.run_all_tests()
    
    # 退出码
    exit_code = 0 if results['failed_tests'] == 0 else 1
    sys.exit(exit_code)
