"""
检查数据库内容
"""
import duckdb
import os
import sys
import io

# 设置UTF-8编码（仅在非测试环境下）
if 'pytest' not in sys.modules and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 数据库路径
db_path = r"D:\shixun\project\data\stock_data_20260101_102133.duckdb"

print("=" * 80)
print("检查数据库内容")
print("=" * 80)

if not os.path.exists(db_path):
    print(f"❌ 数据库文件不存在: {db_path}")
    exit(1)

print(f"✓ 数据库文件: {db_path}")
print(f"✓ 文件大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB\n")

try:
    # 以只读模式连接
    conn = duckdb.connect(db_path, read_only=True)

    # 1. 查看所有表
    print("[1] 数据库中的表:")
    print("-" * 80)
    tables = conn.execute("SHOW TABLES").fetchall()
    if tables:
        for table in tables:
            print(f"  ✓ {table[0]}")
    else:
        print("  ❌ 没有找到任何表！")
    print()

    # 2. 如果有表，显示表结构和数据统计
    if tables:
        for table in tables:
            table_name = table[0]
            print(f"[2] 表 '{table_name}' 详细信息:")
            print("-" * 80)

            # 表结构
            columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
            print(f"  列数: {len(columns)}")
            print(f"  前 10 列:")
            for i, col in enumerate(columns[:10], 1):
                print(f"    {i:2d}. {col[0]:20s} - {col[1]}")
            if len(columns) > 10:
                print(f"    ... 还有 {len(columns) - 10} 列")

            # 数据统计
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"\n  总行数: {row_count:,}")

            # 显示示例数据
            if row_count > 0:
                print(f"\n  前 3 行数据:")
                sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchdf()
                print(sample.to_string())
            else:
                print("  ⚠️  表是空的，没有数据！")
            print()

    conn.close()
    print("=" * 80)
    print("✓ 检查完成")
    print("=" * 80)

except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
