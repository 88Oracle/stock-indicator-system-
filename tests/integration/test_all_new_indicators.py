"""
测试所有新增的技术指标

测试17个新增指标：
1. ADX (平均趋向指标)
2. Envelopes (包络线)
3. Alligator (鳄鱼指标)
4. Awesome Oscillator (动量震荡指标)
5. Fractals (分形指标)
6. Gator Oscillator (鳄鱼震荡指标)
7. Schaff Trend Cycle (STC)
8. Chaikin Oscillator
9. Know Sure Thing (KST)
10. Bollinger %B
11. ATR Bands
12. Chandelier Exit
13. KAMA
14. DEMA
15. TEMA
16. ZigZag
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import ExtraIndicators, VolatilityIndicators
from core.utils import Logger


def create_test_data(n=100):
    """创建测试数据"""
    np.random.seed(42)

    # 生成随机价格走势
    prices = [100]
    for i in range(n-1):
        change = np.random.normal(0, 2)
        prices.append(max(prices[-1] + change, 50))  # 确保价格>50

    high = [float(p + np.random.uniform(0, 2)) for p in prices]
    low = [float(p - np.random.uniform(0, 2)) for p in prices]
    close = [float(p) for p in prices]
    open_prices = [float(c + np.random.uniform(-1, 1)) for c in close]
    volume = [int(1000 + np.random.uniform(-200, 200)) for _ in range(n)]

    return pl.DataFrame({
        '日期': [f'2025-{i//30+1:02d}-{i%30+1:02d}' for i in range(n)],
        '开盘': open_prices,
        '最高': high,
        '最低': low,
        '收盘': close,
        '成交量': volume
    }, strict=False)


def test_all_new_indicators():
    """测试所有新增指标"""
    logger = Logger()
    logger.section("测试所有新增指标")

    # 创建测试数据
    df = create_test_data(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 17
    passed = 0
    failed = 0

    # 1. ADX
    try:
        logger.info("[1/17] 测试 ADX...")
        df = ExtraIndicators.adx(df, '最高', '最低', '收盘', 14)
        assert 'ADX_14' in df.columns
        assert '+DI_14' in df.columns
        assert '-DI_14' in df.columns
        logger.success("✓ ADX 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ ADX 测试失败: {e}")
        failed += 1

    # 2. Envelopes
    try:
        logger.info("[2/17] 测试 Envelopes...")
        df = ExtraIndicators.envelopes(df, '收盘', 20, 2.5)
        assert 'ENV_Upper_20' in df.columns
        assert 'ENV_Middle_20' in df.columns
        assert 'ENV_Lower_20' in df.columns
        logger.success("✓ Envelopes 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Envelopes 测试失败: {e}")
        failed += 1

    # 3. Alligator
    try:
        logger.info("[3/17] 测试 Alligator...")
        df = ExtraIndicators.alligator(df, '收盘')
        assert 'Alligator_Jaw' in df.columns
        assert 'Alligator_Teeth' in df.columns
        assert 'Alligator_Lips' in df.columns
        logger.success("✓ Alligator 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Alligator 测试失败: {e}")
        failed += 1

    # 4. Awesome Oscillator
    try:
        logger.info("[4/17] 测试 Awesome Oscillator...")
        df = ExtraIndicators.awesome_oscillator(df, '最高', '最低')
        assert 'AO' in df.columns
        logger.success("✓ Awesome Oscillator 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Awesome Oscillator 测试失败: {e}")
        failed += 1

    # 5. Fractals
    try:
        logger.info("[5/17] 测试 Fractals...")
        df = ExtraIndicators.fractals(df, '最高', '最低', 5)
        assert 'Fractal_Up' in df.columns
        assert 'Fractal_Down' in df.columns
        logger.success("✓ Fractals 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Fractals 测试失败: {e}")
        failed += 1

    # 6. Gator Oscillator
    try:
        logger.info("[6/17] 测试 Gator Oscillator...")
        # 注意：这会重新计算Alligator
        df_gator = df.clone()
        df_gator = ExtraIndicators.gator_oscillator(df_gator, '收盘')
        assert 'Gator_Upper' in df_gator.columns
        assert 'Gator_Lower' in df_gator.columns
        logger.success("✓ Gator Oscillator 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Gator Oscillator 测试失败: {e}")
        failed += 1

    # 7. Schaff Trend Cycle
    try:
        logger.info("[7/17] 测试 Schaff Trend Cycle...")
        df = ExtraIndicators.schaff_trend_cycle(df, '收盘')
        assert 'STC' in df.columns
        logger.success("✓ Schaff Trend Cycle 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Schaff Trend Cycle 测试失败: {e}")
        failed += 1

    # 8. Chaikin Oscillator
    try:
        logger.info("[8/17] 测试 Chaikin Oscillator...")
        df = ExtraIndicators.chaikin_oscillator(df, '最高', '最低', '收盘', '成交量')
        assert 'Chaikin_Osc' in df.columns
        logger.success("✓ Chaikin Oscillator 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Chaikin Oscillator 测试失败: {e}")
        failed += 1

    # 9. Know Sure Thing (KST)
    try:
        logger.info("[9/17] 测试 Know Sure Thing...")
        df = ExtraIndicators.kst(df, '收盘')
        assert 'KST' in df.columns
        assert 'KST_Signal' in df.columns
        logger.success("✓ Know Sure Thing 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Know Sure Thing 测试失败: {e}")
        failed += 1

    # 10. Bollinger %B
    try:
        logger.info("[10/17] 测试 Bollinger %B...")
        df = ExtraIndicators.bollinger_pct_b(df, '收盘', 20, 2.0)
        assert 'BB_PctB_20' in df.columns
        assert 'BB_Width_20' in df.columns
        logger.success("✓ Bollinger %B 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Bollinger %B 测试失败: {e}")
        failed += 1

    # 11. ATR Bands
    try:
        logger.info("[11/17] 测试 ATR Bands...")
        df = ExtraIndicators.atr_bands(df, '最高', '最低', '收盘', 14, 2.0)
        assert 'ATR_Upper_14' in df.columns
        assert 'ATR_Middle_14' in df.columns
        assert 'ATR_Lower_14' in df.columns
        logger.success("✓ ATR Bands 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ ATR Bands 测试失败: {e}")
        failed += 1

    # 12. Chandelier Exit
    try:
        logger.info("[12/17] 测试 Chandelier Exit...")
        df = ExtraIndicators.chandelier_exit(df, '最高', '最低', '收盘', 22, 3.0)
        assert 'Chandelier_Long' in df.columns
        assert 'Chandelier_Short' in df.columns
        logger.success("✓ Chandelier Exit 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Chandelier Exit 测试失败: {e}")
        failed += 1

    # 13. KAMA
    try:
        logger.info("[13/17] 测试 KAMA...")
        df = ExtraIndicators.kama(df, '收盘', 10)
        assert 'KAMA_10' in df.columns
        logger.success("✓ KAMA 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ KAMA 测试失败: {e}")
        failed += 1

    # 14. DEMA
    try:
        logger.info("[14/17] 测试 DEMA...")
        df = ExtraIndicators.dema(df, '收盘', 20)
        assert 'DEMA_20' in df.columns
        logger.success("✓ DEMA 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ DEMA 测试失败: {e}")
        failed += 1

    # 15. TEMA
    try:
        logger.info("[15/17] 测试 TEMA...")
        df = ExtraIndicators.tema(df, '收盘', 20)
        assert 'TEMA_20' in df.columns
        logger.success("✓ TEMA 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ TEMA 测试失败: {e}")
        failed += 1

    # 16. ZigZag
    try:
        logger.info("[16/17] 测试 ZigZag...")
        df = ExtraIndicators.zigzag(df, '最高', '最低', 5.0)
        assert 'ZigZag' in df.columns
        assert 'ZigZag_Signal' in df.columns
        logger.success("✓ ZigZag 测试通过")
        passed += 1
    except Exception as e:
        logger.error(f"✗ ZigZag 测试失败: {e}")
        failed += 1

    # 17. 综合测试 - 计算所有新指标
    try:
        logger.info("[17/17] 综合测试 - 所有新指标...")
        df_all = create_test_data(100)

        # 计算所有新指标
        df_all = ExtraIndicators.adx(df_all, '最高', '最低', '收盘')
        df_all = ExtraIndicators.envelopes(df_all, '收盘')
        df_all = ExtraIndicators.alligator(df_all, '收盘')
        df_all = ExtraIndicators.awesome_oscillator(df_all, '最高', '最低')
        df_all = ExtraIndicators.fractals(df_all, '最高', '最低')
        df_all = ExtraIndicators.schaff_trend_cycle(df_all, '收盘')
        df_all = ExtraIndicators.chaikin_oscillator(df_all, '最高', '最低', '收盘', '成交量')
        df_all = ExtraIndicators.kst(df_all, '收盘')
        df_all = ExtraIndicators.bollinger_pct_b(df_all, '收盘')
        df_all = ExtraIndicators.atr_bands(df_all, '最高', '最低', '收盘')
        df_all = ExtraIndicators.chandelier_exit(df_all, '最高', '最低', '收盘')
        df_all = ExtraIndicators.kama(df_all, '收盘')
        df_all = ExtraIndicators.dema(df_all, '收盘')
        df_all = ExtraIndicators.tema(df_all, '收盘')
        df_all = ExtraIndicators.zigzag(df_all, '最高', '最低')

        new_columns = df_all.width - 6  # 减去原始列数
        logger.success(f"✓ 综合测试通过! 新增 {new_columns} 列指标")
        passed += 1
    except Exception as e:
        logger.error(f"✗ 综合测试失败: {e}")
        failed += 1

    # 总结
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")
    if failed > 0:
        logger.error(f"失败: {failed}")
    else:
        logger.success("✓ 所有测试通过!")

    logger.info(f"\n最终数据集: {df_all.height} 行, {df_all.width} 列")
    logger.info(f"新增指标列: {df_all.width - 6} 列")

    return passed == total_tests


if __name__ == '__main__':
    success = test_all_new_indicators()
    sys.exit(0 if success else 1)
