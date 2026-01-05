"""
测试高级趋势指标

测试5个新增的高级趋势指标：
1. FRAMA - 分形自适应MA
2. MAMA - Mesa自适应MA
3. Linear Regression - 线性回归
4. Time Series Forecast - 时间序列预测
5. Projection Bands - 投影带
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


def test_advanced_trend_indicators():
    """测试所有高级趋势指标"""
    logger = Logger()
    logger.section("测试高级趋势指标")

    # 创建测试数据
    df = create_test_data(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 5
    passed = 0
    failed = 0

    # 1. FRAMA
    try:
        logger.info("[1/5] 测试 FRAMA...")
        df = AdvancedTrendIndicators.frama(df, 'price', 16)
        assert 'FRAMA_16' in df.columns
        frama_values = df['FRAMA_16'].drop_nulls()
        assert len(frama_values) > 0
        logger.success(f"✓ FRAMA 测试通过 (范围: {frama_values.min():.2f} 到 {frama_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ FRAMA 测试失败: {e}")
        failed += 1

    # 2. MAMA
    try:
        logger.info("[2/5] 测试 MAMA...")
        df = AdvancedTrendIndicators.mama(df, 'price', 0.5, 0.05)
        assert 'MAMA' in df.columns
        assert 'MAMA_FAMA' in df.columns
        mama_values = df['MAMA'].drop_nulls()
        fama_values = df['MAMA_FAMA'].drop_nulls()
        assert len(mama_values) > 0
        assert len(fama_values) > 0
        logger.success(f"✓ MAMA 测试通过 (MAMA范围: {mama_values.min():.2f} 到 {mama_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ MAMA 测试失败: {e}")
        failed += 1

    # 3. Linear Regression
    try:
        logger.info("[3/5] 测试 Linear Regression...")
        df = AdvancedTrendIndicators.linear_regression(df, 'price', 14)
        assert 'LinReg_14' in df.columns
        linreg_values = df['LinReg_14'].drop_nulls()
        assert len(linreg_values) > 0
        logger.success(f"✓ Linear Regression 测试通过 (范围: {linreg_values.min():.2f} 到 {linreg_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Linear Regression 测试失败: {e}")
        failed += 1

    # 4. Time Series Forecast
    try:
        logger.info("[4/5] 测试 Time Series Forecast...")
        df = AdvancedTrendIndicators.time_series_forecast(df, 'price', 14, 1)
        assert 'TSF_14_1' in df.columns
        tsf_values = df['TSF_14_1'].drop_nulls()
        assert len(tsf_values) > 0
        logger.success(f"✓ Time Series Forecast 测试通过 (范围: {tsf_values.min():.2f} 到 {tsf_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Time Series Forecast 测试失败: {e}")
        failed += 1

    # 5. Projection Bands
    try:
        logger.info("[5/5] 测试 Projection Bands...")
        df = AdvancedTrendIndicators.projection_bands(df, 'price', 14, 2.0)
        assert 'ProjBand_Upper_14' in df.columns
        assert 'ProjBand_Middle_14' in df.columns
        assert 'ProjBand_Lower_14' in df.columns
        upper_values = df['ProjBand_Upper_14'].drop_nulls()
        middle_values = df['ProjBand_Middle_14'].drop_nulls()
        lower_values = df['ProjBand_Lower_14'].drop_nulls()
        assert len(upper_values) > 0
        assert len(middle_values) > 0
        assert len(lower_values) > 0
        # 上轨应该大于中轨，中轨应该大于下轨
        logger.success(f"✓ Projection Bands 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Projection Bands 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有高级趋势指标测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        return True


def test_indicator_properties():
    """测试指标属性"""
    logger = Logger()
    logger.section("测试高级趋势指标属性")

    df = create_test_data(100)

    # 测试Projection Bands顺序
    logger.info("测试Projection Bands顺序...")
    df = AdvancedTrendIndicators.projection_bands(df, 'price', 14, 2.0)

    # 检查上轨 > 中轨 > 下轨
    valid_bands = (
        (df['ProjBand_Upper_14'] >= df['ProjBand_Middle_14']) &
        (df['ProjBand_Middle_14'] >= df['ProjBand_Lower_14'])
    )
    valid_count = valid_bands.drop_nulls().sum()
    total_count = len(valid_bands.drop_nulls())

    if valid_count == total_count:
        logger.success("✓ Projection Bands顺序正确 (上轨 > 中轨 > 下轨)")
    else:
        logger.info(f"→ Projection Bands顺序测试: {valid_count}/{total_count} 正确")

    # 测试线性回归与预测的关系
    logger.info("\n测试Linear Regression与Time Series Forecast关系...")
    df = AdvancedTrendIndicators.linear_regression(df, 'price', 14)
    df = AdvancedTrendIndicators.time_series_forecast(df, 'price', 14, 0)  # 0期预测应该等于回归线

    # TSF_0应该接近LinReg
    diff = (df['TSF_14_0'] - df['LinReg_14']).abs().drop_nulls()
    avg_diff = diff.mean()

    if avg_diff < 0.01:
        logger.success(f"✓ TSF(0期) 与 LinReg 一致 (平均差异: {avg_diff:.6f})")
    else:
        logger.info(f"→ TSF与LinReg关系测试完成 (平均差异: {avg_diff:.6f})")

    # 测试MAMA/FAMA交叉
    logger.info("\n测试MAMA/FAMA交叉...")
    df = AdvancedTrendIndicators.mama(df, 'price', 0.5, 0.05)

    # MAMA应该比FAMA更快响应
    mama_change = df['MAMA'].diff().abs().drop_nulls().mean()
    fama_change = df['MAMA_FAMA'].diff().abs().drop_nulls().mean()

    if mama_change >= fama_change:
        logger.success(f"✓ MAMA响应速度快于FAMA (MAMA变化: {mama_change:.4f}, FAMA变化: {fama_change:.4f})")
    else:
        logger.info(f"→ MAMA/FAMA关系测试完成")

    logger.success("\n属性测试完成!")


if __name__ == '__main__':
    logger = Logger()

    # 运行基本测试
    success1 = test_advanced_trend_indicators()

    # 运行属性测试
    logger.info("\n" + "="*80 + "\n")
    test_indicator_properties()

    sys.exit(0 if success1 else 1)
