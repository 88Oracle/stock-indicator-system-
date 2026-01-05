"""
技术指标计算模块
功能：实现各类技术指标的 Polars 高性能计算
"""

import polars as pl
import numpy as np
from typing import Union, Optional


class TrendIndicators:
    """趋势指标类"""

    @staticmethod
    def sma(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        简单移动平均线 (Simple Moving Average)

        参数:
        df: Polars DataFrame
        column: 要计算的列名（通常是收盘价）
        period: 计算周期
        result_col: 结果列名（可选，默认为 'SMA_{period}'）

        返回:
        pl.DataFrame: 添加了 SMA 列的 DataFrame
        """
        if result_col is None:
            result_col = f'SMA_{period}'

        df = df.with_columns(
            pl.col(column).rolling_mean(window_size=period).alias(result_col)
        )

        return df

    @staticmethod
    def ema(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        指数移动平均线 (Exponential Moving Average)

        参数:
        df: Polars DataFrame
        column: 要计算的列名（通常是收盘价）
        period: 计算周期
        result_col: 结果列名（可选，默认为 'EMA_{period}'）

        返回:
        pl.DataFrame: 添加了 EMA 列的 DataFrame
        """
        if result_col is None:
            result_col = f'EMA_{period}'

        # TA-Lib 使用标准 EMA: alpha = 2/(period+1), adjust=True, min_periods=period
        df = df.with_columns(
            pl.col(column).ewm_mean(span=period, adjust=True, min_periods=period).alias(result_col)
        )

        return df

    @staticmethod
    def wma(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        加权移动平均线 (Weighted Moving Average)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 WMA 列的 DataFrame
        """
        if result_col is None:
            result_col = f'WMA_{period}'

        # 创建权重
        weights = np.arange(1, period + 1)
        weight_sum = weights.sum()

        # 使用滚动窗口计算加权平均
        df = df.with_columns(
            pl.col(column).rolling_map(
                lambda s: np.dot(s, weights) / weight_sum if len(s) == period else None,
                window_size=period
            ).alias(result_col)
        )

        return df


class MomentumIndicators:
    """动量指标类"""

    @staticmethod
    def rsi(df: pl.DataFrame, column: str, period: int = 14, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        相对强弱指标 (Relative Strength Index)

        参数:
        df: Polars DataFrame
        column: 要计算的列名（通常是收盘价）
        period: 计算周期（默认 14）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 RSI 列的 DataFrame
        """
        if result_col is None:
            result_col = f'RSI_{period}'

        # 计算价格变化
        df = df.with_columns(
            (pl.col(column) - pl.col(column).shift(1)).alias('_price_change')
        )

        # 分离涨跌
        df = df.with_columns([
            pl.when(pl.col('_price_change') > 0)
              .then(pl.col('_price_change'))
              .otherwise(0)
              .alias('_gain'),
            pl.when(pl.col('_price_change') < 0)
              .then(-pl.col('_price_change'))
              .otherwise(0)
              .alias('_loss')
        ])

        # 计算平均涨跌幅 - 使用 Wilder's Smoothing (SMMA): alpha = 1/period
        # TA-Lib 使用这种平滑方式，与标准 EMA 不同
        df = df.with_columns([
            pl.col('_gain').ewm_mean(alpha=1/period, adjust=False, min_periods=period).alias('_avg_gain'),
            pl.col('_loss').ewm_mean(alpha=1/period, adjust=False, min_periods=period).alias('_avg_loss')
        ])

        # 计算 RSI
        df = df.with_columns(
            pl.when(pl.col('_avg_loss') == 0)
              .then(100)
              .otherwise(100 - (100 / (1 + pl.col('_avg_gain') / pl.col('_avg_loss'))))
              .alias(result_col)
        )

        # 删除临时列
        df = df.drop(['_price_change', '_gain', '_loss', '_avg_gain', '_avg_loss'])

        return df

    @staticmethod
    def momentum(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        动量指标 (Momentum)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Momentum 列的 DataFrame
        """
        if result_col is None:
            result_col = f'Momentum_{period}'

        df = df.with_columns(
            (pl.col(column) - pl.col(column).shift(period)).alias(result_col)
        )

        return df

    @staticmethod
    def roc(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        变动率指标 (Rate of Change)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 ROC 列的 DataFrame
        """
        if result_col is None:
            result_col = f'ROC_{period}'

        df = df.with_columns(
            ((pl.col(column) - pl.col(column).shift(period)) / pl.col(column).shift(period) * 100).alias(result_col)
        )

        return df


class VolatilityIndicators:
    """波动率指标类"""

    @staticmethod
    def bollinger_bands(df: pl.DataFrame, column: str, period: int = 20, num_std: float = 2.0) -> pl.DataFrame:
        """
        布林带 (Bollinger Bands)

        参数:
        df: Polars DataFrame
        column: 要计算的列名（通常是收盘价）
        period: 计算周期（默认 20）
        num_std: 标准差倍数（默认 2.0）

        返回:
        pl.DataFrame: 添加了 BB_Upper_{period}, BB_Middle_{period}, BB_Lower_{period} 列的 DataFrame
        """
        # 计算中轨（SMA）
        df = df.with_columns(
            pl.col(column).rolling_mean(window_size=period).alias(f'BB_Middle_{period}')
        )

        # 计算标准差
        df = df.with_columns(
            pl.col(column).rolling_std(window_size=period).alias('_bb_std')
        )

        # 计算上下轨
        df = df.with_columns([
            (pl.col(f'BB_Middle_{period}') + num_std * pl.col('_bb_std')).alias(f'BB_Upper_{period}'),
            (pl.col(f'BB_Middle_{period}') - num_std * pl.col('_bb_std')).alias(f'BB_Lower_{period}')
        ])

        # 删除临时列
        df = df.drop('_bb_std')

        return df

    @staticmethod
    def atr(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
            period: int = 14, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        平均真实波幅 (Average True Range)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period: 计算周期（默认 14）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 ATR 列的 DataFrame
        """
        if result_col is None:
            result_col = f'ATR_{period}'

        # 计算真实波幅 (True Range)
        df = df.with_columns([
            (pl.col(high_col) - pl.col(low_col)).alias('_tr1'),
            (pl.col(high_col) - pl.col(close_col).shift(1)).abs().alias('_tr2'),
            (pl.col(low_col) - pl.col(close_col).shift(1)).abs().alias('_tr3')
        ])

        # 取三者最大值作为真实波幅
        df = df.with_columns(
            pl.max_horizontal('_tr1', '_tr2', '_tr3').alias('_tr')
        )

        # 计算 ATR - 使用 Wilder's Smoothing (SMMA): alpha = 1/period
        # TA-Lib 使用这种平滑方式，与标准 EMA 不同
        df = df.with_columns(
            pl.col('_tr').ewm_mean(alpha=1/period, adjust=False, min_periods=period).alias(result_col)
        )

        # 删除临时列
        df = df.drop(['_tr1', '_tr2', '_tr3', '_tr'])

        return df

    @staticmethod
    def volatility(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        波动率 (Volatility) - 使用标准差计算

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Volatility 列的 DataFrame
        """
        if result_col is None:
            result_col = f'Volatility_{period}'

        df = df.with_columns(
            pl.col(column).rolling_std(window_size=period).alias(result_col)
        )

        return df


class VolumeIndicators:
    """成交量指标类"""

    @staticmethod
    def obv(df: pl.DataFrame, close_col: str, volume_col: str, result_col: str = 'OBV') -> pl.DataFrame:
        """
        能量潮 (On Balance Volume)

        参数:
        df: Polars DataFrame
        close_col: 收盘价列名
        volume_col: 成交量列名
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 OBV 列的 DataFrame
        """
        # 计算价格变化
        df = df.with_columns(
            (pl.col(close_col) - pl.col(close_col).shift(1)).alias('_price_change')
        )

        # 根据价格变化计算成交量方向
        df = df.with_columns(
            pl.when(pl.col('_price_change') > 0)
              .then(pl.col(volume_col))
              .when(pl.col('_price_change') < 0)
              .then(-pl.col(volume_col))
              .otherwise(0)
              .alias('_signed_volume')
        )

        # 计算累计成交量
        df = df.with_columns(
            pl.col('_signed_volume').cum_sum().alias(result_col)
        )

        # 删除临时列
        df = df.drop(['_price_change', '_signed_volume'])

        return df

    @staticmethod
    def volume_sma(df: pl.DataFrame, volume_col: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        成交量移动平均线

        参数:
        df: Polars DataFrame
        volume_col: 成交量列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Volume_SMA 列的 DataFrame
        """
        if result_col is None:
            result_col = f'Volume_SMA_{period}'

        df = df.with_columns(
            pl.col(volume_col).rolling_mean(window_size=period).alias(result_col)
        )

        return df

    @staticmethod
    def vwap(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
             volume_col: str, result_col: str = 'VWAP') -> pl.DataFrame:
        """
        成交量加权平均价 (Volume Weighted Average Price)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        volume_col: 成交量列名
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 VWAP 列的 DataFrame
        """
        # 计算典型价格
        df = df.with_columns(
            ((pl.col(high_col) + pl.col(low_col) + pl.col(close_col)) / 3).alias('_typical_price')
        )

        # 计算成交额
        df = df.with_columns(
            (pl.col('_typical_price') * pl.col(volume_col)).alias('_pv')
        )

        # 计算 VWAP
        df = df.with_columns(
            (pl.col('_pv').cum_sum() / pl.col(volume_col).cum_sum()).alias(result_col)
        )

        # 删除临时列
        df = df.drop(['_typical_price', '_pv'])

        return df


class OscillatorIndicators:
    """震荡指标类"""

    @staticmethod
    def macd(df: pl.DataFrame, column: str, fast_period: int = 12,
             slow_period: int = 26, signal_period: int = 9) -> pl.DataFrame:
        """
        MACD (Moving Average Convergence Divergence)

        参数:
        df: Polars DataFrame
        column: 要计算的列名（通常是收盘价）
        fast_period: 快线周期（默认 12）
        slow_period: 慢线周期（默认 26）
        signal_period: 信号线周期（默认 9）

        返回:
        pl.DataFrame: 添加了 MACD_Line, MACD_Signal, MACD_Hist 列的 DataFrame
        """
        # 计算快线和慢线 EMA - 使用标准 EMA，与 TA-Lib 一致
        # 使用 adjust=True, min_periods 与 TA-Lib 匹配
        df = df.with_columns([
            pl.col(column).ewm_mean(span=fast_period, adjust=True, min_periods=fast_period).alias('_ema_fast'),
            pl.col(column).ewm_mean(span=slow_period, adjust=True, min_periods=slow_period).alias('_ema_slow')
        ])

        # 计算 MACD 线
        df = df.with_columns(
            (pl.col('_ema_fast') - pl.col('_ema_slow')).alias('MACD_Line')
        )

        # 计算信号线 - 同样使用标准 EMA
        df = df.with_columns(
            pl.col('MACD_Line').ewm_mean(span=signal_period, adjust=True, min_periods=signal_period).alias('MACD_Signal')
        )

        # 计算 MACD 柱状图
        df = df.with_columns(
            (pl.col('MACD_Line') - pl.col('MACD_Signal')).alias('MACD_Hist')
        )

        # 删除临时列
        df = df.drop(['_ema_fast', '_ema_slow'])

        return df

    @staticmethod
    def stochastic(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                   k_period: int = 14, d_period: int = 3) -> pl.DataFrame:
        """
        随机指标 (Stochastic Oscillator)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        k_period: K线周期（默认 14）
        d_period: D线周期（默认 3）

        返回:
        pl.DataFrame: 添加了 Stoch_K, Stoch_D 列的 DataFrame
        """
        # 计算周期内的最高价和最低价
        df = df.with_columns([
            pl.col(high_col).rolling_max(window_size=k_period).alias('_highest_high'),
            pl.col(low_col).rolling_min(window_size=k_period).alias('_lowest_low')
        ])

        # 计算 %K
        df = df.with_columns(
            ((pl.col(close_col) - pl.col('_lowest_low')) /
             (pl.col('_highest_high') - pl.col('_lowest_low')) * 100).alias('Stoch_K')
        )

        # 计算 %D（%K 的移动平均）
        df = df.with_columns(
            pl.col('Stoch_K').rolling_mean(window_size=d_period).alias('Stoch_D')
        )

        # 删除临时列
        df = df.drop(['_highest_high', '_lowest_low'])

        return df

    @staticmethod
    def cci(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
            period: int = 20, result_col: str = 'CCI') -> pl.DataFrame:
        """
        顺势指标 (Commodity Channel Index)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period: 计算周期（默认 20）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 CCI 列的 DataFrame
        """
        # 计算典型价格
        df = df.with_columns(
            ((pl.col(high_col) + pl.col(low_col) + pl.col(close_col)) / 3).alias('_tp')
        )

        # 计算典型价格的移动平均
        df = df.with_columns(
            pl.col('_tp').rolling_mean(window_size=period).alias('_tp_sma')
        )

        # 计算平均绝对偏差
        df = df.with_columns(
            (pl.col('_tp') - pl.col('_tp_sma')).abs().rolling_mean(window_size=period).alias('_mad')
        )

        # 计算 CCI
        df = df.with_columns(
            ((pl.col('_tp') - pl.col('_tp_sma')) / (0.015 * pl.col('_mad'))).alias(result_col)
        )

        # 删除临时列
        df = df.drop(['_tp', '_tp_sma', '_mad'])

        return df


class PriceIndicators:
    """价格相关指标类"""

    @staticmethod
    def price_change(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        价格变化

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: 周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Price_Change 列的 DataFrame
        """
        if result_col is None:
            result_col = f'Price_Change_{period}d'

        df = df.with_columns(
            (pl.col(column) - pl.col(column).shift(period)).alias(result_col)
        )

        return df

    @staticmethod
    def price_change_pct(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        价格变化百分比

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: 周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Price_Change_Pct 列的 DataFrame
        """
        if result_col is None:
            result_col = f'Price_Change_Pct_{period}d'

        df = df.with_columns(
            ((pl.col(column) - pl.col(column).shift(period)) / pl.col(column).shift(period) * 100).alias(result_col)
        )

        return df


class AdvancedTrendIndicators:
    """高级趋势指标类"""

    @staticmethod
    def hma(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        赫尔移动平均线 (Hull Moving Average)
        HMA = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 HMA 列的 DataFrame
        """
        if result_col is None:
            result_col = f'HMA_{period}'

        import numpy as np

        half_period = int(period / 2)
        sqrt_period = int(np.sqrt(period))

        # 计算 WMA(n/2)
        df = TrendIndicators.wma(df, column, half_period, '_wma_half')

        # 计算 WMA(n)
        df = TrendIndicators.wma(df, column, period, '_wma_full')

        # 计算 2 * WMA(n/2) - WMA(n)
        df = df.with_columns(
            (2 * pl.col('_wma_half') - pl.col('_wma_full')).alias('_diff')
        )

        # 计算最终的 HMA
        df = TrendIndicators.wma(df, '_diff', sqrt_period, result_col)

        # 删除临时列
        df = df.drop(['_wma_half', '_wma_full', '_diff'])

        return df

    @staticmethod
    def trix(df: pl.DataFrame, column: str, period: int = 15, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        三重指数平滑平均线 (TRIX)
        TRIX = (EMA(EMA(EMA(price))) - prev_EMA3) / prev_EMA3 * 100

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认15）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 TRIX 列的 DataFrame
        """
        if result_col is None:
            result_col = f'TRIX_{period}'

        # 第一次 EMA
        df = df.with_columns(
            pl.col(column).ewm_mean(span=period, adjust=False).alias('_ema1')
        )

        # 第二次 EMA
        df = df.with_columns(
            pl.col('_ema1').ewm_mean(span=period, adjust=False).alias('_ema2')
        )

        # 第三次 EMA
        df = df.with_columns(
            pl.col('_ema2').ewm_mean(span=period, adjust=False).alias('_ema3')
        )

        # 计算 TRIX
        df = df.with_columns(
            ((pl.col('_ema3') - pl.col('_ema3').shift(1)) / pl.col('_ema3').shift(1) * 100).alias(result_col)
        )

        # 删除临时列
        df = df.drop(['_ema1', '_ema2', '_ema3'])

        return df

    @staticmethod
    def vwma(df: pl.DataFrame, price_col: str, volume_col: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        成交量加权移动平均 (Volume Weighted Moving Average)

        参数:
        df: Polars DataFrame
        price_col: 价格列名
        volume_col: 成交量列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 VWMA 列的 DataFrame
        """
        if result_col is None:
            result_col = f'VWMA_{period}'

        # 计算价格 * 成交量
        df = df.with_columns(
            (pl.col(price_col) * pl.col(volume_col)).alias('_pv')
        )

        # 计算滚动窗口内的 sum(pv) / sum(volume)
        df = df.with_columns(
            (pl.col('_pv').rolling_sum(window_size=period) /
             pl.col(volume_col).rolling_sum(window_size=period)).alias(result_col)
        )

        # 删除临时列
        df = df.drop('_pv')

        return df

    @staticmethod
    def smma(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        平滑移动平均 (Smoothed Moving Average / RMA)

        SMMA[i] = (SMMA[i-1] * (period - 1) + Price[i]) / period
        等同于 EMA with alpha = 1/period

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 SMMA 列的 DataFrame

        用途:
        - 比SMA更平滑
        - 常用于ATR、ADX等指标的平滑
        """
        if result_col is None:
            result_col = f'SMMA_{period}'

        # SMMA等同于alpha=1/period的EMA
        smma = df[column].ewm_mean(alpha=1/period, adjust=False)

        return df.with_columns(smma.alias(result_col))

    @staticmethod
    def lwma(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        线性加权移动平均 (Linear Weighted Moving Average)

        LWMA = (n*P1 + (n-1)*P2 + ... + 1*Pn) / (n + (n-1) + ... + 1)
        权重线性递减

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 LWMA 列的 DataFrame

        用途:
        - 比WMA更重视近期价格
        - 权重线性分布
        """
        if result_col is None:
            result_col = f'LWMA_{period}'

        import numpy as np

        # 创建线性权重：n, n-1, ..., 2, 1
        weights = np.arange(period, 0, -1)
        weight_sum = weights.sum()

        # 使用rolling_map计算LWMA
        lwma = df[column].rolling_map(
            lambda s: np.dot(s, weights) / weight_sum if len(s) == period else None,
            window_size=period
        )

        return df.with_columns(lwma.alias(result_col))

    @staticmethod
    def tma(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        三角移动平均 (Triangular Moving Average)

        TMA = SMA(SMA(price, n), n)
        双重平滑，形成三角形权重分布

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 TMA 列的 DataFrame

        用途:
        - 极度平滑的趋势线
        - 滞后性较大，但噪音最小
        """
        if result_col is None:
            result_col = f'TMA_{period}'

        # 第一次SMA
        sma1 = df[column].rolling_mean(window_size=period)

        # 第二次SMA
        tma = sma1.rolling_mean(window_size=period)

        return df.with_columns(tma.alias(result_col))

    @staticmethod
    def zlema(df: pl.DataFrame, column: str, period: int, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        零滞后指数移动平均 (Zero Lag Exponential Moving Average)

        ZLEMA = EMA(Price + (Price - Price[lag]), period)
        lag = (period - 1) / 2

        通过价格外推减少EMA的滞后

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 ZLEMA 列的 DataFrame

        用途:
        - 减少传统EMA的滞后
        - 更快响应价格变化
        """
        if result_col is None:
            result_col = f'ZLEMA_{period}'

        # 计算滞后期数
        lag = int((period - 1) / 2)

        # 计算价格变化：Price - Price[lag]
        price_change = df[column] - df[column].shift(lag)

        # 外推价格：Price + (Price - Price[lag])
        adjusted_price = df[column] + price_change

        # 对外推价格计算EMA
        zlema = adjusted_price.ewm_mean(span=period, adjust=False)

        return df.with_columns(zlema.alias(result_col))

    @staticmethod
    def t3(df: pl.DataFrame, column: str, period: int = 5, vfactor: float = 0.7,
           result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Tillson T3 移动平均 (T3 Moving Average)

        T3是GD(Generalized DEMA)的特例，通过6次EMA平滑
        公式较复杂，结果是超级平滑的曲线

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认5）
        vfactor: 体积因子（默认0.7，范围0-1）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 T3 列的 DataFrame

        用途:
        - 极度平滑，几乎无噪音
        - 适合识别长期趋势
        - 滞后性较大
        """
        if result_col is None:
            result_col = f'T3_{period}'

        # T3系数
        c1 = -vfactor ** 3
        c2 = 3 * vfactor ** 2 + 3 * vfactor ** 3
        c3 = -6 * vfactor ** 2 - 3 * vfactor - 3 * vfactor ** 3
        c4 = 1 + 3 * vfactor + vfactor ** 3 + 3 * vfactor ** 2

        # 6次EMA
        ema1 = df[column].ewm_mean(span=period, adjust=False)
        ema2 = ema1.ewm_mean(span=period, adjust=False)
        ema3 = ema2.ewm_mean(span=period, adjust=False)
        ema4 = ema3.ewm_mean(span=period, adjust=False)
        ema5 = ema4.ewm_mean(span=period, adjust=False)
        ema6 = ema5.ewm_mean(span=period, adjust=False)

        # T3 = c1*ema6 + c2*ema5 + c3*ema4 + c4*ema3
        t3 = c1 * ema6 + c2 * ema5 + c3 * ema4 + c4 * ema3

        return df.with_columns(t3.alias(result_col))

    @staticmethod
    def alma(df: pl.DataFrame, column: str, period: int = 9, offset: float = 0.85,
             sigma: float = 6.0, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Arnaud Legoux 移动平均 (ALMA)

        使用高斯分布作为权重，可以同时减少滞后和平滑噪音

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认9）
        offset: 偏移量（默认0.85，范围0-1）
        sigma: 高斯标准差（默认6.0）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 ALMA 列的 DataFrame

        用途:
        - 平衡平滑性和响应速度
        - 通过offset调整：接近1时更敏感，接近0时更平滑
        """
        if result_col is None:
            result_col = f'ALMA_{period}'

        import numpy as np

        # 计算高斯权重
        m = offset * (period - 1)
        s = period / sigma

        # 生成权重
        weights = np.zeros(period)
        weight_sum = 0

        for i in range(period):
            weights[i] = np.exp(-((i - m) ** 2) / (2 * s ** 2))
            weight_sum += weights[i]

        # 标准化权重
        weights = weights / weight_sum

        # 翻转权重（最新的数据权重最大）
        weights = weights[::-1]

        # 使用rolling_map计算ALMA
        alma = df[column].rolling_map(
            lambda x: np.dot(x, weights) if len(x) == period else None,
            window_size=period
        )

        return df.with_columns(alma.alias(result_col))

    @staticmethod
    def jma(df: pl.DataFrame, column: str, period: int = 7, phase: float = 0,
            power: float = 2, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Jurik 移动平均 (JMA)

        专业级平滑算法，在减少滞后的同时保持平滑性
        这是一个简化版本的实现

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认7）
        phase: 相位调整（默认0，范围-100到100）
        power: 功率参数（默认2）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 JMA 列的 DataFrame

        用途:
        - 专业交易员使用
        - 极佳的平滑性和响应性平衡
        - 可通过phase调整滞后
        """
        if result_col is None:
            result_col = f'JMA_{period}'

        import numpy as np

        # JMA完整实现非常复杂，这里使用简化版
        # 使用自适应EMA来近似JMA

        # 计算动态alpha
        price = df[column].to_numpy()
        n = len(price)

        # 初始化
        jma_values = np.full(n, np.nan)
        if n > 0:
            jma_values[0] = price[0]

        # 计算参数
        phase_ratio = phase / 100 if -100 <= phase <= 100 else 0
        beta = 0.45 * (period - 1) / (0.45 * (period - 1) + 2)

        # 简化的JMA计算
        for i in range(1, n):
            # 价格变化率
            if not np.isnan(jma_values[i-1]):
                volatility = abs(price[i] - jma_values[i-1])

                # 自适应alpha
                if volatility > 0:
                    alpha = np.power(beta, power)
                else:
                    alpha = beta

                # 相位调整
                alpha = alpha * (1 + phase_ratio)
                alpha = max(0, min(1, alpha))

                # 更新JMA
                jma_values[i] = alpha * price[i] + (1 - alpha) * jma_values[i-1]
            else:
                jma_values[i] = price[i]

        df = df.with_columns(
            pl.Series(result_col, jma_values)
        )

        return df

    @staticmethod
    def mcginley_dynamic(df: pl.DataFrame, column: str, period: int = 14,
                         result_col: Optional[str] = None) -> pl.DataFrame:
        """
        McGinley Dynamic 指标

        自动调整的移动平均，随市场速度变化而变化
        MD[i] = MD[i-1] + (Price - MD[i-1]) / (K * N * (Price/MD[i-1])^4)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认14）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 McGinley Dynamic 列的 DataFrame

        用途:
        - 自动跟踪市场
        - 减少假信号
        - 不需要调整参数
        """
        if result_col is None:
            result_col = f'McGinley_{period}'

        import numpy as np

        price = df[column].to_numpy()
        n = len(price)

        # 初始化：使用SMA
        md = np.full(n, np.nan)

        # 第一个值使用价格本身
        if n > 0:
            md[0] = price[0]

        # 计算McGinley Dynamic
        for i in range(1, n):
            if not np.isnan(md[i-1]) and md[i-1] > 0:
                # 价格与MD的比率
                ratio = price[i] / md[i-1]

                # 防止除零和过大值
                if ratio > 0:
                    k = period * ratio ** 4
                    k = max(1, k)  # 防止k过小

                    # McGinley公式
                    md[i] = md[i-1] + (price[i] - md[i-1]) / k
                else:
                    md[i] = md[i-1]
            else:
                md[i] = price[i]

        df = df.with_columns(
            pl.Series(result_col, md)
        )

        return df

    @staticmethod
    def frama(df: pl.DataFrame, column: str, period: int = 16,
             result_col: Optional[str] = None) -> pl.DataFrame:
        """
        FRAMA (Fractal Adaptive Moving Average) - 分形自适应移动平均

        根据市场分形维度自动调整平滑度
        在趋势市场中快速响应，在震荡市场中平滑

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认16，必须是偶数）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 FRAMA 列的 DataFrame

        用途:
        - 自适应趋势跟踪
        - 减少震荡市场假信号
        - 保持趋势市场响应性
        """
        if result_col is None:
            result_col = f'FRAMA_{period}'

        import numpy as np

        if period % 2 != 0:
            period = period + 1  # 确保是偶数

        price = df[column].to_numpy()
        n = len(price)
        frama = np.full(n, np.nan)

        # 初始化
        if n > 0:
            frama[0] = price[0]

        half_period = period // 2

        for i in range(period, n):
            # 计算两个半周期的最高和最低
            h1 = np.max(price[i - period:i - half_period])
            l1 = np.min(price[i - period:i - half_period])
            n1 = (h1 - l1) / half_period

            h2 = np.max(price[i - half_period:i])
            l2 = np.min(price[i - half_period:i])
            n2 = (h2 - l2) / half_period

            h3 = np.max(price[i - period:i])
            l3 = np.min(price[i - period:i])
            n3 = (h3 - l3) / period

            # 计算分形维度
            if n1 > 0 and n2 > 0 and n3 > 0:
                dimen = (np.log(n1 + n2) - np.log(n3)) / np.log(2)
                dimen = max(1.0, min(dimen, 2.0))  # 限制在1-2之间
            else:
                dimen = 1.5

            # 计算自适应alpha
            alpha = np.exp(-4.6 * (dimen - 1))
            alpha = max(0.01, min(alpha, 1.0))

            # 更新FRAMA
            if not np.isnan(frama[i-1]):
                frama[i] = alpha * price[i] + (1 - alpha) * frama[i-1]
            else:
                frama[i] = price[i]

        df = df.with_columns(
            pl.Series(result_col, frama)
        )

        return df

    @staticmethod
    def mama(df: pl.DataFrame, column: str, fast_limit: float = 0.5,
            slow_limit: float = 0.05, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        MAMA (MESA Adaptive Moving Average) - Mesa自适应移动平均

        由John Ehlers开发，基于希尔伯特变换的自适应MA
        根据市场周期自动调整

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        fast_limit: 快速限制（默认0.5）
        slow_limit: 慢速限制（默认0.05）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 MAMA, FAMA 列的 DataFrame

        用途:
        - 周期自适应
        - MAMA/FAMA交叉信号
        - 减少滞后
        """
        if result_col is None:
            result_col = f'MAMA'

        import numpy as np

        price = df[column].to_numpy()
        n = len(price)

        mama = np.full(n, np.nan)
        fama = np.full(n, np.nan)

        # 简化版MAMA实现
        # 完整实现需要希尔伯特变换，这里使用近似方法

        # 初始化
        if n > 0:
            mama[0] = price[0]
            fama[0] = price[0]

        for i in range(1, n):
            # 计算价格变化率
            if i > 5:
                price_change = abs(price[i] - price[i-1])
                avg_change = np.mean(np.abs(np.diff(price[max(0, i-20):i])))

                # 自适应alpha
                if avg_change > 0:
                    volatility_ratio = price_change / avg_change
                    alpha = slow_limit + (fast_limit - slow_limit) * min(volatility_ratio, 1.0)
                else:
                    alpha = slow_limit
            else:
                alpha = slow_limit

            # 更新MAMA和FAMA
            if not np.isnan(mama[i-1]):
                mama[i] = alpha * price[i] + (1 - alpha) * mama[i-1]
                fama[i] = 0.5 * alpha * mama[i] + (1 - 0.5 * alpha) * fama[i-1]
            else:
                mama[i] = price[i]
                fama[i] = price[i]

        df = df.with_columns([
            pl.Series(result_col, mama),
            pl.Series(f'{result_col.split("_")[0]}_FAMA', fama)
        ])

        return df

    @staticmethod
    def linear_regression(df: pl.DataFrame, column: str, period: int = 14,
                         result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Linear Regression - 线性回归

        对价格序列进行线性回归拟合
        提供趋势线

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 回归周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 LinReg 列的 DataFrame

        用途:
        - 趋势线识别
        - 支撑阻力位
        - 价格预测
        """
        if result_col is None:
            result_col = f'LinReg_{period}'

        import numpy as np

        price = df[column].to_numpy()
        n = len(price)
        linreg = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = price[i - period + 1:i + 1]
            x = np.arange(period)

            # 线性回归
            slope, intercept = np.polyfit(x, window, 1)

            # 当前值（回归线的最后一个点）
            linreg[i] = slope * (period - 1) + intercept

        df = df.with_columns(
            pl.Series(result_col, linreg)
        )

        return df

    @staticmethod
    def time_series_forecast(df: pl.DataFrame, column: str, period: int = 14,
                            forecast_periods: int = 1, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Time Series Forecast - 时间序列预测

        基于线性回归的简单预测
        向前预测N个周期

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 回归周期
        forecast_periods: 预测周期数（默认1）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 TSF 列的 DataFrame

        用途:
        - 短期价格预测
        - 趋势延伸
        - 目标位设定
        """
        if result_col is None:
            result_col = f'TSF_{period}_{forecast_periods}'

        import numpy as np

        price = df[column].to_numpy()
        n = len(price)
        tsf = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = price[i - period + 1:i + 1]
            x = np.arange(period)

            # 线性回归
            slope, intercept = np.polyfit(x, window, 1)

            # 预测未来值
            tsf[i] = slope * (period - 1 + forecast_periods) + intercept

        df = df.with_columns(
            pl.Series(result_col, tsf)
        )

        return df

    @staticmethod
    def projection_bands(df: pl.DataFrame, column: str, period: int = 14,
                        num_std: float = 2.0) -> pl.DataFrame:
        """
        Projection Bands - 投影带

        基于线性回归的通道
        中轨是回归线，上下轨是标准差带

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期
        num_std: 标准差倍数（默认2.0）

        返回:
        pl.DataFrame: 添加了 ProjBand_Upper, ProjBand_Middle, ProjBand_Lower 列的 DataFrame

        用途:
        - 趋势通道
        - 突破信号
        - 支撑阻力
        """
        import numpy as np

        price = df[column].to_numpy()
        n = len(price)

        middle = np.full(n, np.nan)
        upper = np.full(n, np.nan)
        lower = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = price[i - period + 1:i + 1]
            x = np.arange(period)

            # 线性回归
            slope, intercept = np.polyfit(x, window, 1)
            regression_line = slope * x + intercept

            # 计算残差的标准差
            residuals = window - regression_line
            std_dev = np.std(residuals, ddof=1)

            # 当前值
            current_value = slope * (period - 1) + intercept

            middle[i] = current_value
            upper[i] = current_value + num_std * std_dev
            lower[i] = current_value - num_std * std_dev

        df = df.with_columns([
            pl.Series(f'ProjBand_Upper_{period}', upper),
            pl.Series(f'ProjBand_Middle_{period}', middle),
            pl.Series(f'ProjBand_Lower_{period}', lower)
        ])

        return df


class AdvancedVolatilityIndicators:
    """高级波动率指标类"""

    @staticmethod
    def keltner_channels(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                        ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0) -> pl.DataFrame:
        """
        肯特纳通道 (Keltner Channels)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        ema_period: EMA周期（默认20）
        atr_period: ATR周期（默认10）
        multiplier: ATR倍数（默认2.0）

        返回:
        pl.DataFrame: 添加了 KC_Upper, KC_Middle, KC_Lower 列的 DataFrame
        """
        # 计算中轨（EMA）
        df = df.with_columns(
            pl.col(close_col).ewm_mean(span=ema_period, adjust=False).alias('KC_Middle')
        )

        # 计算 ATR
        df = VolatilityIndicators.atr(df, high_col, low_col, close_col, atr_period, '_kc_atr')

        # 计算上下轨
        df = df.with_columns([
            (pl.col('KC_Middle') + multiplier * pl.col('_kc_atr')).alias('KC_Upper'),
            (pl.col('KC_Middle') - multiplier * pl.col('_kc_atr')).alias('KC_Lower')
        ])

        # 删除临时列
        df = df.drop('_kc_atr')

        return df

    @staticmethod
    def donchian_channel(df: pl.DataFrame, high_col: str, low_col: str, period: int = 20) -> pl.DataFrame:
        """
        唐奇安通道 (Donchian Channel)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        period: 计算周期（默认20）

        返回:
        pl.DataFrame: 添加了 DC_Upper, DC_Middle, DC_Lower 列的 DataFrame
        """
        # 计算上轨（周期内最高价）
        df = df.with_columns(
            pl.col(high_col).rolling_max(window_size=period).alias('DC_Upper')
        )

        # 计算下轨（周期内最低价）
        df = df.with_columns(
            pl.col(low_col).rolling_min(window_size=period).alias('DC_Lower')
        )

        # 计算中轨（上下轨平均）
        df = df.with_columns(
            ((pl.col('DC_Upper') + pl.col('DC_Lower')) / 2).alias('DC_Middle')
        )

        return df

    @staticmethod
    def true_range_pct(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, result_col: str = 'TR_Pct') -> pl.DataFrame:
        """
        真实波幅百分比 (True Range Percentage)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 TR_Pct 列的 DataFrame
        """
        # 计算真实波幅
        df = df.with_columns([
            (pl.col(high_col) - pl.col(low_col)).alias('_tr1'),
            (pl.col(high_col) - pl.col(close_col).shift(1)).abs().alias('_tr2'),
            (pl.col(low_col) - pl.col(close_col).shift(1)).abs().alias('_tr3')
        ])

        df = df.with_columns(
            pl.max_horizontal('_tr1', '_tr2', '_tr3').alias('_tr')
        )

        # 计算真实波幅百分比
        df = df.with_columns(
            (pl.col('_tr') / pl.col(close_col) * 100).alias(result_col)
        )

        # 删除临时列
        df = df.drop(['_tr1', '_tr2', '_tr3', '_tr'])

        return df

    @staticmethod
    def historical_volatility(df: pl.DataFrame, column: str, period: int = 20,
                             annualize: bool = True, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Historical Volatility - 历史波动率

        使用对数收益率的标准差计算

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: 计算周期（默认20）
        annualize: 是否年化（默认True）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 HV 列的 DataFrame

        用途:
        - 衡量价格波动程度
        - 期权定价
        - 风险管理
        """
        if result_col is None:
            result_col = f'HV_{period}'

        import numpy as np

        # 计算对数收益率
        log_returns = (df[column] / df[column].shift(1)).log()

        # 计算滚动标准差
        hv = log_returns.rolling_std(window_size=period)

        # 年化（假设252个交易日）
        if annualize:
            hv = hv * np.sqrt(252)

        df = df.with_columns(hv.alias(result_col))

        return df

    @staticmethod
    def chaikin_volatility(df: pl.DataFrame, high_col: str, low_col: str,
                          ema_period: int = 10, roc_period: int = 10,
                          result_col: str = 'Chaikin_Vol') -> pl.DataFrame:
        """
        Chaikin Volatility - 蔡金波动率

        基于高低价差的变化率

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        ema_period: EMA周期（默认10）
        roc_period: ROC周期（默认10）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Chaikin_Vol 列的 DataFrame

        用途:
        - 识别波动率变化
        - 正值：波动率增加，负值：波动率减少
        """
        # 高低价差
        hl_diff = df[high_col] - df[low_col]

        # 对差值计算EMA
        ema_hl = hl_diff.ewm_mean(span=ema_period, adjust=False)

        # 计算ROC
        chaikin_vol = (ema_hl - ema_hl.shift(roc_period)) / ema_hl.shift(roc_period) * 100

        df = df.with_columns(chaikin_vol.alias(result_col))

        return df

    @staticmethod
    def atr_trailing_stop(df: pl.DataFrame, high_col: str, low_col: str,
                         close_col: str, atr_period: int = 14,
                         multiplier: float = 3.0) -> pl.DataFrame:
        """
        ATR Trailing Stop - ATR跟踪止损

        基于ATR的动态止损位

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col: 价格列名
        atr_period: ATR周期（默认14）
        multiplier: ATR倍数（默认3.0）

        返回:
        pl.DataFrame: 添加了 ATR_Stop_Long, ATR_Stop_Short 列的 DataFrame

        用途:
        - 动态止损位
        - 趋势跟踪
        - Long Stop：价格跌破则平多仓
        - Short Stop：价格突破则平空仓
        """
        import numpy as np

        # 先计算ATR（如果还没有）
        if f'ATR_{atr_period}' not in df.columns:
            from . import indicators
            df = VolatilityIndicators.atr(df, high_col, low_col, close_col, atr_period)

        # 转为numpy进行迭代计算
        close = df[close_col].to_numpy()
        atr = df[f'ATR_{atr_period}'].to_numpy()

        n = len(close)
        stop_long = np.full(n, np.nan)
        stop_short = np.full(n, np.nan)

        for i in range(1, n):
            if not np.isnan(atr[i]):
                # Long止损：收盘价 - multiplier * ATR
                basic_stop_long = close[i] - multiplier * atr[i]

                # 止损只能上移，不能下移
                if not np.isnan(stop_long[i-1]):
                    stop_long[i] = max(basic_stop_long, stop_long[i-1])
                else:
                    stop_long[i] = basic_stop_long

                # Short止损：收盘价 + multiplier * ATR
                basic_stop_short = close[i] + multiplier * atr[i]

                # 止损只能下移，不能上移
                if not np.isnan(stop_short[i-1]):
                    stop_short[i] = min(basic_stop_short, stop_short[i-1])
                else:
                    stop_short[i] = basic_stop_short

        df = df.with_columns([
            pl.Series('ATR_Stop_Long', stop_long),
            pl.Series('ATR_Stop_Short', stop_short)
        ])

        return df

    @staticmethod
    def normalized_atr(df: pl.DataFrame, high_col: str, low_col: str,
                      close_col: str, period: int = 14,
                      result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Normalized ATR (NATR) - 标准化ATR

        ATR除以收盘价，便于跨市场比较

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col: 价格列名
        period: ATR周期（默认14）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 NATR 列的 DataFrame

        用途:
        - 比较不同价格水平的波动率
        - 归一化表示，百分比形式
        """
        if result_col is None:
            result_col = f'NATR_{period}'

        # 先计算ATR（如果还没有）
        if f'ATR_{period}' not in df.columns:
            from . import indicators
            df = VolatilityIndicators.atr(df, high_col, low_col, close_col, period)

        # 标准化：ATR / 收盘价 * 100
        natr = df[f'ATR_{period}'] / df[close_col] * 100

        df = df.with_columns(natr.alias(result_col))

        return df

    @staticmethod
    def parkinson_volatility(df: pl.DataFrame, high_col: str, low_col: str,
                            period: int = 20, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Parkinson Volatility - Parkinson波动率

        使用高低价信息的高效波动率估计
        公式：sqrt(1/(4*n*ln2) * sum((ln(High/Low))^2))

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        period: 计算周期（默认20）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Parkinson_Vol 列的 DataFrame

        用途:
        - 比标准差更高效的波动率估计
        - 利用日内高低价信息
        - 适用于高频数据
        """
        if result_col is None:
            result_col = f'Parkinson_{period}'

        import numpy as np

        # 计算 ln(High/Low)
        hl_ratio = (df[high_col] / df[low_col]).log()

        # 计算平方
        hl_ratio_sq = hl_ratio ** 2

        # 滚动求和
        sum_sq = hl_ratio_sq.rolling_sum(window_size=period)

        # Parkinson公式
        # Vol = sqrt(1/(4*n*ln2) * sum)
        factor = 1 / (4 * period * np.log(2))
        parkinson = (factor * sum_sq).sqrt()

        # 年化（假设252个交易日）
        parkinson = parkinson * np.sqrt(252)

        df = df.with_columns(parkinson.alias(result_col))

        return df


class AdvancedVolumeIndicators:
    """高级成交量指标类"""

    @staticmethod
    def cmf(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, volume_col: str, period: int = 20) -> pl.DataFrame:
        """
        蔡金资金流量 (Chaikin Money Flow)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        volume_col: 成交量列名
        period: 计算周期（默认20）

        返回:
        pl.DataFrame: 添加了 CMF 列的 DataFrame
        """
        # 计算资金流量乘数
        df = df.with_columns(
            (((pl.col(close_col) - pl.col(low_col)) - (pl.col(high_col) - pl.col(close_col))) /
             (pl.col(high_col) - pl.col(low_col))).alias('_mf_multiplier')
        )

        # 计算资金流量成交量
        df = df.with_columns(
            (pl.col('_mf_multiplier') * pl.col(volume_col)).alias('_mf_volume')
        )

        # 计算 CMF
        df = df.with_columns(
            (pl.col('_mf_volume').rolling_sum(window_size=period) /
             pl.col(volume_col).rolling_sum(window_size=period)).alias('CMF')
        )

        # 删除临时列
        df = df.drop(['_mf_multiplier', '_mf_volume'])

        return df

    @staticmethod
    def fi(df: pl.DataFrame, close_col: str, volume_col: str, period: int = 13, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        力度指标 (Force Index)

        参数:
        df: Polars DataFrame
        close_col: 收盘价列名
        volume_col: 成交量列名
        period: EMA平滑周期（默认13）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 FI 列的 DataFrame
        """
        if result_col is None:
            result_col = f'FI_{period}'

        # 计算原始力度指标
        df = df.with_columns(
            ((pl.col(close_col) - pl.col(close_col).shift(1)) * pl.col(volume_col)).alias('_raw_fi')
        )

        # 使用 EMA 平滑
        df = df.with_columns(
            pl.col('_raw_fi').ewm_mean(span=period, adjust=False).alias(result_col)
        )

        # 删除临时列
        df = df.drop('_raw_fi')

        return df

    @staticmethod
    def volume_oscillator(df: pl.DataFrame, volume_col: str, short_period: int = 5, long_period: int = 10) -> pl.DataFrame:
        """
        成交量震荡指标 (Volume Oscillator)

        参数:
        df: Polars DataFrame
        volume_col: 成交量列名
        short_period: 短期周期（默认5）
        long_period: 长期周期（默认10）

        返回:
        pl.DataFrame: 添加了 VO 列的 DataFrame
        """
        # 计算短期和长期成交量移动平均
        df = df.with_columns([
            pl.col(volume_col).rolling_mean(window_size=short_period).alias('_vol_short'),
            pl.col(volume_col).rolling_mean(window_size=long_period).alias('_vol_long')
        ])

        # 计算震荡指标
        df = df.with_columns(
            ((pl.col('_vol_short') - pl.col('_vol_long')) / pl.col('_vol_long') * 100).alias('Volume_Oscillator')
        )

        # 删除临时列
        df = df.drop(['_vol_short', '_vol_long'])

        return df

    @staticmethod
    def vwap_std(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, volume_col: str, period: int = 20) -> pl.DataFrame:
        """
        VWAP标准差 (VWAP Standard Deviation)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        volume_col: 成交量列名
        period: 计算周期（默认20）

        返回:
        pl.DataFrame: 添加了 VWAP_STD 列的 DataFrame
        """
        # 先计算 VWAP（如果还没有）
        if 'VWAP' not in df.columns:
            df = VolumeIndicators.vwap(df, high_col, low_col, close_col, volume_col)

        # 计算典型价格
        df = df.with_columns(
            ((pl.col(high_col) + pl.col(low_col) + pl.col(close_col)) / 3).alias('_tp')
        )

        # 计算与VWAP的偏差的标准差
        df = df.with_columns(
            (pl.col('_tp') - pl.col('VWAP')).alias('_deviation')
        )

        df = df.with_columns(
            pl.col('_deviation').rolling_std(window_size=period).alias('VWAP_STD')
        )

        # 删除临时列
        df = df.drop(['_tp', '_deviation'])

        return df


class AdvancedOscillatorIndicators:
    """高级震荡指标类"""

    @staticmethod
    def aroon(df: pl.DataFrame, high_col: str, low_col: str, period: int = 25) -> pl.DataFrame:
        """
        阿隆指标 (Aroon Indicator)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        period: 计算周期（默认25）

        返回:
        pl.DataFrame: 添加了 Aroon_Up, Aroon_Down, Aroon_Oscillator 列的 DataFrame
        """
        # 计算 Aroon Up：距离最高价的天数
        df = df.with_columns(
            pl.col(high_col).rolling_map(
                lambda s: ((period - s.arg_max()) / period * 100) if len(s) == period else None,
                window_size=period
            ).alias('Aroon_Up')
        )

        # 计算 Aroon Down：距离最低价的天数
        df = df.with_columns(
            pl.col(low_col).rolling_map(
                lambda s: ((period - s.arg_min()) / period * 100) if len(s) == period else None,
                window_size=period
            ).alias('Aroon_Down')
        )

        # 计算 Aroon Oscillator
        df = df.with_columns(
            (pl.col('Aroon_Up') - pl.col('Aroon_Down')).alias('Aroon_Oscillator')
        )

        return df

    @staticmethod
    def ultimate_oscillator(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                           period1: int = 7, period2: int = 14, period3: int = 28) -> pl.DataFrame:
        """
        终极震荡指标 (Ultimate Oscillator)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period1: 短期周期（默认7）
        period2: 中期周期（默认14）
        period3: 长期周期（默认28）

        返回:
        pl.DataFrame: 添加了 UO 列的 DataFrame
        """
        # 计算买压（Buying Pressure）
        df = df.with_columns(
            (pl.col(close_col) - pl.min_horizontal(pl.col(low_col), pl.col(close_col).shift(1))).alias('_bp')
        )

        # 计算真实波幅
        df = df.with_columns(
            (pl.max_horizontal(pl.col(high_col), pl.col(close_col).shift(1)) -
             pl.min_horizontal(pl.col(low_col), pl.col(close_col).shift(1))).alias('_tr')
        )

        # 计算三个周期的平均值
        for period in [period1, period2, period3]:
            df = df.with_columns([
                pl.col('_bp').rolling_sum(window_size=period).alias(f'_bp_sum_{period}'),
                pl.col('_tr').rolling_sum(window_size=period).alias(f'_tr_sum_{period}')
            ])

        # 计算 UO
        df = df.with_columns(
            (100 * (
                (4 * pl.col(f'_bp_sum_{period1}') / pl.col(f'_tr_sum_{period1}')) +
                (2 * pl.col(f'_bp_sum_{period2}') / pl.col(f'_tr_sum_{period2}')) +
                (pl.col(f'_bp_sum_{period3}') / pl.col(f'_tr_sum_{period3}'))
            ) / 7).alias('Ultimate_Oscillator')
        )

        # 删除临时列
        temp_cols = ['_bp', '_tr'] + [f'_bp_sum_{p}' for p in [period1, period2, period3]] + [f'_tr_sum_{p}' for p in [period1, period2, period3]]
        df = df.drop(temp_cols)

        return df

    @staticmethod
    def stochastic_rsi(df: pl.DataFrame, column: str, rsi_period: int = 14, stoch_period: int = 14) -> pl.DataFrame:
        """
        随机RSI (Stochastic RSI)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        rsi_period: RSI周期（默认14）
        stoch_period: Stochastic周期（默认14）

        返回:
        pl.DataFrame: 添加了 StochRSI 列的 DataFrame
        """
        # 先计算 RSI
        df = MomentumIndicators.rsi(df, column, rsi_period, '_temp_rsi')

        # 计算 RSI 的最高和最低值
        df = df.with_columns([
            pl.col('_temp_rsi').rolling_max(window_size=stoch_period).alias('_rsi_high'),
            pl.col('_temp_rsi').rolling_min(window_size=stoch_period).alias('_rsi_low')
        ])

        # 计算 Stochastic RSI
        df = df.with_columns(
            ((pl.col('_temp_rsi') - pl.col('_rsi_low')) /
             (pl.col('_rsi_high') - pl.col('_rsi_low')) * 100).alias('StochRSI')
        )

        # 删除临时列
        df = df.drop(['_temp_rsi', '_rsi_high', '_rsi_low'])

        return df

    @staticmethod
    def tsi(df: pl.DataFrame, column: str, long_period: int = 25, short_period: int = 13) -> pl.DataFrame:
        """
        真实强度指标 (True Strength Index)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        long_period: 长期周期（默认25）
        short_period: 短期周期（默认13）

        返回:
        pl.DataFrame: 添加了 TSI 列的 DataFrame
        """
        # 计算价格变化
        df = df.with_columns(
            (pl.col(column) - pl.col(column).shift(1)).alias('_pc')
        )

        # 双重平滑价格变化
        df = df.with_columns(
            pl.col('_pc').ewm_mean(span=long_period, adjust=False).alias('_pc_ema1')
        )
        df = df.with_columns(
            pl.col('_pc_ema1').ewm_mean(span=short_period, adjust=False).alias('_pc_ema2')
        )

        # 双重平滑绝对价格变化
        df = df.with_columns(
            pl.col('_pc').abs().ewm_mean(span=long_period, adjust=False).alias('_apc_ema1')
        )
        df = df.with_columns(
            pl.col('_apc_ema1').ewm_mean(span=short_period, adjust=False).alias('_apc_ema2')
        )

        # 计算 TSI
        df = df.with_columns(
            (100 * pl.col('_pc_ema2') / pl.col('_apc_ema2')).alias('TSI')
        )

        # 删除临时列
        df = df.drop(['_pc', '_pc_ema1', '_pc_ema2', '_apc_ema1', '_apc_ema2'])

        return df

    @staticmethod
    def fisher_transform(df: pl.DataFrame, high_col: str, low_col: str,
                        period: int = 10, result_col: str = 'Fisher') -> pl.DataFrame:
        """
        Fisher Transform - Fisher变换

        将价格转换为高斯分布，使转折点更明显

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        period: 计算周期（默认10）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Fisher, Fisher_Signal 列的 DataFrame

        用途:
        - 识别价格转折点
        - 交叉信号：Fisher上穿信号线买入，下穿卖出
        """
        import numpy as np

        # 计算HL2（中间价）
        hl2 = (df[high_col] + df[low_col]) / 2

        # 标准化到-1到1之间
        highest = hl2.rolling_max(window_size=period)
        lowest = hl2.rolling_min(window_size=period)

        # 避免除零
        value = 2 * ((hl2 - lowest) / (highest - lowest + 1e-10) - 0.5)

        # 限制到(-0.999, 0.999)避免log无穷
        value = value.clip(-0.999, 0.999)

        # Fisher变换: 0.5 * ln((1+x)/(1-x))
        fisher = 0.5 * ((1 + value) / (1 - value)).log()

        # 信号线：前一个Fisher值
        fisher_signal = fisher.shift(1)

        df = df.with_columns([
            fisher.alias(result_col),
            fisher_signal.alias(f'{result_col}_Signal')
        ])

        return df

    @staticmethod
    def inverse_fisher_transform(df: pl.DataFrame, column: str,
                                 result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Inverse Fisher Transform - 逆Fisher变换

        将任何指标转换到-1到1的范围

        参数:
        df: Polars DataFrame
        column: 要转换的列名
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 IFT 列的 DataFrame

        用途:
        - 将RSI等指标转换为更清晰的信号
        - 增强超买超卖信号
        """
        if result_col is None:
            result_col = f'IFT_{column}'

        import numpy as np

        # IFT = (e^(2*x) - 1) / (e^(2*x) + 1)
        # 等价于 tanh(x)
        ift = (pl.col(column) * 2).exp()
        ift = (ift - 1) / (ift + 1)

        df = df.with_columns(ift.alias(result_col))

        return df

    @staticmethod
    def coppock_curve(df: pl.DataFrame, column: str,
                     roc1_period: int = 14, roc2_period: int = 11,
                     wma_period: int = 10, result_col: str = 'Coppock') -> pl.DataFrame:
        """
        Coppock Curve - 库科克曲线

        长期趋势震荡指标，用于识别熊市底部

        参数:
        df: Polars DataFrame
        column: 价格列名
        roc1_period: 第一个ROC周期（默认14）
        roc2_period: 第二个ROC周期（默认11）
        wma_period: WMA周期（默认10）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Coppock 列的 DataFrame

        用途:
        - 识别长期买入机会
        - 从负转正：买入信号
        - 主要用于月线数据
        """
        # 计算两个ROC
        roc1 = (df[column] - df[column].shift(roc1_period)) / df[column].shift(roc1_period) * 100
        roc2 = (df[column] - df[column].shift(roc2_period)) / df[column].shift(roc2_period) * 100

        # ROC之和
        roc_sum = roc1 + roc2

        # 对ROC之和计算WMA
        import numpy as np
        weights = np.arange(1, wma_period + 1)
        weight_sum = weights.sum()

        # 创建临时列
        df = df.with_columns(roc_sum.alias('_roc_sum'))

        coppock = df['_roc_sum'].rolling_map(
            lambda s: np.dot(s, weights) / weight_sum if len(s) == wma_period else None,
            window_size=wma_period
        )

        df = df.with_columns(coppock.alias(result_col))
        df = df.drop('_roc_sum')

        return df

    @staticmethod
    def klinger_oscillator(df: pl.DataFrame, high_col: str, low_col: str,
                          close_col: str, volume_col: str,
                          fast_period: int = 34, slow_period: int = 55,
                          signal_period: int = 13) -> pl.DataFrame:
        """
        Klinger Oscillator - Klinger震荡指标

        结合价格和成交量的震荡指标

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col: 价格列名
        volume_col: 成交量列名
        fast_period: 快速EMA周期（默认34）
        slow_period: 慢速EMA周期（默认55）
        signal_period: 信号线周期（默认13）

        返回:
        pl.DataFrame: 添加了 KO, KO_Signal 列的 DataFrame

        用途:
        - 识别趋势和趋势反转
        - 交叉信号
        """
        import numpy as np

        # 计算典型价格
        tp = (df[high_col] + df[low_col] + df[close_col]) / 3

        # 计算趋势方向
        dm = df[high_col] - df[low_col]

        # 趋势（上涨或下跌）
        trend = np.where(tp > tp.shift(1), 1, -1)
        trend = pl.Series('_trend', trend)

        # 成交量力度 (Volume Force)
        vf = df[volume_col] * trend * dm * 100

        df = df.with_columns(vf.alias('_vf'))

        # 计算快慢EMA
        fast_ema = df['_vf'].ewm_mean(span=fast_period, adjust=False)
        slow_ema = df['_vf'].ewm_mean(span=slow_period, adjust=False)

        # KO = fast - slow
        ko = fast_ema - slow_ema

        # 信号线
        ko_signal = ko.ewm_mean(span=signal_period, adjust=False)

        df = df.with_columns([
            ko.alias('KO'),
            ko_signal.alias('KO_Signal')
        ])

        df = df.drop('_vf')

        return df

    @staticmethod
    def ppo(df: pl.DataFrame, column: str,
            fast_period: int = 12, slow_period: int = 26,
            signal_period: int = 9, result_col: str = 'PPO') -> pl.DataFrame:
        """
        Percentage Price Oscillator (PPO) - 百分比价格震荡

        类似MACD，但使用百分比而非绝对值

        参数:
        df: Polars DataFrame
        column: 价格列名
        fast_period: 快速EMA周期（默认12）
        slow_period: 慢速EMA周期（默认26）
        signal_period: 信号线周期（默认9）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 PPO, PPO_Signal, PPO_Hist 列的 DataFrame

        用途:
        - 比较不同价格水平的证券
        - 百分比表示更适合跨市场比较
        """
        # 计算快慢EMA
        fast_ema = df[column].ewm_mean(span=fast_period, adjust=False)
        slow_ema = df[column].ewm_mean(span=slow_period, adjust=False)

        # PPO = (fast - slow) / slow * 100
        ppo = (fast_ema - slow_ema) / slow_ema * 100

        # 信号线
        ppo_signal = ppo.ewm_mean(span=signal_period, adjust=False)

        # 柱状图
        ppo_hist = ppo - ppo_signal

        df = df.with_columns([
            ppo.alias(result_col),
            ppo_signal.alias(f'{result_col}_Signal'),
            ppo_hist.alias(f'{result_col}_Hist')
        ])

        return df

    @staticmethod
    def squeeze_momentum(df: pl.DataFrame, high_col: str, low_col: str,
                        close_col: str, bb_period: int = 20,
                        kc_period: int = 20, kc_mult: float = 1.5) -> pl.DataFrame:
        """
        Squeeze Momentum Indicator - 挤压动量指标

        识别波动率收缩（挤压）和扩张

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col: 价格列名
        bb_period: 布林带周期（默认20）
        kc_period: Keltner通道周期（默认20）
        kc_mult: Keltner倍数（默认1.5）

        返回:
        pl.DataFrame: 添加了 Squeeze_On, Momentum_Val 列的 DataFrame

        用途:
        - Squeeze_On = True: 波动率压缩，可能突破
        - 动量值：正为上涨动量，负为下跌动量
        """
        # 计算布林带
        sma = df[close_col].rolling_mean(window_size=bb_period)
        std = df[close_col].rolling_std(window_size=bb_period)
        bb_upper = sma + 2 * std
        bb_lower = sma - 2 * std

        # 计算Keltner通道
        ema = df[close_col].ewm_mean(span=kc_period, adjust=False)

        # 简化的ATR计算
        tr = pl.max_horizontal(
            df[high_col] - df[low_col],
            (df[high_col] - df[close_col].shift(1)).abs(),
            (df[low_col] - df[close_col].shift(1)).abs()
        )
        atr = tr.ewm_mean(span=kc_period, adjust=False)

        kc_upper = ema + kc_mult * atr
        kc_lower = ema - kc_mult * atr

        # 挤压：BB在KC内部
        squeeze_on = (bb_lower > kc_lower) & (bb_upper < kc_upper)

        # 动量计算：当前价格与中线的偏离
        # 使用线性回归方法
        momentum = df[close_col] - sma

        df = df.with_columns([
            squeeze_on.alias('Squeeze_On'),
            momentum.alias('Squeeze_Momentum')
        ])

        return df


class ExtraIndicators:
    """额外技术指标类"""

    @staticmethod
    def williams_r(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, period: int = 14) -> pl.DataFrame:
        """
        威廉指标 (Williams %R)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period: 计算周期（默认14）

        返回:
        pl.DataFrame: 添加了 Williams_R 列的 DataFrame
        """
        # 计算周期内最高价和最低价
        df = df.with_columns([
            pl.col(high_col).rolling_max(window_size=period).alias('_hh'),
            pl.col(low_col).rolling_min(window_size=period).alias('_ll')
        ])

        # 计算 Williams %R
        df = df.with_columns(
            ((pl.col('_hh') - pl.col(close_col)) / (pl.col('_hh') - pl.col('_ll')) * -100).alias('Williams_R')
        )

        # 删除临时列
        df = df.drop(['_hh', '_ll'])

        return df

    @staticmethod
    def mfi(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, volume_col: str, period: int = 14) -> pl.DataFrame:
        """
        资金流量指标 (Money Flow Index)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        volume_col: 成交量列名
        period: 计算周期（默认14）

        返回:
        pl.DataFrame: 添加了 MFI 列的 DataFrame
        """
        # 计算典型价格
        df = df.with_columns(
            ((pl.col(high_col) + pl.col(low_col) + pl.col(close_col)) / 3).alias('_tp')
        )

        # 计算资金流量
        df = df.with_columns(
            (pl.col('_tp') * pl.col(volume_col)).alias('_mf')
        )

        # 区分正负资金流
        df = df.with_columns([
            pl.when(pl.col('_tp') > pl.col('_tp').shift(1))
              .then(pl.col('_mf'))
              .otherwise(0)
              .alias('_positive_mf'),
            pl.when(pl.col('_tp') < pl.col('_tp').shift(1))
              .then(pl.col('_mf'))
              .otherwise(0)
              .alias('_negative_mf')
        ])

        # 计算资金流比率
        df = df.with_columns([
            pl.col('_positive_mf').rolling_sum(window_size=period).alias('_positive_sum'),
            pl.col('_negative_mf').rolling_sum(window_size=period).alias('_negative_sum')
        ])

        # 计算 MFI
        df = df.with_columns(
            (100 - (100 / (1 + pl.col('_positive_sum') / pl.col('_negative_sum')))).alias('MFI')
        )

        # 删除临时列
        df = df.drop(['_tp', '_mf', '_positive_mf', '_negative_mf', '_positive_sum', '_negative_sum'])

        return df

    @staticmethod
    def adl(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, volume_col: str) -> pl.DataFrame:
        """
        聚散指标 (Accumulation/Distribution Line)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        volume_col: 成交量列名

        返回:
        pl.DataFrame: 添加了 ADL 列的 DataFrame
        """
        # 计算资金流量乘数
        df = df.with_columns(
            (((pl.col(close_col) - pl.col(low_col)) - (pl.col(high_col) - pl.col(close_col))) /
             (pl.col(high_col) - pl.col(low_col))).alias('_mfm')
        )

        # 计算资金流量成交量
        df = df.with_columns(
            (pl.col('_mfm') * pl.col(volume_col)).alias('_mfv')
        )

        # 计算 ADL（累计）
        df = df.with_columns(
            pl.col('_mfv').cum_sum().alias('ADL')
        )

        # 删除临时列
        df = df.drop(['_mfm', '_mfv'])

        return df

    @staticmethod
    def bop(df: pl.DataFrame, high_col: str, low_col: str, open_col: str, close_col: str) -> pl.DataFrame:
        """
        力量平衡 (Balance of Power)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        open_col: 开盘价列名
        close_col: 收盘价列名

        返回:
        pl.DataFrame: 添加了 BOP 列的 DataFrame
        """
        df = df.with_columns(
            ((pl.col(close_col) - pl.col(open_col)) / (pl.col(high_col) - pl.col(low_col))).alias('BOP')
        )

        return df

    @staticmethod
    def cmo(df: pl.DataFrame, column: str, period: int = 14) -> pl.DataFrame:
        """
        钱德动量摆动指标 (Chande Momentum Oscillator)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认14）

        返回:
        pl.DataFrame: 添加了 CMO 列的 DataFrame
        """
        # 计算价格变化
        df = df.with_columns(
            (pl.col(column) - pl.col(column).shift(1)).alias('_change')
        )

        # 分离涨跌
        df = df.with_columns([
            pl.when(pl.col('_change') > 0).then(pl.col('_change')).otherwise(0).alias('_up'),
            pl.when(pl.col('_change') < 0).then(-pl.col('_change')).otherwise(0).alias('_down')
        ])

        # 计算周期内总涨跌
        df = df.with_columns([
            pl.col('_up').rolling_sum(window_size=period).alias('_sum_up'),
            pl.col('_down').rolling_sum(window_size=period).alias('_sum_down')
        ])

        # 计算 CMO
        df = df.with_columns(
            (100 * (pl.col('_sum_up') - pl.col('_sum_down')) / (pl.col('_sum_up') + pl.col('_sum_down'))).alias('CMO')
        )

        # 删除临时列
        df = df.drop(['_change', '_up', '_down', '_sum_up', '_sum_down'])

        return df

    @staticmethod
    def dpo(df: pl.DataFrame, column: str, period: int = 20) -> pl.DataFrame:
        """
        去趋势价格震荡指标 (Detrended Price Oscillator)

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 计算周期（默认20）

        返回:
        pl.DataFrame: 添加了 DPO 列的 DataFrame
        """
        # 计算移动平均
        df = df.with_columns(
            pl.col(column).rolling_mean(window_size=period).alias('_sma')
        )

        # 计算偏移量
        offset = int(period / 2) + 1

        # 计算 DPO
        df = df.with_columns(
            (pl.col(column).shift(-offset) - pl.col('_sma')).alias('DPO')
        )

        # 删除临时列
        df = df.drop('_sma')

        return df

    @staticmethod
    def mass_index(df: pl.DataFrame, high_col: str, low_col: str, ema_period: int = 9, sum_period: int = 25) -> pl.DataFrame:
        """
        质量指标 (Mass Index)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        ema_period: EMA周期（默认9）
        sum_period: 求和周期（默认25）

        返回:
        pl.DataFrame: 添加了 Mass_Index 列的 DataFrame
        """
        # 计算高低价差
        df = df.with_columns(
            (pl.col(high_col) - pl.col(low_col)).alias('_range')
        )

        # 第一次EMA
        df = df.with_columns(
            pl.col('_range').ewm_mean(span=ema_period, adjust=False).alias('_ema1')
        )

        # 第二次EMA
        df = df.with_columns(
            pl.col('_ema1').ewm_mean(span=ema_period, adjust=False).alias('_ema2')
        )

        # 计算比率
        df = df.with_columns(
            (pl.col('_ema1') / pl.col('_ema2')).alias('_ratio')
        )

        # 计算质量指标
        df = df.with_columns(
            pl.col('_ratio').rolling_sum(window_size=sum_period).alias('Mass_Index')
        )

        # 删除临时列
        df = df.drop(['_range', '_ema1', '_ema2', '_ratio'])

        return df

    @staticmethod
    def vortex(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, period: int = 14) -> pl.DataFrame:
        """
        涡旋指标 (Vortex Indicator)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period: 计算周期（默认14）

        返回:
        pl.DataFrame: 添加了 Vortex_Pos, Vortex_Neg 列的 DataFrame
        """
        # 计算真实波幅
        df = df.with_columns([
            (pl.col(high_col) - pl.col(low_col)).alias('_tr1'),
            (pl.col(high_col) - pl.col(close_col).shift(1)).abs().alias('_tr2'),
            (pl.col(low_col) - pl.col(close_col).shift(1)).abs().alias('_tr3')
        ])

        df = df.with_columns(
            pl.max_horizontal('_tr1', '_tr2', '_tr3').alias('_tr')
        )

        # 计算涡旋移动
        df = df.with_columns([
            (pl.col(high_col) - pl.col(low_col).shift(1)).abs().alias('_vm_plus'),
            (pl.col(low_col) - pl.col(high_col).shift(1)).abs().alias('_vm_minus')
        ])

        # 计算周期内总和
        df = df.with_columns([
            pl.col('_vm_plus').rolling_sum(window_size=period).alias('_vm_plus_sum'),
            pl.col('_vm_minus').rolling_sum(window_size=period).alias('_vm_minus_sum'),
            pl.col('_tr').rolling_sum(window_size=period).alias('_tr_sum')
        ])

        # 计算涡旋指标
        df = df.with_columns([
            (pl.col('_vm_plus_sum') / pl.col('_tr_sum')).alias('Vortex_Pos'),
            (pl.col('_vm_minus_sum') / pl.col('_tr_sum')).alias('Vortex_Neg')
        ])

        # 删除临时列
        df = df.drop(['_tr1', '_tr2', '_tr3', '_tr', '_vm_plus', '_vm_minus',
                     '_vm_plus_sum', '_vm_minus_sum', '_tr_sum'])

        return df

    @staticmethod
    def rvi(df: pl.DataFrame, open_col: str, high_col: str, low_col: str, close_col: str, period: int = 10) -> pl.DataFrame:
        """
        相对活力指数 (Relative Vigor Index)

        参数:
        df: Polars DataFrame
        open_col: 开盘价列名
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period: 计算周期（默认10）

        返回:
        pl.DataFrame: 添加了 RVI, RVI_Signal 列的 DataFrame
        """
        # 计算分子：收盘-开盘
        df = df.with_columns(
            (pl.col(close_col) - pl.col(open_col)).alias('_numerator')
        )

        # 计算分母：最高-最低
        df = df.with_columns(
            (pl.col(high_col) - pl.col(low_col)).alias('_denominator')
        )

        # 应用加权平均（简化版：使用SMA）
        df = df.with_columns([
            pl.col('_numerator').rolling_mean(window_size=period).alias('_num_sma'),
            pl.col('_denominator').rolling_mean(window_size=period).alias('_den_sma')
        ])

        # 计算 RVI
        df = df.with_columns(
            (pl.col('_num_sma') / pl.col('_den_sma')).alias('RVI')
        )

        # 计算信号线（RVI的4周期SMA）
        df = df.with_columns(
            pl.col('RVI').rolling_mean(window_size=4).alias('RVI_Signal')
        )

        # 删除临时列
        df = df.drop(['_numerator', '_denominator', '_num_sma', '_den_sma'])

        return df

    @staticmethod
    def elder_ray(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, period: int = 13) -> pl.DataFrame:
        """
        艾达透视指标 (Elder Ray Index)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period: EMA周期（默认13）

        返回:
        pl.DataFrame: 添加了 Bull_Power, Bear_Power 列的 DataFrame
        """
        # 计算EMA
        df = df.with_columns(
            pl.col(close_col).ewm_mean(span=period, adjust=False).alias('_ema')
        )

        # 计算牛力和熊力
        df = df.with_columns([
            (pl.col(high_col) - pl.col('_ema')).alias('Bull_Power'),
            (pl.col(low_col) - pl.col('_ema')).alias('Bear_Power')
        ])

        # 删除临时列
        df = df.drop('_ema')

        return df

    @staticmethod
    def parabolic_sar(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                      af_start: float = 0.02, af_increment: float = 0.02, af_max: float = 0.2) -> pl.DataFrame:
        """
        抛物线转向指标 (Parabolic SAR)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        af_start: 加速因子初始值（默认0.02）
        af_increment: 加速因子增量（默认0.02）
        af_max: 加速因子最大值（默认0.2）

        返回:
        pl.DataFrame: 添加了 PSAR 列的 DataFrame
        """
        import numpy as np

        # 转换为numpy进行迭代计算
        high = df[high_col].to_numpy()
        low = df[low_col].to_numpy()
        close = df[close_col].to_numpy()

        n = len(df)
        psar = np.zeros(n)
        bull = True  # True=上涨趋势, False=下跌趋势
        af = af_start
        ep = low[0]  # Extreme Point
        hp = high[0]  # Highest Point
        lp = low[0]   # Lowest Point

        psar[0] = close[0]

        for i in range(1, n):
            # 更新SAR
            psar[i] = psar[i-1] + af * (ep - psar[i-1])

            if bull:
                # 上涨趋势
                if low[i] < psar[i]:
                    # 趋势反转
                    bull = False
                    psar[i] = hp
                    ep = low[i]
                    lp = low[i]
                    af = af_start
                else:
                    # 继续上涨
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + af_increment, af_max)
                    if high[i] > hp:
                        hp = high[i]
                    # 确保SAR不超过前两根K线的最低价
                    psar[i] = min(psar[i], low[i-1])
                    if i > 1:
                        psar[i] = min(psar[i], low[i-2])
            else:
                # 下跌趋势
                if high[i] > psar[i]:
                    # 趋势反转
                    bull = True
                    psar[i] = lp
                    ep = high[i]
                    hp = high[i]
                    af = af_start
                else:
                    # 继续下跌
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + af_increment, af_max)
                    if low[i] < lp:
                        lp = low[i]
                    # 确保SAR不低于前两根K线的最高价
                    psar[i] = max(psar[i], high[i-1])
                    if i > 1:
                        psar[i] = max(psar[i], high[i-2])

        df = df.with_columns(
            pl.Series('PSAR', psar)
        )

        return df

    @staticmethod
    def ichimoku_cloud(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                       tenkan_period: int = 9, kijun_period: int = 26,
                       senkou_b_period: int = 52, displacement: int = 26) -> pl.DataFrame:
        """
        一目均衡表 (Ichimoku Cloud)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        tenkan_period: 转换线周期（默认9）
        kijun_period: 基准线周期（默认26）
        senkou_b_period: 先行带B周期（默认52）
        displacement: 位移周期（默认26）

        返回:
        pl.DataFrame: 添加了 Tenkan_sen, Kijun_sen, Senkou_A, Senkou_B, Chikou_span 列的 DataFrame
        """
        # 转换线 (Tenkan-sen): (9日最高+9日最低)/2
        df = df.with_columns([
            ((pl.col(high_col).rolling_max(window_size=tenkan_period) +
              pl.col(low_col).rolling_min(window_size=tenkan_period)) / 2).alias('Tenkan_sen')
        ])

        # 基准线 (Kijun-sen): (26日最高+26日最低)/2
        df = df.with_columns([
            ((pl.col(high_col).rolling_max(window_size=kijun_period) +
              pl.col(low_col).rolling_min(window_size=kijun_period)) / 2).alias('Kijun_sen')
        ])

        # 先行带A (Senkou Span A): (转换线+基准线)/2, 向前位移26日
        df = df.with_columns([
            ((pl.col('Tenkan_sen') + pl.col('Kijun_sen')) / 2).shift(-displacement).alias('Senkou_A')
        ])

        # 先行带B (Senkou Span B): (52日最高+52日最低)/2, 向前位移26日
        df = df.with_columns([
            ((pl.col(high_col).rolling_max(window_size=senkou_b_period) +
              pl.col(low_col).rolling_min(window_size=senkou_b_period)) / 2).shift(-displacement).alias('Senkou_B')
        ])

        # 迟行带 (Chikou Span): 当前收盘价，向后位移26日
        df = df.with_columns([
            pl.col(close_col).shift(displacement).alias('Chikou_span')
        ])

        return df

    @staticmethod
    def supertrend(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                   period: int = 10, multiplier: float = 3.0) -> pl.DataFrame:
        """
        超级趋势指标 (Supertrend)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名
        period: ATR周期（默认10）
        multiplier: ATR乘数（默认3.0）

        返回:
        pl.DataFrame: 添加了 Supertrend, Supertrend_Direction 列的 DataFrame
        """
        # 计算ATR
        df = VolatilityIndicators.atr(df, high_col, low_col, close_col, period, '_st_atr')

        # 计算基础上下轨
        df = df.with_columns([
            ((pl.col(high_col) + pl.col(low_col)) / 2).alias('_hl_avg')
        ])

        df = df.with_columns([
            (pl.col('_hl_avg') - multiplier * pl.col('_st_atr')).alias('_basic_lower'),
            (pl.col('_hl_avg') + multiplier * pl.col('_st_atr')).alias('_basic_upper')
        ])

        # 使用numpy进行迭代计算最终上下轨和趋势
        import numpy as np

        close = df[close_col].to_numpy()
        basic_lower = df['_basic_lower'].to_numpy()
        basic_upper = df['_basic_upper'].to_numpy()

        n = len(df)
        final_lower = np.zeros(n)
        final_upper = np.zeros(n)
        supertrend = np.zeros(n)
        direction = np.zeros(n)  # 1=上涨, -1=下跌

        final_lower[0] = basic_lower[0]
        final_upper[0] = basic_upper[0]
        supertrend[0] = basic_upper[0]
        direction[0] = -1

        for i in range(1, n):
            # 计算最终下轨
            if basic_lower[i] > final_lower[i-1] or close[i-1] < final_lower[i-1]:
                final_lower[i] = basic_lower[i]
            else:
                final_lower[i] = final_lower[i-1]

            # 计算最终上轨
            if basic_upper[i] < final_upper[i-1] or close[i-1] > final_upper[i-1]:
                final_upper[i] = basic_upper[i]
            else:
                final_upper[i] = final_upper[i-1]

            # 确定趋势方向
            if supertrend[i-1] == final_upper[i-1]:
                if close[i] <= final_upper[i]:
                    supertrend[i] = final_upper[i]
                    direction[i] = -1
                else:
                    supertrend[i] = final_lower[i]
                    direction[i] = 1
            else:
                if close[i] >= final_lower[i]:
                    supertrend[i] = final_lower[i]
                    direction[i] = 1
                else:
                    supertrend[i] = final_upper[i]
                    direction[i] = -1

        df = df.with_columns([
            pl.Series('Supertrend', supertrend),
            pl.Series('Supertrend_Direction', direction)
        ])

        # 删除临时列
        df = df.drop(['_st_atr', '_hl_avg', '_basic_lower', '_basic_upper'])

        return df

    @staticmethod
    def pivot_points(df: pl.DataFrame, high_col: str, low_col: str, close_col: str) -> pl.DataFrame:
        """
        枢轴点 (Pivot Points) - 标准枢轴点

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        close_col: 收盘价列名

        返回:
        pl.DataFrame: 添加了 PP, R1, R2, R3, S1, S2, S3 列的 DataFrame
        """
        # 使用前一天的最高、最低、收盘计算枢轴点
        df = df.with_columns([
            pl.col(high_col).shift(1).alias('_prev_high'),
            pl.col(low_col).shift(1).alias('_prev_low'),
            pl.col(close_col).shift(1).alias('_prev_close')
        ])

        # 计算枢轴点 (Pivot Point)
        df = df.with_columns([
            ((pl.col('_prev_high') + pl.col('_prev_low') + pl.col('_prev_close')) / 3).alias('PP')
        ])

        # 计算支撑位和阻力位
        df = df.with_columns([
            (2 * pl.col('PP') - pl.col('_prev_low')).alias('R1'),
            (pl.col('PP') + (pl.col('_prev_high') - pl.col('_prev_low'))).alias('R2'),
            (pl.col('_prev_high') + 2 * (pl.col('PP') - pl.col('_prev_low'))).alias('R3'),
            (2 * pl.col('PP') - pl.col('_prev_high')).alias('S1'),
            (pl.col('PP') - (pl.col('_prev_high') - pl.col('_prev_low'))).alias('S2'),
            (pl.col('_prev_low') - 2 * (pl.col('_prev_high') - pl.col('PP'))).alias('S3')
        ])

        # 删除临时列
        df = df.drop(['_prev_high', '_prev_low', '_prev_close'])

        return df

    @staticmethod
    def fibonacci_retracement(df: pl.DataFrame, high_col: str, low_col: str, period: int = 50) -> pl.DataFrame:
        """
        斐波那契回撤 (Fibonacci Retracement)

        参数:
        df: Polars DataFrame
        high_col: 最高价列名
        low_col: 最低价列名
        period: 回溯周期（默认50）

        返回:
        pl.DataFrame: 添加了 Fib_0, Fib_236, Fib_382, Fib_500, Fib_618, Fib_786, Fib_1000 列的 DataFrame
        """
        # 计算周期内的最高价和最低价
        df = df.with_columns([
            pl.col(high_col).rolling_max(window_size=period).alias('_period_high'),
            pl.col(low_col).rolling_min(window_size=period).alias('_period_low')
        ])

        # 计算价格区间
        df = df.with_columns([
            (pl.col('_period_high') - pl.col('_period_low')).alias('_range')
        ])

        # 计算斐波那契回撤水平
        df = df.with_columns([
            pl.col('_period_high').alias('Fib_0'),      # 0% (最高点)
            (pl.col('_period_high') - 0.236 * pl.col('_range')).alias('Fib_236'),
            (pl.col('_period_high') - 0.382 * pl.col('_range')).alias('Fib_382'),
            (pl.col('_period_high') - 0.500 * pl.col('_range')).alias('Fib_500'),
            (pl.col('_period_high') - 0.618 * pl.col('_range')).alias('Fib_618'),
            (pl.col('_period_high') - 0.786 * pl.col('_range')).alias('Fib_786'),
            pl.col('_period_low').alias('Fib_1000')     # 100% (最低点)
        ])

        # 删除临时列
        df = df.drop(['_period_high', '_period_low', '_range'])

        return df

    @staticmethod
    def adx(df: pl.DataFrame, high_col: str, low_col: str, close_col: str, period: int = 14) -> pl.DataFrame:
        """
        ADX (Average Directional Index) - 平均趋向指标

        衡量趋势强度的指标，结合DMI(方向运动指标)

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col: 价格列名
        period: 计算周期 (默认14)

        返回:
        pl.DataFrame: 添加了ADX, +DI, -DI列
        """
        import numpy as np

        high = df[high_col].to_numpy()
        low = df[low_col].to_numpy()
        close = df[close_col].to_numpy()

        # 计算+DM和-DM
        plus_dm = np.maximum(high[1:] - high[:-1], 0)
        minus_dm = np.maximum(low[:-1] - low[1:], 0)

        # 当+DM > -DM时，-DM=0；反之+DM=0
        plus_dm = np.where(plus_dm > minus_dm, plus_dm, 0)
        minus_dm = np.where(minus_dm > plus_dm, minus_dm, 0)

        # 计算TR
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # 平滑TR, +DM, -DM
        def wilder_smooth(data, period):
            result = np.zeros(len(data))
            result[period-1] = np.sum(data[:period])
            for i in range(period, len(data)):
                result[i] = result[i-1] - result[i-1]/period + data[i]
            return result

        tr_smooth = wilder_smooth(tr, period)
        plus_dm_smooth = wilder_smooth(plus_dm, period)
        minus_dm_smooth = wilder_smooth(minus_dm, period)

        # 计算+DI和-DI - 添加小常数避免除以零
        plus_di = 100 * plus_dm_smooth / (tr_smooth + 1e-10)
        minus_di = 100 * minus_dm_smooth / (tr_smooth + 1e-10)

        # 计算DX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)

        # 计算ADX
        adx = wilder_smooth(dx, period)

        # 填充首行
        plus_di = np.concatenate([[np.nan], plus_di])
        minus_di = np.concatenate([[np.nan], minus_di])
        adx = np.concatenate([[np.nan], adx])

        df = df.with_columns([
            pl.Series(f'ADX_{period}', adx),
            pl.Series(f'+DI_{period}', plus_di),
            pl.Series(f'-DI_{period}', minus_di)
        ])

        return df

    @staticmethod
    def envelopes(df: pl.DataFrame, column: str, period: int = 20, percent: float = 2.5) -> pl.DataFrame:
        """
        Envelopes - 包络线指标

        在移动平均线上下各偏移一定百分比形成通道

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: MA周期 (默认20)
        percent: 偏移百分比 (默认2.5%)

        返回:
        pl.DataFrame: 添加了ENV_Upper, ENV_Middle, ENV_Lower列
        """
        ma = df[column].rolling_mean(window_size=period)
        upper = ma * (1 + percent / 100)
        lower = ma * (1 - percent / 100)

        df = df.with_columns([
            upper.alias(f'ENV_Upper_{period}'),
            ma.alias(f'ENV_Middle_{period}'),
            lower.alias(f'ENV_Lower_{period}')
        ])

        return df

    @staticmethod
    def alligator(df: pl.DataFrame, column: str,
                  jaw_period: int = 13, jaw_offset: int = 8,
                  teeth_period: int = 8, teeth_offset: int = 5,
                  lips_period: int = 5, lips_offset: int = 3) -> pl.DataFrame:
        """
        Alligator - 鳄鱼指标 (Bill Williams)

        由三条平滑移动平均线组成：
        - Jaw (下颚): 13期SMMA，向未来偏移8期
        - Teeth (牙齿): 8期SMMA，向未来偏移5期
        - Lips (嘴唇): 5期SMMA，向未来偏移3期

        参数:
        df: Polars DataFrame
        column: 价格列名
        jaw_period, teeth_period, lips_period: 三条线的周期
        jaw_offset, teeth_offset, lips_offset: 向未来偏移的期数

        返回:
        pl.DataFrame: 添加了Alligator_Jaw, Alligator_Teeth, Alligator_Lips列
        """
        # SMMA (Smoothed MA) = (Sum - Prev_SMMA + New_Price) / Period
        # 等同于 EMA with alpha = 1/period

        def smma(series: pl.Series, period: int) -> pl.Series:
            return series.ewm_mean(alpha=1/period, adjust=False)

        jaw = smma(df[column], jaw_period).shift(jaw_offset)
        teeth = smma(df[column], teeth_period).shift(teeth_offset)
        lips = smma(df[column], lips_period).shift(lips_offset)

        df = df.with_columns([
            jaw.alias('Alligator_Jaw'),
            teeth.alias('Alligator_Teeth'),
            lips.alias('Alligator_Lips')
        ])

        return df

    @staticmethod
    def awesome_oscillator(df: pl.DataFrame, high_col: str, low_col: str,
                          fast_period: int = 5, slow_period: int = 34) -> pl.DataFrame:
        """
        Awesome Oscillator (AO) - 动量震荡指标 (Bill Williams)

        基于中间价(high+low)/2的快慢SMA差值

        参数:
        df: Polars DataFrame
        high_col, low_col: 最高价和最低价列名
        fast_period: 快速周期 (默认5)
        slow_period: 慢速周期 (默认34)

        返回:
        pl.DataFrame: 添加了AO列
        """
        median_price = (df[high_col] + df[low_col]) / 2
        fast_ma = median_price.rolling_mean(window_size=fast_period)
        slow_ma = median_price.rolling_mean(window_size=slow_period)
        ao = fast_ma - slow_ma

        df = df.with_columns([
            ao.alias('AO')
        ])

        return df

    @staticmethod
    def fractals(df: pl.DataFrame, high_col: str, low_col: str, period: int = 5) -> pl.DataFrame:
        """
        Fractals - 分形指标 (Bill Williams)

        识别局部高点和低点：
        - 上分形：中间的高点是N期内最高
        - 下分形：中间的低点是N期内最低

        参数:
        df: Polars DataFrame
        high_col, low_col: 最高价和最低价列名
        period: 周期 (默认5，通常使用奇数)

        返回:
        pl.DataFrame: 添加了Fractal_Up, Fractal_Down列 (True/False)
        """
        import numpy as np

        high = df[high_col].to_numpy()
        low = df[low_col].to_numpy()
        n = len(high)

        # 需要period为奇数
        if period % 2 == 0:
            period += 1

        mid = period // 2

        fractal_up = np.full(n, False)
        fractal_down = np.full(n, False)

        for i in range(mid, n - mid):
            # 上分形：中间的高点是period期内最高
            if high[i] == np.max(high[i-mid:i+mid+1]):
                fractal_up[i] = True

            # 下分形：中间的低点是period期内最低
            if low[i] == np.min(low[i-mid:i+mid+1]):
                fractal_down[i] = True

        df = df.with_columns([
            pl.Series('Fractal_Up', fractal_up),
            pl.Series('Fractal_Down', fractal_down)
        ])

        return df

    @staticmethod
    def gator_oscillator(df: pl.DataFrame, column: str) -> pl.DataFrame:
        """
        Gator Oscillator - 鳄鱼震荡指标 (Bill Williams)

        基于Alligator指标，显示三条线之间的距离

        参数:
        df: Polars DataFrame
        column: 价格列名

        返回:
        pl.DataFrame: 添加了Gator_Upper, Gator_Lower列
        """
        # 先计算Alligator
        df = ExtraIndicators.alligator(df, column)

        # Gator Upper: abs(Jaw - Teeth)
        gator_upper = (df['Alligator_Jaw'] - df['Alligator_Teeth']).abs()

        # Gator Lower: abs(Teeth - Lips) (取负值)
        gator_lower = -(df['Alligator_Teeth'] - df['Alligator_Lips']).abs()

        df = df.with_columns([
            gator_upper.alias('Gator_Upper'),
            gator_lower.alias('Gator_Lower')
        ])

        return df

    @staticmethod
    def schaff_trend_cycle(df: pl.DataFrame, column: str,
                          fast_period: int = 23, slow_period: int = 50,
                          cycle_period: int = 10) -> pl.DataFrame:
        """
        Schaff Trend Cycle (STC) - 沙夫趋势周期

        结合MACD和Stochastic的优点

        参数:
        df: Polars DataFrame
        column: 价格列名
        fast_period: 快速EMA周期 (默认23)
        slow_period: 慢速EMA周期 (默认50)
        cycle_period: 周期 (默认10)

        返回:
        pl.DataFrame: 添加了STC列
        """
        import numpy as np

        # 计算MACD
        fast_ema = df[column].ewm_mean(span=fast_period, adjust=False)
        slow_ema = df[column].ewm_mean(span=slow_period, adjust=False)
        macd = fast_ema - slow_ema

        # 第一次Stochastic
        macd_array = macd.to_numpy()
        stoch1 = np.zeros(len(macd_array))

        for i in range(cycle_period-1, len(macd_array)):
            window = macd_array[i-cycle_period+1:i+1]
            min_val = np.min(window)
            max_val = np.max(window)
            if max_val - min_val != 0:
                stoch1[i] = 100 * (macd_array[i] - min_val) / (max_val - min_val)

        # 平滑
        stoch1_smooth = pl.Series(stoch1).ewm_mean(span=3, adjust=False).to_numpy()

        # 第二次Stochastic
        stc = np.zeros(len(stoch1_smooth))

        for i in range(cycle_period-1, len(stoch1_smooth)):
            window = stoch1_smooth[i-cycle_period+1:i+1]
            min_val = np.min(window)
            max_val = np.max(window)
            if max_val - min_val != 0:
                stc[i] = 100 * (stoch1_smooth[i] - min_val) / (max_val - min_val)

        # 最终平滑
        stc_smooth = pl.Series(stc).ewm_mean(span=3, adjust=False)

        df = df.with_columns([
            stc_smooth.alias('STC')
        ])

        return df

    @staticmethod
    def chaikin_oscillator(df: pl.DataFrame, high_col: str, low_col: str,
                          close_col: str, volume_col: str,
                          fast_period: int = 3, slow_period: int = 10) -> pl.DataFrame:
        """
        Chaikin Oscillator - 蔡金震荡指标

        基于ADL(累积/派发线)的快慢EMA差值

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col, volume_col: 价格和成交量列名
        fast_period: 快速EMA周期 (默认3)
        slow_period: 慢速EMA周期 (默认10)

        返回:
        pl.DataFrame: 添加了Chaikin_Osc列
        """
        # 先计算ADL
        if 'ADL' not in df.columns:
            df = ExtraIndicators.adl(df, high_col, low_col, close_col, volume_col)

        # 计算快慢EMA
        fast_ema = df['ADL'].ewm_mean(span=fast_period, adjust=False)
        slow_ema = df['ADL'].ewm_mean(span=slow_period, adjust=False)

        chaikin_osc = fast_ema - slow_ema

        df = df.with_columns([
            chaikin_osc.alias('Chaikin_Osc')
        ])

        return df

    @staticmethod
    def kst(df: pl.DataFrame, column: str) -> pl.DataFrame:
        """
        Know Sure Thing (KST) - 确然指标

        多时间框架的ROC加权和

        参数:
        df: Polars DataFrame
        column: 价格列名

        返回:
        pl.DataFrame: 添加了KST, KST_Signal列
        """
        # ROC周期：10, 15, 20, 30
        # SMA周期：10, 10, 10, 15
        # 权重：1, 2, 3, 4

        roc1 = ((df[column] - df[column].shift(10)) / df[column].shift(10) * 100).rolling_mean(window_size=10)
        roc2 = ((df[column] - df[column].shift(15)) / df[column].shift(15) * 100).rolling_mean(window_size=10)
        roc3 = ((df[column] - df[column].shift(20)) / df[column].shift(20) * 100).rolling_mean(window_size=10)
        roc4 = ((df[column] - df[column].shift(30)) / df[column].shift(30) * 100).rolling_mean(window_size=15)

        kst = roc1 * 1 + roc2 * 2 + roc3 * 3 + roc4 * 4
        kst_signal = kst.rolling_mean(window_size=9)

        df = df.with_columns([
            kst.alias('KST'),
            kst_signal.alias('KST_Signal')
        ])

        return df

    @staticmethod
    def bollinger_pct_b(df: pl.DataFrame, column: str, period: int = 20, num_std: float = 2.0) -> pl.DataFrame:
        """
        Bollinger %B - 布林带百分比位置

        显示价格在布林带中的相对位置
        %B = (Price - Lower Band) / (Upper Band - Lower Band)

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: 周期 (默认20)
        num_std: 标准差倍数 (默认2.0)

        返回:
        pl.DataFrame: 添加了BB_PctB, BB_Width列
        """
        # 先计算布林带(如果还没有)
        if f'BB_Upper_{period}' not in df.columns:
            from . import indicators
            df = VolatilityIndicators.bollinger_bands(df, column, period, num_std)

        # %B
        pct_b = (df[column] - df[f'BB_Lower_{period}']) / (df[f'BB_Upper_{period}'] - df[f'BB_Lower_{period}'])

        # Bandwidth
        bb_width = (df[f'BB_Upper_{period}'] - df[f'BB_Lower_{period}']) / df[f'BB_Middle_{period}']

        df = df.with_columns([
            pct_b.alias(f'BB_PctB_{period}'),
            bb_width.alias(f'BB_Width_{period}')
        ])

        return df

    @staticmethod
    def atr_bands(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                  period: int = 14, multiplier: float = 2.0) -> pl.DataFrame:
        """
        ATR Bands - ATR通道

        基于ATR的价格通道

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col: 价格列名
        period: ATR周期 (默认14)
        multiplier: ATR倍数 (默认2.0)

        返回:
        pl.DataFrame: 添加了ATR_Upper, ATR_Middle, ATR_Lower列
        """
        # 先计算ATR(如果还没有)
        if f'ATR_{period}' not in df.columns:
            df = VolatilityIndicators.atr(df, high_col, low_col, close_col, period)

        # 中轨：收盘价MA
        middle = df[close_col].rolling_mean(window_size=period)

        # 上下轨
        upper = middle + multiplier * df[f'ATR_{period}']
        lower = middle - multiplier * df[f'ATR_{period}']

        df = df.with_columns([
            upper.alias(f'ATR_Upper_{period}'),
            middle.alias(f'ATR_Middle_{period}'),
            lower.alias(f'ATR_Lower_{period}')
        ])

        return df

    @staticmethod
    def chandelier_exit(df: pl.DataFrame, high_col: str, low_col: str, close_col: str,
                       period: int = 22, multiplier: float = 3.0) -> pl.DataFrame:
        """
        Chandelier Exit - 吊灯止损

        基于ATR的跟踪止损指标

        参数:
        df: Polars DataFrame
        high_col, low_col, close_col: 价格列名
        period: ATR周期 (默认22)
        multiplier: ATR倍数 (默认3.0)

        返回:
        pl.DataFrame: 添加了Chandelier_Long, Chandelier_Short列
        """
        # 计算ATR
        if f'ATR_{period}' not in df.columns:
            df = VolatilityIndicators.atr(df, high_col, low_col, close_col, period)

        # 最高价和最低价的rolling max/min
        highest = df[high_col].rolling_max(window_size=period)
        lowest = df[low_col].rolling_min(window_size=period)

        # Long Exit: Highest - ATR * multiplier
        # Short Exit: Lowest + ATR * multiplier
        chandelier_long = highest - multiplier * df[f'ATR_{period}']
        chandelier_short = lowest + multiplier * df[f'ATR_{period}']

        df = df.with_columns([
            chandelier_long.alias('Chandelier_Long'),
            chandelier_short.alias('Chandelier_Short')
        ])

        return df

    @staticmethod
    def kama(df: pl.DataFrame, column: str, period: int = 10,
             fast_ema: int = 2, slow_ema: int = 30) -> pl.DataFrame:
        """
        Kaufman's Adaptive Moving Average (KAMA) - 考夫曼自适应移动平均

        根据市场噪音自动调整平滑度

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: 效率比计算周期 (默认10)
        fast_ema: 快速EMA周期 (默认2)
        slow_ema: 慢速EMA周期 (默认30)

        返回:
        pl.DataFrame: 添加了KAMA列
        """
        import numpy as np

        price = df[column].to_numpy()
        n = len(price)

        # 计算效率比 (Efficiency Ratio)
        change = np.abs(price - np.roll(price, period))
        volatility = np.sum(np.abs(np.diff(price, prepend=price[0])).reshape(-1, 1).repeat(period, axis=1), axis=1)
        volatility = np.roll(volatility, period)

        er = np.zeros(n)
        for i in range(period, n):
            signal = abs(price[i] - price[i - period])
            noise = np.sum(np.abs(np.diff(price[i - period:i + 1])))
            er[i] = signal / noise if noise != 0 else 0

        # 平滑常数
        fast_sc = 2 / (fast_ema + 1)
        slow_sc = 2 / (slow_ema + 1)

        # KAMA
        kama = np.zeros(n)
        kama[period-1] = price[period-1]

        for i in range(period, n):
            sc = np.power(er[i] * (fast_sc - slow_sc) + slow_sc, 2)
            kama[i] = kama[i-1] + sc * (price[i] - kama[i-1])

        df = df.with_columns([
            pl.Series(f'KAMA_{period}', kama)
        ])

        return df

    @staticmethod
    def dema(df: pl.DataFrame, column: str, period: int = 20) -> pl.DataFrame:
        """
        DEMA (Double Exponential Moving Average) - 双重指数移动平均

        DEMA = 2 * EMA - EMA(EMA)
        减少滞后性

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: 周期 (默认20)

        返回:
        pl.DataFrame: 添加了DEMA列
        """
        ema1 = df[column].ewm_mean(span=period, adjust=False)
        ema2 = ema1.ewm_mean(span=period, adjust=False)
        dema = 2 * ema1 - ema2

        df = df.with_columns([
            dema.alias(f'DEMA_{period}')
        ])

        return df

    @staticmethod
    def tema(df: pl.DataFrame, column: str, period: int = 20) -> pl.DataFrame:
        """
        TEMA (Triple Exponential Moving Average) - 三重指数移动平均

        TEMA = 3*EMA - 3*EMA(EMA) + EMA(EMA(EMA))
        进一步减少滞后性

        参数:
        df: Polars DataFrame
        column: 价格列名
        period: 周期 (默认20)

        返回:
        pl.DataFrame: 添加了TEMA列
        """
        ema1 = df[column].ewm_mean(span=period, adjust=False)
        ema2 = ema1.ewm_mean(span=period, adjust=False)
        ema3 = ema2.ewm_mean(span=period, adjust=False)
        tema = 3 * ema1 - 3 * ema2 + ema3

        df = df.with_columns([
            tema.alias(f'TEMA_{period}')
        ])

        return df

    @staticmethod
    def zigzag(df: pl.DataFrame, high_col: str, low_col: str,
               deviation: float = 5.0) -> pl.DataFrame:
        """
        ZigZag - 之字转向指标

        过滤小幅波动，只显示重要的价格转折点

        参数:
        df: Polars DataFrame
        high_col, low_col: 最高价和最低价列名
        deviation: 最小变动百分比 (默认5%)

        返回:
        pl.DataFrame: 添加了ZigZag, ZigZag_Signal列
        """
        import numpy as np

        high = df[high_col].to_numpy()
        low = df[low_col].to_numpy()
        n = len(high)

        zigzag = np.full(n, np.nan)
        signal = np.zeros(n)  # 1=高点, -1=低点, 0=无信号

        # 寻找第一个极值点
        last_pivot_idx = 0
        last_pivot_value = high[0]
        is_high_pivot = True

        threshold = deviation / 100

        for i in range(1, n):
            if is_high_pivot:
                # 当前在高点，寻找低点
                if low[i] < last_pivot_value * (1 - threshold):
                    # 找到低点
                    zigzag[last_pivot_idx] = last_pivot_value
                    signal[last_pivot_idx] = 1

                    last_pivot_idx = i
                    last_pivot_value = low[i]
                    is_high_pivot = False
                elif high[i] > last_pivot_value:
                    # 更新高点
                    last_pivot_value = high[i]
                    last_pivot_idx = i
            else:
                # 当前在低点，寻找高点
                if high[i] > last_pivot_value * (1 + threshold):
                    # 找到高点
                    zigzag[last_pivot_idx] = last_pivot_value
                    signal[last_pivot_idx] = -1

                    last_pivot_idx = i
                    last_pivot_value = high[i]
                    is_high_pivot = True
                elif low[i] < last_pivot_value:
                    # 更新低点
                    last_pivot_value = low[i]
                    last_pivot_idx = i

        # 最后一个点
        zigzag[last_pivot_idx] = last_pivot_value
        signal[last_pivot_idx] = 1 if is_high_pivot else -1

        df = df.with_columns([
            pl.Series('ZigZag', zigzag),
            pl.Series('ZigZag_Signal', signal)
        ])

        return df


class StatisticalIndicators:
    """统计指标类"""

    @staticmethod
    def zscore(df: pl.DataFrame, column: str, period: int = 20,
               result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Z-Score - 标准分数

        Z = (X - μ) / σ
        其中 μ 是均值，σ 是标准差

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 滚动窗口周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 ZScore 列的 DataFrame

        用途:
        - 识别异常值（|Z| > 2 或 3）
        - 标准化价格
        - 均值回归策略
        """
        if result_col is None:
            result_col = f'ZScore_{period}'

        # 计算滚动均值和标准差
        mean = df[column].rolling_mean(window_size=period)
        std = df[column].rolling_std(window_size=period)

        # 计算Z-Score
        zscore = (df[column] - mean) / std

        df = df.with_columns(
            zscore.alias(result_col)
        )

        return df

    @staticmethod
    def percentile(df: pl.DataFrame, column: str, period: int = 20,
                   percentile: float = 50, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Percentile - 百分位数

        计算滚动窗口内的百分位数

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 滚动窗口周期
        percentile: 百分位数 (0-100)
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Percentile 列的 DataFrame

        用途:
        - 识别相对位置（价格在历史分布中的位置）
        - 超买超卖判断
        """
        if result_col is None:
            result_col = f'Percentile_{int(percentile)}_{period}'

        # 使用rolling_map计算百分位数
        import numpy as np

        pct = df[column].rolling_map(
            lambda s: np.percentile(s, percentile) if len(s) == period else None,
            window_size=period
        )

        df = df.with_columns(
            pct.alias(result_col)
        )

        return df

    @staticmethod
    def skewness(df: pl.DataFrame, column: str, period: int = 20,
                 result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Skewness - 偏度

        衡量分布的对称性
        - Skew > 0: 右偏（长尾在右）
        - Skew < 0: 左偏（长尾在左）
        - Skew = 0: 对称分布

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 滚动窗口周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Skewness 列的 DataFrame

        用途:
        - 识别分布形态
        - 风险评估（负偏度表示下行风险）
        """
        if result_col is None:
            result_col = f'Skewness_{period}'

        import numpy as np
        from scipy import stats

        # 使用rolling_map计算偏度
        skew = df[column].rolling_map(
            lambda s: stats.skew(s) if len(s) == period else None,
            window_size=period
        )

        df = df.with_columns(
            skew.alias(result_col)
        )

        return df

    @staticmethod
    def kurtosis(df: pl.DataFrame, column: str, period: int = 20,
                 result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Kurtosis - 峰度

        衡量分布的尾部厚度
        - Kurt > 3: 厚尾（Leptokurtic）- 极端事件多
        - Kurt < 3: 薄尾（Platykurtic）- 极端事件少
        - Kurt = 3: 正态分布

        参数:
        df: Polars DataFrame
        column: 要计算的列名
        period: 滚动窗口周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Kurtosis 列的 DataFrame

        用途:
        - 识别极端波动风险
        - 尾部风险评估
        """
        if result_col is None:
            result_col = f'Kurtosis_{period}'

        import numpy as np
        from scipy import stats

        # 使用rolling_map计算峰度
        kurt = df[column].rolling_map(
            lambda s: stats.kurtosis(s, fisher=False) if len(s) == period else None,
            window_size=period
        )

        df = df.with_columns(
            kurt.alias(result_col)
        )

        return df

    @staticmethod
    def correlation(df: pl.DataFrame, column1: str, column2: str,
                    period: int = 20, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Correlation - 相关系数

        计算两个序列的滚动相关系数
        - Corr = 1: 完全正相关
        - Corr = 0: 无相关
        - Corr = -1: 完全负相关

        参数:
        df: Polars DataFrame
        column1: 第一列名
        column2: 第二列名
        period: 滚动窗口周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Correlation 列的 DataFrame

        用途:
        - 配对交易
        - 组合分散化
        - 领先滞后关系
        """
        if result_col is None:
            result_col = f'Corr_{column1}_{column2}_{period}'

        import numpy as np

        # 获取两列数据
        col1_data = df[column1].to_numpy()
        col2_data = df[column2].to_numpy()

        # 计算滚动相关系数
        n = len(col1_data)
        corr = np.full(n, np.nan)

        for i in range(period - 1, n):
            window1 = col1_data[i - period + 1:i + 1]
            window2 = col2_data[i - period + 1:i + 1]

            # 计算相关系数
            if len(window1) == period and len(window2) == period:
                corr[i] = np.corrcoef(window1, window2)[0, 1]

        df = df.with_columns(
            pl.Series(result_col, corr)
        )

        return df

    @staticmethod
    def rolling_correlation(df: pl.DataFrame, column1: str, column2: str,
                           short_period: int = 10, long_period: int = 30) -> pl.DataFrame:
        """
        Rolling Correlation - 多周期滚动相关

        计算短期和长期相关系数，用于识别关系变化

        参数:
        df: Polars DataFrame
        column1: 第一列名
        column2: 第二列名
        short_period: 短期周期
        long_period: 长期周期

        返回:
        pl.DataFrame: 添加了短期和长期相关系数列的 DataFrame

        用途:
        - 识别相关性突变
        - 配对交易信号
        """
        # 计算短期相关
        df = StatisticalIndicators.correlation(
            df, column1, column2, short_period,
            f'Corr_Short_{short_period}'
        )

        # 计算长期相关
        df = StatisticalIndicators.correlation(
            df, column1, column2, long_period,
            f'Corr_Long_{long_period}'
        )

        # 计算相关差值
        df = df.with_columns(
            (pl.col(f'Corr_Short_{short_period}') -
             pl.col(f'Corr_Long_{long_period}')).alias('Corr_Diff')
        )

        return df

    @staticmethod
    def beta(df: pl.DataFrame, asset_col: str, benchmark_col: str,
             period: int = 60, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Beta - Beta系数

        衡量资产相对于基准的系统性风险
        Beta = Cov(Asset, Benchmark) / Var(Benchmark)

        - Beta > 1: 比市场波动大
        - Beta = 1: 与市场同步
        - Beta < 1: 比市场波动小
        - Beta < 0: 与市场反向

        参数:
        df: Polars DataFrame
        asset_col: 资产收益率列名
        benchmark_col: 基准收益率列名
        period: 滚动窗口周期（默认60，约3个月）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Beta 列的 DataFrame

        用途:
        - 风险管理
        - 投资组合构建
        - 市场中性策略
        """
        if result_col is None:
            result_col = f'Beta_{period}'

        import numpy as np

        asset_data = df[asset_col].to_numpy()
        benchmark_data = df[benchmark_col].to_numpy()

        n = len(asset_data)
        beta = np.full(n, np.nan)

        for i in range(period - 1, n):
            asset_window = asset_data[i - period + 1:i + 1]
            benchmark_window = benchmark_data[i - period + 1:i + 1]

            if len(asset_window) == period and len(benchmark_window) == period:
                # 计算协方差和方差
                covariance = np.cov(asset_window, benchmark_window)[0, 1]
                variance = np.var(benchmark_window, ddof=1)

                if variance != 0:
                    beta[i] = covariance / variance

        df = df.with_columns(
            pl.Series(result_col, beta)
        )

        return df

    @staticmethod
    def sharpe_ratio(df: pl.DataFrame, return_col: str, period: int = 252,
                     risk_free_rate: float = 0.0, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Sharpe Ratio - 夏普比率

        衡量风险调整后的收益
        Sharpe = (Return - RiskFreeRate) / StdDev

        参数:
        df: Polars DataFrame
        return_col: 收益率列名（需要先计算收益率）
        period: 年化周期（默认252个交易日）
        risk_free_rate: 无风险利率（年化，默认0）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Sharpe_Ratio 列的 DataFrame

        用途:
        - 策略评估
        - 风险调整收益比较
        - 投资组合优化

        注意:
        - Sharpe > 1: 良好
        - Sharpe > 2: 优秀
        - Sharpe > 3: 极好
        """
        if result_col is None:
            result_col = f'Sharpe_{period}'

        # 计算滚动均值和标准差
        mean_return = df[return_col].rolling_mean(window_size=period)
        std_return = df[return_col].rolling_std(window_size=period)

        # 计算年化夏普比率
        # 假设period是滚动窗口，需要根据数据频率调整年化因子
        import numpy as np
        annualization_factor = np.sqrt(252)  # 假设日频数据

        sharpe = (mean_return * 252 - risk_free_rate) / (std_return * annualization_factor)

        df = df.with_columns(
            sharpe.alias(result_col)
        )

        return df


class RiskIndicators:
    """风险管理指标类"""

    @staticmethod
    def maximum_drawdown(df: pl.DataFrame, column: str, period: Optional[int] = None,
                        result_col: str = 'Max_Drawdown') -> pl.DataFrame:
        """
        Maximum Drawdown - 最大回撤

        衡量从历史峰值到最低点的最大跌幅
        MDD = (Trough - Peak) / Peak

        参数:
        df: Polars DataFrame
        column: 价格或净值列名
        period: 滚动周期（可选，None表示全局）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Max_Drawdown 列的 DataFrame

        用途:
        - 风险评估核心指标
        - 策略回测必备
        - 风险调整收益计算
        """
        import numpy as np

        values = df[column].to_numpy()
        n = len(values)

        if period is None:
            # 全局最大回撤
            max_dd = np.full(n, np.nan)
            running_max = values[0]

            for i in range(n):
                running_max = max(running_max, values[i])
                if running_max > 0:
                    drawdown = (values[i] - running_max) / running_max
                    max_dd[i] = min(max_dd[i-1] if i > 0 and not np.isnan(max_dd[i-1]) else 0, drawdown)
                else:
                    max_dd[i] = 0
        else:
            # 滚动最大回撤
            max_dd = np.full(n, np.nan)

            for i in range(period - 1, n):
                window = values[max(0, i - period + 1):i + 1]
                running_max = window[0]
                min_dd = 0

                for val in window:
                    running_max = max(running_max, val)
                    if running_max > 0:
                        drawdown = (val - running_max) / running_max
                        min_dd = min(min_dd, drawdown)

                max_dd[i] = min_dd

        df = df.with_columns(
            pl.Series(result_col, max_dd * 100)  # 转换为百分比
        )

        return df

    @staticmethod
    def sortino_ratio(df: pl.DataFrame, return_col: str, period: int = 252,
                     target_return: float = 0.0, result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Sortino Ratio - 索提诺比率

        只考虑下行风险的风险调整收益比率
        Sortino = (Return - Target) / Downside_StdDev

        参数:
        df: Polars DataFrame
        return_col: 收益率列名
        period: 滚动周期（默认252，约1年）
        target_return: 目标收益率（默认0）
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Sortino_Ratio 列的 DataFrame

        用途:
        - 下行风险评估
        - 比Sharpe更关注损失
        - 策略优化
        """
        if result_col is None:
            result_col = f'Sortino_{period}'

        import numpy as np

        returns = df[return_col].to_numpy()
        n = len(returns)
        sortino = np.full(n, np.nan)

        for i in range(period - 1, n):
            window_returns = returns[i - period + 1:i + 1]

            # 计算平均收益
            mean_return = np.mean(window_returns)

            # 只计算下行标准差（低于目标收益的部分）
            downside_returns = window_returns[window_returns < target_return]

            if len(downside_returns) > 0:
                downside_std = np.std(downside_returns, ddof=1)

                if downside_std > 0:
                    # 年化
                    annualized_return = mean_return * 252
                    annualized_downside_std = downside_std * np.sqrt(252)
                    sortino[i] = (annualized_return - target_return) / annualized_downside_std
            else:
                # 没有下行风险，设为高值
                sortino[i] = 999.0

        df = df.with_columns(
            pl.Series(result_col, sortino)
        )

        return df

    @staticmethod
    def calmar_ratio(df: pl.DataFrame, return_col: str, value_col: str,
                    period: int = 36, result_col: str = 'Calmar_Ratio') -> pl.DataFrame:
        """
        Calmar Ratio - 卡玛比率

        年化收益率与最大回撤的比率
        Calmar = Annualized_Return / abs(Max_Drawdown)

        参数:
        df: Polars DataFrame
        return_col: 收益率列名
        value_col: 净值列名
        period: 计算周期（默认36个月）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Calmar_Ratio 列的 DataFrame

        用途:
        - 收益风险比评估
        - 策略比较
        - 风险调整收益
        """
        import numpy as np

        returns = df[return_col].to_numpy()
        values = df[value_col].to_numpy()
        n = len(returns)

        calmar = np.full(n, np.nan)

        for i in range(period - 1, n):
            # 计算期间年化收益
            window_returns = returns[i - period + 1:i + 1]
            mean_return = np.mean(window_returns)
            annualized_return = mean_return * 252  # 假设日频

            # 计算期间最大回撤
            window_values = values[i - period + 1:i + 1]
            running_max = window_values[0]
            max_dd = 0

            for val in window_values:
                running_max = max(running_max, val)
                if running_max > 0:
                    drawdown = (val - running_max) / running_max
                    max_dd = min(max_dd, drawdown)

            # 计算Calmar比率
            if abs(max_dd) > 0.001:  # 避免除零
                calmar[i] = annualized_return / abs(max_dd)
            else:
                calmar[i] = 999.0 if annualized_return > 0 else 0.0

        df = df.with_columns(
            pl.Series(result_col, calmar)
        )

        return df

    @staticmethod
    def win_rate(df: pl.DataFrame, return_col: str, period: int = 20,
                result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Win Rate - 胜率

        盈利交易占总交易的百分比
        Win_Rate = 盈利次数 / 总交易次数 * 100

        参数:
        df: Polars DataFrame
        return_col: 收益率列名
        period: 滚动周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Win_Rate 列的 DataFrame

        用途:
        - 策略评估
        - 交易系统质量
        - 信号质量分析
        """
        if result_col is None:
            result_col = f'Win_Rate_{period}'

        import numpy as np

        returns = df[return_col].to_numpy()
        n = len(returns)

        win_rate = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = returns[i - period + 1:i + 1]

            # 计算盈利次数
            wins = np.sum(window > 0)
            total = len(window)

            if total > 0:
                win_rate[i] = (wins / total) * 100

        df = df.with_columns(
            pl.Series(result_col, win_rate)
        )

        return df

    @staticmethod
    def profit_factor(df: pl.DataFrame, return_col: str, period: int = 20,
                     result_col: Optional[str] = None) -> pl.DataFrame:
        """
        Profit Factor - 盈亏比

        总盈利与总亏损的比率
        Profit_Factor = 总盈利 / abs(总亏损)

        参数:
        df: Polars DataFrame
        return_col: 收益率列名
        period: 滚动周期
        result_col: 结果列名（可选）

        返回:
        pl.DataFrame: 添加了 Profit_Factor 列的 DataFrame

        用途:
        - 策略质量评估
        - PF > 1.5 为良好
        - PF > 2.0 为优秀
        """
        if result_col is None:
            result_col = f'Profit_Factor_{period}'

        import numpy as np

        returns = df[return_col].to_numpy()
        n = len(returns)

        profit_factor = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = returns[i - period + 1:i + 1]

            # 计算总盈利和总亏损
            total_profit = np.sum(window[window > 0])
            total_loss = abs(np.sum(window[window < 0]))

            if total_loss > 0:
                profit_factor[i] = total_profit / total_loss
            else:
                # 没有亏损
                profit_factor[i] = 999.0 if total_profit > 0 else 1.0

        df = df.with_columns(
            pl.Series(result_col, profit_factor)
        )

        return df


class PatternIndicators:
    """蜡烛图形态识别指标类"""

    @staticmethod
    def doji(df: pl.DataFrame, open_col: str, high_col: str, low_col: str, close_col: str,
            body_threshold: float = 0.1, result_col: str = 'Doji') -> pl.DataFrame:
        """
        Doji - 十字星形态

        识别开盘价和收盘价几乎相等的蜡烛图
        特征：实体很小，上下影线较长

        参数:
        df: Polars DataFrame
        open_col, high_col, low_col, close_col: OHLC列名
        body_threshold: 实体阈值（占总范围的百分比，默认10%）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Doji 列的 DataFrame（True/False）

        用途:
        - 市场犹豫不决信号
        - 可能的趋势反转
        - 结合趋势使用效果更好
        """
        # 计算实体大小
        body = (df[close_col] - df[open_col]).abs()

        # 计算总范围
        total_range = df[high_col] - df[low_col]

        # Doji: 实体占总范围的比例很小
        is_doji = (body / (total_range + 1e-10)) <= body_threshold

        df = df.with_columns(
            is_doji.alias(result_col)
        )

        return df

    @staticmethod
    def hammer(df: pl.DataFrame, open_col: str, high_col: str, low_col: str, close_col: str,
              body_position: float = 0.3, shadow_ratio: float = 2.0, result_col: str = 'Hammer') -> pl.DataFrame:
        """
        Hammer - 锤子线形态

        识别下跌趋势中的底部反转信号
        特征：小实体在顶部，长下影线，上影线很短或没有

        参数:
        df: Polars DataFrame
        open_col, high_col, low_col, close_col: OHLC列名
        body_position: 实体位置阈值（从顶部算，默认30%）
        shadow_ratio: 下影线与实体的比率（默认2倍）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Hammer 列的 DataFrame（True/False）

        用途:
        - 底部反转信号
        - 下跌趋势中出现更有效
        - 需要后续确认
        """
        # 计算实体
        body = (df[close_col] - df[open_col]).abs()

        # 计算影线
        lower_shadow = pl.min_horizontal(df[open_col], df[close_col]) - df[low_col]
        upper_shadow = df[high_col] - pl.max_horizontal(df[open_col], df[close_col])

        # 总范围
        total_range = df[high_col] - df[low_col]

        # Hammer条件：
        # 1. 下影线至少是实体的2倍
        # 2. 上影线很短（小于实体）
        # 3. 实体在上方30%区域
        body_top = pl.max_horizontal(df[open_col], df[close_col])
        body_position_ratio = (df[high_col] - body_top) / (total_range + 1e-10)

        is_hammer = (
            (lower_shadow >= body * shadow_ratio) &
            (upper_shadow <= body) &
            (body_position_ratio <= body_position) &
            (body > 0)  # 必须有实体
        )

        df = df.with_columns(
            is_hammer.alias(result_col)
        )

        return df

    @staticmethod
    def engulfing(df: pl.DataFrame, open_col: str, close_col: str,
                 result_col_bullish: str = 'Bullish_Engulfing',
                 result_col_bearish: str = 'Bearish_Engulfing') -> pl.DataFrame:
        """
        Engulfing - 吞没形态

        识别看涨和看跌吞没形态
        特征：当前蜡烛实体完全包含前一根蜡烛实体

        参数:
        df: Polars DataFrame
        open_col, close_col: 开盘价和收盘价列名
        result_col_bullish: 看涨吞没列名
        result_col_bearish: 看跌吞没列名

        返回:
        pl.DataFrame: 添加了看涨/看跌吞没列的 DataFrame（True/False）

        用途:
        - 强烈的反转信号
        - 看涨吞没：底部反转
        - 看跌吞没：顶部反转
        """
        # 当前蜡烛
        curr_open = df[open_col]
        curr_close = df[close_col]

        # 前一根蜡烛
        prev_open = df[open_col].shift(1)
        prev_close = df[close_col].shift(1)

        # 看涨吞没：
        # 1. 前一根是阴线（close < open）
        # 2. 当前是阳线（close > open）
        # 3. 当前实体完全包含前一根
        bullish_engulfing = (
            (prev_close < prev_open) &  # 前一根阴线
            (curr_close > curr_open) &  # 当前阳线
            (curr_open <= prev_close) &  # 当前开盘低于前收盘
            (curr_close >= prev_open)    # 当前收盘高于前开盘
        )

        # 看跌吞没：
        # 1. 前一根是阳线（close > open）
        # 2. 当前是阴线（close < open）
        # 3. 当前实体完全包含前一根
        bearish_engulfing = (
            (prev_close > prev_open) &  # 前一根阳线
            (curr_close < curr_open) &  # 当前阴线
            (curr_open >= prev_close) &  # 当前开盘高于前收盘
            (curr_close <= prev_open)    # 当前收盘低于前开盘
        )

        df = df.with_columns([
            bullish_engulfing.alias(result_col_bullish),
            bearish_engulfing.alias(result_col_bearish)
        ])

        return df

    @staticmethod
    def shooting_star(df: pl.DataFrame, open_col: str, high_col: str, low_col: str, close_col: str,
                     body_position: float = 0.3, shadow_ratio: float = 2.0,
                     result_col: str = 'Shooting_Star') -> pl.DataFrame:
        """
        Shooting Star - 流星线形态

        识别上涨趋势中的顶部反转信号
        特征：小实体在底部，长上影线，下影线很短或没有

        参数:
        df: Polars DataFrame
        open_col, high_col, low_col, close_col: OHLC列名
        body_position: 实体位置阈值（从底部算，默认30%）
        shadow_ratio: 上影线与实体的比率（默认2倍）
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Shooting_Star 列的 DataFrame（True/False）

        用途:
        - 顶部反转信号
        - 上涨趋势中出现更有效
        - 需要后续确认
        """
        # 计算实体
        body = (df[close_col] - df[open_col]).abs()

        # 计算影线
        lower_shadow = pl.min_horizontal(df[open_col], df[close_col]) - df[low_col]
        upper_shadow = df[high_col] - pl.max_horizontal(df[open_col], df[close_col])

        # 总范围
        total_range = df[high_col] - df[low_col]

        # Shooting Star条件：
        # 1. 上影线至少是实体的2倍
        # 2. 下影线很短（小于实体）
        # 3. 实体在下方30%区域
        body_bottom = pl.min_horizontal(df[open_col], df[close_col])
        body_position_ratio = (body_bottom - df[low_col]) / (total_range + 1e-10)

        is_shooting_star = (
            (upper_shadow >= body * shadow_ratio) &
            (lower_shadow <= body) &
            (body_position_ratio <= body_position) &
            (body > 0)  # 必须有实体
        )

        df = df.with_columns(
            is_shooting_star.alias(result_col)
        )

        return df

    @staticmethod
    def morning_star(df: pl.DataFrame, open_col: str, high_col: str, low_col: str, close_col: str,
                    result_col: str = 'Morning_Star') -> pl.DataFrame:
        """
        Morning Star - 早晨之星形态

        三根蜡烛组合的底部反转形态
        特征：
        1. 第一根：大阴线
        2. 第二根：小实体（星线），向下跳空
        3. 第三根：大阳线，收盘在第一根实体中部以上

        参数:
        df: Polars DataFrame
        open_col, high_col, low_col, close_col: OHLC列名
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Morning_Star 列的 DataFrame（True/False）

        用途:
        - 强烈的底部反转信号
        - 三星形态之一
        - 可靠性较高
        """
        import numpy as np

        open_arr = df[open_col].to_numpy()
        high_arr = df[high_col].to_numpy()
        low_arr = df[low_col].to_numpy()
        close_arr = df[close_col].to_numpy()

        n = len(open_arr)
        morning_star = np.full(n, False)

        for i in range(2, n):
            # 第一根蜡烛（i-2）：大阴线
            body1 = abs(close_arr[i-2] - open_arr[i-2])
            is_bearish1 = close_arr[i-2] < open_arr[i-2]
            range1 = high_arr[i-2] - low_arr[i-2]

            # 第二根蜡烛（i-1）：小实体星线
            body2 = abs(close_arr[i-1] - open_arr[i-1])
            range2 = high_arr[i-1] - low_arr[i-1]
            is_small_body = body2 < body1 * 0.3  # 实体小于第一根的30%

            # 向下跳空
            gap_down = max(open_arr[i-1], close_arr[i-1]) < close_arr[i-2]

            # 第三根蜡烛（i）：大阳线
            body3 = abs(close_arr[i] - open_arr[i])
            is_bullish3 = close_arr[i] > open_arr[i]

            # 第三根收盘在第一根实体中部以上
            first_midpoint = (open_arr[i-2] + close_arr[i-2]) / 2
            closes_above_mid = close_arr[i] > first_midpoint

            # Morning Star条件
            if (is_bearish1 and is_small_body and gap_down and
                is_bullish3 and closes_above_mid and body1 > 0 and body3 > 0):
                morning_star[i] = True

        df = df.with_columns(
            pl.Series(result_col, morning_star)
        )

        return df

    @staticmethod
    def three_white_soldiers(df: pl.DataFrame, open_col: str, close_col: str,
                            result_col: str = 'Three_White_Soldiers') -> pl.DataFrame:
        """
        Three White Soldiers - 三白兵形态

        三根连续上涨的阳线
        特征：
        1. 三根连续阳线
        2. 每根收盘价高于前一根
        3. 每根开盘在前一根实体内
        4. 实体较大，影线较短

        参数:
        df: Polars DataFrame
        open_col, close_col: 开盘价和收盘价列名
        result_col: 结果列名

        返回:
        pl.DataFrame: 添加了 Three_White_Soldiers 列的 DataFrame（True/False）

        用途:
        - 强烈的看涨信号
        - 趋势延续或反转
        - 可靠性较高
        """
        import numpy as np

        open_arr = df[open_col].to_numpy()
        close_arr = df[close_col].to_numpy()

        n = len(open_arr)
        three_white = np.full(n, False)

        for i in range(2, n):
            # 三根都是阳线
            is_bullish_1 = close_arr[i-2] > open_arr[i-2]
            is_bullish_2 = close_arr[i-1] > open_arr[i-1]
            is_bullish_3 = close_arr[i] > open_arr[i]

            if not (is_bullish_1 and is_bullish_2 and is_bullish_3):
                continue

            # 收盘价依次升高
            closes_rising = (close_arr[i-1] > close_arr[i-2] and
                           close_arr[i] > close_arr[i-1])

            # 开盘在前一根实体内
            open_in_body_2 = (open_arr[i-1] >= open_arr[i-2] and
                            open_arr[i-1] <= close_arr[i-2])
            open_in_body_3 = (open_arr[i] >= open_arr[i-1] and
                            open_arr[i] <= close_arr[i-1])

            # 实体较大（至少占一定比例）
            body_1 = close_arr[i-2] - open_arr[i-2]
            body_2 = close_arr[i-1] - open_arr[i-1]
            body_3 = close_arr[i] - open_arr[i]

            has_substantial_bodies = (body_1 > 0 and body_2 > 0 and body_3 > 0)

            # Three White Soldiers条件
            if (closes_rising and open_in_body_2 and open_in_body_3 and
                has_substantial_bodies):
                three_white[i] = True

        df = df.with_columns(
            pl.Series(result_col, three_white)
        )

        return df


class MarketStructureIndicators:
    """市场结构指标类"""

    @staticmethod
    def market_structure(df: pl.DataFrame, high_col: str, low_col: str,
                        swing_period: int = 5, result_col_highs: str = 'Structure_High',
                        result_col_lows: str = 'Structure_Low') -> pl.DataFrame:
        """
        Market Structure - 市场结构

        识别市场的摆动高点和摆动低点
        用于判断趋势和结构转变

        参数:
        df: Polars DataFrame
        high_col, low_col: 最高价和最低价列名
        swing_period: 摆动周期（默认5，需要前后各5根K线确认）
        result_col_highs: 结构高点列名
        result_col_lows: 结构低点列名

        返回:
        pl.DataFrame: 添加了结构高点和低点列的 DataFrame

        用途:
        - 识别趋势变化
        - 支撑阻力位
        - 交易区间识别
        """
        import numpy as np

        high = df[high_col].to_numpy()
        low = df[low_col].to_numpy()
        n = len(high)

        structure_highs = np.full(n, np.nan)
        structure_lows = np.full(n, np.nan)

        for i in range(swing_period, n - swing_period):
            # 摆动高点：当前高点是前后swing_period根K线中的最高
            window_highs = high[i - swing_period:i + swing_period + 1]
            if high[i] == np.max(window_highs):
                structure_highs[i] = high[i]

            # 摆动低点：当前低点是前后swing_period根K线中的最低
            window_lows = low[i - swing_period:i + swing_period + 1]
            if low[i] == np.min(window_lows):
                structure_lows[i] = low[i]

        df = df.with_columns([
            pl.Series(result_col_highs, structure_highs),
            pl.Series(result_col_lows, structure_lows)
        ])

        return df

    @staticmethod
    def order_blocks(df: pl.DataFrame, open_col: str, high_col: str, low_col: str,
                    close_col: str, volume_col: Optional[str] = None,
                    lookback: int = 10) -> pl.DataFrame:
        """
        Order Blocks - 订单块

        识别机构订单集中的价格区域
        通常在强势突破前的最后一根反向K线

        参数:
        df: Polars DataFrame
        open_col, high_col, low_col, close_col: OHLC列名
        volume_col: 成交量列名（可选）
        lookback: 回溯周期

        返回:
        pl.DataFrame: 添加了订单块识别列的 DataFrame

        用途:
        - 识别供需区域
        - 机构级别支撑阻力
        - 高概率反转区域
        """
        import numpy as np

        open_arr = df[open_col].to_numpy()
        high_arr = df[high_col].to_numpy()
        low_arr = df[low_col].to_numpy()
        close_arr = df[close_col].to_numpy()

        n = len(open_arr)
        bullish_ob = np.full(n, False)  # 看涨订单块
        bearish_ob = np.full(n, False)  # 看跌订单块

        for i in range(lookback, n - 1):
            # 看涨订单块：
            # 1. 当前K线是阴线（close < open）
            # 2. 下一根K线强势上涨突破当前高点
            if close_arr[i] < open_arr[i]:  # 当前是阴线
                if close_arr[i+1] > high_arr[i]:  # 下一根突破
                    # 检查是否是近期最后一根阴线
                    is_last_bearish = True
                    for j in range(i+1, min(i+lookback, n)):
                        if close_arr[j] < open_arr[j]:
                            is_last_bearish = False
                            break

                    if is_last_bearish:
                        bullish_ob[i] = True

            # 看跌订单块：
            # 1. 当前K线是阳线（close > open）
            # 2. 下一根K线强势下跌突破当前低点
            if close_arr[i] > open_arr[i]:  # 当前是阳线
                if close_arr[i+1] < low_arr[i]:  # 下一根突破
                    # 检查是否是近期最后一根阳线
                    is_last_bullish = True
                    for j in range(i+1, min(i+lookback, n)):
                        if close_arr[j] > open_arr[j]:
                            is_last_bullish = False
                            break

                    if is_last_bullish:
                        bearish_ob[i] = True

        df = df.with_columns([
            pl.Series('Bullish_OB', bullish_ob),
            pl.Series('Bearish_OB', bearish_ob)
        ])

        return df

    @staticmethod
    def fair_value_gaps(df: pl.DataFrame, high_col: str, low_col: str,
                       min_gap_ratio: float = 0.001) -> pl.DataFrame:
        """
        Fair Value Gaps (FVG) - 公允价值缺口

        识别价格快速移动时留下的未填补缺口
        市场倾向于回补这些缺口

        参数:
        df: Polars DataFrame
        high_col, low_col: 最高价和最低价列名
        min_gap_ratio: 最小缺口比例（默认0.1%）

        返回:
        pl.DataFrame: 添加了FVG识别和缺口大小列的 DataFrame

        用途:
        - 识别价格失衡区域
        - 回补交易机会
        - 支撑阻力位
        """
        import numpy as np

        high = df[high_col].to_numpy()
        low = df[low_col].to_numpy()
        n = len(high)

        bullish_fvg = np.full(n, False)  # 看涨FVG
        bearish_fvg = np.full(n, False)  # 看跌FVG
        gap_size = np.full(n, np.nan)    # 缺口大小

        for i in range(2, n):
            # 看涨FVG：第三根K线的低点 > 第一根K线的高点
            # 即：low[i] > high[i-2]
            if low[i] > high[i-2]:
                gap = low[i] - high[i-2]
                gap_ratio = gap / high[i-2]

                if gap_ratio >= min_gap_ratio:
                    bullish_fvg[i-1] = True  # 标记在中间那根K线
                    gap_size[i-1] = gap

            # 看跌FVG：第三根K线的高点 < 第一根K线的低点
            # 即：high[i] < low[i-2]
            if high[i] < low[i-2]:
                gap = low[i-2] - high[i]
                gap_ratio = gap / low[i-2]

                if gap_ratio >= min_gap_ratio:
                    bearish_fvg[i-1] = True  # 标记在中间那根K线
                    gap_size[i-1] = gap

        df = df.with_columns([
            pl.Series('Bullish_FVG', bullish_fvg),
            pl.Series('Bearish_FVG', bearish_fvg),
            pl.Series('FVG_Gap_Size', gap_size)
        ])

        return df

    @staticmethod
    def liquidity_levels(df: pl.DataFrame, high_col: str, low_col: str,
                        volume_col: str, period: int = 20,
                        threshold_percentile: float = 90) -> pl.DataFrame:
        """
        Liquidity Levels - 流动性水平

        识别高流动性区域（价格磁石）
        机构倾向于在这些区域扫荡止损

        参数:
        df: Polars DataFrame
        high_col, low_col: 最高价和最低价列名
        volume_col: 成交量列名
        period: 回溯周期
        threshold_percentile: 流动性阈值百分位（默认90%）

        返回:
        pl.DataFrame: 添加了流动性水平列的 DataFrame

        用途:
        - 识别止损集中区域
        - 预测价格目标
        - 反转区域
        """
        import numpy as np

        high = df[high_col].to_numpy()
        low = df[low_col].to_numpy()
        volume = df[volume_col].to_numpy()
        n = len(high)

        liquidity_highs = np.full(n, False)  # 高流动性高点
        liquidity_lows = np.full(n, False)   # 高流动性低点
        liquidity_score = np.full(n, np.nan) # 流动性得分

        for i in range(period, n):
            # 计算局部高低点
            window_high_max = np.max(high[i-period:i])
            window_low_min = np.min(low[i-period:i])
            window_volume = volume[i-period:i]

            # 计算流动性得分（成交量的分位数）
            volume_threshold = np.percentile(window_volume, threshold_percentile)

            # 如果当前高点接近局部最高点且成交量大
            if high[i] >= window_high_max * 0.999 and volume[i] >= volume_threshold:
                liquidity_highs[i] = True
                liquidity_score[i] = volume[i]

            # 如果当前低点接近局部最低点且成交量大
            if low[i] <= window_low_min * 1.001 and volume[i] >= volume_threshold:
                liquidity_lows[i] = True
                liquidity_score[i] = volume[i]

        df = df.with_columns([
            pl.Series('Liquidity_High', liquidity_highs),
            pl.Series('Liquidity_Low', liquidity_lows),
            pl.Series('Liquidity_Score', liquidity_score)
        ])

        return df


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("技术指标模块测试")
    print("=" * 80)

    # 创建测试数据
    test_data = {
        '日期': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05',
                '2025-01-06', '2025-01-07', '2025-01-08', '2025-01-09', '2025-01-10',
                '2025-01-11', '2025-01-12', '2025-01-13', '2025-01-14', '2025-01-15',
                '2025-01-16', '2025-01-17', '2025-01-18', '2025-01-19', '2025-01-20'],
        '收盘': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                110, 112, 111, 113, 115, 114, 116, 118, 117, 119],
        '最高': [101, 103, 102, 104, 106, 105, 107, 109, 108, 110,
                111, 113, 112, 114, 116, 115, 117, 119, 118, 120],
        '最低': [99, 101, 100, 102, 104, 103, 105, 107, 106, 108,
                109, 111, 110, 112, 114, 113, 115, 117, 116, 118],
        '成交量': [1000, 1100, 950, 1200, 1300, 1150, 1250, 1400, 1350, 1500,
                 1450, 1600, 1550, 1700, 1800, 1750, 1850, 1900, 1880, 2000]
    }

    df = pl.DataFrame(test_data)

    print("\n原始数据:")
    print(df.head())

    # 测试 SMA
    print("\n测试 SMA...")
    df = TrendIndicators.sma(df, '收盘', 5)
    print("[OK] SMA_5 计算完成")

    # 测试 EMA
    print("测试 EMA...")
    df = TrendIndicators.ema(df, '收盘', 5)
    print("[OK] EMA_5 计算完成")

    # 测试 RSI
    print("测试 RSI...")
    df = MomentumIndicators.rsi(df, '收盘', 14)
    print("[OK] RSI_14 计算完成")

    # 测试 MACD
    print("测试 MACD...")
    df = OscillatorIndicators.macd(df, '收盘', 12, 26, 9)
    print("[OK] MACD 计算完成")

    # 测试布林带
    print("测试布林带...")
    df = VolatilityIndicators.bollinger_bands(df, '收盘', 10, 2.0)
    print("[OK] 布林带计算完成")

    # 测试 ATR
    print("测试 ATR...")
    df = VolatilityIndicators.atr(df, '最高', '最低', '收盘', 14)
    print("[OK] ATR_14 计算完成")

    # 测试 OBV
    print("测试 OBV...")
    df = VolumeIndicators.obv(df, '收盘', '成交量')
    print("[OK] OBV 计算完成")

    # 测试 Stochastic
    print("测试 Stochastic...")
    df = OscillatorIndicators.stochastic(df, '最高', '最低', '收盘', 14, 3)
    print("[OK] Stochastic 计算完成")

    print("\n计算结果（最后5行）:")
    print(df.tail())

    print("\n" + "=" * 80)
    print(f"[OK] 所有测试完成！共计算了 {len(df.columns) - 5} 个指标")
    print("=" * 80)
