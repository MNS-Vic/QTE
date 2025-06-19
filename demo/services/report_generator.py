"""
报告生成器服务 - 负责生成回测报告
"""

import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


class ReportGeneratorService:
    """报告生成器服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化报告生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger('ReportGeneratorService')
        
        self.output_dir = Path(config.get('output_dir', 'demo_output'))
        self.reports_dir = Path(config.get('reports_dir', 'demo_reports'))
        
        # 确保目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"📊 报告生成器初始化完成")
    
    def generate_backtest_report(self, 
                                backtest_result: Any,
                                demo_name: str = "backtest",
                                additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成回测报告
        
        Args:
            backtest_result: 回测结果
            demo_name: 演示名称
            additional_data: 额外数据
            
        Returns:
            报告信息字典
        """
        self.logger.info(f"📋 生成回测报告: {demo_name}")
        
        # 准备报告数据
        report_data = self._prepare_report_data(backtest_result, additional_data)
        
        # 生成JSON报告
        json_report_path = self._generate_json_report(report_data, demo_name)
        
        # 生成文本摘要
        summary_path = self._generate_text_summary(report_data, demo_name)
        
        # 生成HTML报告 (简化版)
        html_report_path = self._generate_html_report(report_data, demo_name)
        
        report_info = {
            'demo_name': demo_name,
            'generated_at': datetime.now().isoformat(),
            'reports': {
                'json': str(json_report_path),
                'summary': str(summary_path),
                'html': str(html_report_path)
            },
            'metrics': report_data.get('metrics', {}),
            'summary_stats': report_data.get('summary', {})
        }
        
        self.logger.info(f"✅ 报告生成完成: {json_report_path}")
        return report_info
    
    def _prepare_report_data(self, backtest_result: Any, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备报告数据"""
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'generator': 'QTE ReportGeneratorService',
                'version': '1.0.0'
            },
            'summary': {
                'initial_capital': getattr(backtest_result, 'initial_capital', 0),
                'final_equity': getattr(backtest_result, 'final_equity', 0),
                'total_pnl': getattr(backtest_result, 'total_pnl', 0),
                'total_trades': getattr(backtest_result, 'total_trades', 0),
                'winning_trades': getattr(backtest_result, 'winning_trades', 0),
                'losing_trades': getattr(backtest_result, 'losing_trades', 0)
            },
            'metrics': getattr(backtest_result, 'metrics', {}),
            'equity_curve': getattr(backtest_result, 'equity_curve', []),
            'transactions': getattr(backtest_result, 'transactions', [])
        }
        
        # 添加额外数据
        if additional_data:
            report_data['additional_data'] = additional_data
        
        return report_data
    
    def _generate_json_report(self, report_data: Dict[str, Any], demo_name: str) -> Path:
        """生成JSON格式报告"""
        filename = f"{demo_name}_report.json"
        file_path = self.output_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            self.logger.error(f"❌ JSON报告生成失败: {e}")
            raise
        
        return file_path
    
    def _generate_text_summary(self, report_data: Dict[str, Any], demo_name: str) -> Path:
        """生成文本摘要"""
        filename = f"{demo_name}_summary.txt"
        file_path = self.output_dir / filename
        
        summary = report_data.get('summary', {})
        metrics = report_data.get('metrics', {})
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"QTE回测报告摘要 - {demo_name}\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("📊 基本统计:\n")
                f.write(f"   初始资金: ${summary.get('initial_capital', 0):,.2f}\n")
                f.write(f"   最终权益: ${summary.get('final_equity', 0):,.2f}\n")
                f.write(f"   总收益: ${summary.get('total_pnl', 0):,.2f}\n")
                f.write(f"   收益率: {metrics.get('total_return', 0):.2%}\n")
                f.write(f"   交易次数: {summary.get('total_trades', 0)}\n\n")
                
                f.write("📈 性能指标:\n")
                f.write(f"   年化收益率: {metrics.get('annual_return', 0):.2%}\n")
                f.write(f"   最大回撤: {metrics.get('max_drawdown', 0):.2%}\n")
                f.write(f"   夏普比率: {metrics.get('sharpe_ratio', 0):.3f}\n")
                f.write(f"   胜率: {metrics.get('win_rate', 0):.2%}\n")
                f.write(f"   盈亏比: {metrics.get('avg_profit_loss_ratio', 0):.2f}\n\n")
                
                f.write("🎯 交易统计:\n")
                f.write(f"   盈利交易: {summary.get('winning_trades', 0)}\n")
                f.write(f"   亏损交易: {summary.get('losing_trades', 0)}\n")
                
                f.write(f"\n报告生成时间: {report_data['metadata']['generated_at']}\n")
        
        except Exception as e:
            self.logger.error(f"❌ 文本摘要生成失败: {e}")
            raise
        
        return file_path
    
    def _generate_html_report(self, report_data: Dict[str, Any], demo_name: str) -> Path:
        """生成HTML报告 (简化版)"""
        filename = f"{demo_name}_report.html"
        file_path = self.reports_dir / filename
        
        summary = report_data.get('summary', {})
        metrics = report_data.get('metrics', {})
        
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QTE回测报告 - {demo_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #2d2d2d;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            color: #4CAF50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background-color: #3d3d3d;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .metric-title {{
            font-size: 14px;
            color: #b0b0b0;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
        }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        .neutral {{ color: #ff9800; }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #888;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 QTE量化回测报告</h1>
        <h2 style="text-align: center; color: #888; margin-bottom: 30px;">{demo_name}</h2>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">初始资金</div>
                <div class="metric-value">${summary.get('initial_capital', 0):,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">最终权益</div>
                <div class="metric-value">${summary.get('final_equity', 0):,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">总收益</div>
                <div class="metric-value {'positive' if summary.get('total_pnl', 0) >= 0 else 'negative'}">${summary.get('total_pnl', 0):,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">收益率</div>
                <div class="metric-value {'positive' if metrics.get('total_return', 0) >= 0 else 'negative'}">{metrics.get('total_return', 0):.2%}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">年化收益率</div>
                <div class="metric-value {'positive' if metrics.get('annual_return', 0) >= 0 else 'negative'}">{metrics.get('annual_return', 0):.2%}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">最大回撤</div>
                <div class="metric-value negative">{metrics.get('max_drawdown', 0):.2%}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">夏普比率</div>
                <div class="metric-value {'positive' if metrics.get('sharpe_ratio', 0) >= 0 else 'negative'}">{metrics.get('sharpe_ratio', 0):.3f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">交易次数</div>
                <div class="metric-value">{summary.get('total_trades', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">胜率</div>
                <div class="metric-value">{metrics.get('win_rate', 0):.2%}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">盈亏比</div>
                <div class="metric-value">{metrics.get('avg_profit_loss_ratio', 0):.2f}</div>
            </div>
        </div>
        
        <div class="footer">
            <p>报告生成时间: {report_data['metadata']['generated_at']}</p>
            <p>由 QTE量化交易引擎 生成</p>
        </div>
    </div>
</body>
</html>
"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        except Exception as e:
            self.logger.error(f"❌ HTML报告生成失败: {e}")
            raise
        
        return file_path
    
    def generate_comparison_report(self, results: List[Dict[str, Any]], report_name: str = "comparison") -> Dict[str, Any]:
        """
        生成对比报告
        
        Args:
            results: 多个回测结果
            report_name: 报告名称
            
        Returns:
            报告信息字典
        """
        self.logger.info(f"📊 生成对比报告: {report_name}")
        
        # 这里可以实现多个结果的对比分析
        # 目前简化实现
        comparison_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'comparison',
                'results_count': len(results)
            },
            'results': results
        }
        
        # 生成JSON报告
        filename = f"{report_name}_comparison.json"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False, default=str)
        
        return {
            'report_name': report_name,
            'file_path': str(file_path),
            'results_count': len(results)
        }
