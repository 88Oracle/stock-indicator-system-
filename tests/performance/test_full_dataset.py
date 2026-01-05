"""
完整数据集 pytest 测试
功能：使用 pytest 测试完整数据集处理
作者：AI Assistant
日期：2025-01-01
"""

import pytest
import polars as pl
import time
import os
from datetime import datetime

from core.utils import Logger, FileUtils
from core.data_processor import DataProcessor, IndicatorCalculator, ResultSaver


@pytest.fixture
def db_path():
    """获取数据库路径"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(script_dir, "data")

    db_files = [f for f in os.listdir(data_dir) if f.endswith('.duckdb')]

    if not db_files:
        pytest.skip("未找到数据库文件")

    db_file = sorted(db_files)[-1]
    return os.path.join(data_dir, db_file)


@pytest.fixture
def processor(db_path):
    """创建数据处理器"""
    proc = DataProcessor(db_path)
    yield proc
    proc.disconnect()


@pytest.fixture
def output_dir():
    """创建输出目录"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(script_dir, "output", "results", "test")
    FileUtils.ensure_dir(out_dir)
    return out_dir


def test_polars_small_sample(processor, output_dir):
    """测试 Polars 处理小样本数据（1000行）"""
    Logger.section("Polars 小样本测试 (1000行)")

    # 读取数据
    df = processor.read_data_polars(limit=1000)
    assert len(df) == 1000
    assert len(df.columns) == 243

    # 计算指标
    df_result = IndicatorCalculator.calculate_all_indicators_polars(df)
    assert len(df_result) == 1000
    assert len(df_result.columns) > len(df.columns)

    new_indicators = len(df_result.columns) - len(df.columns)
    Logger.success(f"成功计算 {new_indicators} 个指标")

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"test_small_{timestamp}.csv")
    ResultSaver.save_to_csv(df_result, output_file)

    assert os.path.exists(output_file)
    Logger.success(f"结果已保存: {output_file}")


def test_polars_medium_sample(processor, output_dir):
    """测试 Polars 处理中等样本数据（10000行）"""
    Logger.section("Polars 中等样本测试 (10000行)")

    # 读取数据
    df = processor.read_data_polars(limit=10000)
    assert len(df) == 10000

    # 计算指标
    start_time = time.time()
    df_result = IndicatorCalculator.calculate_all_indicators_polars(df)
    calc_time = time.time() - start_time

    assert len(df_result) == 10000

    speed = len(df) / calc_time
    Logger.success(f"处理速度: {speed:,.0f} 行/秒")

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"test_medium_{timestamp}.parquet")
    ResultSaver.save_to_parquet(df_result, output_file)

    assert os.path.exists(output_file)


@pytest.mark.slow
def test_polars_large_sample(processor, output_dir):
    """测试 Polars 处理大样本数据（100000行）"""
    Logger.section("Polars 大样本测试 (100000行)")

    # 读取数据
    df = processor.read_data_polars(limit=100000)
    assert len(df) == 100000

    # 计算指标
    start_time = time.time()
    df_result = IndicatorCalculator.calculate_all_indicators_polars(df)
    calc_time = time.time() - start_time

    assert len(df_result) == 100000

    speed = len(df) / calc_time
    Logger.success(f"处理速度: {speed:,.0f} 行/秒")
    Logger.info(f"计算耗时: {calc_time:.2f} 秒")

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"test_large_{timestamp}.parquet")
    ResultSaver.save_to_parquet(df_result, output_file)

    assert os.path.exists(output_file)


@pytest.mark.slow
@pytest.mark.full
def test_polars_full_dataset(processor, output_dir):
    """测试 Polars 处理完整数据集（所有数据）"""
    Logger.section("Polars 完整数据集测试")

    # 读取数据
    Logger.info("读取完整数据集...")
    read_start = time.time()
    df = processor.read_data_polars()
    read_time = time.time() - read_start

    Logger.success(f"读取完成: {len(df):,} 行，耗时 {read_time:.2f} 秒")

    # 计算指标
    Logger.info("计算技术指标...")
    calc_start = time.time()
    df_result = IndicatorCalculator.calculate_all_indicators_polars(df)
    calc_time = time.time() - calc_start

    speed = len(df) / calc_time
    Logger.success(f"计算完成: {speed:,.0f} 行/秒，耗时 {calc_time:.2f} 秒")

    # 保存结果
    Logger.info("保存结果...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"test_full_{timestamp}.parquet")

    save_start = time.time()
    ResultSaver.save_to_parquet(df_result, output_file)
    save_time = time.time() - save_start

    Logger.success(f"保存完成: 耗时 {save_time:.2f} 秒")

    # 统计
    total_time = read_time + calc_time + save_time
    file_size = os.path.getsize(output_file) / 1024 / 1024

    Logger.section("测试结果")
    print(f"\n数据规模: {len(df):,} 行 x {len(df_result.columns)} 列")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"  - 读取: {read_time:.2f} 秒")
    print(f"  - 计算: {calc_time:.2f} 秒")
    print(f"  - 保存: {save_time:.2f} 秒")
    print(f"处理速度: {len(df) / calc_time:,.0f} 行/秒")
    print(f"输出文件: {output_file}")
    print(f"文件大小: {file_size:.2f} MB")

    assert os.path.exists(output_file)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
