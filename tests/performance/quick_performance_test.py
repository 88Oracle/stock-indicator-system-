"""
快速性能测试脚本 - 验证优化效果

对比优化前后的性能：
1. 优化1：只读15列 vs 读243列
2. 优化2：快速Parquet vs 默认Parquet
3. 优化4：CSV直接读取 vs DuckDB读取
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.data_processor import DataProcessor, IndicatorCalculator, ResultSaver
from src.core.utils import Logger, PerformanceMonitor

def test_reading_performance():
    """测试数据读取性能"""
    Logger.section("测试1: 数据读取性能对比")

    db_path = "data/stock_data.duckdb"

    # 测试1.1: 读取全部243列（优化前）
    Logger.info("测试1.1: 读取全部243列（优化前）...")
    processor_old = DataProcessor(db_path, use_essential_columns=False)
    start = time.time()
    df_old = processor_old.read_data_polars(limit=100000)
    time_old = time.time() - start
    Logger.success(f"完成！耗时: {time_old:.3f}秒, 读取 {len(df_old.columns)} 列")

    # 测试1.2: 只读15个核心列（优化后）
    Logger.info("测试1.2: 只读15个核心列（优化后）...")
    processor_new = DataProcessor(db_path, use_essential_columns=True)
    start = time.time()
    df_new = processor_new.read_data_polars(limit=100000)
    time_new = time.time() - start
    Logger.success(f"完成！耗时: {time_new:.3f}秒, 读取 {len(df_new.columns)} 列")

    # 计算提升
    speedup = time_old / time_new
    improvement = (time_old - time_new) / time_old * 100

    Logger.info(f"\n📊 优化1效果:")
    Logger.info(f"  - 优化前: {time_old:.3f}秒 ({len(df_old.columns)}列)")
    Logger.info(f"  - 优化后: {time_new:.3f}秒 ({len(df_new.columns)}列)")
    Logger.info(f"  - 性能提升: {speedup:.2f}倍 ({improvement:.1f}%)")

    return df_new, processor_new

def test_csv_vs_duckdb():
    """测试CSV直接读取 vs DuckDB读取"""
    Logger.section("测试2: CSV直接读取 vs DuckDB")

    db_path = "data/stock_data.duckdb"
    processor = DataProcessor(db_path, use_essential_columns=True)

    # 测试2.1: DuckDB读取
    Logger.info("测试2.1: 通过DuckDB读取...")
    start = time.time()
    df_duckdb = processor.read_data_polars(limit=100000)
    time_duckdb = time.time() - start
    Logger.success(f"完成！耗时: {time_duckdb:.3f}秒")

    # 测试2.2: CSV直接读取
    Logger.info("测试2.2: 直接从CSV读取...")
    start = time.time()
    df_csv = processor.read_csv_direct(limit=100000)
    time_csv = time.time() - start
    Logger.success(f"完成！耗时: {time_csv:.3f}秒")

    # 计算提升
    speedup = time_duckdb / time_csv
    improvement = (time_duckdb - time_csv) / time_duckdb * 100

    Logger.info(f"\n📊 优化4效果:")
    Logger.info(f"  - DuckDB: {time_duckdb:.3f}秒")
    Logger.info(f"  - CSV直接: {time_csv:.3f}秒")
    Logger.info(f"  - 性能提升: {speedup:.2f}倍 ({improvement:.1f}%)")

    return df_csv

def test_parquet_saving(df):
    """测试Parquet保存性能"""
    Logger.section("测试3: Parquet保存性能对比")

    output_dir = "output/test_results"
    os.makedirs(output_dir, exist_ok=True)

    # 测试3.1: 默认保存
    Logger.info("测试3.1: 默认Parquet保存...")
    file1 = os.path.join(output_dir, "test_default.parquet")
    start = time.time()
    ResultSaver.save_to_parquet(df, file1, fast_mode=False)
    time_old = time.time() - start
    size1 = os.path.getsize(file1) / 1024 / 1024
    Logger.success(f"完成！耗时: {time_old:.3f}秒, 大小: {size1:.2f}MB")

    # 测试3.2: 快速保存（优化后）
    Logger.info("测试3.2: 快速Parquet保存（优化后）...")
    file2 = os.path.join(output_dir, "test_fast.parquet")
    start = time.time()
    ResultSaver.save_to_parquet(df, file2, fast_mode=True)
    time_new = time.time() - start
    size2 = os.path.getsize(file2) / 1024 / 1024
    Logger.success(f"完成！耗时: {time_new:.3f}秒, 大小: {size2:.2f}MB")

    # 计算提升
    speedup = time_old / time_new
    improvement = (time_old - time_new) / time_old * 100

    Logger.info(f"\n📊 优化2效果:")
    Logger.info(f"  - 优化前: {time_old:.3f}秒, {size1:.2f}MB")
    Logger.info(f"  - 优化后: {time_new:.3f}秒, {size2:.2f}MB")
    Logger.info(f"  - 性能提升: {speedup:.2f}倍 ({improvement:.1f}%)")

    # 清理测试文件
    try:
        os.remove(file1)
        os.remove(file2)
    except:
        pass

def main():
    """主测试流程"""
    Logger.section("🚀 快速性能测试 - 验证优化效果")

    print("\n" + "="*70)
    print("测试说明:")
    print("- 测试数据量: 100,000行")
    print("- 优化1: 只读15列 vs 读243列")
    print("- 优化2: 快速Parquet vs 默认Parquet")
    print("- 优化4: CSV直接读取 vs DuckDB读取")
    print("="*70 + "\n")

    try:
        # 测试1: 数据读取优化
        df, processor = test_reading_performance()

        # 测试2: CSV vs DuckDB
        df_csv = test_csv_vs_duckdb()

        # 测试3: Parquet保存优化
        test_parquet_saving(df)

        # 总结
        Logger.section("✅ 所有测试完成!")
        Logger.info("\n预期总体性能提升:")
        Logger.info("  - 数据读取: 快30-50%")
        Logger.info("  - 结果保存: 快40-60%")
        Logger.info("  - 总体流程: 快35-55%")
        Logger.info("\n建议:")
        Logger.info("  1. 使用 use_essential_columns=True（默认）")
        Logger.info("  2. 使用 read_csv_direct() 替代 read_data_polars()")
        Logger.info("  3. 使用 fast_mode=True 保存Parquet（默认）")

    except Exception as e:
        Logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    Logger.section("测试结束")

if __name__ == "__main__":
    main()
