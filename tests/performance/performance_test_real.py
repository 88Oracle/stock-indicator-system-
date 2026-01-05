"""
真实数据性能对比测试
功能：使用真实数据集对比 Polars 和 Pandas 的性能
作者：AI Assistant
日期：2025-01-03
"""

import polars as pl
import pandas as pd
import time
import psutil
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Optional

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import Logger, PerformanceMonitor, FileUtils
from core.data_processor import DataProcessor
from core.indicators import *


class RealDataPerformanceTest:
    """真实数据性能测试类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.processor = DataProcessor(db_path)
        self.process = psutil.Process()
        self.results = []

    def get_memory_mb(self) -> float:
        """获取当前内存占用（MB）"""
        return self.process.memory_info().rss / 1024 / 1024

    def calculate_indicators_polars(self, df: pl.DataFrame) -> pl.DataFrame:
        """使用Polars计算所有指标"""
        # 基础趋势指标
        df = TrendIndicators.sma(df, '收盘价', 5)
        df = TrendIndicators.sma(df, '收盘价', 10)
        df = TrendIndicators.sma(df, '收盘价', 20)
        df = TrendIndicators.ema(df, '收盘价', 5)
        df = TrendIndicators.ema(df, '收盘价', 10)
        df = TrendIndicators.ema(df, '收盘价', 20)

        # 动量指标
        df = MomentumIndicators.rsi(df, '收盘价', 14)
        df = MomentumIndicators.momentum(df, '收盘价', 5)
        df = MomentumIndicators.roc(df, '收盘价', 5)

        # 波动率指标
        df = VolatilityIndicators.bollinger_bands(df, '收盘价', 20, 2.0)
        if '最高' in df.columns and '最低' in df.columns:
            df = VolatilityIndicators.atr(df, '最高', '最低', '收盘价', 14)
        df = VolatilityIndicators.volatility(df, '收盘价', 10)

        # 成交量指标
        if '总量' in df.columns:
            df = VolumeIndicators.obv(df, '收盘价', '总量')
            df = VolumeIndicators.volume_sma(df, '总量', 5)
            if '最高' in df.columns and '最低' in df.columns:
                df = VolumeIndicators.vwap(df, '最高', '最低', '收盘价', '总量')

        # 震荡指标
        df = OscillatorIndicators.macd(df, '收盘价', 12, 26, 9)
        if '最高' in df.columns and '最低' in df.columns:
            df = OscillatorIndicators.stochastic(df, '最高', '最低', '收盘价', 14, 3)
            df = OscillatorIndicators.cci(df, '最高', '最低', '收盘价', 20)

        # 价格指标
        df = PriceIndicators.price_change(df, '收盘价', 1)
        df = PriceIndicators.price_change_pct(df, '收盘价', 1)

        # 高级指标
        df = AdvancedTrendIndicators.hma(df, '收盘价', 9)
        df = AdvancedTrendIndicators.trix(df, '收盘价', 15)

        if '总量' in df.columns:
            df = AdvancedTrendIndicators.vwma(df, '收盘价', '总量', 10)

        if '最高' in df.columns and '最低' in df.columns:
            df = AdvancedVolatilityIndicators.keltner_channels(df, '最高', '最低', '收盘价', 20, 10, 2.0)
            df = AdvancedVolatilityIndicators.donchian_channel(df, '最高', '最低', 20)
            df = AdvancedVolatilityIndicators.true_range_pct(df, '最高', '最低', '收盘价')

        if '总量' in df.columns and '最高' in df.columns and '最低' in df.columns:
            df = AdvancedVolumeIndicators.cmf(df, '最高', '最低', '收盘价', '总量', 20)
            df = AdvancedVolumeIndicators.fi(df, '收盘价', '总量', 13)
            df = AdvancedVolumeIndicators.volume_oscillator(df, '总量', 5, 10)

        if '最高' in df.columns and '最低' in df.columns:
            df = AdvancedOscillatorIndicators.aroon(df, '最高', '最低', 25)

        df = AdvancedOscillatorIndicators.stochastic_rsi(df, '收盘价', 14, 14)
        df = AdvancedOscillatorIndicators.tsi(df, '收盘价', 25, 13)

        return df

    def calculate_indicators_pandas(self, df: pd.DataFrame) -> pd.DataFrame:
        """使用Pandas计算所有指标（通过转换为Polars）"""
        # 转换为 Polars
        df_polars = pl.from_pandas(df)

        # 计算指标
        df_polars = self.calculate_indicators_polars(df_polars)

        # 转回 Pandas
        df_result = df_polars.to_pandas()

        return df_result

    def test_polars_single_stock(self, stock_code: int) -> Dict:
        """测试单只股票的Polars性能"""
        Logger.section(f"Polars 测试 - 股票 {stock_code}")

        start_time = time.time()
        start_memory = self.get_memory_mb()

        # 读取数据（Polars）
        read_start = time.time()
        df = self.processor.get_stock_data_polars(stock_code)
        read_time = time.time() - read_start

        initial_columns = len(df.columns)
        initial_rows = len(df)

        # 计算指标
        calc_start = time.time()
        df_result = self.calculate_indicators_polars(df)
        calc_time = time.time() - calc_start

        end_time = time.time()
        end_memory = self.get_memory_mb()

        result = {
            'framework': 'Polars',
            'stock_code': stock_code,
            'rows': initial_rows,
            'initial_columns': initial_columns,
            'final_columns': len(df_result.columns),
            'new_indicators': len(df_result.columns) - initial_columns,
            'read_time': read_time,
            'calc_time': calc_time,
            'total_time': end_time - start_time,
            'memory_used_mb': end_memory - start_memory,
            'rows_per_second': initial_rows / calc_time if calc_time > 0 else 0
        }

        Logger.success(f"Polars 完成：总时间 {result['total_time']:.4f}秒，计算时间 {calc_time:.4f}秒")

        return result

    def test_pandas_single_stock(self, stock_code: int) -> Dict:
        """测试单只股票的Pandas性能"""
        Logger.section(f"Pandas 测试 - 股票 {stock_code}")

        start_time = time.time()
        start_memory = self.get_memory_mb()

        # 读取数据（Pandas）
        read_start = time.time()
        df = self.processor.get_stock_data_pandas(stock_code)
        read_time = time.time() - read_start

        initial_columns = len(df.columns)
        initial_rows = len(df)

        # 计算指标
        calc_start = time.time()
        df_result = self.calculate_indicators_pandas(df)
        calc_time = time.time() - calc_start

        end_time = time.time()
        end_memory = self.get_memory_mb()

        result = {
            'framework': 'Pandas',
            'stock_code': stock_code,
            'rows': initial_rows,
            'initial_columns': initial_columns,
            'final_columns': len(df_result.columns),
            'new_indicators': len(df_result.columns) - initial_columns,
            'read_time': read_time,
            'calc_time': calc_time,
            'total_time': end_time - start_time,
            'memory_used_mb': end_memory - start_memory,
            'rows_per_second': initial_rows / calc_time if calc_time > 0 else 0
        }

        Logger.success(f"Pandas 完成：总时间 {result['total_time']:.4f}秒，计算时间 {calc_time:.4f}秒")

        return result

    def compare_results(self, result_polars: Dict, result_pandas: Dict):
        """对比测试结果"""
        Logger.section("性能对比结果")

        # 计算加速比
        total_speedup = result_pandas['total_time'] / result_polars['total_time']
        calc_speedup = result_pandas['calc_time'] / result_polars['calc_time']
        read_speedup = result_pandas['read_time'] / result_polars['read_time']

        print("\n" + "="*100)
        print(f"{'指标':<25} {'Polars':<25} {'Pandas':<25} {'加速比':<25}")
        print("="*100)
        print(f"{'股票代码':<25} {result_polars['stock_code']:<25} {result_pandas['stock_code']:<25} {'-':<25}")
        print(f"{'数据行数':<25} {result_polars['rows']:<25,} {result_pandas['rows']:<25,} {'-':<25}")
        print(f"{'计算指标数':<25} {result_polars['new_indicators']:<25} {result_pandas['new_indicators']:<25} {'-':<25}")
        print("-"*100)
        print(f"{'数据读取时间(秒)':<25} {result_polars['read_time']:<25.4f} {result_pandas['read_time']:<25.4f} {f'{read_speedup:.2f}x':<25}")
        print(f"{'指标计算时间(秒)':<25} {result_polars['calc_time']:<25.4f} {result_pandas['calc_time']:<25.4f} {f'{calc_speedup:.2f}x':<25}")
        print(f"{'总执行时间(秒)':<25} {result_polars['total_time']:<25.4f} {result_pandas['total_time']:<25.4f} {f'{total_speedup:.2f}x':<25}")
        print("-"*100)
        print(f"{'内存使用(MB)':<25} {result_polars['memory_used_mb']:<25.2f} {result_pandas['memory_used_mb']:<25.2f} {'-':<25}")
        print(f"{'处理速度(行/秒)':<25} {result_polars['rows_per_second']:<25,.0f} {result_pandas['rows_per_second']:<25,.0f} {'-':<25}")
        print("="*100)

        print(f"\n总结:")
        print(f"  - 数据读取：Polars 比 Pandas 快 {read_speedup:.2f} 倍")
        print(f"  - 指标计算：Polars 比 Pandas 快 {calc_speedup:.2f} 倍")
        print(f"  - 总体性能：Polars 比 Pandas 快 {total_speedup:.2f} 倍")

        if total_speedup >= 60:
            print(f"\n  ✓ 已达到 60-80 倍性能目标！")
        elif total_speedup >= 10:
            print(f"\n  [良好] 性能显著提升，但未达到 60-80 倍目标")
        else:
            print(f"\n  [需改进] 性能提升不明显")

        print("="*100)

        return {
            'read_speedup': read_speedup,
            'calc_speedup': calc_speedup,
            'total_speedup': total_speedup
        }

    def run_test(self, stock_code: Optional[int] = None):
        """运行完整测试"""
        Logger.section("真实数据性能对比测试")

        # 如果没有指定股票，选择第一个
        if stock_code is None:
            codes = self.processor.get_stock_codes(limit=1)
            if not codes:
                Logger.error("数据库中没有数据")
                return None
            stock_code = codes[0]

        Logger.info(f"测试股票代码: {stock_code}")

        # Polars 测试
        result_polars = self.test_polars_single_stock(stock_code)

        # Pandas 测试
        result_pandas = self.test_pandas_single_stock(stock_code)

        # 对比结果
        comparison = self.compare_results(result_polars, result_pandas)

        return {
            'stock_code': stock_code,
            'polars': result_polars,
            'pandas': result_pandas,
            'comparison': comparison
        }


def main():
    """主函数"""
    # 配置路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(script_dir, "data")

    # 查找数据库文件
    db_files = [f for f in os.listdir(data_dir) if f.endswith('.duckdb')]

    if not db_files:
        Logger.error("未找到数据库文件！")
        return

    db_file = sorted(db_files)[-1]
    db_path = os.path.join(data_dir, db_file)

    Logger.info(f"使用数据库: {db_file}")

    # 创建测试器
    tester = RealDataPerformanceTest(db_path)

    # 运行测试
    result = tester.run_test()

    if result:
        Logger.section("测试完成！")

        # 断开连接
        tester.processor.disconnect()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
