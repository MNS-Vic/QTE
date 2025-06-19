"""
数据生成器服务 - 负责生成演示所需的市场数据
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import json


class DataGeneratorService:
    """数据生成器服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger('DataGeneratorService')
        
        # 从配置中获取参数
        self.default_symbols = config.get('test_symbols', ['AAPL', 'GOOGL', 'MSFT'])
        self.default_period_days = config.get('test_period_days', 30)
        self.data_frequency = config.get('data_frequency', '1d')
        self.output_dir = Path(config.get('output_dir', 'demo_output'))
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_sample_data(self, 
                           symbols: Optional[List[str]] = None,
                           period_days: Optional[int] = None,
                           start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        生成示例市场数据
        
        Args:
            symbols: 交易标的列表
            period_days: 数据周期天数
            start_date: 开始日期
            
        Returns:
            包含市场数据的字典
        """
        symbols = symbols or self.default_symbols
        period_days = period_days or self.default_period_days
        start_date = start_date or (datetime.now() - timedelta(days=period_days))
        
        self.logger.info(f"📊 生成示例市场数据: {symbols}, 周期: {period_days}天")
        
        # 生成日期序列
        dates = pd.date_range(start_date, periods=period_days, freq='D')
        
        market_data = {}
        
        for symbol in symbols:
            # 生成价格数据
            price_data = self._generate_price_series(symbol, dates)
            market_data[symbol] = price_data
        
        # 保存数据到文件
        output_file = self.output_dir / 'sample_market_data.json'
        self._save_market_data(market_data, output_file)
        
        self.logger.info(f"✅ 市场数据已生成并保存: {output_file}")
        
        return {
            'data': market_data,
            'symbols': symbols,
            'period_days': period_days,
            'start_date': start_date,
            'output_file': str(output_file)
        }
    
    def _generate_price_series(self, symbol: str, dates: pd.DatetimeIndex) -> Dict[str, Any]:
        """
        生成单个标的的价格序列
        
        Args:
            symbol: 交易标的
            dates: 日期序列
            
        Returns:
            价格数据字典
        """
        np.random.seed(hash(symbol) % 2**32)  # 为每个标的设置不同的随机种子
        
        # 基础价格参数
        base_price = 100.0
        volatility = 0.02  # 日波动率
        trend = 0.001      # 趋势
        
        # 生成价格序列 (几何布朗运动)
        returns = np.random.normal(trend, volatility, len(dates))
        prices = [base_price]
        
        for i in range(1, len(dates)):
            new_price = prices[-1] * (1 + returns[i])
            prices.append(max(new_price, 0.01))  # 确保价格为正
        
        # 生成OHLC数据
        ohlc_data = []
        for i, (date, close_price) in enumerate(zip(dates, prices)):
            # 生成开高低收
            if i == 0:
                open_price = close_price
            else:
                open_price = prices[i-1]
            
            # 高低价在开收价基础上随机波动
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            # 成交量
            volume = int(np.random.normal(1000000, 200000))
            volume = max(volume, 100000)  # 最小成交量
            
            ohlc_data.append({
                'timestamp': date.isoformat(),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        return {
            'symbol': symbol,
            'data': ohlc_data,
            'metadata': {
                'data_points': len(ohlc_data),
                'start_date': dates[0].isoformat(),
                'end_date': dates[-1].isoformat(),
                'frequency': self.data_frequency
            }
        }
    
    def _save_market_data(self, market_data: Dict[str, Any], output_file: Path):
        """
        保存市场数据到文件
        
        Args:
            market_data: 市场数据
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(market_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"❌ 保存市场数据失败: {e}")
            raise
    
    def load_market_data(self, data_file: Path) -> Dict[str, Any]:
        """
        从文件加载市场数据
        
        Args:
            data_file: 数据文件路径
            
        Returns:
            市场数据字典
        """
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"❌ 加载市场数据失败: {e}")
            raise
    
    def generate_realtime_data(self, symbol: str, base_price: float = 100.0) -> Dict[str, Any]:
        """
        生成实时数据点
        
        Args:
            symbol: 交易标的
            base_price: 基础价格
            
        Returns:
            实时数据点
        """
        # 生成随机价格变动
        change_pct = np.random.normal(0, 0.001)  # 0.1%的标准波动
        new_price = base_price * (1 + change_pct)
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price': round(new_price, 2),
            'change': round(new_price - base_price, 2),
            'change_pct': round(change_pct * 100, 2),
            'volume': int(np.random.normal(10000, 2000))
        }
    
    def get_data_summary(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取数据摘要信息
        
        Args:
            market_data: 市场数据
            
        Returns:
            数据摘要
        """
        summary = {
            'symbols_count': len(market_data),
            'symbols': list(market_data.keys()),
            'total_data_points': 0,
            'date_range': {},
            'price_ranges': {}
        }
        
        for symbol, data in market_data.items():
            if 'data' in data and data['data']:
                summary['total_data_points'] += len(data['data'])
                
                # 价格范围
                prices = [point['close'] for point in data['data']]
                summary['price_ranges'][symbol] = {
                    'min': min(prices),
                    'max': max(prices),
                    'start': prices[0],
                    'end': prices[-1]
                }
                
                # 日期范围
                if 'metadata' in data:
                    summary['date_range'][symbol] = {
                        'start': data['metadata'].get('start_date'),
                        'end': data['metadata'].get('end_date')
                    }
        
        return summary
