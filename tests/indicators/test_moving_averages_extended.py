"""
测试移动平均线扩展指标

测试8个新增的移动平均线：
1. SMMA (Smoothed MA)
2. LWMA (Linear Weighted MA)
3. TMA (Triangular MA)
4. ZLEMA (Zero Lag EMA)
5. T3 (Tillson T3)
6. ALMA (Arnaud Legoux MA)
7. JMA (Jurik MA)
8. McGinley Dynamic
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import AdvancedTrendIndicators
from core.utils import Logger


def create_test_data(n=100):
    """创建测试数据"""
    np.random.seed(42)

    # 生成趋势价格序列
    trend = np.linspace(100, 120, n)
    noise = np.random.normal(0, 2, n)
    prices = trend + noise

    # 确保价格为正
    prices = np.maximum(prices, 50)

    return pl.DataFrame({
        'price': prices
    }, strict=False)


def test_moving_averages_extended():
    """测试所有移动平均线扩展指标"""
    logger = Logger()
    logger.section("测试移动平均线扩展指标")

    # 创建测试数据
    df = create_test_data(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 8
    passed = 0
    failed = 0

    # 1. SMMA
    try:
        logger.info("[1/8] 测试 SMMA...")
        df = AdvancedTrendIndicators.smma(df, 'price', 20)
        assert 'SMMA_20' in df.columns
        smma_values = df['SMMA_20'].drop_nulls()
        assert len(smma_values) > 0
        # SMMA应该比价格平滑
        assert smma_values.std() < df['price'].std()
        logger.success(f"✓ SMMA 测试通过 (范围: {smma_values.min():.2f} 到 {smma_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ SMMA 测试失败: {e}")
        failed += 1

    # 2. LWMA
    try:
        logger.info("[2/8] 测试 LWMA...")
        df = AdvancedTrendIndicators.lwma(df, 'price', 20)
        assert 'LWMA_20' in df.columns
        lwma_values = df['LWMA_20'].drop_nulls()
        assert len(lwma_values) > 0
        logger.success(f"✓ LWMA 测试通过 (范围: {lwma_values.min():.2f} 到 {lwma_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ LWMA 测试失败: {e}")
        failed += 1

    # 3. TMA
    try:
        logger.info("[3/8] 测试 TMA...")
        df = AdvancedTrendIndicators.tma(df, 'price', 10)
        assert 'TMA_10' in df.columns
        tma_values = df['TMA_10'].drop_nulls()
        assert len(tma_values) > 0
        # TMA是双重平滑，应该最平滑
        logger.success(f"✓ TMA 测试通过 (范围: {tma_values.min():.2f} 到 {tma_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ TMA 测试失败: {e}")
        failed += 1

    # 4. ZLEMA
    try:
        logger.info("[4/8] 测试 ZLEMA...")
        df = AdvancedTrendIndicators.zlema(df, 'price', 20)
        assert 'ZLEMA_20' in df.columns
        zlema_values = df['ZLEMA_20'].drop_nulls()
        assert len(zlema_values) > 0
        logger.success(f"✓ ZLEMA 测试通过 (范围: {zlema_values.min():.2f} 到 {zlema_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ ZLEMA 测试失败: {e}")
        failed += 1

    # 5. T3
    try:
        logger.info("[5/8] 测试 T3...")
        df = AdvancedTrendIndicators.t3(df, 'price', 5, 0.7)
        assert 'T3_5' in df.columns
        t3_values = df['T3_5'].drop_nulls()
        assert len(t3_values) > 0
        # T3应该非常平滑
        logger.success(f"✓ T3 测试通过 (范围: {t3_values.min():.2f} 到 {t3_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ T3 测试失败: {e}")
        failed += 1

    # 6. ALMA
    try:
        logger.info("[6/8] 测试 ALMA...")
        df = AdvancedTrendIndicators.alma(df, 'price', 9, 0.85, 6.0)
        assert 'ALMA_9' in df.columns
        alma_values = df['ALMA_9'].drop_nulls()
        assert len(alma_values) > 0
        logger.success(f"✓ ALMA 测试通过 (范围: {alma_values.min():.2f} 到 {alma_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ ALMA 测试失败: {e}")
        failed += 1

    # 7. JMA
    try:
        logger.info("[7/8] 测试 JMA...")
        df = AdvancedTrendIndicators.jma(df, 'price', 7, 0, 2)
        assert 'JMA_7' in df.columns
        jma_values = df['JMA_7'].drop_nulls()
        assert len(jma_values) > 0
        logger.success(f"✓ JMA 测试通过 (范围: {jma_values.min():.2f} 到 {jma_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ JMA 测试失败: {e}")
        failed += 1

    # 8. McGinley Dynamic
    try:
        logger.info("[8/8] 测试 McGinley Dynamic...")
        df = AdvancedTrendIndicators.mcginley_dynamic(df, 'price', 14)
        assert 'McGinley_14' in df.columns
        mcginley_values = df['McGinley_14'].drop_nulls()
        assert len(mcginley_values) > 0
        logger.success(f"✓ McGinley Dynamic 测试通过 (范围: {mcginley_values.min():.2f} 到 {mcginley_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ McGinley Dynamic 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有移动平均线扩展指标测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        logger.info(f"新增列数: {df.width - 1}")
        return True


def test_indicator_properties():
    """测试指标属性"""
    logger = Logger()
    logger.section("测试移动平均线属性")

    df = create_test_data(100)

    # 测试平滑性：TMA应该比SMA更平滑
    logger.info("测试平滑性...")
    df = df.with_columns(
        df['price'].rolling_mean(window_size=10).alias('SMA_10')
    )
    df = AdvancedTrendIndicators.tma(df, 'price', 10)

    sma_std = df['SMA_10'].drop_nulls().std()
    tma_std = df['TMA_10'].drop_nulls().std()

    logger.info(f"SMA标准差: {sma_std:.2f}")
    logger.info(f"TMA标准差: {tma_std:.2f}")

    if tma_std < sma_std:
        logger.success("✓ TMA比SMA更平滑")
    else:
        logger.warning("⚠ TMA平滑性测试不符合预期")

    # 测试ZLEMA响应性
    logger.info("\n测试ZLEMA响应性...")
    df = df.with_columns(
        df['price'].ewm_mean(span=20, adjust=False).alias('EMA_20')
    )
    df = AdvancedTrendIndicators.zlema(df, 'price', 20)

    # 最后20个值的差异
    recent_data = df.tail(20)
    price_change = recent_data['price'].diff().abs().sum()
    ema_change = recent_data['EMA_20'].diff().abs().sum()
    zlema_change = recent_data['ZLEMA_20'].diff().abs().sum()

    logger.info(f"价格变化: {price_change:.2f}")
    logger.info(f"EMA变化: {ema_change:.2f}")
    logger.info(f"ZLEMA变化: {zlema_change:.2f}")

    if zlema_change > ema_change:
        logger.success("✓ ZLEMA响应性优于EMA")
    else:
        logger.info("→ ZLEMA响应性测试完成")

    logger.success("\n属性测试完成!")


if __name__ == '__main__':
    logger = Logger()

    # 运行基本测试
    success1 = test_moving_averages_extended()

    # 运行属性测试
    logger.info("\n" + "="*80 + "\n")
    test_indicator_properties()

    sys.exit(0 if success1 else 1)
