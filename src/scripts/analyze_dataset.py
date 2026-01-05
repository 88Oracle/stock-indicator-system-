"""
数据集分析脚本
用于分析通达信数据集的结构、字段和样本数据
"""
import polars as pl
import time
import sys
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("开始分析数据集...")
print("=" * 80)

# 数据文件路径
data_path = r"D:\shixun\project\data\通达信数据_20251229.csv"

# 开始计时
start_time = time.time()

try:
    # 使用 Polars 读取 CSV 文件（只读取前1000行进行快速分析）
    print("\n[1] 读取数据集的前1000行进行分析...")
    df = pl.read_csv(data_path, n_rows=1000)

    # 基本信息
    print(f"\n✓ 数据读取成功！")
    print(f"读取耗时: {time.time() - start_time:.2f}秒")

    # 数据维度
    print(f"\n[2] 数据维度（前1000行样本）:")
    print(f"  - 行数: {df.shape[0]:,}")
    print(f"  - 列数: {df.shape[1]}")

    # 列名列表
    print(f"\n[3] 所有字段名称（共{len(df.columns)}个）:")
    print("-" * 80)
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:3d}. {col}")

    # 数据类型
    print(f"\n[4] 数据类型分布:")
    print("-" * 80)
    dtype_counts = {}
    for dtype in df.dtypes:
        dtype_name = str(dtype)
        dtype_counts[dtype_name] = dtype_counts.get(dtype_name, 0) + 1

    for dtype, count in sorted(dtype_counts.items()):
        print(f"  {dtype}: {count}个字段")

    # 查找可能与技术指标计算相关的字段
    print(f"\n[5] 可能用于技术指标计算的关键字段:")
    print("-" * 80)

    # 定义关键词
    price_keywords = ['价', '收盘', '开盘', '最高', '最低', 'close', 'open', 'high', 'low', 'price']
    volume_keywords = ['量', '成交量', '总量', 'volume', 'vol']

    price_cols = []
    volume_cols = []

    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col or keyword in col_lower for keyword in price_keywords):
            price_cols.append(col)
        if any(keyword in col or keyword in col_lower for keyword in volume_keywords):
            volume_cols.append(col)

    print(f"\n  价格相关字段 ({len(price_cols)}个):")
    for col in price_cols[:20]:  # 只显示前20个
        print(f"    - {col}")
    if len(price_cols) > 20:
        print(f"    ... 还有 {len(price_cols) - 20} 个")

    print(f"\n  成交量相关字段 ({len(volume_cols)}个):")
    for col in volume_cols[:20]:  # 只显示前20个
        print(f"    - {col}")
    if len(volume_cols) > 20:
        print(f"    ... 还有 {len(volume_cols) - 20} 个")

    # 显示前5行数据样例
    print(f"\n[6] 数据样例（前5行，前10列）:")
    print("-" * 80)
    print(df.head(5).select(df.columns[:10]))

    # 统计缺失值
    print(f"\n[7] 缺失值统计（前20个字段）:")
    print("-" * 80)
    null_counts = []
    for col in df.columns[:20]:
        null_count = df[col].null_count()
        null_pct = (null_count / len(df)) * 100
        if null_count > 0:
            null_counts.append((col, null_count, null_pct))

    if null_counts:
        for col, count, pct in sorted(null_counts, key=lambda x: x[1], reverse=True):
            print(f"  {col}: {count} ({pct:.1f}%)")
    else:
        print("  前20个字段无缺失值")

    # 现在读取完整数据集的行数（不加载全部数据）
    print(f"\n[8] 获取完整数据集的总行数...")
    df_full = pl.scan_csv(data_path)
    total_rows = df_full.select(pl.len()).collect().item()
    print(f"  ✓ 完整数据集总行数: {total_rows:,}")

    # 保存字段列表到文件
    print(f"\n[9] 保存字段列表到文件...")
    with open(r"D:\shixun\project\data\字段列表.txt", "w", encoding="utf-8") as f:
        f.write(f"通达信数据集字段列表\n")
        f.write(f"=" * 80 + "\n")
        f.write(f"总字段数: {len(df.columns)}\n")
        f.write(f"总行数: {total_rows:,}\n\n")

        f.write("所有字段:\n")
        f.write("-" * 80 + "\n")
        for i, col in enumerate(df.columns, 1):
            f.write(f"{i:3d}. {col}\n")

        f.write(f"\n价格相关字段 ({len(price_cols)}个):\n")
        f.write("-" * 80 + "\n")
        for col in price_cols:
            f.write(f"  - {col}\n")

        f.write(f"\n成交量相关字段 ({len(volume_cols)}个):\n")
        f.write("-" * 80 + "\n")
        for col in volume_cols:
            f.write(f"  - {col}\n")

    print(f"  ✓ 字段列表已保存至: D:\\shixun\\project\\data\\字段列表.txt")

    print("\n" + "=" * 80)
    print("数据集分析完成！")
    print(f"总耗时: {time.time() - start_time:.2f}秒")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
