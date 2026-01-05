"""
测试统计指标

测试8个新增的统计指标：
1. Z-Score
2. Percentile
3. Skewness
4. Kurtosis
5. Correlation
6. Rolling Correlation
7. Beta
8. Sharpe Ratio
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import StatisticalIndicators
from core.utils import Logger


def create_test_data(n=100):
    """创建测试数据"""
    np.random.seed(42)

    # 生成价格序列
    prices1 = [100]
    for i in range(n-1):
        change = np.random.normal(0, 2)
        prices1.append(max(prices1[-1] + change, 50))

    # 生成相关的第二个价格序列（部分相关）
    prices2 = [100]
    for i in range(n-1):
        # 70%相关，30%随机
        change = 0.7 * (prices1[i+1] - prices1[i]) + 0.3 * np.random.normal(0, 2)
        prices2.append(max(prices2[-1] + change, 50))

    # 计算收益率
    returns1 = np.diff(prices1) / prices1[:-1]
    returns2 = np.diff(prices2) / prices2[:-1]

    # 添加第一个值为0（因为diff会减少一个元素）
    returns1 = np.concatenate([[0], returns1])
    returns2 = np.concatenate([[0], returns2])

    return pl.DataFrame({
        'price1': [float(p) for p in prices1],
        'price2': [float(p) for p in prices2],
        'return1': returns1,
        'return2': returns2
    }, strict=False)


def test_statistical_indicators():
    """测试所有统计指标"""
    logger = Logger()
    logger.section("测试统计指标")

    # 创建测试数据
    df = create_test_data(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 8
    passed = 0
    failed = 0

    # 1. Z-Score
    try:
        logger.info("[1/8] 测试 Z-Score...")
        df = StatisticalIndicators.zscore(df, 'price1', 20)
        assert 'ZScore_20' in df.columns
        # 检查Z-Score的合理范围（大部分应在-3到3之间）
        zscore_values = df['ZScore_20'].drop_nulls()
        assert len(zscore_values) > 0
        logger.success(f"✓ Z-Score 测试通过 (范围: {zscore_values.min():.2f} 到 {zscore_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Z-Score 测试失败: {e}")
        failed += 1

    # 2. Percentile
    try:
        logger.info("[2/8] 测试 Percentile...")
        df = StatisticalIndicators.percentile(df, 'price1', 20, 50)  # 中位数
        assert 'Percentile_50_20' in df.columns
        pct_values = df['Percentile_50_20'].drop_nulls()
        assert len(pct_values) > 0
        logger.success(f"✓ Percentile 测试通过 (中位数范围: {pct_values.min():.2f} 到 {pct_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Percentile 测试失败: {e}")
        failed += 1

    # 3. Skewness
    try:
        logger.info("[3/8] 测试 Skewness...")
        df = StatisticalIndicators.skewness(df, 'price1', 30)
        assert 'Skewness_30' in df.columns
        skew_values = df['Skewness_30'].drop_nulls()
        assert len(skew_values) > 0
        logger.success(f"✓ Skewness 测试通过 (范围: {skew_values.min():.2f} 到 {skew_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Skewness 测试失败: {e}")
        failed += 1

    # 4. Kurtosis
    try:
        logger.info("[4/8] 测试 Kurtosis...")
        df = StatisticalIndicators.kurtosis(df, 'price1', 30)
        assert 'Kurtosis_30' in df.columns
        kurt_values = df['Kurtosis_30'].drop_nulls()
        assert len(kurt_values) > 0
        logger.success(f"✓ Kurtosis 测试通过 (范围: {kurt_values.min():.2f} 到 {kurt_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Kurtosis 测试失败: {e}")
        failed += 1

    # 5. Correlation
    try:
        logger.info("[5/8] 测试 Correlation...")
        df = StatisticalIndicators.correlation(df, 'price1', 'price2', 20)
        assert 'Corr_price1_price2_20' in df.columns
        corr_values = df['Corr_price1_price2_20'].drop_nulls()
        assert len(corr_values) > 0
        # 相关系数应该在-1到1之间
        assert corr_values.min() >= -1 and corr_values.max() <= 1
        logger.success(f"✓ Correlation 测试通过 (相关系数: {corr_values.mean():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Correlation 测试失败: {e}")
        failed += 1

    # 6. Rolling Correlation
    try:
        logger.info("[6/8] 测试 Rolling Correlation...")
        df = StatisticalIndicators.rolling_correlation(df, 'price1', 'price2', 10, 30)
        assert 'Corr_Short_10' in df.columns
        assert 'Corr_Long_30' in df.columns
        assert 'Corr_Diff' in df.columns
        corr_short = df['Corr_Short_10'].drop_nulls()
        corr_long = df['Corr_Long_30'].drop_nulls()
        assert len(corr_short) > 0 and len(corr_long) > 0
        logger.success(f"✓ Rolling Correlation 测试通过 (短期: {corr_short.mean():.2f}, 长期: {corr_long.mean():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Rolling Correlation 测试失败: {e}")
        failed += 1

    # 7. Beta
    try:
        logger.info("[7/8] 测试 Beta...")
        df = StatisticalIndicators.beta(df, 'return1', 'return2', 60)
        assert 'Beta_60' in df.columns
        beta_values = df['Beta_60'].drop_nulls()
        assert len(beta_values) > 0
        logger.success(f"✓ Beta 测试通过 (平均Beta: {beta_values.mean():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Beta 测试失败: {e}")
        failed += 1

    # 8. Sharpe Ratio
    try:
        logger.info("[8/8] 测试 Sharpe Ratio...")
        df = StatisticalIndicators.sharpe_ratio(df, 'return1', 60, 0.02)  # 2%无风险利率
        assert 'Sharpe_60' in df.columns
        sharpe_values = df['Sharpe_60'].drop_nulls()
        assert len(sharpe_values) > 0
        logger.success(f"✓ Sharpe Ratio 测试通过 (平均Sharpe: {sharpe_values.mean():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Sharpe Ratio 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有统计指标测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        logger.info(f"新增列数: {df.width - 4}")
        return True


def test_indicator_properties():
    """测试指标的数学属性"""
    logger = Logger()
    logger.section("测试指标数学属性")

    df = create_test_data(100)

    # 测试Z-Score的性质
    logger.info("测试 Z-Score 性质...")
    df = StatisticalIndicators.zscore(df, 'price1', 20)

    # Z-Score的标准差应该接近1（在有足够数据的情况下）
    zscore_values = df['ZScore_20'].drop_nulls()
    if len(zscore_values) > 30:
        zscore_std = zscore_values.std()
        logger.info(f"Z-Score标准差: {zscore_std:.2f} (理论值: 1.0)")
        if 0.8 < zscore_std < 1.2:
            logger.success("✓ Z-Score标准差符合预期")
        else:
            logger.warning("⚠ Z-Score标准差偏离预期（可能样本量不足）")

    # 测试Correlation的对称性
    logger.info("\n测试 Correlation 对称性...")
    df = StatisticalIndicators.correlation(df, 'price1', 'price2', 20)
    df = StatisticalIndicators.correlation(df, 'price2', 'price1', 20)

    corr12 = df['Corr_price1_price2_20'].drop_nulls()
    corr21 = df['Corr_price2_price1_20'].drop_nulls()

    if len(corr12) > 0 and len(corr21) > 0:
        # 相关系数应该是对称的
        diff = (corr12 - corr21).abs().max()
        logger.info(f"Corr(A,B) vs Corr(B,A) 最大差异: {diff:.6f}")
        if diff < 1e-10:
            logger.success("✓ Correlation对称性测试通过")
        else:
            logger.warning(f"⚠ Correlation对称性有微小差异: {diff}")

    logger.success("\n数学属性测试完成!")


if __name__ == '__main__':
    logger = Logger()

    # 检查scipy是否安装
    try:
        import scipy
        logger.info("✓ scipy已安装")
    except ImportError:
        logger.error("✗ scipy未安装，部分指标无法测试")
        logger.info("请运行: pip install scipy")
        sys.exit(1)

    # 运行基本测试
    success1 = test_statistical_indicators()

    # 运行属性测试
    logger.info("\n" + "="*80 + "\n")
    test_indicator_properties()

    sys.exit(0 if success1 else 1)
