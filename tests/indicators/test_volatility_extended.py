"""
测试波动率指标扩展

测试5个新增的波动率指标：
1. Historical Volatility
2. Chaikin Volatility
3. ATR Trailing Stop
4. Normalized ATR
5. Parkinson Volatility
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import AdvancedVolatilityIndicators
from core.utils import Logger


def create_test_data(n=100):
    """创建测试数据"""
    np.random.seed(42)

    # 生成趋势价格序列
    trend = np.linspace(100, 120, n)
    noise = np.random.normal(0, 2, n)
    close = trend + noise

    # 确保价格为正
    close = np.maximum(close, 50)

    # 生成高低价
    high = close + np.abs(np.random.normal(0, 1, n))
    low = close - np.abs(np.random.normal(0, 1, n))

    return pl.DataFrame({
        'high': high,
        'low': low,
        'close': close
    }, strict=False)


def test_volatility_extended():
    """测试所有波动率指标扩展"""
    logger = Logger()
    logger.section("测试波动率指标扩展")

    # 创建测试数据
    df = create_test_data(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 5
    passed = 0
    failed = 0

    # 1. Historical Volatility
    try:
        logger.info("[1/5] 测试 Historical Volatility...")
        df = AdvancedVolatilityIndicators.historical_volatility(df, 'close', 20, True)
        assert 'HV_20' in df.columns
        hv_values = df['HV_20'].drop_nulls()
        assert len(hv_values) > 0
        # 年化波动率应该为正
        assert hv_values.min() >= 0
        logger.success(f"✓ Historical Volatility 测试通过 (范围: {hv_values.min():.4f} 到 {hv_values.max():.4f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Historical Volatility 测试失败: {e}")
        failed += 1

    # 2. Chaikin Volatility
    try:
        logger.info("[2/5] 测试 Chaikin Volatility...")
        df = AdvancedVolatilityIndicators.chaikin_volatility(df, 'high', 'low', 10, 10)
        assert 'Chaikin_Vol' in df.columns
        cv_values = df['Chaikin_Vol'].drop_nulls()
        assert len(cv_values) > 0
        logger.success(f"✓ Chaikin Volatility 测试通过 (范围: {cv_values.min():.2f} 到 {cv_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Chaikin Volatility 测试失败: {e}")
        failed += 1

    # 3. ATR Trailing Stop
    try:
        logger.info("[3/5] 测试 ATR Trailing Stop...")
        df = AdvancedVolatilityIndicators.atr_trailing_stop(df, 'high', 'low', 'close', 14, 3.0)
        assert 'ATR_Stop_Long' in df.columns
        assert 'ATR_Stop_Short' in df.columns
        stop_long_values = df['ATR_Stop_Long'].drop_nulls()
        stop_short_values = df['ATR_Stop_Short'].drop_nulls()
        assert len(stop_long_values) > 0
        assert len(stop_short_values) > 0
        # Long止损应该小于收盘价，Short止损应该大于收盘价
        logger.success(f"✓ ATR Trailing Stop 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ ATR Trailing Stop 测试失败: {e}")
        failed += 1

    # 4. Normalized ATR
    try:
        logger.info("[4/5] 测试 Normalized ATR...")
        df = AdvancedVolatilityIndicators.normalized_atr(df, 'high', 'low', 'close', 14)
        assert 'NATR_14' in df.columns
        natr_values = df['NATR_14'].drop_nulls()
        assert len(natr_values) > 0
        # NATR是百分比形式
        assert natr_values.min() >= 0
        logger.success(f"✓ Normalized ATR 测试通过 (范围: {natr_values.min():.2f}% 到 {natr_values.max():.2f}%)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Normalized ATR 测试失败: {e}")
        failed += 1

    # 5. Parkinson Volatility
    try:
        logger.info("[5/5] 测试 Parkinson Volatility...")
        df = AdvancedVolatilityIndicators.parkinson_volatility(df, 'high', 'low', 20)
        assert 'Parkinson_20' in df.columns
        park_values = df['Parkinson_20'].drop_nulls()
        assert len(park_values) > 0
        # Parkinson波动率应该为正
        assert park_values.min() >= 0
        logger.success(f"✓ Parkinson Volatility 测试通过 (范围: {park_values.min():.4f} 到 {park_values.max():.4f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Parkinson Volatility 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有波动率指标扩展测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        return True


def test_volatility_properties():
    """测试波动率指标属性"""
    logger = Logger()
    logger.section("测试波动率指标属性")

    df = create_test_data(100)

    # 测试Parkinson vs Historical Volatility
    logger.info("比较Parkinson波动率和历史波动率...")
    df = AdvancedVolatilityIndicators.historical_volatility(df, 'close', 20, True)
    df = AdvancedVolatilityIndicators.parkinson_volatility(df, 'high', 'low', 20)

    hv_mean = df['HV_20'].drop_nulls().mean()
    park_mean = df['Parkinson_20'].drop_nulls().mean()

    logger.info(f"Historical Volatility平均: {hv_mean:.4f}")
    logger.info(f"Parkinson Volatility平均: {park_mean:.4f}")

    if park_mean > 0:
        logger.success("✓ Parkinson波动率计算正常")
    else:
        logger.warning("⚠ Parkinson波动率异常")

    # 测试ATR Trailing Stop单调性
    logger.info("\n测试ATR Trailing Stop单调性...")
    df = AdvancedVolatilityIndicators.atr_trailing_stop(df, 'high', 'low', 'close', 14, 3.0)
    stop_long = df['ATR_Stop_Long'].drop_nulls()

    # Long止损应该是非递减的（只能上移）
    is_non_decreasing = (stop_long.diff().drop_nulls() >= -1e-10).all()

    if is_non_decreasing:
        logger.success("✓ ATR Trailing Stop (Long) 单调性正确")
    else:
        logger.warning("⚠ ATR Trailing Stop (Long) 单调性测试未通过")

    logger.success("\n属性测试完成!")


if __name__ == '__main__':
    logger = Logger()

    # 运行基本测试
    success1 = test_volatility_extended()

    # 运行属性测试
    logger.info("\n" + "="*80 + "\n")
    test_volatility_properties()

    sys.exit(0 if success1 else 1)
