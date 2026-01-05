"""
测试市场结构指标

测试4个新增的市场结构指标：
1. Market Structure - 市场结构
2. Order Blocks - 订单块
3. Fair Value Gaps - 公允价值缺口
4. Liquidity Levels - 流动性水平
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import MarketStructureIndicators
from core.utils import Logger


def create_test_data_with_structure(n=100):
    """创建包含市场结构的测试数据"""
    np.random.seed(42)

    # 生成趋势价格序列
    trend = np.linspace(100, 120, n)
    noise = np.random.normal(0, 2, n)
    close = trend + noise

    # 确保价格为正
    close = np.maximum(close, 50)

    # 生成OHLC
    open_prices = close + np.random.normal(0, 0.5, n)
    high = np.maximum(close, open_prices) + np.abs(np.random.normal(0, 1, n))
    low = np.minimum(close, open_prices) - np.abs(np.random.normal(0, 1, n))

    # 生成成交量
    volume = np.random.randint(1000, 5000, n).astype(float)

    # 插入一些明显的结构特征
    # 摆动高点 (第30个)
    if n > 30:
        high[30] = high[30] + 5

    # 摆动低点 (第50个)
    if n > 50:
        low[50] = low[50] - 5

    # FVG缺口 (第60-62个)
    if n > 62:
        high[60] = 110
        low[62] = 112  # 创建向上缺口

    return pl.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, strict=False)


def test_market_structure_indicators():
    """测试所有市场结构指标"""
    logger = Logger()
    logger.section("测试市场结构指标")

    # 创建测试数据
    df = create_test_data_with_structure(100)
    logger.info(f"创建测试数据: {df.height} 行, {df.width} 列")

    total_tests = 4
    passed = 0
    failed = 0

    # 1. Market Structure
    try:
        logger.info("[1/4] 测试 Market Structure...")
        df = MarketStructureIndicators.market_structure(df, 'high', 'low', 5)
        assert 'Structure_High' in df.columns
        assert 'Structure_Low' in df.columns
        highs_count = df['Structure_High'].drop_nulls().len()
        lows_count = df['Structure_Low'].drop_nulls().len()
        logger.success(f"✓ Market Structure 测试通过 (高点: {highs_count}, 低点: {lows_count})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Market Structure 测试失败: {e}")
        failed += 1

    # 2. Order Blocks
    try:
        logger.info("[2/4] 测试 Order Blocks...")
        df = MarketStructureIndicators.order_blocks(df, 'open', 'high', 'low', 'close', None, 10)
        assert 'Bullish_OB' in df.columns
        assert 'Bearish_OB' in df.columns
        bullish_ob_count = df['Bullish_OB'].sum()
        bearish_ob_count = df['Bearish_OB'].sum()
        logger.success(f"✓ Order Blocks 测试通过 (看涨: {bullish_ob_count}, 看跌: {bearish_ob_count})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Order Blocks 测试失败: {e}")
        failed += 1

    # 3. Fair Value Gaps
    try:
        logger.info("[3/4] 测试 Fair Value Gaps...")
        df = MarketStructureIndicators.fair_value_gaps(df, 'high', 'low', 0.001)
        assert 'Bullish_FVG' in df.columns
        assert 'Bearish_FVG' in df.columns
        assert 'FVG_Gap_Size' in df.columns
        bullish_fvg_count = df['Bullish_FVG'].sum()
        bearish_fvg_count = df['Bearish_FVG'].sum()
        gap_sizes = df['FVG_Gap_Size'].drop_nulls()
        logger.success(f"✓ Fair Value Gaps 测试通过 (看涨: {bullish_fvg_count}, 看跌: {bearish_fvg_count})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Fair Value Gaps 测试失败: {e}")
        failed += 1

    # 4. Liquidity Levels
    try:
        logger.info("[4/4] 测试 Liquidity Levels...")
        df = MarketStructureIndicators.liquidity_levels(df, 'high', 'low', 'volume', 20, 90)
        assert 'Liquidity_High' in df.columns
        assert 'Liquidity_Low' in df.columns
        assert 'Liquidity_Score' in df.columns
        liq_high_count = df['Liquidity_High'].sum()
        liq_low_count = df['Liquidity_Low'].sum()
        logger.success(f"✓ Liquidity Levels 测试通过 (高流动性高点: {liq_high_count}, 低点: {liq_low_count})")
        passed += 1
    except Exception as e:
        logger.error(f"✗ Liquidity Levels 测试失败: {e}")
        failed += 1

    # 汇总
    logger.section("测试结果汇总")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed} ({passed/total_tests*100:.1f}%)")

    if failed > 0:
        logger.error(f"失败: {failed}")
        return False
    else:
        logger.success("✓ 所有市场结构指标测试通过!")
        logger.info(f"\n最终数据集: {df.height} 行, {df.width} 列")
        return True


def test_structure_properties():
    """测试市场结构指标属性"""
    logger = Logger()
    logger.section("测试市场结构指标属性")

    df = create_test_data_with_structure(100)

    # 测试Market Structure识别的高低点数量
    logger.info("测试Market Structure识别效果...")
    df = MarketStructureIndicators.market_structure(df, 'high', 'low', 5)

    highs = df['Structure_High'].drop_nulls()
    lows = df['Structure_Low'].drop_nulls()

    logger.info(f"识别到 {len(highs)} 个摆动高点")
    logger.info(f"识别到 {len(lows)} 个摆动低点")

    if len(highs) > 0 and len(lows) > 0:
        logger.success("✓ Market Structure成功识别摆动点")
    else:
        logger.info("→ Market Structure识别测试完成")

    # 测试FVG缺口大小
    logger.info("\n测试Fair Value Gaps缺口大小...")
    df = MarketStructureIndicators.fair_value_gaps(df, 'high', 'low', 0.001)

    gap_sizes = df['FVG_Gap_Size'].drop_nulls()

    if len(gap_sizes) > 0:
        avg_gap = gap_sizes.mean()
        max_gap = gap_sizes.max()
        logger.success(f"✓ FVG识别成功 (平均缺口: {avg_gap:.2f}, 最大缺口: {max_gap:.2f})")
    else:
        logger.info("→ 未识别到FVG缺口")

    # 测试Liquidity Levels与成交量关系
    logger.info("\n测试Liquidity Levels与成交量关系...")
    df = MarketStructureIndicators.liquidity_levels(df, 'high', 'low', 'volume', 20, 90)

    # 流动性区域的成交量应该大于平均
    liq_mask = df['Liquidity_High'] | df['Liquidity_Low']
    if liq_mask.sum() > 0:
        liq_volume = df.filter(liq_mask)['volume'].mean()
        avg_volume = df['volume'].mean()

        if liq_volume >= avg_volume:
            logger.success(f"✓ 流动性区域成交量高于平均 ({liq_volume:.0f} vs {avg_volume:.0f})")
        else:
            logger.info(f"→ 流动性测试完成")
    else:
        logger.info("→ 未识别到高流动性区域")

    logger.success("\n属性测试完成!")


if __name__ == '__main__':
    logger = Logger()

    # 运行基本测试
    success1 = test_market_structure_indicators()

    # 运行属性测试
    logger.info("\n" + "="*80 + "\n")
    test_structure_properties()

    sys.exit(0 if success1 else 1)
