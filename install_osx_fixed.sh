#!/usr/bin/env bash

# 修复版vnpy 4.0.0 macOS安装脚本
# 解决原始脚本的依赖和配置问题

echo "🚀 开始安装vnpy 4.0.0..."

# 检查Python版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "当前Python版本: $python_version"

# 升级基础工具
echo "📦 升级pip和wheel..."
python -m pip install --upgrade pip wheel

# 安装核心依赖（按照pyproject.toml中的顺序）
echo "📦 安装核心依赖..."
python -m pip install tzlocal>=5.3.1
python -m pip install PySide6>=6.8.2.1
python -m pip install pyqtgraph>=0.13.7
python -m pip install qdarkstyle>=3.2.3
python -m pip install numpy>=2.2.3
python -m pip install pandas>=2.2.3

# ta-lib已经通过conda安装，跳过
echo "✅ ta-lib已通过conda安装"

# 继续安装其他依赖
echo "📦 安装其他依赖..."
python -m pip install deap>=1.4.2
python -m pip install pyzmq>=26.3.0
python -m pip install plotly>=6.0.0
python -m pip install tqdm>=4.67.1
python -m pip install loguru>=0.7.3
python -m pip install nbformat>=5.10.4

# 安装vnpy本身
echo "📦 安装vnpy..."
python -m pip install .

echo "✅ vnpy 4.0.0安装完成！"
echo ""
echo "🎯 验证安装:"
echo "python -c \"import vnpy; print('vnpy版本:', vnpy.__version__)\""
echo ""
echo "🚀 启动vnpy:"
echo "python -c \"from vnpy.trader.ui import MainWindow, create_qapp; from vnpy.event import EventEngine; from vnpy.trader.engine import MainEngine; qapp = create_qapp(); event_engine = EventEngine(); main_engine = MainEngine(event_engine); main_window = MainWindow(main_engine, event_engine); main_window.show(); qapp.exec()\"" 