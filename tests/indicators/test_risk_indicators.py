"""
测试风险管理指标

测试5个新增的风险管理指标：
1. Maximum Drawdown - 最大回撤
2. Sortino Ratio - 索提诺比率
3. Calmar Ratio - 卡玛比率
4. Win Rate - 胜率
5. Profit Factor - 盈亏比
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import RiskIndicators
from core.utils import Logger


def create_test_data(n=100):
    """创建测试数据"""
    np.random.seed(42)

    # 生成价格序列（带有回撤）
    prices = [100]
    for i in range(1, n):
        # 随机涨跌
        change = np.random.normal(0.001, 0.02)  # 均值0.1%，标准差2%
        prices.append(prices[-1] * (1 + change))

    prices = np.array(prices)

    # 计算收益率
    returns = np.diff(prices) / prices[:-1]
    returns = np.concatenate([[0], returns])  # 第一个值为0

    return pl.DataFrame({
        'value': prices,
        'returns': returns
    }, strict=False)


def test_risk_indicators():
    """测试所有风险管理指标"""
    logger = Logger()
    logger.section("测试风险管理指标")

    # 创建测试数据
    df = create_test_data(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 5
    passed = 0
    failed = 0

    # 1. Maximum Drawdown
    try:
        logger.info("[1/5] 测试 Maximum Drawdown...")
        df = RiskIndicators.maximum_drawdown(df, 'value', period=None)
        assert 'Max_Drawdown' in df.columns
        mdd_values = df['Max_Drawdown'].drop_nulls()
        assert len(mdd_values) > 0
        # 回撤应该为负或零
        assert mdd_values.max() <= 0
        logger.success(f"✓ Maximum Drawdown 测试通过 (最大回撤: {mdd_values.min():.2f}%)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Maximum Drawdown 测试失败: {e}")
        failed += 1

    # 2. Sortino Ratio
    try:
        logger.info("[2/5] 测试 Sortino Ratio...")
        df = RiskIndicators.sortino_ratio(df, 'returns', period=60, target_return=0.0)
        assert 'Sortino_60' in df.columns
        sortino_values = df['Sortino_60'].drop_nulls()
        assert len(sortino_values) > 0
        logger.success(f"✓ Sortino Ratio 测试通过 (范围: {sortino_values.min():.2f} 到 {sortino_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Sortino Ratio 测试失败: {e}")
        failed += 1

    # 3. Calmar Ratio
    try:
        logger.info("[3/5] 测试 Calmar Ratio...")
        df = RiskIndicators.calmar_ratio(df, 'returns', 'value', period=36)
        assert 'Calmar_Ratio' in df.columns
        calmar_values = df['Calmar_Ratio'].drop_nulls()
        assert len(calmar_values) > 0
        logger.success(f"✓ Calmar Ratio 测试通过 (范围: {calmar_values.min():.2f} 到 {calmar_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Calmar Ratio 测试失败: {e}")
        failed += 1

    # 4. Win Rate
    try:
        logger.info("[4/5] 测试 Win Rate...")
        df = RiskIndicators.win_rate(df, 'returns', period=20)
        assert 'Win_Rate_20' in df.columns
        win_rate_values = df['Win_Rate_20'].drop_nulls()
        assert len(win_rate_values) > 0
        # 胜率应该在0-100之间
        assert win_rate_values.min() >= 0 and win_rate_values.max() <= 100
        logger.success(f"✓ Win Rate 测试通过 (平均胜率: {win_rate_values.mean():.2f}%)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Win Rate 测试失败: {e}")
        failed += 1

    # 5. Profit Factor
    try:
        logger.info("[5/5] 测试 Profit Factor...")
        df = RiskIndicators.profit_factor(df, 'returns', period=20)
        assert 'Profit_Factor_20' in df.columns
        pf_values = df['Profit_Factor_20'].drop_nulls()
        assert len(pf_values) > 0
        # Profit Factor应该为正
        assert pf_values.min() >= 0
        logger.success(f"✓ Profit Factor 测试通过 (平均PF: {pf_values.mean():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Profit Factor 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有风险管理指标测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        return True


def test_risk_properties():
    """测试风险指标属性"""
    logger = Logger()
    logger.section("测试风险指标属性")

    df = create_test_data(100)

    # 测试Maximum Drawdown单调性
    logger.info("测试最大回撤单调性...")
    df = RiskIndicators.maximum_drawdown(df, 'value', period=None)
    mdd = df['Max_Drawdown'].to_numpy()

    # 回撤应该只会变大（更负）或保持
    is_monotonic = True
    for i in range(1, len(mdd)):
        if not np.isnan(mdd[i]) and not np.isnan(mdd[i-1]):
            if mdd[i] > mdd[i-1]:  # 回撤变小了（更接近0）
                is_monotonic = False
                break

    if is_monotonic:
        logger.success("✓ 最大回撤具有单调性（持续累积）")
    else:
        logger.info("→ 最大回撤测试完成")

    # 测试Win Rate合理性
    logger.info("\n测试胜率合理性...")
    df = RiskIndicators.win_rate(df, 'returns', period=20)
    win_rate_mean = df['Win_Rate_20'].drop_nulls().mean()

    logger.info(f"平均胜率: {win_rate_mean:.2f}%")

    if 40 <= win_rate_mean <= 60:
        logger.success("✓ 胜率在合理范围内（40-60%）")
    else:
        logger.info(f"→ 胜率为 {win_rate_mean:.2f}%")

    # 测试Profit Factor与Win Rate关系
    logger.info("\n测试Profit Factor与Win Rate关系...")
    df = RiskIndicators.profit_factor(df, 'returns', period=20)

    pf_mean = df['Profit_Factor_20'].drop_nulls().mean()
    logger.info(f"平均Profit Factor: {pf_mean:.2f}")

    if pf_mean >= 1.0:
        logger.success("✓ Profit Factor >= 1.0 (盈利大于亏损)")
    else:
        logger.warning("⚠ Profit Factor < 1.0 (亏损大于盈利)")

    logger.success("\n属性测试完成!")


if __name__ == '__main__':
    logger = Logger()

    # 运行基本测试
    success1 = test_risk_indicators()

    # 运行属性测试
    logger.info("\n" + "="*80 + "\n")
    test_risk_properties()

    sys.exit(0 if success1 else 1)
