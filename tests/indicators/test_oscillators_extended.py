"""
测试震荡指标补充

测试6个新增的震荡指标：
1. Fisher Transform
2. Inverse Fisher Transform
3. Coppock Curve
4. Klinger Oscillator
5. PPO (Percentage Price Oscillator)
6. Squeeze Momentum
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import AdvancedOscillatorIndicators, MomentumIndicators
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

    # 生成成交量
    volume = np.random.randint(1000, 5000, n)

    return pl.DataFrame({
        'high': high,
        'low': low,
        'close': close,
        'volume': volume.astype(float)
    }, strict=False)


def test_oscillators_extended():
    """测试所有震荡指标补充"""
    logger = Logger()
    logger.section("测试震荡指标补充")

    # 创建测试数据
    df = create_test_data(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 6
    passed = 0
    failed = 0

    # 1. Fisher Transform
    try:
        logger.info("[1/6] 测试 Fisher Transform...")
        df = AdvancedOscillatorIndicators.fisher_transform(df, 'high', 'low', 10)
        assert 'Fisher' in df.columns
        assert 'Fisher_Signal' in df.columns
        fisher_values = df['Fisher'].drop_nulls()
        assert len(fisher_values) > 0
        logger.success(f"✓ Fisher Transform 测试通过 (范围: {fisher_values.min():.2f} 到 {fisher_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Fisher Transform 测试失败: {e}")
        failed += 1

    # 2. Inverse Fisher Transform
    try:
        logger.info("[2/6] 测试 Inverse Fisher Transform...")
        # 先计算RSI用于测试
        df = MomentumIndicators.rsi(df, 'close', 14)
        df = AdvancedOscillatorIndicators.inverse_fisher_transform(df, 'RSI_14')
        assert 'IFT_RSI_14' in df.columns
        ift_values = df['IFT_RSI_14'].drop_nulls()
        assert len(ift_values) > 0
        # IFT值应该在-1到1之间
        assert ift_values.min() >= -1 and ift_values.max() <= 1
        logger.success(f"✓ Inverse Fisher Transform 测试通过 (范围: {ift_values.min():.2f} 到 {ift_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Inverse Fisher Transform 测试失败: {e}")
        failed += 1

    # 3. Coppock Curve
    try:
        logger.info("[3/6] 测试 Coppock Curve...")
        df = AdvancedOscillatorIndicators.coppock_curve(df, 'close', 14, 11, 10)
        assert 'Coppock' in df.columns
        coppock_values = df['Coppock'].drop_nulls()
        assert len(coppock_values) > 0
        logger.success(f"✓ Coppock Curve 测试通过 (范围: {coppock_values.min():.2f} 到 {coppock_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Coppock Curve 测试失败: {e}")
        failed += 1

    # 4. Klinger Oscillator
    try:
        logger.info("[4/6] 测试 Klinger Oscillator...")
        df = AdvancedOscillatorIndicators.klinger_oscillator(
            df, 'high', 'low', 'close', 'volume', 34, 55, 13
        )
        assert 'KO' in df.columns
        assert 'KO_Signal' in df.columns
        ko_values = df['KO'].drop_nulls()
        assert len(ko_values) > 0
        logger.success(f"✓ Klinger Oscillator 测试通过 (范围: {ko_values.min():.2f} 到 {ko_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Klinger Oscillator 测试失败: {e}")
        failed += 1

    # 5. PPO
    try:
        logger.info("[5/6] 测试 PPO...")
        df = AdvancedOscillatorIndicators.ppo(df, 'close', 12, 26, 9)
        assert 'PPO' in df.columns
        assert 'PPO_Signal' in df.columns
        assert 'PPO_Hist' in df.columns
        ppo_values = df['PPO'].drop_nulls()
        assert len(ppo_values) > 0
        logger.success(f"✓ PPO 测试通过 (范围: {ppo_values.min():.2f} 到 {ppo_values.max():.2f})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ PPO 测试失败: {e}")
        failed += 1

    # 6. Squeeze Momentum
    try:
        logger.info("[6/6] 测试 Squeeze Momentum...")
        df = AdvancedOscillatorIndicators.squeeze_momentum(df, 'high', 'low', 'close', 20, 20, 1.5)
        assert 'Squeeze_On' in df.columns
        assert 'Squeeze_Momentum' in df.columns
        squeeze_values = df['Squeeze_On'].drop_nulls()
        momentum_values = df['Squeeze_Momentum'].drop_nulls()
        assert len(squeeze_values) > 0
        assert len(momentum_values) > 0
        squeeze_count = squeeze_values.sum()
        logger.success(f"✓ Squeeze Momentum 测试通过 (挤压次数: {squeeze_count}/{len(squeeze_values)})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Squeeze Momentum 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有震荡指标补充测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        return True


if __name__ == '__main__':
    logger = Logger()

    # 运行基本测试
    success = test_oscillators_extended()

    sys.exit(0 if success else 1)
