"""
股票技术指标计算系统 - 命令行工具 (CLI)

提供便捷的命令行接口,用于:
- 单只股票处理
- 批量处理
- 数据库管理
- 性能测试
- 数据导出

作者: 胡树群
日期: 2026-01-01
版本: v1.0
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import argparse
import duckdb
from datetime import datetime
from typing import Optional, List

from core.utils import Logger, FileUtils
from core.data_processor import DataProcessor, IndicatorCalculator, ResultSaver
from scripts.batch_processor import BatchProcessor


class StockCLI:
    """股票技术指标计算系统 CLI"""

    def __init__(self):
        self.logger = Logger()
        self.version = "v1.0"

    def find_database(self, db_path: Optional[str] = None) -> Optional[str]:
        """
        查找数据库文件

        参数:
        db_path: 指定的数据库路径, None表示自动搜索

        返回:
        str: 数据库路径, 找不到返回None
        """
        if db_path and Path(db_path).exists():
            return db_path

        # 自动搜索数据库 - 尝试多个位置
        search_paths = [
            Path('data'),  # 相对于当前目录
            Path('../data'),  # 相对于src目录
            Path('D:/shixun/project/data'),  # 绝对路径
        ]

        for data_dir in search_paths:
            if data_dir.exists():
                db_files = list(data_dir.glob('stock_data_*.duckdb'))
                if db_files:
                    # 返回最新的数据库文件
                    latest_db = max(db_files, key=lambda p: p.stat().st_mtime)
                    return str(latest_db)

        return None

    def cmd_info(self, args):
        """显示系统信息"""
        self.logger.section("股票技术指标计算系统")
        print(f"版本: {self.version}")
        print(f"基于: Polars + DuckDB")
        print(f"技术指标数量: 63个")
        print()
        print("主要功能:")
        print("  - 单只股票技术指标计算")
        print("  - 批量股票处理")
        print("  - 高性能数据处理 (246万行/秒)")
        print("  - 多种输出格式 (Parquet, CSV)")
        print()
        print("使用 'python cli.py --help' 查看详细命令")

    def cmd_list_stocks(self, args):
        """列出所有股票"""
        db_path = self.find_database(args.db)
        if not db_path:
            self.logger.error("未找到数据库文件")
            return

        self.logger.info(f"数据库: {db_path}")

        conn = duckdb.connect(db_path, read_only=True)
        try:
            result = conn.execute("""
                SELECT 代码, 名称, COUNT(*) as 记录数
                FROM stock_data
                GROUP BY 代码, 名称
                ORDER BY 代码
            """).fetchall()

            total_stocks = len(result)
            self.logger.info(f"总共 {total_stocks} 只股票")

            if args.limit:
                result = result[:args.limit]
                print(f"\n显示前 {args.limit} 只股票:\n")
            else:
                print(f"\n所有股票列表:\n")

            print(f"{'代码':<10} {'名称':<20} {'记录数':>10}")
            print("-" * 45)
            for code, name, count in result:
                print(f"{code:<10} {name:<20} {count:>10,}")

            if args.limit and total_stocks > args.limit:
                print(f"\n... 还有 {total_stocks - args.limit} 只股票")

        finally:
            conn.close()

    def cmd_process_stock(self, args):
        """处理单只股票"""
        db_path = self.find_database(args.db)
        if not db_path:
            self.logger.error("未找到数据库文件")
            return

        self.logger.section(f"处理股票 {args.code}")

        # 创建数据处理器
        processor = DataProcessor(db_path)

        try:
            # 读取数据
            self.logger.info("读取股票数据...")
            df = processor.get_stock_data_polars(args.code)

            if df.height == 0:
                self.logger.error(f"股票 {args.code} 无数据")
                return

            self.logger.info(f"读取 {df.height} 行数据")

            # 计算指标
            self.logger.info("计算技术指标...")
            df_result = IndicatorCalculator.calculate_all_indicators_polars(df)

            self.logger.success(f"计算完成! 共 {df_result.width} 列 ({df_result.width - df.width} 个新指标)")

            # 保存结果
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            if args.format == 'parquet':
                output_file = output_dir / f"stock_{args.code}.parquet"
                ResultSaver.save_to_parquet(df_result, str(output_file))
            elif args.format == 'csv':
                output_file = output_dir / f"stock_{args.code}.csv"
                ResultSaver.save_to_csv(df_result, str(output_file))

            file_size = FileUtils.get_file_size(output_file)
            self.logger.success(f"结果已保存: {output_file}")
            self.logger.info(f"文件大小: {file_size['readable_size']}")

        finally:
            processor.disconnect()

    def cmd_batch_process(self, args):
        """批量处理股票"""
        db_path = self.find_database(args.db)
        if not db_path:
            self.logger.error("未找到数据库文件")
            return

        self.logger.section("批量股票处理")

        # 创建批量处理器
        processor = BatchProcessor(db_path, args.output)

        # 获取股票列表
        stock_list = processor.get_stock_list()

        if args.codes:
            # 处理指定的股票代码
            codes = [int(c) for c in args.codes.split(',')]
            stock_list = [(code, name) for code, name in stock_list if code in codes]
            self.logger.info(f"将处理 {len(stock_list)} 只指定股票")
        elif args.max:
            stock_list = stock_list[:args.max]
            self.logger.info(f"将处理前 {args.max} 只股票")

        if not stock_list:
            self.logger.error("没有可处理的股票")
            return

        # 执行批量处理
        if args.parallel:
            summary = processor.process_batch_parallel(
                stock_list=stock_list,
                save_format=args.format,
                max_workers=args.workers
            )
        else:
            summary = processor.process_batch_sequential(
                stock_list=stock_list,
                save_format=args.format
            )

        # 导出报告
        if args.report:
            processor.export_summary_report(summary, args.report)

    def cmd_db_info(self, args):
        """显示数据库信息"""
        db_path = self.find_database(args.db)
        if not db_path:
            self.logger.error("未找到数据库文件")
            return

        self.logger.section("数据库信息")

        db_file = Path(db_path)
        file_size = FileUtils.get_file_size(db_file)

        print(f"文件路径: {db_path}")
        print(f"文件大小: {file_size['readable_size']}")
        print(f"修改时间: {datetime.fromtimestamp(db_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        conn = duckdb.connect(db_path, read_only=True)
        try:
            # 表信息
            tables = conn.execute("SHOW TABLES").fetchall()
            print(f"数据表数量: {len(tables)}")
            print()

            # 股票数据统计
            result = conn.execute("""
                SELECT
                    COUNT(*) as 总记录数,
                    COUNT(DISTINCT 代码) as 股票数量,
                    MIN(日期) as 最早日期,
                    MAX(日期) as 最新日期
                FROM stock_data
            """).fetchone()

            total_rows, stock_count, min_date, max_date = result
            print("数据统计:")
            print(f"  总记录数: {total_rows:,} 行")
            print(f"  股票数量: {stock_count:,} 只")
            print(f"  日期范围: {min_date} ~ {max_date}")
            print()

            # 字段信息
            if args.verbose:
                columns = conn.execute("DESCRIBE stock_data").fetchall()
                print(f"字段数量: {len(columns)}")
                print()
                print("字段列表:")
                print(f"{'字段名':<30} {'类型':<20}")
                print("-" * 55)
                for col_name, col_type, *_ in columns:
                    print(f"{col_name:<30} {col_type:<20}")

        finally:
            conn.close()

    def cmd_export(self, args):
        """导出数据"""
        db_path = self.find_database(args.db)
        if not db_path:
            self.logger.error("未找到数据库文件")
            return

        self.logger.section("数据导出")

        processor = DataProcessor(db_path)

        try:
            # 读取数据
            if args.code:
                self.logger.info(f"导出股票 {args.code} 的数据...")
                df = processor.get_stock_data_polars(args.code)
            else:
                self.logger.info("导出全部数据...")
                df = processor.read_data_polars()

            if df.height == 0:
                self.logger.error("没有数据可导出")
                return

            self.logger.info(f"读取 {df.height:,} 行数据")

            # 计算指标(可选)
            if args.indicators:
                self.logger.info("计算技术指标...")
                df = IndicatorCalculator.calculate_all_indicators_polars(df)
                self.logger.success(f"计算完成! 共 {df.width} 列")

            # 导出
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if args.format == 'csv':
                df.write_csv(str(output_path))
            elif args.format == 'parquet':
                df.write_parquet(str(output_path), compression='snappy')
            elif args.format == 'excel':
                # Polars不直接支持Excel,需要转换
                df.to_pandas().to_excel(str(output_path), index=False)

            file_size = FileUtils.get_file_size(output_path)
            self.logger.success(f"导出完成: {output_path}")
            self.logger.info(f"文件大小: {file_size['readable_size']}")

        finally:
            processor.disconnect()

    def run(self):
        """运行CLI"""
        parser = argparse.ArgumentParser(
            description='股票技术指标计算系统 CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  # 显示系统信息
  python cli.py info

  # 列出所有股票
  python cli.py list --limit 10

  # 处理单只股票
  python cli.py process 1 -o output/results

  # 批量处理(串行)
  python cli.py batch --max 10 -o output/batch

  # 批量处理(并行)
  python cli.py batch --max 10 --parallel --workers 4

  # 显示数据库信息
  python cli.py db-info -v

  # 导出数据
  python cli.py export --code 1 --indicators -o output/stock_1.csv
            """
        )

        parser.add_argument('--version', action='version', version=f'%(prog)s {self.version}')

        # 子命令
        subparsers = parser.add_subparsers(dest='command', help='可用命令')

        # info命令
        parser_info = subparsers.add_parser('info', help='显示系统信息')

        # list命令
        parser_list = subparsers.add_parser('list', help='列出所有股票')
        parser_list.add_argument('--db', help='数据库路径')
        parser_list.add_argument('--limit', type=int, help='限制显示数量')

        # process命令
        parser_process = subparsers.add_parser('process', help='处理单只股票')
        parser_process.add_argument('code', type=int, help='股票代码')
        parser_process.add_argument('--db', help='数据库路径')
        parser_process.add_argument('-o', '--output', default='output/single', help='输出目录')
        parser_process.add_argument('-f', '--format', choices=['parquet', 'csv'],
                                   default='parquet', help='输出格式')

        # batch命令
        parser_batch = subparsers.add_parser('batch', help='批量处理股票')
        parser_batch.add_argument('--db', help='数据库路径')
        parser_batch.add_argument('-o', '--output', default='output/batch', help='输出目录')
        parser_batch.add_argument('-f', '--format', choices=['parquet', 'csv'],
                                 default='parquet', help='输出格式')
        parser_batch.add_argument('--max', type=int, help='最大处理数量')
        parser_batch.add_argument('--codes', help='指定股票代码(逗号分隔)')
        parser_batch.add_argument('--parallel', action='store_true', help='启用并行处理')
        parser_batch.add_argument('--workers', type=int, help='并行worker数量')
        parser_batch.add_argument('--report', help='汇总报告输出路径')

        # db-info命令
        parser_db = subparsers.add_parser('db-info', help='显示数据库信息')
        parser_db.add_argument('--db', help='数据库路径')
        parser_db.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')

        # export命令
        parser_export = subparsers.add_parser('export', help='导出数据')
        parser_export.add_argument('--db', help='数据库路径')
        parser_export.add_argument('--code', type=int, help='股票代码(不指定则导出全部)')
        parser_export.add_argument('-o', '--output', required=True, help='输出文件路径')
        parser_export.add_argument('-f', '--format', choices=['csv', 'parquet', 'excel'],
                                   default='csv', help='输出格式')
        parser_export.add_argument('--indicators', action='store_true', help='计算技术指标')

        # 解析参数
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        # 执行命令
        command_map = {
            'info': self.cmd_info,
            'list': self.cmd_list_stocks,
            'process': self.cmd_process_stock,
            'batch': self.cmd_batch_process,
            'db-info': self.cmd_db_info,
            'export': self.cmd_export,
        }

        if args.command in command_map:
            command_map[args.command](args)
        else:
            parser.print_help()


def main():
    """主函数"""
    cli = StockCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
