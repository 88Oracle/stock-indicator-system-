"""
简单指标测试脚本
不依赖数据库，使用模拟数据测试
"""

import polars as pl
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import Logger, PerformanceMonitor
from core.indicators import *

def create_test_data(n_rows=1000):
    """创建测试数据"""
    import numpy as np

    # 生成模拟股票数据
    np.random.seed(42)

    dates = [f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n_rows)]
    base_price = 100
    prices = []

    for i in range(n_rows):
        change = np.random.randn() * 2
        base_price = max(base_price + change, 50)  # 价格不低于50
        prices.append(base_price)

    data = {
        '日期': dates,
        '代码': ['600000'] * n_rows,
        '收盘': prices,
        '最高': [p * (1 + abs(np.random.randn() * 0.02)) for p in prices],
        '最低': [p * (1 - abs(np.random.randn() * 0.02)) for p in prices],
        '总量': [int(1000000 + np.random.randn() * 200000) for _ in range(n_rows)]
    }

    return pl.DataFrame(data)


def test_all_indicators():
    """测试所有指标"""
    Logger.section("技术指标功能测试")

    # 创建测试数据
    Logger.info("创建测试数据...")
    df = create_test_data(1000)
    Logger.success(f"测试数据创建完成: {len(df)} 行")

    initial_columns = len(df.columns)

    with PerformanceMonitor("计算所有指标"):
        # 1. 趋势指标
        Logger.info("1. 计算趋势指标...")
        df = TrendIndicators.sma(df, '收盘', 5)
        df = TrendIndicators.sma(df, '收盘', 10)
        df = TrendIndicators.sma(df, '收盘', 20)
        df = TrendIndicators.ema(df, '收盘', 5)
        df = TrendIndicators.ema(df, '收盘', 10)
        Logger.success(f"  完成 5 个趋势指标")

        # 2. 动量指标
        Logger.info("2. 计算动量指标...")
        df = MomentumIndicators.rsi(df, '收盘', 14)
        df = MomentumIndicators.momentum(df, '收盘', 5)
        df = MomentumIndicators.momentum(df, '收盘', 10)
        df = MomentumIndicators.roc(df, '收盘', 5)
        df = MomentumIndicators.roc(df, '收盘', 10)
        Logger.success(f"  完成 5 个动量指标")

        # 3. 波动率指标
        Logger.info("3. 计算波动率指标...")
        df = VolatilityIndicators.bollinger_bands(df, '收盘', 20, 2.0)
        df = VolatilityIndicators.atr(df, '最高', '最低', '收盘', 14)
        df = VolatilityIndicators.volatility(df, '收盘', 5)
        df = VolatilityIndicators.volatility(df, '收盘', 10)
        Logger.success(f"  完成 6 个波动率指标 (BB_Upper, BB_Middle, BB_Lower, ATR, Volatility x2)")

        # 4. 成交量指标
        Logger.info("4. 计算成交量指标...")
        df = VolumeIndicators.obv(df, '收盘', '总量')
        df = VolumeIndicators.volume_sma(df, '总量', 5)
        df = VolumeIndicators.volume_sma(df, '总量', 10)
        df = VolumeIndicators.vwap(df, '最高', '最低', '收盘', '总量')
        Logger.success(f"  完成 4 个成交量指标")

        # 5. 震荡指标
        Logger.info("5. 计算震荡指标...")
        df = OscillatorIndicators.macd(df, '收盘', 12, 26, 9)
        df = OscillatorIndicators.stochastic(df, '最高', '最低', '收盘', 14, 3)
        df = OscillatorIndicators.cci(df, '最高', '最低', '收盘', 20)
        Logger.success(f"  完成 6 个震荡指标 (MACD_Line, MACD_Signal, MACD_Hist, Stoch_K, Stoch_D, CCI)")

        # 6. 价格指标
        Logger.info("6. 计算价格指标...")
        df = PriceIndicators.price_change(df, '收盘', 1)
        df = PriceIndicators.price_change(df, '收盘', 5)
        df = PriceIndicators.price_change_pct(df, '收盘', 1)
        df = PriceIndicators.price_change_pct(df, '收盘', 5)
        Logger.success(f"  完成 4 个价格指标")

    final_columns = len(df.columns)
    new_indicators = final_columns - initial_columns

    Logger.section("测试结果")
    print(f"初始列数: {initial_columns}")
    print(f"最终列数: {final_columns}")
    print(f"新增指标: {new_indicators}")
    print(f"\n所有列名:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    # 显示部分结果
    print(f"\n示例数据（最后5行，前10列）:")
    print(df.tail(5).select(df.columns[:10]))

    Logger.success("所有指标测试通过！")


if __name__ == "__main__":
    try:
        test_all_indicators()
    except Exception as e:
        Logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
