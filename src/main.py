"""
主程序
功能：在真实数据集上计算所有技术指标
作者：胡树群
日期：2025-01-02
"""

import polars as pl
import os
import sys
import time
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import Logger, PerformanceMonitor, FileUtils
from core.data_processor import DataProcessor, IndicatorCalculator, ResultSaver


def main():
    """主函数"""
    Logger.section("股票技术指标计算系统 v1.0")

    # 配置路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(script_dir, "data")
    output_dir = os.path.join(script_dir, "output", "results")

    # 确保输出目录存在
    FileUtils.ensure_dir(output_dir)

    # 查找数据库文件
    db_files = [f for f in os.listdir(data_dir) if f.endswith('.duckdb')]

    if not db_files:
        Logger.error("未找到数据库文件！请先运行 import_data.py")
        return

    # 使用最新的数据库文件
    db_file = sorted(db_files)[-1]
    db_path = os.path.join(data_dir, db_file)

    Logger.info(f"使用数据库: {db_file}")

    try:
        # 创建数据处理器
        processor = DataProcessor(db_path)

        # 获取统计信息
        Logger.info("获取数据库统计信息...")
        processor.connect()

        row_count = processor.conn.execute("SELECT COUNT(*) FROM stock_data").fetchone()[0]
        col_count = len(processor.conn.execute("SELECT * FROM stock_data LIMIT 1").fetchdf().columns)
        stock_count = processor.conn.execute("SELECT COUNT(DISTINCT 代码) FROM stock_data").fetchone()[0]

        Logger.info(f"数据库信息：")
        Logger.info(f"  - 总行数: {row_count:,}")
        Logger.info(f"  - 总列数: {col_count}")
        Logger.info(f"  - 股票数: {stock_count:,}")

        # 选项菜单
        print("\n" + "="*80)
        print("请选择操作模式：")
        print("  1. 快速测试（处理 1000 行数据）")
        print("  2. 单只股票测试（处理一只股票的完整数据）")
        print("  3. 完整处理（处理所有数据，116万行）")
        print("="*80)

        choice = input("\n请输入选项 (1-3): ").strip()

        if choice == '1':
            # 快速测试
            Logger.section("快速测试模式 - 1000行数据")
            df = processor.read_data_polars(limit=1000)

            Logger.info(f"读取数据完成：{len(df)} 行, {len(df.columns)} 列")

            # 计算指标
            df_with_indicators = IndicatorCalculator.calculate_all_indicators_polars(df)

            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"indicators_test_{timestamp}.csv")
            ResultSaver.save_to_csv(df_with_indicators, output_file)

            Logger.success(f"快速测试完成！结果已保存到: {output_file}")

        elif choice == '2':
            # 单只股票测试
            Logger.section("单只股票测试模式")

            # 获取所有股票列表（代码和名称）
            stock_list = processor.get_stock_list()
            stock_dict = {code: name for code, name in stock_list}
            all_codes = list(stock_dict.keys())

            Logger.info(f"数据库中共有 {len(all_codes)} 只股票")

            # 显示前20个股票供参考
            preview_stocks = stock_list[:20]
            print("\n前 20 个股票（供参考）:")
            print("=" * 80)
            for i in range(0, len(preview_stocks), 5):
                batch = preview_stocks[i:i+5]
                for code, name in batch:
                    print(f"  {code:6d} - {name}")
                if i + 5 < len(preview_stocks):
                    print()
            if len(stock_list) > 20:
                print(f"\n  ... 还有 {len(stock_list) - 20} 只股票")
            print("=" * 80)

            # 让用户选择股票代码
            while True:
                user_input = input(f"\n请输入要分析的股票代码（直接回车使用第一个: {all_codes[0]} - {stock_dict[all_codes[0]]}）: ").strip()

                if not user_input:
                    # 使用默认的第一个股票
                    test_code = all_codes[0]
                    Logger.info(f"使用默认股票: {test_code} - {stock_dict[test_code]}")
                    break

                # 尝试转换为整数
                try:
                    test_code = int(user_input)
                    if test_code in all_codes:
                        Logger.info(f"已选择股票: {test_code} - {stock_dict[test_code]}")
                        break
                    else:
                        print(f"  ❌ 股票代码 {test_code} 不存在，请重新输入")
                except ValueError:
                    print(f"  ❌ 无效的股票代码格式，请输入数字")

            print()
            df = processor.get_stock_data_polars(test_code)
            Logger.info(f"读取数据完成：{len(df)} 行, {len(df.columns)} 列")

            # 计算指标
            df_with_indicators = IndicatorCalculator.calculate_all_indicators_polars(df)

            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"indicators_{test_code}_{timestamp}.csv")
            ResultSaver.save_to_csv(df_with_indicators, output_file)

            Logger.success(f"单只股票处理完成！结果已保存到: {output_file}")

        elif choice == '3':
            # 完整处理
            Logger.section("完整处理模式 - 所有数据")

            confirm = input(f"\n即将处理 {row_count:,} 行数据，这可能需要较长时间。是否继续？(y/n): ").strip().lower()

            if confirm != 'y':
                Logger.info("操作已取消")
                return

            # 读取所有数据
            Logger.info("读取所有数据...")
            df = processor.read_data_polars()

            Logger.info(f"读取数据完成：{len(df)} 行, {len(df.columns)} 列")

            # 计算指标
            df_with_indicators = IndicatorCalculator.calculate_all_indicators_polars(df)

            # 保存结果（使用 Parquet 格式，更高效）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"indicators_all_{timestamp}.parquet")

            Logger.info("保存结果到 Parquet 文件...")
            ResultSaver.save_to_parquet(df_with_indicators, output_file)

            # 也保存一个 CSV 样本（前1000行）
            sample_file = os.path.join(output_dir, f"indicators_sample_{timestamp}.csv")
            Logger.info("保存样本数据到 CSV...")
            ResultSaver.save_to_csv(df_with_indicators.head(1000), sample_file)

            Logger.success(f"完整处理完成！")
            Logger.info(f"  - 完整结果: {output_file}")
            Logger.info(f"  - 样本数据: {sample_file}")

        else:
            Logger.error("无效的选项")
            return

        # 断开连接
        processor.disconnect()

        Logger.section("所有操作完成！")

    except Exception as e:
        Logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已被用户中断")
        sys.exit(0)
    except Exception as e:
        Logger.error(f"程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
