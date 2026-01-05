"""
测试新指标与批量计算的集成

验证17个新增指标能够正常集成到data_processor的批量计算流程中
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.data_processor import IndicatorCalculator
from core.utils import Logger

def create_test_data(n=100):
    """创建测试数据"""
    np.random.seed(42)

    # 生成随机价格走势
    prices = [100]
    for i in range(n-1):
        change = np.random.normal(0, 2)
        prices.append(max(prices[-1] + change, 50))

    high = [float(p + np.random.uniform(0, 2)) for p in prices]
    low = [float(p - np.random.uniform(0, 2)) for p in prices]
    close = [float(p) for p in prices]
    open_prices = [float(c + np.random.uniform(-1, 1)) for c in close]
    volume = [int(1000 + np.random.uniform(-200, 200)) for _ in range(n)]

    return pl.DataFrame({
        '日期': [f'2025-{i//30+1:02d}-{i%30+1:02d}' for i in range(n)],
        '开盘价': open_prices,
        '最高': high,
        '最低': low,
        '收盘价': close,
        '总量': volume
    }, strict=False)


def test_integration():
    """测试新指标集成"""
    logger = Logger()
    logger.section("测试新指标集成到批量计算")

    # 创建测试数据
    logger.info("创建测试数据...")
    df = create_test_data(100)
    logger.info(f"原始数据: {df.height} 行, {df.width} 列")

    # 使用批量计算功能计算所有指标
    logger.info("\n开始批量计算所有指标...")
    try:
        df_result = IndicatorCalculator.calculate_all_indicators_polars(df)

        logger.success(f"\n✓ 批量计算成功!")
        logger.info(f"计算前列数: {df.width}")
        logger.info(f"计算后列数: {df_result.width}")
        logger.info(f"新增指标列数: {df_result.width - df.width}")

        # 检查新增指标是否存在
        logger.info("\n检查新增的17个指标...")

        new_indicators = {
            'ADX_14': 'ADX平均趋向指标',
            'ENV_Upper_20': 'Envelopes包络线',
            'Alligator_Jaw': 'Alligator鳄鱼指标',
            'AO': 'Awesome Oscillator',
            'Fractal_Up': 'Fractals分形',
            'STC': 'Schaff Trend Cycle',
            'Chaikin_Osc': 'Chaikin Oscillator',
            'KST': 'Know Sure Thing',
            'BB_PctB_20': 'Bollinger %B',
            'ATR_Upper_14': 'ATR Bands',
            'Chandelier_Long': 'Chandelier Exit',
            'KAMA_10': 'KAMA',
            'DEMA_20': 'DEMA',
            'TEMA_20': 'TEMA',
            'ZigZag': 'ZigZag'
        }

        found_count = 0
        missing = []

        for col, desc in new_indicators.items():
            if col in df_result.columns:
                logger.success(f"✓ {desc} ({col})")
                found_count += 1
            else:
                logger.error(f"✗ {desc} ({col}) - 未找到")
                missing.append(col)

        logger.section("测试结果")
        logger.info(f"期望指标数: {len(new_indicators)}")
        logger.info(f"找到指标数: {found_count}")

        if missing:
            logger.error(f"缺失指标: {', '.join(missing)}")
            return False
        else:
            logger.success("✓ 所有新增指标都已成功集成!")
            return True

    except Exception as e:
        logger.error(f"✗ 批量计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_integration()
    sys.exit(0 if success else 1)
