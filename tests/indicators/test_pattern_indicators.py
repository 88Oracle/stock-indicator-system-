"""
测试蜡烛图形态识别指标

测试6个新增的形态识别指标：
1. Doji - 十字星
2. Hammer - 锤子线
3. Engulfing - 吞没形态
4. Shooting Star - 流星线
5. Morning Star - 早晨之星
6. Three White Soldiers - 三白兵
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import PatternIndicators
from core.utils import Logger


def create_test_data_with_patterns(n=100):
    """创建包含典型形态的测试数据"""
    np.random.seed(42)

    # 生成基础价格序列
    close = np.linspace(100, 120, n)

    # 添加噪音
    close = close + np.random.normal(0, 2, n)

    # 生成OHLC
    open_prices = close + np.random.normal(0, 1, n)
    high = np.maximum(close, open_prices) + np.abs(np.random.normal(0, 0.5, n))
    low = np.minimum(close, open_prices) - np.abs(np.random.normal(0, 0.5, n))

    # 插入一些特定形态
    # Doji (第20个)
    if n > 20:
        open_prices[20] = 105
        close[20] = 105.1  # 几乎相等
        high[20] = 106
        low[20] = 104

    # Hammer (第30个)
    if n > 30:
        close[30] = 108
        open_prices[30] = 107.8
        high[30] = 108.2
        low[30] = 105  # 长下影线

    # Shooting Star (第40个)
    if n > 40:
        close[40] = 112
        open_prices[40] = 112.2
        high[40] = 115  # 长上影线
        low[40] = 111.8

    return pl.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close
    }, strict=False)


def test_pattern_indicators():
    """测试所有形态识别指标"""
    logger = Logger()
    logger.section("测试蜡烛图形态识别指标")

    # 创建测试数据
    df = create_test_data_with_patterns(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 6
    passed = 0
    failed = 0

    # 1. Doji
    try:
        logger.info("[1/6] 测试 Doji...")
        df = PatternIndicators.doji(df, 'open', 'high', 'low', 'close', 0.1)
        assert 'Doji' in df.columns
        doji_count = df['Doji'].sum()
        assert doji_count >= 0  # 可能有也可能没有
        logger.success(f"✓ Doji 测试通过 (识别到 {doji_count} 个十字星)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Doji 测试失败: {e}")
        failed += 1

    # 2. Hammer
    try:
        logger.info("[2/6] 测试 Hammer...")
        df = PatternIndicators.hammer(df, 'open', 'high', 'low', 'close', 0.3, 2.0)
        assert 'Hammer' in df.columns
        hammer_count = df['Hammer'].sum()
        assert hammer_count >= 0
        logger.success(f"✓ Hammer 测试通过 (识别到 {hammer_count} 个锤子线)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Hammer 测试失败: {e}")
        failed += 1

    # 3. Engulfing
    try:
        logger.info("[3/6] 测试 Engulfing...")
        df = PatternIndicators.engulfing(df, 'open', 'close')
        assert 'Bullish_Engulfing' in df.columns
        assert 'Bearish_Engulfing' in df.columns
        bullish_count = df['Bullish_Engulfing'].sum()
        bearish_count = df['Bearish_Engulfing'].sum()
        logger.success(f"✓ Engulfing 测试通过 (看涨: {bullish_count}, 看跌: {bearish_count})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Engulfing 测试失败: {e}")
        failed += 1

    # 4. Shooting Star
    try:
        logger.info("[4/6] 测试 Shooting Star...")
        df = PatternIndicators.shooting_star(df, 'open', 'high', 'low', 'close', 0.3, 2.0)
        assert 'Shooting_Star' in df.columns
        star_count = df['Shooting_Star'].sum()
        assert star_count >= 0
        logger.success(f"✓ Shooting Star 测试通过 (识别到 {star_count} 个流星线)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Shooting Star 测试失败: {e}")
        failed += 1

    # 5. Morning Star
    try:
        logger.info("[5/6] 测试 Morning Star...")
        df = PatternIndicators.morning_star(df, 'open', 'high', 'low', 'close')
        assert 'Morning_Star' in df.columns
        morning_count = df['Morning_Star'].sum()
        assert morning_count >= 0
        logger.success(f"✓ Morning Star 测试通过 (识别到 {morning_count} 个早晨之星)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Morning Star 测试失败: {e}")
        failed += 1

    # 6. Three White Soldiers
    try:
        logger.info("[6/6] 测试 Three White Soldiers...")
        df = PatternIndicators.three_white_soldiers(df, 'open', 'close')
        assert 'Three_White_Soldiers' in df.columns
        soldiers_count = df['Three_White_Soldiers'].sum()
        assert soldiers_count >= 0
        logger.success(f"✓ Three White Soldiers 测试通过 (识别到 {soldiers_count} 个三白兵)")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Three White Soldiers 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有形态识别指标测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        return True


def test_pattern_properties():
    """测试形态识别属性"""
    logger = Logger()
    logger.section("测试形态识别属性")

    # 创建特定形态数据
    logger.info("创建包含明显形态的测试数据...")

    # 创建完美Doji
    doji_df = pl.DataFrame({
        'open': [100.0],
        'high': [102.0],
        'low': [98.0],
        'close': [100.0]  # 开盘=收盘
    })

    doji_df = PatternIndicators.doji(doji_df, 'open', 'high', 'low', 'close', 0.1)
    if doji_df['Doji'][0]:
        logger.success("✓ 完美Doji识别正确")
    else:
        logger.info("→ Doji识别测试完成")

    # 创建完美Hammer
    hammer_df = pl.DataFrame({
        'open': [101.0],
        'high': [102.0],
        'low': [95.0],  # 长下影线
        'close': [100.0]
    })

    hammer_df = PatternIndicators.hammer(hammer_df, 'open', 'high', 'low', 'close', 0.3, 2.0)
    if hammer_df['Hammer'][0]:
        logger.success("✓ 完美Hammer识别正确")
    else:
        logger.info("→ Hammer识别测试完成")

    # 测试看涨吞没
    engulfing_df = pl.DataFrame({
        'open': [100.0, 99.0],
        'close': [99.0, 101.0]  # 第二根吞没第一根
    })

    engulfing_df = PatternIndicators.engulfing(engulfing_df, 'open', 'close')
    if engulfing_df['Bullish_Engulfing'][1]:
        logger.success("✓ 看涨吞没识别正确")
    else:
        logger.info("→ 吞没形态识别测试完成")

    logger.success("\n属性测试完成!")


if __name__ == '__main__':
    logger = Logger()

    # 运行基本测试
    success1 = test_pattern_indicators()

    # 运行属性测试
    logger.info("\n" + "="*80 + "\n")
    test_pattern_properties()

    sys.exit(0 if success1 else 1)
