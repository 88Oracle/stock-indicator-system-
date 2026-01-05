"""
数据导入脚本
功能：将通达信 CSV 数据导入到 DuckDB 数据库

"""

import polars as pl
import duckdb
import time
import os
import sys
import io

# 设置UTF-8编码（仅在非测试环境下）
if 'pytest' not in sys.modules and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class DataImporter:
    """数据导入类"""

    def __init__(self, csv_path, db_path):
        """
        初始化数据导入器

        参数:
        csv_path: CSV 文件路径
        db_path: DuckDB 数据库路径
        """
        self.csv_path = csv_path
        self.db_path = db_path

    def import_to_duckdb(self, batch_size=100000):
        """
        将 CSV 数据导入 DuckDB

        参数:
        batch_size: 批次大小（行数）

        返回:
        bool: 是否导入成功
        """
        print("=" * 80)
        print("开始导入数据到 DuckDB...")
        print("=" * 80)

        start_time = time.time()

        try:
            # 1. 检查 CSV 文件是否存在
            if not os.path.exists(self.csv_path):
                print(f"❌ 错误：找不到 CSV 文件: {self.csv_path}")
                return False

            csv_size_mb = os.path.getsize(self.csv_path) / 1024 / 1024
            print(f"\n[1] CSV 文件信息:")
            print(f"  - 文件路径: {self.csv_path}")
            print(f"  - 文件大小: {csv_size_mb:.2f} MB")

            # 2. 使用 Polars 读取 CSV（逐批读取以节省内存）
            print(f"\n[2] 使用 Polars 读取 CSV 数据...")
            print(f"  - 批次大小: {batch_size:,} 行")

            # 先读取第一批数据以获取结构
            df = pl.read_csv(self.csv_path, n_rows=batch_size)
            print(f"  ✓ 成功读取前 {batch_size:,} 行")
            print(f"  - 列数: {len(df.columns)}")
            print(f"  - 行数: {len(df)}")

            # 3. 连接 DuckDB
            print(f"\n[3] 连接 DuckDB 数据库...")
            print(f"  - 数据库路径: {self.db_path}")

            # 如果数据库已存在，先尝试连接并删除旧表
            db_exists = os.path.exists(self.db_path)
            if db_exists:
                print(f"  ⚠️  数据库文件已存在，将删除旧数据")

            conn = duckdb.connect(self.db_path)

            # 如果表已存在，删除它
            if db_exists:
                try:
                    conn.execute("DROP TABLE IF EXISTS stock_data")
                    print(f"  ✓ 已删除旧表")
                except Exception as e:
                    print(f"  ℹ️  删除旧表时出错（可能不存在）: {e}")

            print(f"  ✓ 数据库连接成功")

            # 4. 创建表并导入数据
            print(f"\n[4] 创建表并导入数据...")

            # 使用 DuckDB 的 CSV 读取功能（更高效）
            import_start = time.time()

            # 方法1：直接从 CSV 创建表（最快）
            conn.execute(f"""
                CREATE TABLE stock_data AS
                SELECT * FROM read_csv_auto('{self.csv_path}',
                    header=true,
                    delim=',',
                    quote='"',
                    escape='"',
                    ignore_errors=true
                )
            """)

            import_time = time.time() - import_start
            print(f"  ✓ 数据导入完成，耗时: {import_time:.2f} 秒")

            # 5. 验证数据
            print(f"\n[5] 验证导入数据...")

            # 获取表信息
            row_count = conn.execute("SELECT COUNT(*) FROM stock_data").fetchone()[0]
            col_count = len(conn.execute("SELECT * FROM stock_data LIMIT 1").fetchdf().columns)

            print(f"  ✓ 表名: stock_data")
            print(f"  ✓ 总行数: {row_count:,}")
            print(f"  ✓ 总列数: {col_count}")

            # 6. 创建索引（可选，提高查询性能）
            print(f"\n[6] 创建索引...")

            # 检查是否存在"代码"和"日期"列
            columns = [col for col in df.columns]
            if '代码' in columns and '日期' in columns:
                try:
                    # DuckDB 不支持直接的 CREATE INDEX，但可以通过排序优化查询
                    print(f"  ℹ️  DuckDB 使用列式存储，查询已自动优化")
                    print(f"  ✓ 建议在查询时使用 WHERE 子句过滤 '代码' 和 '日期'")
                except Exception as e:
                    print(f"  ⚠️  索引创建跳过: {e}")

            # 7. 显示示例数据
            print(f"\n[7] 数据样例（前5行）:")
            print("-" * 80)
            sample_df = conn.execute("SELECT * FROM stock_data LIMIT 5").fetchdf()
            print(sample_df.head())

            # 8. 数据统计信息
            print(f"\n[8] 数据统计:")
            print("-" * 80)

            # 获取唯一股票代码数
            if '代码' in columns:
                unique_codes = conn.execute("SELECT COUNT(DISTINCT 代码) FROM stock_data").fetchone()[0]
                print(f"  - 唯一股票数: {unique_codes:,}")

            # 获取日期范围
            if '日期' in columns:
                date_info = conn.execute("SELECT MIN(日期) as min_date, MAX(日期) as max_date FROM stock_data").fetchone()
                print(f"  - 日期范围: {date_info[0]} ~ {date_info[1]}")

            # 数据库文件大小
            db_size_mb = os.path.getsize(self.db_path) / 1024 / 1024
            print(f"  - 数据库大小: {db_size_mb:.2f} MB")
            print(f"  - 压缩比: {csv_size_mb / db_size_mb:.2f}x")

            # 关闭连接
            conn.close()

            # 总结
            total_time = time.time() - start_time
            print("\n" + "=" * 80)
            print("✅ 数据导入成功！")
            print("=" * 80)
            print(f"总耗时: {total_time:.2f} 秒")
            print(f"导入速度: {row_count / total_time:.0f} 行/秒")
            print(f"数据库路径: {self.db_path}")
            print("=" * 80)

            return True

        except Exception as e:
            print(f"\n❌ 导入过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def verify_data(self):
        """验证数据库中的数据"""
        print("\n" + "=" * 80)
        print("验证数据库...")
        print("=" * 80)

        try:
            conn = duckdb.connect(self.db_path)

            # 获取表列表
            tables = conn.execute("SHOW TABLES").fetchall()
            print(f"\n数据库中的表: {tables}")

            # 获取表结构
            columns = conn.execute("DESCRIBE stock_data").fetchall()
            print(f"\n表结构（前10列）:")
            for i, col in enumerate(columns[:10], 1):
                print(f"  {i:2d}. {col[0]:20s} - {col[1]}")

            if len(columns) > 10:
                print(f"  ... 还有 {len(columns) - 10} 列")

            conn.close()

            print("\n✅ 数据验证完成")

        except Exception as e:
            print(f"❌ 验证失败: {e}")


def main():
    """主函数"""
    # 配置路径（使用相对于脚本的路径）
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(script_dir, "data", "通达信数据_20251229.csv")

    # 使用带时间戳的数据库文件名，避免文件被占用
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_filename = f"stock_data_{timestamp}.duckdb"
    db_path = os.path.join(script_dir, "data", db_filename)

    print(f"数据库文件: {db_filename}")
    print()

    # 创建导入器
    importer = DataImporter(csv_path, db_path)

    # 导入数据
    success = importer.import_to_duckdb()

    if success:
        # 验证数据
        importer.verify_data()
        print("\n🎉 所有操作完成！现在可以开始数据分析了。")
    else:
        print("\n❌ 数据导入失败，请检查错误信息。")


if __name__ == "__main__":
    main()
