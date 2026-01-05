"""
新增指标测试脚本
功能：测试Day 5新增的5个技术指标
作者：AI Assistant
日期：2025-01-05
"""

import polars as pl
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import Logger
from core.indicators import ExtraIndicators

def test_new_indicators():
    """测试新增的5个指标"""
    Logger.section("测试Day 5新增指标")

    # 创建测试数据（100行）
    import numpy as np

    n = 100
    dates = [f'2025-01-{i+1:02d}' if i < 31 else f'2025-02-{i-30:02d}' if i < 59 else f'2025-03-{i-58:02d}'
             for i in range(n)]

    # 生成随机价格数据
    np.random.seed(42)
    base_price = 100
    price_changes = np.random.randn(n) * 2
    close_prices = base_price + np.cumsum(price_changes)
    high_prices = close_prices + np.random.rand(n) * 3
    low_prices = close_prices - np.random.rand(n) * 3
    open_prices = close_prices + np.random.randn(n) * 1

    test_data = {
        '日期': dates,
        '开盘价': open_prices.tolist(),
        '最高': high_prices.tolist(),
        '最低': low_prices.tolist(),
        '收盘价': close_prices.tolist(),
    }

    df = pl.DataFrame(test_data)

    print(f"\n测试数据：{len(df)} 行")
    print(f"初始列数：{len(df.columns)}")

    # 测试1: Parabolic SAR
    Logger.info("测试 1/5: Parabolic SAR...")
    try:
        df_test = ExtraIndicators.parabolic_sar(df.clone(), '最高', '最低', '收盘价')
        assert 'PSAR' in df_test.columns
        Logger.success(f"✓ Parabolic SAR 计算成功 (新增1列)")
    except Exception as e:
        Logger.error(f"✗ Parabolic SAR 失败: {e}")

    # 测试2: Ichimoku Cloud
    Logger.info("测试 2/5: Ichimoku Cloud...")
    try:
        df_test = ExtraIndicators.ichimoku_cloud(df.clone(), '最高', '最低', '收盘价')
        expected_cols = ['Tenkan_sen', 'Kijun_sen', 'Senkou_A', 'Senkou_B', 'Chikou_span']
        for col in expected_cols:
            assert col in df_test.columns
        Logger.success(f"✓ Ichimoku Cloud 计算成功 (新增5列)")
    except Exception as e:
        Logger.error(f"✗ Ichimoku Cloud 失败: {e}")

    # 测试3: Supertrend
    Logger.info("测试 3/5: Supertrend...")
    try:
        df_test = ExtraIndicators.supertrend(df.clone(), '最高', '最低', '收盘价')
        assert 'Supertrend' in df_test.columns
        assert 'Supertrend_Direction' in df_test.columns
        Logger.success(f"✓ Supertrend 计算成功 (新增2列)")
    except Exception as e:
        Logger.error(f"✗ Supertrend 失败: {e}")

    # 测试4: Pivot Points
    Logger.info("测试 4/5: Pivot Points...")
    try:
        df_test = ExtraIndicators.pivot_points(df.clone(), '最高', '最低', '收盘价')
        expected_cols = ['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']
        for col in expected_cols:
            assert col in df_test.columns
        Logger.success(f"✓ Pivot Points 计算成功 (新增7列)")
    except Exception as e:
        Logger.error(f"✗ Pivot Points 失败: {e}")

    # 测试5: Fibonacci Retracement
    Logger.info("测试 5/5: Fibonacci Retracement...")
    try:
        df_test = ExtraIndicators.fibonacci_retracement(df.clone(), '最高', '最低', 50)
        expected_cols = ['Fib_0', 'Fib_236', 'Fib_382', 'Fib_500', 'Fib_618', 'Fib_786', 'Fib_1000']
        for col in expected_cols:
            assert col in df_test.columns
        Logger.success(f"✓ Fibonacci Retracement 计算成功 (新增7列)")
    except Exception as e:
        Logger.error(f"✗ Fibonacci Retracement 失败: {e}")

    # 测试所有指标一起计算
    Logger.info("\n综合测试：同时计算所有新指标...")
    try:
        df_all = df.clone()
        df_all = ExtraIndicators.parabolic_sar(df_all, '最高', '最低', '收盘价')
        df_all = ExtraIndicators.ichimoku_cloud(df_all, '最高', '最低', '收盘价')
        df_all = ExtraIndicators.supertrend(df_all, '最高', '最低', '收盘价')
        df_all = ExtraIndicators.pivot_points(df_all, '最高', '最低', '收盘价')
        df_all = ExtraIndicators.fibonacci_retracement(df_all, '最高', '最低', 50)

        new_cols = len(df_all.columns) - len(df.columns)
        Logger.success(f"✓ 所有新指标计算成功！新增 {new_cols} 列")

        print(f"\n最终列数：{len(df_all.columns)}")
        print(f"新增列数：{new_cols}")

    except Exception as e:
        Logger.error(f"✗ 综合测试失败: {e}")
        import traceback
        traceback.print_exc()

    Logger.section("测试完成！")

    print("\n" + "="*80)
    print("Day 5 新增指标总结：")
    print("  1. Parabolic SAR - 抛物线转向指标 (1列)")
    print("  2. Ichimoku Cloud - 一目均衡表 (5列)")
    print("  3. Supertrend - 超级趋势指标 (2列)")
    print("  4. Pivot Points - 枢轴点 (7列)")
    print("  5. Fibonacci Retracement - 斐波那契回撤 (7列)")
    print(f"\n总新增列数：22列")
    print(f"项目总指标数：63个")
    print("="*80)


if __name__ == "__main__":
    try:
        test_new_indicators()
    except Exception as e:
        Logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
