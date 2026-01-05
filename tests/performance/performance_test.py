"""
性能对比测试脚本
功能：对比 Polars 和 Pandas 在指标计算上的性能差异
作者：AI Assistant
日期：2025-01-02
"""

import polars as pl
import pandas as pd
import time
import psutil
import os
import sys
from typing import Dict, List

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import Logger, PerformanceMonitor
from core.indicators import *


class TestPerformance:
    """性能测试类"""

    def __init__(self):
        self.results = []
        self.process = psutil.Process()

    def get_memory_mb(self) -> float:
        """获取当前内存占用（MB）"""
        return self.process.memory_info().rss / 1024 / 1024

    def test_polars_indicators(self, df: pl.DataFrame) -> Dict:
        """测试 Polars 指标计算性能"""
        Logger.section("Polars 性能测试")

        start_time = time.time()
        start_memory = self.get_memory_mb()

        # 基础指标
        df = TrendIndicators.sma(df, '收盘', 5)
        df = TrendIndicators.sma(df, '收盘', 10)
        df = TrendIndicators.sma(df, '收盘', 20)
        df = TrendIndicators.ema(df, '收盘', 5)
        df = TrendIndicators.ema(df, '收盘', 10)
        df = TrendIndicators.ema(df, '收盘', 20)

        # 动量指标
        df = MomentumIndicators.rsi(df, '收盘', 14)
        df = MomentumIndicators.momentum(df, '收盘', 5)
        df = MomentumIndicators.roc(df, '收盘', 5)

        # 波动率指标
        df = VolatilityIndicators.bollinger_bands(df, '收盘', 20, 2.0)
        df = VolatilityIndicators.atr(df, '最高', '最低', '收盘', 14)
        df = VolatilityIndicators.volatility(df, '收盘', 10)

        # 成交量指标
        df = VolumeIndicators.obv(df, '收盘', '总量')
        df = VolumeIndicators.volume_sma(df, '总量', 5)
        df = VolumeIndicators.vwap(df, '最高', '最低', '收盘', '总量')

        # 震荡指标
        df = OscillatorIndicators.macd(df, '收盘', 12, 26, 9)
        df = OscillatorIndicators.stochastic(df, '最高', '最低', '收盘', 14, 3)
        df = OscillatorIndicators.cci(df, '最高', '最低', '收盘', 20)

        # 价格指标
        df = PriceIndicators.price_change(df, '收盘', 1)
        df = PriceIndicators.price_change_pct(df, '收盘', 1)

        # 高级指标
        df = AdvancedTrendIndicators.hma(df, '收盘', 9)
        df = AdvancedTrendIndicators.trix(df, '收盘', 15)
        df = AdvancedTrendIndicators.vwma(df, '收盘', '总量', 10)

        df = AdvancedVolatilityIndicators.keltner_channels(df, '最高', '最低', '收盘', 20, 10, 2.0)
        df = AdvancedVolatilityIndicators.donchian_channel(df, '最高', '最低', 20)
        df = AdvancedVolatilityIndicators.true_range_pct(df, '最高', '最低', '收盘')

        df = AdvancedVolumeIndicators.cmf(df, '最高', '最低', '收盘', '总量', 20)
        df = AdvancedVolumeIndicators.fi(df, '收盘', '总量', 13)
        df = AdvancedVolumeIndicators.volume_oscillator(df, '总量', 5, 10)

        df = AdvancedOscillatorIndicators.aroon(df, '最高', '最低', 25)
        df = AdvancedOscillatorIndicators.stochastic_rsi(df, '收盘', 14, 14)
        df = AdvancedOscillatorIndicators.tsi(df, '收盘', 25, 13)

        end_time = time.time()
        end_memory = self.get_memory_mb()

        elapsed = end_time - start_time
        memory_used = end_memory - start_memory

        result = {
            'framework': 'Polars',
            'rows': len(df),
            'initial_columns': 6,
            'final_columns': len(df.columns),
            'new_indicators': len(df.columns) - 6,
            'elapsed_time': elapsed,
            'memory_used_mb': memory_used,
            'rows_per_second': len(df) / elapsed if elapsed > 0 else 0
        }

        Logger.success(f"Polars 测试完成：{elapsed:.4f} 秒，{len(df.columns) - 6} 个指标")

        return result

    def test_pandas_indicators(self, df: pd.DataFrame) -> Dict:
        """测试 Pandas 指标计算性能"""
        Logger.section("Pandas 性能测试")

        start_time = time.time()
        start_memory = self.get_memory_mb()

        # 转换为 Polars 进行计算（因为我们的指标实现是基于 Polars 的）
        df_polars = pl.from_pandas(df)

        # 基础指标
        df_polars = TrendIndicators.sma(df_polars, '收盘', 5)
        df_polars = TrendIndicators.sma(df_polars, '收盘', 10)
        df_polars = TrendIndicators.sma(df_polars, '收盘', 20)
        df_polars = TrendIndicators.ema(df_polars, '收盘', 5)
        df_polars = TrendIndicators.ema(df_polars, '收盘', 10)
        df_polars = TrendIndicators.ema(df_polars, '收盘', 20)

        # 动量指标
        df_polars = MomentumIndicators.rsi(df_polars, '收盘', 14)
        df_polars = MomentumIndicators.momentum(df_polars, '收盘', 5)
        df_polars = MomentumIndicators.roc(df_polars, '收盘', 5)

        # 波动率指标
        df_polars = VolatilityIndicators.bollinger_bands(df_polars, '收盘', 20, 2.0)
        df_polars = VolatilityIndicators.atr(df_polars, '最高', '最低', '收盘', 14)
        df_polars = VolatilityIndicators.volatility(df_polars, '收盘', 10)

        # 成交量指标
        df_polars = VolumeIndicators.obv(df_polars, '收盘', '总量')
        df_polars = VolumeIndicators.volume_sma(df_polars, '总量', 5)
        df_polars = VolumeIndicators.vwap(df_polars, '最高', '最低', '收盘', '总量')

        # 震荡指标
        df_polars = OscillatorIndicators.macd(df_polars, '收盘', 12, 26, 9)
        df_polars = OscillatorIndicators.stochastic(df_polars, '最高', '最低', '收盘', 14, 3)
        df_polars = OscillatorIndicators.cci(df_polars, '最高', '最低', '收盘', 20)

        # 价格指标
        df_polars = PriceIndicators.price_change(df_polars, '收盘', 1)
        df_polars = PriceIndicators.price_change_pct(df_polars, '收盘', 1)

        # 高级指标
        df_polars = AdvancedTrendIndicators.hma(df_polars, '收盘', 9)
        df_polars = AdvancedTrendIndicators.trix(df_polars, '收盘', 15)
        df_polars = AdvancedTrendIndicators.vwma(df_polars, '收盘', '总量', 10)

        df_polars = AdvancedVolatilityIndicators.keltner_channels(df_polars, '最高', '最低', '收盘', 20, 10, 2.0)
        df_polars = AdvancedVolatilityIndicators.donchian_channel(df_polars, '最高', '最低', 20)
        df_polars = AdvancedVolatilityIndicators.true_range_pct(df_polars, '最高', '最低', '收盘')

        df_polars = AdvancedVolumeIndicators.cmf(df_polars, '最高', '最低', '收盘', '总量', 20)
        df_polars = AdvancedVolumeIndicators.fi(df_polars, '收盘', '总量', 13)
        df_polars = AdvancedVolumeIndicators.volume_oscillator(df_polars, '总量', 5, 10)

        df_polars = AdvancedOscillatorIndicators.aroon(df_polars, '最高', '最低', 25)
        df_polars = AdvancedOscillatorIndicators.stochastic_rsi(df_polars, '收盘', 14, 14)
        df_polars = AdvancedOscillatorIndicators.tsi(df_polars, '收盘', 25, 13)

        # 转回 Pandas
        df = df_polars.to_pandas()

        end_time = time.time()
        end_memory = self.get_memory_mb()

        elapsed = end_time - start_time
        memory_used = end_memory - start_memory

        result = {
            'framework': 'Pandas',
            'rows': len(df),
            'initial_columns': 6,
            'final_columns': len(df.columns),
            'new_indicators': len(df.columns) - 6,
            'elapsed_time': elapsed,
            'memory_used_mb': memory_used,
            'rows_per_second': len(df) / elapsed if elapsed > 0 else 0
        }

        Logger.success(f"Pandas 测试完成：{elapsed:.4f} 秒，{len(df.columns) - 6} 个指标")

        return result

    def test_compare_results(self, result_polars: Dict, result_pandas: Dict):
        """对比测试结果"""
        Logger.section("性能对比结果")

        # 计算加速比
        speedup = result_pandas['elapsed_time'] / result_polars['elapsed_time']
        memory_reduction = (1 - result_polars['memory_used_mb'] / result_pandas['memory_used_mb']) * 100 if result_pandas['memory_used_mb'] > 0 else 0

        print("\n" + "="*80)
        print(f"{'指标':<20} {'Polars':<20} {'Pandas':<20} {'对比':<20}")
        print("="*80)
        print(f"{'数据行数':<20} {result_polars['rows']:<20,} {result_pandas['rows']:<20,} {'-':<20}")
        print(f"{'计算指标数':<20} {result_polars['new_indicators']:<20} {result_pandas['new_indicators']:<20} {'-':<20}")
        print(f"{'执行时间(秒)':<20} {result_polars['elapsed_time']:<20.4f} {result_pandas['elapsed_time']:<20.4f} {f'{speedup:.2f}x 更快':<20}")
        print(f"{'内存使用(MB)':<20} {result_polars['memory_used_mb']:<20.2f} {result_pandas['memory_used_mb']:<20.2f} {f'{memory_reduction:.1f}% 更少':<20}")
        print(f"{'处理速度(行/秒)':<20} {result_polars['rows_per_second']:<20,.0f} {result_pandas['rows_per_second']:<20,.0f} {'-':<20}")
        print("="*80)

        print(f"\n总结:")
        print(f"  - Polars 比 Pandas 快 {speedup:.2f} 倍")
        print(f"  - Polars 内存使用减少 {memory_reduction:.1f}%")

        if speedup >= 60:
            print(f"  [OK] 已达到 60-80 倍性能目标！")
        elif speedup >= 10:
            print(f"  [良好] 性能显著提升，但未达到 60-80 倍目标")
        else:
            print(f"  [警告] 性能提升不明显，需要优化")

        print("="*80)

        return {
            'speedup': speedup,
            'memory_reduction_pct': memory_reduction
        }

    def run_test(self, n_rows: int = 10000):
        """运行完整测试"""
        Logger.section(f"性能测试 - {n_rows:,} 行数据")

        # 创建测试数据
        Logger.info("生成测试数据...")
        import numpy as np
        np.random.seed(42)

        dates = [f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n_rows)]
        base_price = 100
        prices = []

        for i in range(n_rows):
            change = np.random.randn() * 2
            base_price = max(base_price + change, 50)
            prices.append(base_price)

        data = {
            '代码': ['600000'] * n_rows,
            '日期': dates,
            '收盘': prices,
            '最高': [p * (1 + abs(np.random.randn() * 0.02)) for p in prices],
            '最低': [p * (1 - abs(np.random.randn() * 0.02)) for p in prices],
            '总量': [int(1000000 + np.random.randn() * 200000) for _ in range(n_rows)]
        }

        Logger.success(f"测试数据生成完成：{n_rows:,} 行")

        # Polars 测试
        df_polars = pl.DataFrame(data)
        result_polars = self.test_polars_indicators(df_polars.clone())

        # Pandas 测试
        df_pandas = pd.DataFrame(data)
        result_pandas = self.test_pandas_indicators(df_pandas.copy())

        # 对比结果
        comparison = self.compare_results(result_polars, result_pandas)

        return {
            'polars': result_polars,
            'pandas': result_pandas,
            'comparison': comparison
        }


def test_main():
    """主函数"""
    tester = PerformanceTest()

    # 测试不同数据规模
    test_sizes = [1000, 5000, 10000, 50000]

    all_results = []

    for size in test_sizes:
        print(f"\n{'='*80}\n")
        result = tester.run_test(n_rows=size)
        all_results.append({
            'size': size,
            'result': result
        })

    # 汇总结果
    Logger.section("汇总结果")

    print("\n" + "="*80)
    print(f"{'数据规模':<15} {'Polars时间(秒)':<20} {'Pandas时间(秒)':<20} {'加速比':<15}")
    print("="*80)

    for item in all_results:
        size = item['size']
        result = item['result']
        speedup = result['comparison']['speedup']

        print(f"{size:<15,} {result['polars']['elapsed_time']:<20.4f} {result['pandas']['elapsed_time']:<20.4f} {speedup:<15.2f}x")

    print("="*80)

    Logger.success("性能测试完成！")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
