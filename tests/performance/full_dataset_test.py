"""
完整数据集处理测试
功能：处理全部116万行数据，测试真实性能
# 运行单个测试
  pytest src/full_dataset_test.py::test_polars_only -v -s      # 仅测试 Polars
  pytest src/full_dataset_test.py::test_pandas_only -v -s      # 仅测试 Pandas
  pytest src/full_dataset_test.py::test_comparison -v -s       # 对比测试

  # 运行所有测试
  pytest src/full_dataset_test.py -v -s

作者：shuqun
日期：2025-01-03
"""

import polars as pl
import pandas as pd
import time
import psutil
import os
import sys
from datetime import datetime

# 添加src目录到路径（回退两级到达 src 目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import Logger, PerformanceMonitor, FileUtils
from core.data_processor import DataProcessor, IndicatorCalculator, ResultSaver


class FullDatasetTest:
    """完整数据集测试类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.processor = DataProcessor(db_path)
        self.process = psutil.Process()

    def get_memory_mb(self) -> float:
        """获取当前内存占用（MB）"""
        return self.process.memory_info().rss / 1024 / 1024

    def test_polars_full_dataset(self):
        """测试Polars处理完整数据集"""
        Logger.section("Polars 完整数据集处理")

        start_time = time.time()
        start_memory = self.get_memory_mb()

        # 1. 读取数据
        Logger.info("步骤 1/3：读取数据...")
        read_start = time.time()
        df = self.processor.read_data_polars()
        read_time = time.time() - read_start

        Logger.success(f"读取完成：{len(df):,} 行, {len(df.columns)} 列，耗时 {read_time:.2f} 秒")

        # 2. 计算指标
        Logger.info("步骤 2/3：计算技术指标...")
        calc_start = time.time()
        df_result = IndicatorCalculator.calculate_all_indicators_polars(df)
        calc_time = time.time() - calc_start

        Logger.success(f"计算完成：新增 {len(df_result.columns) - len(df.columns)} 个指标，耗时 {calc_time:.2f} 秒")

        # 3. 保存结果
        Logger.info("步骤 3/3：保存结果...")
        # 回退到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(project_root, "output", "results")
        FileUtils.ensure_dir(output_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"full_dataset_polars_{timestamp}.parquet")

        save_start = time.time()
        ResultSaver.save_to_parquet(df_result, output_file)
        save_time = time.time() - save_start

        # 总结
        end_time = time.time()
        end_memory = self.get_memory_mb()

        total_time = end_time - start_time
        memory_used = end_memory - start_memory

        result = {
            'framework': 'Polars',
            'rows': len(df),
            'initial_columns': len(df.columns),
            'final_columns': len(df_result.columns),
            'new_indicators': len(df_result.columns) - len(df.columns),
            'read_time': read_time,
            'calc_time': calc_time,
            'save_time': save_time,
            'total_time': total_time,
            'memory_used_mb': memory_used,
            'rows_per_second': len(df) / calc_time if calc_time > 0 else 0,
            'output_file': output_file
        }

        Logger.section("Polars 性能统计")
        print(f"\n数据规模：")
        print(f"  - 总行数：{result['rows']:,}")
        print(f"  - 初始列数：{result['initial_columns']}")
        print(f"  - 最终列数：{result['final_columns']}")
        print(f"  - 新增指标：{result['new_indicators']}")

        print(f"\n时间统计：")
        print(f"  - 数据读取：{read_time:.2f} 秒 ({result['rows']/read_time:,.0f} 行/秒)")
        print(f"  - 指标计算：{calc_time:.2f} 秒 ({result['rows_per_second']:,.0f} 行/秒)")
        print(f"  - 结果保存：{save_time:.2f} 秒")
        print(f"  - 总耗时：{total_time:.2f} 秒")

        print(f"\n内存统计：")
        print(f"  - 内存增量：{memory_used:.2f} MB")
        print(f"  - 最终内存：{end_memory:.2f} MB")

        print(f"\n输出文件：")
        print(f"  - {output_file}")
        print(f"  - 大小：{os.path.getsize(output_file) / 1024 / 1024:.2f} MB")

        return result

    def test_pandas_full_dataset(self):
        """测试Pandas处理完整数据集"""
        Logger.section("Pandas 完整数据集处理")

        start_time = time.time()
        start_memory = self.get_memory_mb()

        # 1. 读取数据
        Logger.info("步骤 1/3：读取数据...")
        read_start = time.time()
        df = self.processor.read_data_pandas()
        read_time = time.time() - read_start

        Logger.success(f"读取完成：{len(df):,} 行, {len(df.columns)} 列，耗时 {read_time:.2f} 秒")

        # 2. 计算指标（通过Polars）
        Logger.info("步骤 2/3：计算技术指标...")
        calc_start = time.time()
        df_result = IndicatorCalculator.calculate_all_indicators_pandas(df)
        calc_time = time.time() - calc_start

        Logger.success(f"计算完成：新增 {len(df_result.columns) - len(df.columns)} 个指标，耗时 {calc_time:.2f} 秒")

        # 3. 保存结果
        Logger.info("步骤 3/3：保存结果...")
        # 回退到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(project_root, "output", "results")
        FileUtils.ensure_dir(output_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"full_dataset_pandas_{timestamp}.parquet")

        save_start = time.time()
        ResultSaver.save_to_parquet(df_result, output_file)
        save_time = time.time() - save_start

        # 总结
        end_time = time.time()
        end_memory = self.get_memory_mb()

        total_time = end_time - start_time
        memory_used = end_memory - start_memory

        result = {
            'framework': 'Pandas',
            'rows': len(df),
            'initial_columns': len(df.columns),
            'final_columns': len(df_result.columns),
            'new_indicators': len(df_result.columns) - len(df.columns),
            'read_time': read_time,
            'calc_time': calc_time,
            'save_time': save_time,
            'total_time': total_time,
            'memory_used_mb': memory_used,
            'rows_per_second': len(df) / calc_time if calc_time > 0 else 0,
            'output_file': output_file
        }

        Logger.section("Pandas 性能统计")
        print(f"\n数据规模：")
        print(f"  - 总行数：{result['rows']:,}")
        print(f"  - 初始列数：{result['initial_columns']}")
        print(f"  - 最终列数：{result['final_columns']}")
        print(f"  - 新增指标：{result['new_indicators']}")

        print(f"\n时间统计：")
        print(f"  - 数据读取：{read_time:.2f} 秒 ({result['rows']/read_time:,.0f} 行/秒)")
        print(f"  - 指标计算：{calc_time:.2f} 秒 ({result['rows_per_second']:,.0f} 行/秒)")
        print(f"  - 结果保存：{save_time:.2f} 秒")
        print(f"  - 总耗时：{total_time:.2f} 秒")

        print(f"\n内存统计：")
        print(f"  - 内存增量：{memory_used:.2f} MB")
        print(f"  - 最终内存：{end_memory:.2f} MB")

        print(f"\n输出文件：")
        print(f"  - {output_file}")
        print(f"  - 大小：{os.path.getsize(output_file) / 1024 / 1024:.2f} MB")

        return result

    def compare_results(self, polars_result, pandas_result):
        """对比两个框架的结果"""
        Logger.section("性能对比结果")

        # 计算加速比
        read_speedup = pandas_result['read_time'] / polars_result['read_time']
        calc_speedup = pandas_result['calc_time'] / polars_result['calc_time']
        total_speedup = pandas_result['total_time'] / polars_result['total_time']

        print("\n" + "="*120)
        print(f"{'指标':<30} {'Polars':<30} {'Pandas':<30} {'加速比':<30}")
        print("="*120)
        print(f"{'数据规模':<30} {polars_result['rows']:<30,} {pandas_result['rows']:<30,} {'-':<30}")
        print(f"{'计算指标数':<30} {polars_result['new_indicators']:<30} {pandas_result['new_indicators']:<30} {'-':<30}")
        print("-"*120)
        print(f"{'数据读取时间(秒)':<30} {polars_result['read_time']:<30.2f} {pandas_result['read_time']:<30.2f} {f'{read_speedup:.2f}x 更快':<30}")
        print(f"{'指标计算时间(秒)':<30} {polars_result['calc_time']:<30.2f} {pandas_result['calc_time']:<30.2f} {f'{calc_speedup:.2f}x 更快':<30}")
        print(f"{'结果保存时间(秒)':<30} {polars_result['save_time']:<30.2f} {pandas_result['save_time']:<30.2f} {'-':<30}")
        print(f"{'总执行时间(秒)':<30} {polars_result['total_time']:<30.2f} {pandas_result['total_time']:<30.2f} {f'{total_speedup:.2f}x 更快':<30}")
        print("-"*120)
        print(f"{'内存使用(MB)':<30} {polars_result['memory_used_mb']:<30.2f} {pandas_result['memory_used_mb']:<30.2f} {'-':<30}")
        print(f"{'处理速度(行/秒)':<30} {polars_result['rows_per_second']:<30,.0f} {pandas_result['rows_per_second']:<30,.0f} {'-':<30}")
        print("="*120)

        print(f"\n性能总结：")
        print(f"  - 数据读取：Polars 比 Pandas 快 {read_speedup:.2f} 倍")
        print(f"  - 指标计算：Polars 比 Pandas 快 {calc_speedup:.2f} 倍")
        print(f"  - 总体性能：Polars 比 Pandas 快 {total_speedup:.2f} 倍")

        if total_speedup >= 60:
            print(f"\n  ✓ 已达到 60-80 倍性能目标！🎉")
        elif total_speedup >= 10:
            print(f"\n  ✓ 性能提升显著（{total_speedup:.1f}倍），但未达到 60-80 倍目标")
        elif total_speedup >= 2:
            print(f"\n  ✓ 有明显性能提升（{total_speedup:.1f}倍）")
        else:
            print(f"\n  ⚠️ 性能提升不明显，需要进一步优化")

        print("="*120)

        return {
            'read_speedup': read_speedup,
            'calc_speedup': calc_speedup,
            'total_speedup': total_speedup
        }


def _get_db_path():
    """获取数据库路径的辅助函数"""
    # 回退到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(project_root, "data")
    db_files = [f for f in os.listdir(data_dir) if f.endswith('.duckdb')]

    if not db_files:
        raise FileNotFoundError("未找到数据库文件")

    db_file = sorted(db_files)[-1]
    return os.path.join(data_dir, db_file)


def test_polars_only():
    """测试1：仅测试Polars"""
    Logger.section("测试模式 1: 仅测试 Polars")

    db_path = _get_db_path()
    Logger.info(f"数据库: {os.path.basename(db_path)}")

    tester = FullDatasetTest(db_path)
    polars_result = tester.test_polars_full_dataset()
    tester.processor.disconnect()

    Logger.section("测试完成！")
    assert polars_result is not None
    assert polars_result['rows'] > 0


def test_pandas_only():
    """测试2：仅测试Pandas"""
    Logger.section("测试模式 2: 仅测试 Pandas")

    db_path = _get_db_path()
    Logger.info(f"数据库: {os.path.basename(db_path)}")

    tester = FullDatasetTest(db_path)
    pandas_result = tester.test_pandas_full_dataset()
    tester.processor.disconnect()

    Logger.section("测试完成！")
    assert pandas_result is not None
    assert pandas_result['rows'] > 0


def test_comparison():
    """测试3：对比测试（Polars vs Pandas）"""
    Logger.section("测试模式 3: 对比测试")

    db_path = _get_db_path()
    Logger.info(f"数据库: {os.path.basename(db_path)}")
    Logger.info("将依次进行 Polars 和 Pandas 测试，请耐心等待...\n")

    tester = FullDatasetTest(db_path)

    # Polars 测试
    polars_result = tester.test_polars_full_dataset()
    print("\n" + "="*80 + "\n")

    # Pandas 测试
    pandas_result = tester.test_pandas_full_dataset()

    # 对比结果
    comparison = tester.compare_results(polars_result, pandas_result)

    tester.processor.disconnect()
    Logger.section("对比测试完成！")

    assert comparison is not None
    assert comparison['total_speedup'] > 0


def main():
    """交互式主函数（用于直接运行脚本）"""
    # 配置路径（回退到项目根目录）
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(project_root, "data")

    # 查找数据库文件
    db_files = [f for f in os.listdir(data_dir) if f.endswith('.duckdb')]

    if not db_files:
        Logger.error("未找到数据库文件！")
        return

    db_file = sorted(db_files)[-1]
    db_path = os.path.join(data_dir, db_file)

    Logger.section("完整数据集性能测试")
    Logger.info(f"数据库文件: {db_file}")

    # 创建测试器
    tester = FullDatasetTest(db_path)

    # 显示测试选项
    print("\n" + "="*80)
    print("请选择测试模式：")
    print("  1. 仅测试 Polars（推荐）")
    print("  2. 仅测试 Pandas")
    print("  3. 对比测试（Polars vs Pandas）")
    print("="*80)

    choice = input("\n请输入选项 (1-3): ").strip()

    if choice == '1':
        # 只测试 Polars
        polars_result = tester.test_polars_full_dataset()
        Logger.section("测试完成！")

    elif choice == '2':
        # 只测试 Pandas
        pandas_result = tester.test_pandas_full_dataset()
        Logger.section("测试完成！")

    elif choice == '3':
        # 对比测试
        Logger.info("将依次进行 Polars 和 Pandas 测试，请耐心等待...\n")

        # Polars 测试
        polars_result = tester.test_polars_full_dataset()

        print("\n" + "="*80 + "\n")

        # Pandas 测试
        pandas_result = tester.test_pandas_full_dataset()

        # 对比结果
        comparison = tester.compare_results(polars_result, pandas_result)

        Logger.section("对比测试完成！")

    else:
        Logger.error("无效的选项")
        return

    # 断开连接
    tester.processor.disconnect()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已被用户中断")
        sys.exit(0)
    except Exception as e:
        Logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
