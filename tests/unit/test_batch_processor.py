"""
批量处理工具测试脚本

测试批量处理器的各种功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到路径 - 确保在所有导入之前
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 项目模块导入
from batch_processor import BatchProcessor  # noqa
from core.utils import Logger  # noqa


def test_batch_processor():
    """测试批量处理器"""
    logger = Logger()
    logger.section("批量处理工具测试")

    # 查找数据库文件
    data_dir = Path('D:/shixun/project/data')
    db_files = list(data_dir.glob('stock_data_*.duckdb'))

    if not db_files:
        logger.error("未找到数据库文件")
        return

    db_path = str(db_files[0])
    logger.info(f"使用数据库: {db_path}")

    # 创建批量处理器
    processor = BatchProcessor(db_path, 'output/batch_test')

    # 测试1: 获取股票列表
    logger.section("测试1: 获取股票列表")
    stock_list = processor.get_stock_list()
    logger.info(f"总共 {len(stock_list)} 只股票")

    if stock_list:
        logger.info("前10只股票:")
        for i, (code, name) in enumerate(stock_list[:10], 1):
            logger.info(f"  {i}. {code} - {name}")

    # 测试2: 处理单只股票
    logger.section("测试2: 处理单只股票")
    if stock_list:
        test_code, test_name = stock_list[0]
        logger.info(f"测试股票: {test_code} ({test_name})")

        result = processor.process_single_stock(test_code, test_name, 'parquet')

        if result['status'] == 'success':
            logger.success("✓ 单股票处理成功")
            logger.info(f"  行数: {result['rows']:,}")
            logger.info(f"  列数: {result['columns']}")
            logger.info(f"  耗时: {result['time']:.2f}秒")
            logger.info(f"  输出: {result['output_file']}")
            logger.info(f"  大小: {result['file_size']}")
        else:
            logger.error(f"✗ 处理失败: {result.get('error', '未知错误')}")

    # 测试3: 串行批量处理(前5只)
    logger.section("测试3: 串行批量处理 (前5只)")
    summary_seq = processor.process_batch_sequential(
        stock_list=stock_list[:5],
        save_format='parquet'
    )

    # 测试4: 并行批量处理(前5只)
    logger.section("测试4: 并行批量处理 (前5只)")
    summary_par = processor.process_batch_parallel(
        stock_list=stock_list[:5],
        save_format='parquet',
        max_workers=2
    )

    # 对比结果
    logger.section("性能对比")
    logger.info(f"串行模式耗时: {summary_seq['total_time']:.2f}秒")
    logger.info(f"并行模式耗时: {summary_par['total_time']:.2f}秒")

    if summary_par['total_time'] > 0:
        speedup = summary_seq['total_time'] / summary_par['total_time']
        logger.info(f"并行加速比: {speedup:.2f}x")

    # 导出报告
    logger.section("导出报告")
    processor.export_summary_report(summary_seq, 'output/batch_test/summary_sequential.txt')
    processor.export_summary_report(summary_par, 'output/batch_test/summary_parallel.txt')

    logger.section("测试完成")


if __name__ == '__main__':
    test_batch_processor()
