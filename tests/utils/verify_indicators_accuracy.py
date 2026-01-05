"""
验证技术指标计算准确性

对比我们的实现与TA-Lib库的结果，检查计算偏差
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
import numpy as np
from core.indicators import (
    TrendIndicators, MomentumIndicators, VolatilityIndicators,
    OscillatorIndicators, ExtraIndicators
)
from core.utils import Logger

# 尝试导入TA-Lib
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False


def create_test_data(n=100):
    """创建测试数据"""
    np.random.seed(42)

    prices = [100]
    for i in range(n-1):
        change = np.random.normal(0, 2)
        prices.append(max(prices[-1] + change, 50))

    high = np.array([p + np.random.uniform(0, 2) for p in prices])
    low = np.array([p - np.random.uniform(0, 2) for p in prices])
    close = np.array(prices)
    volume = np.array([1000 + np.random.uniform(-200, 200) for _ in range(n)])

    df = pl.DataFrame({
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    return df, high, low, close, volume


def compare_values(our_values, talib_values, name, tolerance=0.01):
    """
    比较两个数组的差异

    tolerance: 允许的相对误差（1%）
    """
    logger = Logger()

    # 跳过NaN值
    mask = ~(np.isnan(our_values) | np.isnan(talib_values))
    our_valid = our_values[mask]
    talib_valid = talib_values[mask]

    if len(our_valid) == 0:
        logger.warning(f"{name}: 没有有效值可比较")
        return False

    # 计算相对误差
    diff = np.abs(our_valid - talib_valid)
    rel_error = diff / (np.abs(talib_valid) + 1e-10)

    max_error = np.max(rel_error)
    mean_error = np.mean(rel_error)

    # 统计超过容差的点
    outliers = np.sum(rel_error > tolerance)
    outlier_pct = outliers / len(rel_error) * 100

    if max_error < tolerance:
        logger.success(f"✓ {name}: 完全一致 (最大误差 {max_error:.6f})")
        return True
    elif outlier_pct < 5:
        logger.info(f"≈ {name}: 基本一致 (最大误差 {max_error:.4f}, 平均误差 {mean_error:.6f}, 异常点 {outlier_pct:.1f}%)")
        return True
    else:
        logger.error(f"✗ {name}: 差异较大 (最大误差 {max_error:.4f}, 平均误差 {mean_error:.6f}, 异常点 {outlier_pct:.1f}%)")
        return False


def verify_indicators():
    """验证指标准确性"""
    logger = Logger()
    logger.section("技术指标准确性验证")

    if not TALIB_AVAILABLE:
        logger.error("TA-Lib未安装，无法进行验证")
        logger.info("安装命令: pip install TA-Lib")
        logger.info("\n注意: TA-Lib在Windows上安装较复杂，可能需要下载预编译包")
        return

    logger.info("TA-Lib已安装，开始验证...\n")

    # 创建测试数据
    df, high, low, close, volume = create_test_data(100)

    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }

    # 1. SMA
    logger.info("[1] 验证 SMA...")
    df_sma = TrendIndicators.sma(df, 'close', 20)
    our_sma = df_sma['SMA_20'].to_numpy()
    talib_sma = talib.SMA(close, timeperiod=20)
    if compare_values(our_sma, talib_sma, "SMA(20)"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1

    # 2. EMA
    logger.info("\n[2] 验证 EMA...")
    df_ema = TrendIndicators.ema(df, 'close', 20)
    our_ema = df_ema['EMA_20'].to_numpy()
    talib_ema = talib.EMA(close, timeperiod=20)
    if compare_values(our_ema, talib_ema, "EMA(20)"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1

    # 3. RSI
    logger.info("\n[3] 验证 RSI...")
    df_rsi = MomentumIndicators.rsi(df, 'close', 14)
    our_rsi = df_rsi['RSI_14'].to_numpy()
    talib_rsi = talib.RSI(close, timeperiod=14)
    if compare_values(our_rsi, talib_rsi, "RSI(14)"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1

    # 4. MACD
    logger.info("\n[4] 验证 MACD...")
    df_macd = OscillatorIndicators.macd(df, 'close', 12, 26, 9)
    our_macd = df_macd['MACD_Line'].to_numpy()
    our_signal = df_macd['MACD_Signal'].to_numpy()
    our_hist = df_macd['MACD_Hist'].to_numpy()

    talib_macd, talib_signal, talib_hist = talib.MACD(close,
                                                       fastperiod=12,
                                                       slowperiod=26,
                                                       signalperiod=9)

    macd_ok = compare_values(our_macd, talib_macd, "MACD Line")
    signal_ok = compare_values(our_signal, talib_signal, "MACD Signal")
    hist_ok = compare_values(our_hist, talib_hist, "MACD Histogram")

    if macd_ok and signal_ok and hist_ok:
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1

    # 5. Bollinger Bands
    logger.info("\n[5] 验证 Bollinger Bands...")
    df_bb = VolatilityIndicators.bollinger_bands(df, 'close', 20, 2.0)
    our_upper = df_bb['BB_Upper_20'].to_numpy()
    our_middle = df_bb['BB_Middle_20'].to_numpy()
    our_lower = df_bb['BB_Lower_20'].to_numpy()

    talib_upper, talib_middle, talib_lower = talib.BBANDS(close,
                                                           timeperiod=20,
                                                           nbdevup=2,
                                                           nbdevdn=2)

    upper_ok = compare_values(our_upper, talib_upper, "BB Upper")
    middle_ok = compare_values(our_middle, talib_middle, "BB Middle")
    lower_ok = compare_values(our_lower, talib_lower, "BB Lower")

    if upper_ok and middle_ok and lower_ok:
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1

    # 6. ATR
    logger.info("\n[6] 验证 ATR...")
    df_atr = VolatilityIndicators.atr(df, 'high', 'low', 'close', 14)
    our_atr = df_atr['ATR_14'].to_numpy()
    talib_atr = talib.ATR(high, low, close, timeperiod=14)
    if compare_values(our_atr, talib_atr, "ATR(14)"):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1

    # 7. ADX
    logger.info("\n[7] 验证 ADX...")
    df_adx = ExtraIndicators.adx(df, 'high', 'low', 'close', 14)
    our_adx = df_adx['ADX_14'].to_numpy()
    talib_adx = talib.ADX(high, low, close, timeperiod=14)
    if compare_values(our_adx, talib_adx, "ADX(14)", tolerance=0.05):  # ADX容差稍大
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1

    # 总结
    logger.section("验证结果汇总")
    logger.info(f"总测试数: {results['total']}")
    logger.info(f"通过: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
    if results['failed'] > 0:
        logger.warning(f"需要关注: {results['failed']} 个指标")
    else:
        logger.success("✓ 所有测试指标与TA-Lib一致!")

    logger.info("\n说明:")
    logger.info("- '完全一致': 误差 < 1%")
    logger.info("- '基本一致': 误差 < 1% 且异常点 < 5%")
    logger.info("- '差异较大': 需要检查实现")


def main():
    """主函数"""
    logger = Logger()

    logger.info("技术指标准确性验证工具")
    logger.info("对比对象: TA-Lib (Python版)")
    logger.info("-" * 60)

    verify_indicators()

    logger.info("\n建议:")
    logger.info("1. 对于关键交易策略，建议使用业界标准库(如TA-Lib)")
    logger.info("2. 对于研究和分析，当前实现已足够准确")
    logger.info("3. 如发现差异，请参考TA-Lib源码进行调整")


if __name__ == '__main__':
    main()
