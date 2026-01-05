"""
批量股票处理工具

功能:
- 批量处理多只股票的技术指标计算
- 支持并行和串行两种模式
- 提供进度跟踪和错误处理
- 支持多种输出格式

"""

import polars as pl
import duckdb
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp

from core.utils import Logger, PerformanceMonitor, FileUtils
from core.data_processor import IndicatorCalculator


class BatchProcessor:
    """批量股票处理器"""

    def __init__(self, db_path: str, output_dir: str = 'output/batch_results'):
        """
        初始化批量处理器

        参数:
        db_path: DuckDB数据库路径
        output_dir: 输出目录
        """
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = Logger()
        self.monitor = PerformanceMonitor()

    def get_stock_list(self) -> List[Tuple[int, str]]:
        """
        获取数据库中所有股票列表

        返回:
        List[Tuple[int, str]]: [(股票代码, 股票名称), ...]
        """
        conn = duckdb.connect(self.db_path, read_only=True)
        try:
            # 查询所有不同的股票代码和名称
            result = conn.execute("""
                SELECT DISTINCT 代码, 名称
                FROM stock_data
                ORDER BY 代码
            """).fetchall()

            self.logger.info(f"找到 {len(result)} 只股票")
            return result
        finally:
            conn.close()

    def get_stock_data(self, stock_code: int) -> pl.DataFrame:
        """
        获取单只股票的数据

        参数:
        stock_code: 股票代码

        返回:
        pl.DataFrame: 股票数据
        """
        conn = duckdb.connect(self.db_path, read_only=True)
        try:
            query = f"""
                SELECT *
                FROM stock_data
                WHERE 代码 = {stock_code}
                ORDER BY 日期
            """
            return conn.execute(query).pl()
        finally:
            conn.close()

    def process_single_stock(self, stock_code: int, stock_name: str,
                           save_format: str = 'parquet') -> Dict:
        """
        处理单只股票

        参数:
        stock_code: 股票代码
        stock_name: 股票名称
        save_format: 保存格式 ('parquet', 'csv')

        返回:
        Dict: 处理结果统计
        """
        start_time = time.time()

        try:
            # 读取数据
            df = self.get_stock_data(stock_code)

            if df.height == 0:
                return {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'status': 'skipped',
                    'reason': '无数据',
                    'rows': 0,
                    'time': 0
                }

            # 计算指标
            df_result = IndicatorCalculator.calculate_all_indicators_polars(df)

            # 保存结果
            if save_format == 'parquet':
                output_file = self.output_dir / f"stock_{stock_code}_{stock_name}.parquet"
                df_result.write_parquet(output_file, compression='snappy')
            elif save_format == 'csv':
                output_file = self.output_dir / f"stock_{stock_code}_{stock_name}.csv"
                df_result.write_csv(output_file)
            else:
                raise ValueError(f"不支持的格式: {save_format}")

            elapsed = time.time() - start_time

            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'status': 'success',
                'rows': df_result.height,
                'columns': df_result.width,
                'time': elapsed,
                'output_file': str(output_file),
                'file_size': FileUtils.get_file_size(output_file)
            }

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"处理股票 {stock_code} ({stock_name}) 失败: {str(e)}")

            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'status': 'failed',
                'error': str(e),
                'time': elapsed
            }

    def process_batch_sequential(self, stock_list: Optional[List[Tuple[int, str]]] = None,
                                save_format: str = 'parquet',
                                max_stocks: Optional[int] = None) -> Dict:
        """
        串行批量处理股票

        参数:
        stock_list: 股票列表 [(代码, 名称), ...], None表示处理全部
        save_format: 保存格式
        max_stocks: 最大处理数量, None表示全部

        返回:
        Dict: 批量处理结果统计
        """
        self.logger.section("开始串行批量处理")

        # 获取股票列表
        if stock_list is None:
            stock_list = self.get_stock_list()

        if max_stocks:
            stock_list = stock_list[:max_stocks]

        total_stocks = len(stock_list)
        self.logger.info(f"准备处理 {total_stocks} 只股票")

        # 处理统计
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0
        total_rows = 0
        total_time = 0

        start_time = time.time()

        # 逐个处理
        for i, (stock_code, stock_name) in enumerate(stock_list, 1):
            self.logger.info(f"[{i}/{total_stocks}] 处理 {stock_code} ({stock_name})...")

            result = self.process_single_stock(stock_code, stock_name, save_format)
            results.append(result)

            if result['status'] == 'success':
                success_count += 1
                total_rows += result['rows']
                self.logger.success(
                    f"✓ {stock_code} ({stock_name}): "
                    f"{result['rows']} 行, {result['time']:.2f}秒"
                )
            elif result['status'] == 'failed':
                failed_count += 1
                self.logger.error(f"✗ {stock_code} ({stock_name}): {result.get('error', '未知错误')}")
            else:
                skipped_count += 1

        elapsed = time.time() - start_time

        # 汇总统计
        summary = {
            'mode': 'sequential',
            'total_stocks': total_stocks,
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'total_rows': total_rows,
            'total_time': elapsed,
            'avg_time_per_stock': elapsed / total_stocks if total_stocks > 0 else 0,
            'results': results
        }

        # 打印汇总
        self.logger.section("批量处理完成")
        self.logger.info(f"总股票数: {total_stocks}")
        self.logger.info(f"成功: {success_count} ({success_count/total_stocks*100:.1f}%)")
        self.logger.info(f"失败: {failed_count}")
        self.logger.info(f"跳过: {skipped_count}")
        self.logger.info(f"总数据行数: {total_rows:,}")
        self.logger.info(f"总耗时: {elapsed:.2f}秒")
        self.logger.info(f"平均每只股票: {summary['avg_time_per_stock']:.2f}秒")

        return summary

    def process_batch_parallel(self, stock_list: Optional[List[Tuple[int, str]]] = None,
                              save_format: str = 'parquet',
                              max_stocks: Optional[int] = None,
                              max_workers: Optional[int] = None) -> Dict:
        """
        并行批量处理股票

        参数:
        stock_list: 股票列表
        save_format: 保存格式
        max_stocks: 最大处理数量
        max_workers: 最大并行worker数, None表示自动选择

        返回:
        Dict: 批量处理结果统计
        """
        self.logger.section("开始并行批量处理")

        # 获取股票列表
        if stock_list is None:
            stock_list = self.get_stock_list()

        if max_stocks:
            stock_list = stock_list[:max_stocks]

        total_stocks = len(stock_list)

        # 确定worker数量
        if max_workers is None:
            max_workers = min(mp.cpu_count(), 4)  # 默认最多4个进程

        self.logger.info(f"准备处理 {total_stocks} 只股票")
        self.logger.info(f"并行度: {max_workers} workers")

        # 处理统计
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0
        total_rows = 0

        start_time = time.time()

        # 使用进程池并行处理
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_stock = {
                executor.submit(
                    self.process_single_stock,
                    stock_code,
                    stock_name,
                    save_format
                ): (stock_code, stock_name)
                for stock_code, stock_name in stock_list
            }

            # 收集结果
            completed = 0
            for future in as_completed(future_to_stock):
                completed += 1
                stock_code, stock_name = future_to_stock[future]

                try:
                    result = future.result()
                    results.append(result)

                    if result['status'] == 'success':
                        success_count += 1
                        total_rows += result['rows']
                        self.logger.success(
                            f"[{completed}/{total_stocks}] ✓ {stock_code} ({stock_name}): "
                            f"{result['rows']} 行, {result['time']:.2f}秒"
                        )
                    elif result['status'] == 'failed':
                        failed_count += 1
                        self.logger.error(
                            f"[{completed}/{total_stocks}] ✗ {stock_code} ({stock_name}): "
                            f"{result.get('error', '未知错误')}"
                        )
                    else:
                        skipped_count += 1

                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"[{completed}/{total_stocks}] ✗ {stock_code} ({stock_name}): {str(e)}")
                    results.append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'status': 'failed',
                        'error': str(e)
                    })

        elapsed = time.time() - start_time

        # 汇总统计
        summary = {
            'mode': 'parallel',
            'total_stocks': total_stocks,
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'total_rows': total_rows,
            'total_time': elapsed,
            'avg_time_per_stock': elapsed / total_stocks if total_stocks > 0 else 0,
            'max_workers': max_workers,
            'results': results
        }

        # 打印汇总
        self.logger.section("批量处理完成")
        self.logger.info(f"总股票数: {total_stocks}")
        self.logger.info(f"成功: {success_count} ({success_count/total_stocks*100:.1f}%)")
        self.logger.info(f"失败: {failed_count}")
        self.logger.info(f"跳过: {skipped_count}")
        self.logger.info(f"总数据行数: {total_rows:,}")
        self.logger.info(f"总耗时: {elapsed:.2f}秒")
        self.logger.info(f"平均每只股票: {summary['avg_time_per_stock']:.2f}秒")
        self.logger.info(f"并行加速比: {total_stocks * summary['avg_time_per_stock'] / elapsed:.2f}x")

        return summary

    def export_summary_report(self, summary: Dict, output_file: Optional[str] = None):
        """
        导出批量处理汇总报告

        参数:
        summary: 处理结果汇总
        output_file: 输出文件路径, None表示自动生成
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.output_dir / f"batch_summary_{timestamp}.txt"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("批量股票处理报告\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"处理模式: {summary['mode']}\n")
            f.write(f"总股票数: {summary['total_stocks']}\n")
            f.write(f"成功: {summary['success']}\n")
            f.write(f"失败: {summary['failed']}\n")
            f.write(f"跳过: {summary['skipped']}\n")
            f.write(f"总数据行数: {summary['total_rows']:,}\n")
            f.write(f"总耗时: {summary['total_time']:.2f}秒\n")
            f.write(f"平均每只股票: {summary['avg_time_per_stock']:.2f}秒\n")

            if summary['mode'] == 'parallel':
                f.write(f"并行度: {summary['max_workers']} workers\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("详细结果\n")
            f.write("=" * 80 + "\n\n")

            for result in summary['results']:
                f.write(f"股票代码: {result['stock_code']}\n")
                f.write(f"股票名称: {result['stock_name']}\n")
                f.write(f"状态: {result['status']}\n")

                if result['status'] == 'success':
                    f.write(f"行数: {result['rows']:,}\n")
                    f.write(f"列数: {result['columns']}\n")
                    f.write(f"耗时: {result['time']:.2f}秒\n")
                    f.write(f"输出文件: {result['output_file']}\n")
                    f.write(f"文件大小: {result['file_size']}\n")
                elif result['status'] == 'failed':
                    f.write(f"错误: {result.get('error', '未知错误')}\n")
                elif result['status'] == 'skipped':
                    f.write(f"原因: {result.get('reason', '未知')}\n")

                f.write("\n" + "-" * 80 + "\n\n")

        self.logger.info(f"汇总报告已保存: {output_file}")


def main():
    """主函数 - 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description='批量股票处理工具')
    parser.add_argument('db_path', help='DuckDB数据库路径')
    parser.add_argument('--output', '-o', default='output/batch_results',
                       help='输出目录 (默认: output/batch_results)')
    parser.add_argument('--format', '-f', choices=['parquet', 'csv'],
                       default='parquet', help='输出格式 (默认: parquet)')
    parser.add_argument('--mode', '-m', choices=['sequential', 'parallel'],
                       default='sequential', help='处理模式 (默认: sequential)')
    parser.add_argument('--workers', '-w', type=int, default=None,
                       help='并行worker数 (仅parallel模式, 默认: 自动)')
    parser.add_argument('--max-stocks', '-n', type=int, default=None,
                       help='最大处理股票数 (默认: 全部)')

    args = parser.parse_args()

    # 创建批量处理器
    processor = BatchProcessor(args.db_path, args.output)

    # 执行批量处理
    if args.mode == 'sequential':
        summary = processor.process_batch_sequential(
            save_format=args.format,
            max_stocks=args.max_stocks
        )
    else:
        summary = processor.process_batch_parallel(
            save_format=args.format,
            max_stocks=args.max_stocks,
            max_workers=args.workers
        )

    # 导出报告
    processor.export_summary_report(summary)


if __name__ == '__main__':
    main()
