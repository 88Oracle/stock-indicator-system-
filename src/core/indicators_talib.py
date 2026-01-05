"""
技术指标计算模�?- TA-Lib实现版本
功能：使用专业的TA-Lib库实现各类技术指标的计算
特点：计算准确、性能稳定、与专业交易平台一�?
注意：需要先安装TA-Lib�?- Windows: pip install TA-Lib (或从 https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib 下载whl文件安装)
- Linux/Mac: 参�?https://github.com/mrjbq7/ta-lib
"""

import pandas as pd
import polars as pl
import numpy as np
import talib
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial


class TechnicalIndicatorsTALib:
    """
    用于计算股票技术指标的工具类，基于TA-Lib�?
    这是使用TA-Lib库实现的技术指标计算类，与project中的indicators.py提供的Polars原生实现不同�?    - indicators.py: 使用Polars原生方法，性能好，无需额外依赖
    - indicators_talib.py (本模�?: 使用TA-Lib专业库，计算准确，与专业平台一�?
    根据需求选择使用哪个实现�?    """
    
    # 定义指标列名的模式（用于识别哪些列是指标列）
    INDICATOR_PATTERNS = [
        'SMA_', 'EMA_', 'WMA_', 'DEMA_', 'TEMA_', 'TRIMA_', 'KAMA_', 'MAMA', 'FAMA',
        'MACD_', 'MACDEXT_',
        'ADX_', 'ADXR_', 'APO', 'AROON_', 'AROONOSC', 'BOP', 'CCI_', 'CMO_', 'DX_',
        'MINUS_DI_', 'PLUS_DI_', 'MINUS_DM_', 'PLUS_DM_', 'MOM_', 'PPO', 'ROC_',
        'ROCP_', 'ROCR_', 'ROCR100_',
        'RSI_', 'STOCH_', 'STOCHF_', 'STOCHRSI_', 'TRIX', 'ULTOSC', 'WILLR_',
        'ATR_', 'NATR_', 'TRANGE', 'BB_',
        'AD', 'ADOSC', 'OBV', 'VOL_SMA_',
        'AVGPRICE', 'MEDPRICE', 'TYPPRICE', 'WCLPRICE',
        'MAX_', 'MIN_', 'SUM_',
        'BIAS_', 'Price_Change_', 'Volatility_', 'Relative_Strength_',
        'Volume_Price_Ratio', 'Volume_Change_', 'MA_Cross_', 'EMA_Cross_',
        'MACD_Cross', 'RSI_Overbought_', 'RSI_Oversold_', 'BB_Position', 'BB_Squeeze',
        'Price_Position_', 'STOCH_J', 'Volume_Ratio_'
    ]
    
    @staticmethod
    def get_indicator_columns(columns):
        """
        从列名列表中筛选出指标�?        
        参数:
        columns: 列名列表（可以是pandas Index或polars的列名列表）
        
        返回�?
        list: 指标列名列表
        """
        if hasattr(columns, 'tolist'):
            # pandas Index
            column_list = columns.tolist()
        elif isinstance(columns, list):
            column_list = columns
        else:
            # polars或其他情�?            column_list = list(columns)
        
        indicator_columns = []
        for col in column_list:
            # 检查列名是否匹配任何指标模�?            if any(col.startswith(pattern) or col == pattern for pattern in TechnicalIndicatorsTALib.INDICATOR_PATTERNS):
                indicator_columns.append(col)
        
        return indicator_columns
    
    @staticmethod
    def _to_numpy(data):
        """将数据转换为numpy数组"""
        if isinstance(data, pd.Series):
            return data.values
        elif isinstance(data, pl.Series):
            return data.to_numpy()
        elif isinstance(data, np.ndarray):
            return data
        else:
            return np.array(data)

    @staticmethod
    def _to_series(data, original_data):
        """将numpy数组转换回原始格�?""
        if isinstance(original_data, pd.Series):
            return pd.Series(data, index=original_data.index, name=original_data.name)
        elif isinstance(original_data, pl.Series):
            return pl.Series(data)
        else:
            return data

    # ==================== 移动平均线类 ====================

    @staticmethod
    def calculate_sma(data, window=20):
        """计算简单移动平均线(SMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.SMA(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)

    @staticmethod
    def calculate_ema(data, window=20):
        """计算指数移动平均�?EMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.EMA(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)

    @staticmethod
    def calculate_wma(data, window=20):
        """计算加权移动平均�?WMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.WMA(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_dema(data, window=20):
        """计算双指数移动平均线(DEMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.DEMA(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_tema(data, window=20):
        """计算三重指数移动平均�?TEMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.TEMA(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_trima(data, window=20):
        """计算三角移动平均�?TRIMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.TRIMA(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_kama(data, window=20):
        """计算考夫曼自适应移动平均�?KAMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.KAMA(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_mama(data, fastlimit=0.5, slowlimit=0.05):
        """计算MESA自适应移动平均�?MAMA) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        mama, fama = talib.MAMA(np_data, fastlimit=fastlimit, slowlimit=slowlimit)
        return TechnicalIndicatorsTALib._to_series(mama, data), TechnicalIndicatorsTALib._to_series(fama, data)
    
    # ==================== 趋势指标�?====================
    
    @staticmethod
    def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
        """计算MACD指标 - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        macd, signal, hist = talib.MACD(np_data, fastperiod=fast_period, 
                                        slowperiod=slow_period, signalperiod=signal_period)
        return (TechnicalIndicatorsTALib._to_series(macd, data),
                TechnicalIndicatorsTALib._to_series(signal, data),
                TechnicalIndicatorsTALib._to_series(hist, data))
    
    @staticmethod
    def calculate_macdext(data, fast_period=12, fast_matype=0, slow_period=26, 
                          slow_matype=0, signal_period=9, signal_matype=0):
        """计算MACD扩展指标 - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        macd, signal, hist = talib.MACDEXT(np_data, fastperiod=fast_period, 
                                          fastmatype=fast_matype, slowperiod=slow_period,
                                          slowmatype=slow_matype, signalperiod=signal_period,
                                          signalmatype=signal_matype)
        return (TechnicalIndicatorsTALib._to_series(macd, data),
                TechnicalIndicatorsTALib._to_series(signal, data),
                TechnicalIndicatorsTALib._to_series(hist, data))
    
    @staticmethod
    def calculate_macdfix(data, signal_period=9):
        """计算MACD固定周期指标 - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        macd, signal, hist = talib.MACDFIX(np_data, signalperiod=signal_period)
        return (TechnicalIndicatorsTALib._to_series(macd, data),
                TechnicalIndicatorsTALib._to_series(signal, data),
                TechnicalIndicatorsTALib._to_series(hist, data))
    
    @staticmethod
    def calculate_adx(data_high, data_low, data_close, window=14):
        """计算平均趋向指标(ADX) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.ADX(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_adxr(data_high, data_low, data_close, window=14):
        """计算ADXR指标 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.ADXR(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_apo(data, fast_period=12, slow_period=26, matype=0):
        """计算绝对价格振荡�?APO) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.APO(np_data, fastperiod=fast_period, slowperiod=slow_period, matype=matype)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_aroon(data_high, data_low, window=14):
        """计算Aroon指标 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        aroon_down, aroon_up = talib.AROON(high, low, timeperiod=window)
        return (TechnicalIndicatorsTALib._to_series(aroon_down, data_high),
                TechnicalIndicatorsTALib._to_series(aroon_up, data_high))
    
    @staticmethod
    def calculate_aroonosc(data_high, data_low, window=14):
        """计算Aroon振荡�?- 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        result = talib.AROONOSC(high, low, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_high)
    
    @staticmethod
    def calculate_bop(data_open, data_high, data_low, data_close):
        """计算平衡振荡�?BOP) - 使用TA-Lib"""
        open_price = TechnicalIndicatorsTALib._to_numpy(data_open)
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.BOP(open_price, high, low, close)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_cci(data_high, data_low, data_close, window=14):
        """计算商品通道指数(CCI) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.CCI(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_cmo(data, window=14):
        """计算Chande动量振荡�?CMO) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.CMO(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_dx(data_high, data_low, data_close, window=14):
        """计算方向性指�?DX) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.DX(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_minus_di(data_high, data_low, data_close, window=14):
        """计算-DI指标 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.MINUS_DI(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_plus_di(data_high, data_low, data_close, window=14):
        """计算+DI指标 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.PLUS_DI(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_minus_dm(data_high, data_low, window=14):
        """计算-DM指标 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        result = talib.MINUS_DM(high, low, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_high)
    
    @staticmethod
    def calculate_plus_dm(data_high, data_low, window=14):
        """计算+DM指标 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        result = talib.PLUS_DM(high, low, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_high)
    
    @staticmethod
    def calculate_momentum(data, window=10):
        """计算动量指标 - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.MOM(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_ppo(data, fast_period=12, slow_period=26, matype=0):
        """计算价格振荡�?PPO) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.PPO(np_data, fastperiod=fast_period, slowperiod=slow_period, matype=matype)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_roc(data, window=12):
        """计算变化�?ROC) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.ROC(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_rocp(data, window=12):
        """计算变化率百分比(ROCP) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.ROCP(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_rocr(data, window=12):
        """计算变化率比�?ROCR) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.ROCR(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_rocr100(data, window=12):
        """计算变化率比�?00(ROCR100) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.ROCR100(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_rsi(data, window=14):
        """计算相对强弱指标(RSI) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.RSI(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_stoch(data_high, data_low, data_close, fastk_period=5, 
                        slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0):
        """计算随机指标 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        slowk, slowd = talib.STOCH(high, low, close, fastk_period=fastk_period,
                                   slowk_period=slowk_period, slowk_matype=slowk_matype,
                                   slowd_period=slowd_period, slowd_matype=slowd_matype)
        return (TechnicalIndicatorsTALib._to_series(slowk, data_close),
                TechnicalIndicatorsTALib._to_series(slowd, data_close))
    
    @staticmethod
    def calculate_stochf(data_high, data_low, data_close, fastk_period=5, 
                         fastd_period=3, fastd_matype=0):
        """计算快速随机指�?- 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        fastk, fastd = talib.STOCHF(high, low, close, fastk_period=fastk_period,
                                    fastd_period=fastd_period, fastd_matype=fastd_matype)
        return (TechnicalIndicatorsTALib._to_series(fastk, data_close),
                TechnicalIndicatorsTALib._to_series(fastd, data_close))
    
    @staticmethod
    def calculate_stochrsi(data, window=14, fastk_period=5, fastd_period=3, fastd_matype=0):
        """计算随机RSI - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        fastk, fastd = talib.STOCHRSI(np_data, timeperiod=window, fastk_period=fastk_period,
                                      fastd_period=fastd_period, fastd_matype=fastd_matype)
        return (TechnicalIndicatorsTALib._to_series(fastk, data),
                TechnicalIndicatorsTALib._to_series(fastd, data))
    
    @staticmethod
    def calculate_trix(data, window=30):
        """计算三重指数平滑移动平均(TRIX) - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.TRIX(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_ultosc(data_high, data_low, data_close, timeperiod1=7, 
                        timeperiod2=14, timeperiod3=28):
        """计算终极振荡�?Ultimate Oscillator) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.ULTOSC(high, low, close, timeperiod1=timeperiod1,
                             timeperiod2=timeperiod2, timeperiod3=timeperiod3)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_willr(data_high, data_low, data_close, window=14):
        """计算威廉指标(Williams %R) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.WILLR(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    # ==================== 波动性指标类 ====================
    
    @staticmethod
    def calculate_atr(data_high, data_low, data_close, window=14):
        """计算平均真实范围(ATR) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.ATR(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_natr(data_high, data_low, data_close, window=14):
        """计算归一化平均真实范�?NATR) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.NATR(high, low, close, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_trange(data_high, data_low, data_close):
        """计算真实范围(TRANGE) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.TRANGE(high, low, close)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_bollinger_bands(data, window=20, num_std=2, matype=0):
        """计算布林�?- 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        upper, middle, lower = talib.BBANDS(np_data, timeperiod=window, 
                                           nbdevup=num_std, nbdevdn=num_std, matype=matype)
        return (TechnicalIndicatorsTALib._to_series(upper, data),
                TechnicalIndicatorsTALib._to_series(middle, data),
                TechnicalIndicatorsTALib._to_series(lower, data))
    
    # ==================== 成交量指标类 ====================
    
    @staticmethod
    def calculate_ad(data_high, data_low, data_close, data_volume):
        """计算累积/派发�?A/D) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        volume = TechnicalIndicatorsTALib._to_numpy(data_volume)
        result = talib.AD(high, low, close, volume)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_adosc(data_high, data_low, data_close, data_volume, 
                       fast_period=3, slow_period=10):
        """计算累积/派发振荡�?ADOSC) - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        volume = TechnicalIndicatorsTALib._to_numpy(data_volume)
        result = talib.ADOSC(high, low, close, volume, fastperiod=fast_period, 
                            slowperiod=slow_period)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_obv(data_close, data_volume):
        """计算能量潮指�?OBV) - 使用TA-Lib"""
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        volume = TechnicalIndicatorsTALib._to_numpy(data_volume)
        result = talib.OBV(close, volume)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    # ==================== 价格变换�?====================
    
    @staticmethod
    def calculate_avgprice(data_open, data_high, data_low, data_close):
        """计算平均价格 - 使用TA-Lib"""
        open_price = TechnicalIndicatorsTALib._to_numpy(data_open)
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.AVGPRICE(open_price, high, low, close)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_medprice(data_high, data_low):
        """计算中位价格 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        result = talib.MEDPRICE(high, low)
        return TechnicalIndicatorsTALib._to_series(result, data_high)
    
    @staticmethod
    def calculate_typprice(data_high, data_low, data_close):
        """计算典型价格 - 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.TYPPRICE(high, low, close)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    @staticmethod
    def calculate_wclprice(data_high, data_low, data_close):
        """计算加权收盘�?- 使用TA-Lib"""
        high = TechnicalIndicatorsTALib._to_numpy(data_high)
        low = TechnicalIndicatorsTALib._to_numpy(data_low)
        close = TechnicalIndicatorsTALib._to_numpy(data_close)
        result = talib.WCLPRICE(high, low, close)
        return TechnicalIndicatorsTALib._to_series(result, data_close)
    
    # ==================== 数学变换�?====================
    
    @staticmethod
    def calculate_max(data, window=30):
        """计算最高�?- 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.MAX(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_maxindex(data, window=30):
        """计算最高值索�?- 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.MAXINDEX(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_min(data, window=30):
        """计算最低�?- 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.MIN(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_minindex(data, window=30):
        """计算最低值索�?- 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.MININDEX(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    @staticmethod
    def calculate_sum(data, window=30):
        """计算总和 - 使用TA-Lib"""
        np_data = TechnicalIndicatorsTALib._to_numpy(data)
        result = talib.SUM(np_data, timeperiod=window)
        return TechnicalIndicatorsTALib._to_series(result, data)
    
    # ==================== 主要计算函数 ====================
    
    @staticmethod
    def calculate_all_indicators(data, is_pandas=True):
        """计算所有技术指标（超过100个）"""
        if is_pandas:
            # 在pandas中使用data.copy()是为了避免直接修改原始DataFrame（因为赋值是引用，修改result会影响原data）；
            # 这样可以保证原始数据不被污染。而polars的DataFrame在赋值后默认是惰性和不可变的，因此直接赋值通常不会影响原数据，
            # 所以polars下通常可以直接用result = data而无需copy()�?            result = data.copy()
        else:
            # Polars优化：转换为LazyFrame以启用延迟计算和查询优化
            if isinstance(data, pl.DataFrame):
                result = data.lazy()
            else:
                result = data
        
        # 确保数据有需要的�?        required_columns = ['最�?, '最�?, '收盘�?, '总量']
        
        if is_pandas:
            # 尝试使用'现价'作为收盘价的替代
            if '收盘�? not in result.columns and '现价' in result.columns:
                result['收盘�?] = result['现价']
            if '今开' not in result.columns and '开盘价' in result.columns:
                result['今开'] = result['开盘价']
            elif '今开' not in result.columns:
                result['今开'] = result['收盘�?]  # 如果没有开盘价，使用收盘价
        else:
            # Polars优化：使用collect_schema()获取列名，避免性能警告
            if isinstance(result, pl.LazyFrame):
                column_names = result.collect_schema().names()
            else:
                column_names = result.columns
            
            # Polars LazyFrame使用with_columns来添加列（延迟计算）
            columns_to_add = []
            if '收盘�? not in column_names and '现价' in column_names:
                columns_to_add.append(pl.col('现价').alias('收盘�?))
            if '今开' not in column_names:
                if '开盘价' in column_names:
                    columns_to_add.append(pl.col('开盘价').alias('今开'))
                elif '收盘�? in column_names:
                    columns_to_add.append(pl.col('收盘�?).alias('今开'))
                else:
                    columns_to_add.append(pl.col('现价').alias('今开'))
            if columns_to_add:
                result = result.with_columns(columns_to_add)
                # 更新列名列表
                if isinstance(result, pl.LazyFrame):
                    column_names = result.collect_schema().names()
                else:
                    column_names = result.columns
        
        # 检查必需列（使用已获取的列名列表�?        if is_pandas:
            for col in required_columns:
                if col not in result.columns:
                    raise ValueError(f"缺少必要的列: {col}")
        else:
            for col in required_columns:
                if col not in column_names:
                    raise ValueError(f"缺少必要的列: {col}")
        
        # 获取必要的数据系�?        if is_pandas:
            close = result['收盘�?]
            high = result['最�?]
            low = result['最�?]
            volume = result['总量']
            open_price = result.get('今开', close)
            # 收集所有新列的字典（用于pd.concat，消除碎片化警告�?            new_columns_dict = {}
        else:
            # Polars优化：先collect LazyFrame为DataFrame以获取Series（talib需要numpy数组�?            # 但我们可以先构建所有计算，然后一次性collect
            # 为了使用talib，我们需要先collect获取Series
            result_df = result.collect() if isinstance(result, pl.LazyFrame) else result
            close = result_df['收盘�?]
            high = result_df['最�?]
            low = result_df['最�?]
            volume = result_df['总量']
            # Polars DataFrame不支�?get()方法，使用条件判�?            if '今开' in result_df.columns:
                open_price = result_df['今开']
            else:
                open_price = close
            result = result_df  # 更新result为DataFrame
        
        # ========== 移动平均线类 (1-30) ==========
        if is_pandas:
            new_columns_dict['SMA_5'] = TechnicalIndicatorsTALib.calculate_sma(close, 5)
            new_columns_dict['SMA_10'] = TechnicalIndicatorsTALib.calculate_sma(close, 10)
            new_columns_dict['SMA_20'] = TechnicalIndicatorsTALib.calculate_sma(close, 20)
            new_columns_dict['SMA_30'] = TechnicalIndicatorsTALib.calculate_sma(close, 30)
            new_columns_dict['SMA_50'] = TechnicalIndicatorsTALib.calculate_sma(close, 50)
            new_columns_dict['SMA_60'] = TechnicalIndicatorsTALib.calculate_sma(close, 60)
            new_columns_dict['SMA_100'] = TechnicalIndicatorsTALib.calculate_sma(close, 100)
            new_columns_dict['SMA_120'] = TechnicalIndicatorsTALib.calculate_sma(close, 120)
            new_columns_dict['SMA_200'] = TechnicalIndicatorsTALib.calculate_sma(close, 200)
            new_columns_dict['SMA_250'] = TechnicalIndicatorsTALib.calculate_sma(close, 250)
            
            new_columns_dict['EMA_5'] = TechnicalIndicatorsTALib.calculate_ema(close, 5)
            new_columns_dict['EMA_10'] = TechnicalIndicatorsTALib.calculate_ema(close, 10)
            new_columns_dict['EMA_12'] = TechnicalIndicatorsTALib.calculate_ema(close, 12)
            new_columns_dict['EMA_20'] = TechnicalIndicatorsTALib.calculate_ema(close, 20)
            new_columns_dict['EMA_26'] = TechnicalIndicatorsTALib.calculate_ema(close, 26)
            new_columns_dict['EMA_30'] = TechnicalIndicatorsTALib.calculate_ema(close, 30)
            new_columns_dict['EMA_50'] = TechnicalIndicatorsTALib.calculate_ema(close, 50)
            new_columns_dict['EMA_60'] = TechnicalIndicatorsTALib.calculate_ema(close, 60)
            new_columns_dict['EMA_100'] = TechnicalIndicatorsTALib.calculate_ema(close, 100)
            new_columns_dict['EMA_200'] = TechnicalIndicatorsTALib.calculate_ema(close, 200)
            
            new_columns_dict['WMA_5'] = TechnicalIndicatorsTALib.calculate_wma(close, 5)
            new_columns_dict['WMA_10'] = TechnicalIndicatorsTALib.calculate_wma(close, 10)
            new_columns_dict['WMA_20'] = TechnicalIndicatorsTALib.calculate_wma(close, 20)
            new_columns_dict['WMA_30'] = TechnicalIndicatorsTALib.calculate_wma(close, 30)
            new_columns_dict['WMA_50'] = TechnicalIndicatorsTALib.calculate_wma(close, 50)
            
            new_columns_dict['DEMA_20'] = TechnicalIndicatorsTALib.calculate_dema(close, 20)
            new_columns_dict['DEMA_50'] = TechnicalIndicatorsTALib.calculate_dema(close, 50)
            
            new_columns_dict['TEMA_20'] = TechnicalIndicatorsTALib.calculate_tema(close, 20)
            new_columns_dict['TEMA_50'] = TechnicalIndicatorsTALib.calculate_tema(close, 50)
            
            new_columns_dict['TRIMA_20'] = TechnicalIndicatorsTALib.calculate_trima(close, 20)
            new_columns_dict['TRIMA_50'] = TechnicalIndicatorsTALib.calculate_trima(close, 50)
            
            new_columns_dict['KAMA_20'] = TechnicalIndicatorsTALib.calculate_kama(close, 20)
            new_columns_dict['KAMA_50'] = TechnicalIndicatorsTALib.calculate_kama(close, 50)
            
            mama, fama = TechnicalIndicatorsTALib.calculate_mama(close)
            new_columns_dict['MAMA'] = mama
            new_columns_dict['FAMA'] = fama
        else:
            # Polars优化：批量计算所有指标，减少中间DataFrame操作
            # 先计算所有移动平均线类指�?            sma_5 = TechnicalIndicatorsTALib.calculate_sma(close, 5)
            sma_10 = TechnicalIndicatorsTALib.calculate_sma(close, 10)
            sma_20 = TechnicalIndicatorsTALib.calculate_sma(close, 20)
            sma_30 = TechnicalIndicatorsTALib.calculate_sma(close, 30)
            sma_50 = TechnicalIndicatorsTALib.calculate_sma(close, 50)
            sma_60 = TechnicalIndicatorsTALib.calculate_sma(close, 60)
            sma_100 = TechnicalIndicatorsTALib.calculate_sma(close, 100)
            sma_120 = TechnicalIndicatorsTALib.calculate_sma(close, 120)
            sma_200 = TechnicalIndicatorsTALib.calculate_sma(close, 200)
            sma_250 = TechnicalIndicatorsTALib.calculate_sma(close, 250)
            ema_5 = TechnicalIndicatorsTALib.calculate_ema(close, 5)
            ema_10 = TechnicalIndicatorsTALib.calculate_ema(close, 10)
            ema_12 = TechnicalIndicatorsTALib.calculate_ema(close, 12)
            ema_20 = TechnicalIndicatorsTALib.calculate_ema(close, 20)
            ema_26 = TechnicalIndicatorsTALib.calculate_ema(close, 26)
            ema_30 = TechnicalIndicatorsTALib.calculate_ema(close, 30)
            ema_50 = TechnicalIndicatorsTALib.calculate_ema(close, 50)
            ema_60 = TechnicalIndicatorsTALib.calculate_ema(close, 60)
            ema_100 = TechnicalIndicatorsTALib.calculate_ema(close, 100)
            ema_200 = TechnicalIndicatorsTALib.calculate_ema(close, 200)
            wma_5 = TechnicalIndicatorsTALib.calculate_wma(close, 5)
            wma_10 = TechnicalIndicatorsTALib.calculate_wma(close, 10)
            wma_20 = TechnicalIndicatorsTALib.calculate_wma(close, 20)
            wma_30 = TechnicalIndicatorsTALib.calculate_wma(close, 30)
            wma_50 = TechnicalIndicatorsTALib.calculate_wma(close, 50)
            dema_20 = TechnicalIndicatorsTALib.calculate_dema(close, 20)
            dema_50 = TechnicalIndicatorsTALib.calculate_dema(close, 50)
            tema_20 = TechnicalIndicatorsTALib.calculate_tema(close, 20)
            tema_50 = TechnicalIndicatorsTALib.calculate_tema(close, 50)
            trima_20 = TechnicalIndicatorsTALib.calculate_trima(close, 20)
            trima_50 = TechnicalIndicatorsTALib.calculate_trima(close, 50)
            kama_20 = TechnicalIndicatorsTALib.calculate_kama(close, 20)
            kama_50 = TechnicalIndicatorsTALib.calculate_kama(close, 50)
            mama, fama = TechnicalIndicatorsTALib.calculate_mama(close)
            
            # 计算MACD类指�?            macd_line, signal_line, macd_hist = TechnicalIndicatorsTALib.calculate_macd(close)
            macd_ext_line, macd_ext_signal, macd_ext_hist = TechnicalIndicatorsTALib.calculate_macdext(close)
            
            # 优化：合并移动平均线和MACD类指标为一次with_columns调用
            # 使用列表推导式批量创建Series，减少代码重�?            ma_series = [
                pl.Series('SMA_5', sma_5), pl.Series('SMA_10', sma_10), pl.Series('SMA_20', sma_20),
                pl.Series('SMA_30', sma_30), pl.Series('SMA_50', sma_50), pl.Series('SMA_60', sma_60),
                pl.Series('SMA_100', sma_100), pl.Series('SMA_120', sma_120), pl.Series('SMA_200', sma_200),
                pl.Series('SMA_250', sma_250), pl.Series('EMA_5', ema_5), pl.Series('EMA_10', ema_10),
                pl.Series('EMA_12', ema_12), pl.Series('EMA_20', ema_20), pl.Series('EMA_26', ema_26),
                pl.Series('EMA_30', ema_30), pl.Series('EMA_50', ema_50), pl.Series('EMA_60', ema_60),
                pl.Series('EMA_100', ema_100), pl.Series('EMA_200', ema_200), pl.Series('WMA_5', wma_5),
                pl.Series('WMA_10', wma_10), pl.Series('WMA_20', wma_20), pl.Series('WMA_30', wma_30),
                pl.Series('WMA_50', wma_50), pl.Series('DEMA_20', dema_20), pl.Series('DEMA_50', dema_50),
                pl.Series('TEMA_20', tema_20), pl.Series('TEMA_50', tema_50), pl.Series('TRIMA_20', trima_20),
                pl.Series('TRIMA_50', trima_50), pl.Series('KAMA_20', kama_20), pl.Series('KAMA_50', kama_50),
                pl.Series('MAMA', mama), pl.Series('FAMA', fama),
                pl.Series('MACD_Line', macd_line),
                pl.Series('MACD_Signal', signal_line),
                pl.Series('MACD_Hist', macd_hist),
                pl.Series('MACDEXT_Line', macd_ext_line),
                pl.Series('MACDEXT_Signal', macd_ext_signal),
                pl.Series('MACDEXT_Hist', macd_ext_hist)
            ]
            result = result.with_columns(ma_series)
            # 清理临时变量以释放内�?            del sma_5, sma_10, sma_20, sma_30, sma_50, sma_60, sma_100, sma_120, sma_200, sma_250
            del ema_5, ema_10, ema_12, ema_20, ema_26, ema_30, ema_50, ema_60, ema_100, ema_200
            del wma_5, wma_10, wma_20, wma_30, wma_50, dema_20, dema_50, tema_20, tema_50
            del trima_20, trima_50, kama_20, kama_50, mama, fama
            del macd_line, signal_line, macd_hist, macd_ext_line, macd_ext_signal, macd_ext_hist
            del ma_series
        
        # ========== MACD�?(31-36) ==========
        if is_pandas:
            macd_line, signal_line, macd_hist = TechnicalIndicatorsTALib.calculate_macd(close)
            new_columns_dict['MACD_Line'] = macd_line
            new_columns_dict['MACD_Signal'] = signal_line
            new_columns_dict['MACD_Hist'] = macd_hist
            
            macd_ext_line, macd_ext_signal, macd_ext_hist = TechnicalIndicatorsTALib.calculate_macdext(close)
            new_columns_dict['MACDEXT_Line'] = macd_ext_line
            new_columns_dict['MACDEXT_Signal'] = macd_ext_signal
            new_columns_dict['MACDEXT_Hist'] = macd_ext_hist
        
        # ========== 趋势指标�?(37-55) ==========
        if is_pandas:
            new_columns_dict['ADX_14'] = TechnicalIndicatorsTALib.calculate_adx(high, low, close, 14)
            new_columns_dict['ADX_20'] = TechnicalIndicatorsTALib.calculate_adx(high, low, close, 20)
            new_columns_dict['ADXR_14'] = TechnicalIndicatorsTALib.calculate_adxr(high, low, close, 14)
            new_columns_dict['APO'] = TechnicalIndicatorsTALib.calculate_apo(close)
            aroon_down, aroon_up = TechnicalIndicatorsTALib.calculate_aroon(high, low, 14)
            new_columns_dict['AROON_Down'] = aroon_down
            new_columns_dict['AROON_Up'] = aroon_up
            new_columns_dict['AROONOSC'] = TechnicalIndicatorsTALib.calculate_aroonosc(high, low, 14)
            new_columns_dict['BOP'] = TechnicalIndicatorsTALib.calculate_bop(open_price, high, low, close)
            new_columns_dict['CCI_14'] = TechnicalIndicatorsTALib.calculate_cci(high, low, close, 14)
            new_columns_dict['CCI_20'] = TechnicalIndicatorsTALib.calculate_cci(high, low, close, 20)
            new_columns_dict['CMO_14'] = TechnicalIndicatorsTALib.calculate_cmo(close, 14)
            new_columns_dict['CMO_20'] = TechnicalIndicatorsTALib.calculate_cmo(close, 20)
            new_columns_dict['DX_14'] = TechnicalIndicatorsTALib.calculate_dx(high, low, close, 14)
            new_columns_dict['MINUS_DI_14'] = TechnicalIndicatorsTALib.calculate_minus_di(high, low, close, 14)
            new_columns_dict['PLUS_DI_14'] = TechnicalIndicatorsTALib.calculate_plus_di(high, low, close, 14)
            new_columns_dict['MINUS_DM_14'] = TechnicalIndicatorsTALib.calculate_minus_dm(high, low, 14)
            new_columns_dict['PLUS_DM_14'] = TechnicalIndicatorsTALib.calculate_plus_dm(high, low, 14)
            new_columns_dict['MOM_5'] = TechnicalIndicatorsTALib.calculate_momentum(close, 5)
            new_columns_dict['MOM_10'] = TechnicalIndicatorsTALib.calculate_momentum(close, 10)
            new_columns_dict['MOM_20'] = TechnicalIndicatorsTALib.calculate_momentum(close, 20)
            new_columns_dict['PPO'] = TechnicalIndicatorsTALib.calculate_ppo(close)
            new_columns_dict['ROC_5'] = TechnicalIndicatorsTALib.calculate_roc(close, 5)
            new_columns_dict['ROC_10'] = TechnicalIndicatorsTALib.calculate_roc(close, 10)
            new_columns_dict['ROC_12'] = TechnicalIndicatorsTALib.calculate_roc(close, 12)
            new_columns_dict['ROC_20'] = TechnicalIndicatorsTALib.calculate_roc(close, 20)
            new_columns_dict['ROCP_12'] = TechnicalIndicatorsTALib.calculate_rocp(close, 12)
            new_columns_dict['ROCR_12'] = TechnicalIndicatorsTALib.calculate_rocr(close, 12)
            new_columns_dict['ROCR100_12'] = TechnicalIndicatorsTALib.calculate_rocr100(close, 12)
        else:
            # Polars优化：批量计算趋势指标类和超买超卖指标类，减少with_columns调用
            # 计算趋势指标�?            adx_14 = TechnicalIndicatorsTALib.calculate_adx(high, low, close, 14)
            adx_20 = TechnicalIndicatorsTALib.calculate_adx(high, low, close, 20)
            adxr_14 = TechnicalIndicatorsTALib.calculate_adxr(high, low, close, 14)
            apo = TechnicalIndicatorsTALib.calculate_apo(close)
            aroon_down, aroon_up = TechnicalIndicatorsTALib.calculate_aroon(high, low, 14)
            aroonosc = TechnicalIndicatorsTALib.calculate_aroonosc(high, low, 14)
            bop = TechnicalIndicatorsTALib.calculate_bop(open_price, high, low, close)
            cci_14 = TechnicalIndicatorsTALib.calculate_cci(high, low, close, 14)
            cci_20 = TechnicalIndicatorsTALib.calculate_cci(high, low, close, 20)
            cmo_14 = TechnicalIndicatorsTALib.calculate_cmo(close, 14)
            cmo_20 = TechnicalIndicatorsTALib.calculate_cmo(close, 20)
            dx_14 = TechnicalIndicatorsTALib.calculate_dx(high, low, close, 14)
            minus_di_14 = TechnicalIndicatorsTALib.calculate_minus_di(high, low, close, 14)
            plus_di_14 = TechnicalIndicatorsTALib.calculate_plus_di(high, low, close, 14)
            minus_dm_14 = TechnicalIndicatorsTALib.calculate_minus_dm(high, low, 14)
            plus_dm_14 = TechnicalIndicatorsTALib.calculate_plus_dm(high, low, 14)
            mom_5 = TechnicalIndicatorsTALib.calculate_momentum(close, 5)
            mom_10 = TechnicalIndicatorsTALib.calculate_momentum(close, 10)
            mom_20 = TechnicalIndicatorsTALib.calculate_momentum(close, 20)
            ppo = TechnicalIndicatorsTALib.calculate_ppo(close)
            roc_5 = TechnicalIndicatorsTALib.calculate_roc(close, 5)
            roc_10 = TechnicalIndicatorsTALib.calculate_roc(close, 10)
            roc_12 = TechnicalIndicatorsTALib.calculate_roc(close, 12)
            roc_20 = TechnicalIndicatorsTALib.calculate_roc(close, 20)
            rocp_12 = TechnicalIndicatorsTALib.calculate_rocp(close, 12)
            rocr_12 = TechnicalIndicatorsTALib.calculate_rocr(close, 12)
            rocr100_12 = TechnicalIndicatorsTALib.calculate_rocr100(close, 12)
            
            # 计算超买超卖指标�?            rsi_6 = TechnicalIndicatorsTALib.calculate_rsi(close, 6)
            rsi_7 = TechnicalIndicatorsTALib.calculate_rsi(close, 7)
            rsi_14 = TechnicalIndicatorsTALib.calculate_rsi(close, 14)
            rsi_21 = TechnicalIndicatorsTALib.calculate_rsi(close, 21)
            rsi_30 = TechnicalIndicatorsTALib.calculate_rsi(close, 30)
            stoch_k, stoch_d = TechnicalIndicatorsTALib.calculate_stoch(high, low, close)
            stochf_k, stochf_d = TechnicalIndicatorsTALib.calculate_stochf(high, low, close)
            stochrsi_k, stochrsi_d = TechnicalIndicatorsTALib.calculate_stochrsi(close)
            trix = TechnicalIndicatorsTALib.calculate_trix(close, 30)
            ultosc = TechnicalIndicatorsTALib.calculate_ultosc(high, low, close)
            willr_6 = TechnicalIndicatorsTALib.calculate_willr(high, low, close, 6)
            willr_14 = TechnicalIndicatorsTALib.calculate_willr(high, low, close, 14)
            willr_20 = TechnicalIndicatorsTALib.calculate_willr(high, low, close, 20)
            
            # 优化：合并趋势指标类和超买超卖指标类为一次with_columns调用
            trend_series = [
                pl.Series('ADX_14', adx_14), pl.Series('ADX_20', adx_20), pl.Series('ADXR_14', adxr_14),
                pl.Series('APO', apo), pl.Series('AROON_Down', aroon_down), pl.Series('AROON_Up', aroon_up),
                pl.Series('AROONOSC', aroonosc), pl.Series('BOP', bop), pl.Series('CCI_14', cci_14),
                pl.Series('CCI_20', cci_20), pl.Series('CMO_14', cmo_14), pl.Series('CMO_20', cmo_20),
                pl.Series('DX_14', dx_14), pl.Series('MINUS_DI_14', minus_di_14), pl.Series('PLUS_DI_14', plus_di_14),
                pl.Series('MINUS_DM_14', minus_dm_14), pl.Series('PLUS_DM_14', plus_dm_14),
                pl.Series('MOM_5', mom_5), pl.Series('MOM_10', mom_10), pl.Series('MOM_20', mom_20),
                pl.Series('PPO', ppo), pl.Series('ROC_5', roc_5), pl.Series('ROC_10', roc_10),
                pl.Series('ROC_12', roc_12), pl.Series('ROC_20', roc_20), pl.Series('ROCP_12', rocp_12),
                pl.Series('ROCR_12', rocr_12), pl.Series('ROCR100_12', rocr100_12),
                pl.Series('RSI_6', rsi_6), pl.Series('RSI_7', rsi_7), pl.Series('RSI_14', rsi_14),
                pl.Series('RSI_21', rsi_21), pl.Series('RSI_30', rsi_30), pl.Series('STOCH_K', stoch_k),
                pl.Series('STOCH_D', stoch_d), pl.Series('STOCHF_K', stochf_k), pl.Series('STOCHF_D', stochf_d),
                pl.Series('STOCHRSI_K', stochrsi_k), pl.Series('STOCHRSI_D', stochrsi_d),
                pl.Series('TRIX', trix), pl.Series('ULTOSC', ultosc), pl.Series('WILLR_6', willr_6),
                pl.Series('WILLR_14', willr_14), pl.Series('WILLR_20', willr_20)
            ]
            result = result.with_columns(trend_series)
            # 清理临时变量以释放内�?            del adx_14, adx_20, adxr_14, apo, aroon_down, aroon_up, aroonosc, bop, cci_14, cci_20
            del cmo_14, cmo_20, dx_14, minus_di_14, plus_di_14, minus_dm_14, plus_dm_14
            del mom_5, mom_10, mom_20, ppo, roc_5, roc_10, roc_12, roc_20, rocp_12, rocr_12, rocr100_12
            del rsi_6, rsi_7, rsi_14, rsi_21, rsi_30, stoch_k, stoch_d, stochf_k, stochf_d
            del stochrsi_k, stochrsi_d, trix, ultosc, willr_6, willr_14, willr_20
            del trend_series
        
        # ========== 超买超卖指标�?(56-75) ==========
        if is_pandas:
            new_columns_dict['RSI_6'] = TechnicalIndicatorsTALib.calculate_rsi(close, 6)
            new_columns_dict['RSI_7'] = TechnicalIndicatorsTALib.calculate_rsi(close, 7)
            new_columns_dict['RSI_14'] = TechnicalIndicatorsTALib.calculate_rsi(close, 14)
            new_columns_dict['RSI_21'] = TechnicalIndicatorsTALib.calculate_rsi(close, 21)
            new_columns_dict['RSI_30'] = TechnicalIndicatorsTALib.calculate_rsi(close, 30)
            stoch_k, stoch_d = TechnicalIndicatorsTALib.calculate_stoch(high, low, close)
            new_columns_dict['STOCH_K'] = stoch_k
            new_columns_dict['STOCH_D'] = stoch_d
            stochf_k, stochf_d = TechnicalIndicatorsTALib.calculate_stochf(high, low, close)
            new_columns_dict['STOCHF_K'] = stochf_k
            new_columns_dict['STOCHF_D'] = stochf_d
            stochrsi_k, stochrsi_d = TechnicalIndicatorsTALib.calculate_stochrsi(close)
            new_columns_dict['STOCHRSI_K'] = stochrsi_k
            new_columns_dict['STOCHRSI_D'] = stochrsi_d
            new_columns_dict['TRIX'] = TechnicalIndicatorsTALib.calculate_trix(close, 30)
            new_columns_dict['ULTOSC'] = TechnicalIndicatorsTALib.calculate_ultosc(high, low, close)
            new_columns_dict['WILLR_6'] = TechnicalIndicatorsTALib.calculate_willr(high, low, close, 6)
            new_columns_dict['WILLR_14'] = TechnicalIndicatorsTALib.calculate_willr(high, low, close, 14)
            new_columns_dict['WILLR_20'] = TechnicalIndicatorsTALib.calculate_willr(high, low, close, 20)
        
        # ========== 波动性指标类 (76-85) ==========
        if is_pandas:
            new_columns_dict['ATR_14'] = TechnicalIndicatorsTALib.calculate_atr(high, low, close, 14)
            new_columns_dict['ATR_20'] = TechnicalIndicatorsTALib.calculate_atr(high, low, close, 20)
            new_columns_dict['NATR_14'] = TechnicalIndicatorsTALib.calculate_natr(high, low, close, 14)
            new_columns_dict['TRANGE'] = TechnicalIndicatorsTALib.calculate_trange(high, low, close)
            bb_upper, bb_middle, bb_lower = TechnicalIndicatorsTALib.calculate_bollinger_bands(close, 20, 2)
            new_columns_dict['BB_Upper'] = bb_upper
            new_columns_dict['BB_Middle'] = bb_middle
            new_columns_dict['BB_Lower'] = bb_lower
            new_columns_dict['BB_Width'] = (bb_upper - bb_lower) / bb_middle
            new_columns_dict['BB_Pct'] = (close - bb_lower) / (bb_upper - bb_lower)
            bb_upper2, bb_middle2, bb_lower2 = TechnicalIndicatorsTALib.calculate_bollinger_bands(close, 20, 2.5)
            new_columns_dict['BB_Upper_2.5'] = bb_upper2
            new_columns_dict['BB_Lower_2.5'] = bb_lower2
        else:
            # Polars优化：批量计算波动性、成交量、价格变换和数学变换类指标，合并为一次with_columns调用
            # 计算波动性指标类
            atr_14 = TechnicalIndicatorsTALib.calculate_atr(high, low, close, 14)
            atr_20 = TechnicalIndicatorsTALib.calculate_atr(high, low, close, 20)
            natr_14 = TechnicalIndicatorsTALib.calculate_natr(high, low, close, 14)
            trange = TechnicalIndicatorsTALib.calculate_trange(high, low, close)
            bb_upper, bb_middle, bb_lower = TechnicalIndicatorsTALib.calculate_bollinger_bands(close, 20, 2)
            bb_upper2, bb_middle2, bb_lower2 = TechnicalIndicatorsTALib.calculate_bollinger_bands(close, 20, 2.5)
            bb_width = (bb_upper - bb_lower) / bb_middle
            bb_pct = (close - bb_lower) / (bb_upper - bb_lower)
            
            # 计算成交量指标类
            ad = TechnicalIndicatorsTALib.calculate_ad(high, low, close, volume)
            adosc = TechnicalIndicatorsTALib.calculate_adosc(high, low, close, volume)
            obv = TechnicalIndicatorsTALib.calculate_obv(close, volume)
            
            # 计算价格变换�?            avgprice = TechnicalIndicatorsTALib.calculate_avgprice(open_price, high, low, close)
            medprice = TechnicalIndicatorsTALib.calculate_medprice(high, low)
            typprice = TechnicalIndicatorsTALib.calculate_typprice(high, low, close)
            wclprice = TechnicalIndicatorsTALib.calculate_wclprice(high, low, close)
            
            # 计算数学变换�?            max_20 = TechnicalIndicatorsTALib.calculate_max(close, 20)
            max_50 = TechnicalIndicatorsTALib.calculate_max(close, 50)
            min_20 = TechnicalIndicatorsTALib.calculate_min(close, 20)
            min_50 = TechnicalIndicatorsTALib.calculate_min(close, 50)
            sum_20 = TechnicalIndicatorsTALib.calculate_sum(close, 20)
            sum_50 = TechnicalIndicatorsTALib.calculate_sum(close, 50)
            
            # 优化：合并所有指标为一次with_columns调用
            vol_series = [
                volume.rolling_mean(5).alias('VOL_SMA_5'),
                volume.rolling_mean(10).alias('VOL_SMA_10'),
                volume.rolling_mean(20).alias('VOL_SMA_20')
            ]
            other_series = [
                pl.Series('ATR_14', atr_14), pl.Series('ATR_20', atr_20), pl.Series('NATR_14', natr_14),
                pl.Series('TRANGE', trange), pl.Series('BB_Upper', bb_upper), pl.Series('BB_Middle', bb_middle),
                pl.Series('BB_Lower', bb_lower), pl.Series('BB_Width', bb_width), pl.Series('BB_Pct', bb_pct),
                pl.Series('BB_Upper_2.5', bb_upper2), pl.Series('BB_Lower_2.5', bb_lower2),
                pl.Series('AD', ad), pl.Series('ADOSC', adosc), pl.Series('OBV', obv),
                pl.Series('AVGPRICE', avgprice), pl.Series('MEDPRICE', medprice),
                pl.Series('TYPPRICE', typprice), pl.Series('WCLPRICE', wclprice),
                pl.Series('MAX_20', max_20), pl.Series('MAX_50', max_50),
                pl.Series('MIN_20', min_20), pl.Series('MIN_50', min_50),
                pl.Series('SUM_20', sum_20), pl.Series('SUM_50', sum_50)
            ]
            result = result.with_columns(vol_series + other_series)
            # 清理临时变量以释放内�?            del atr_14, atr_20, natr_14, trange, bb_upper, bb_middle, bb_lower, bb_upper2, bb_middle2, bb_lower2
            del bb_width, bb_pct, ad, adosc, obv, avgprice, medprice, typprice, wclprice
            del max_20, max_50, min_20, min_50, sum_20, sum_50
            del vol_series, other_series
        
        # ========== 成交量指标类 (86-90) ==========
        if is_pandas:
            new_columns_dict['AD'] = TechnicalIndicatorsTALib.calculate_ad(high, low, close, volume)
            new_columns_dict['ADOSC'] = TechnicalIndicatorsTALib.calculate_adosc(high, low, close, volume)
            new_columns_dict['OBV'] = TechnicalIndicatorsTALib.calculate_obv(close, volume)
            new_columns_dict['VOL_SMA_5'] = volume.rolling(5).mean()
            new_columns_dict['VOL_SMA_10'] = volume.rolling(10).mean()
            new_columns_dict['VOL_SMA_20'] = volume.rolling(20).mean()
        
        # ========== 价格变换�?(91-94) ==========
        if is_pandas:
            new_columns_dict['AVGPRICE'] = TechnicalIndicatorsTALib.calculate_avgprice(open_price, high, low, close)
            new_columns_dict['MEDPRICE'] = TechnicalIndicatorsTALib.calculate_medprice(high, low)
            new_columns_dict['TYPPRICE'] = TechnicalIndicatorsTALib.calculate_typprice(high, low, close)
            new_columns_dict['WCLPRICE'] = TechnicalIndicatorsTALib.calculate_wclprice(high, low, close)
        
        # ========== 数学变换�?(95-100) ==========
        if is_pandas:
            new_columns_dict['MAX_20'] = TechnicalIndicatorsTALib.calculate_max(close, 20)
            new_columns_dict['MAX_50'] = TechnicalIndicatorsTALib.calculate_max(close, 50)
            new_columns_dict['MIN_20'] = TechnicalIndicatorsTALib.calculate_min(close, 20)
            new_columns_dict['MIN_50'] = TechnicalIndicatorsTALib.calculate_min(close, 50)
            new_columns_dict['SUM_20'] = TechnicalIndicatorsTALib.calculate_sum(close, 20)
            new_columns_dict['SUM_50'] = TechnicalIndicatorsTALib.calculate_sum(close, 50)
            # 一次性合并所有基础指标列（使用pd.concat消除碎片化警告）
            new_df = pd.DataFrame(new_columns_dict, index=result.index)
            result = pd.concat([result, new_df], axis=1)
        
        # ========== 额外衍生指标 (101-110+) ==========
        if is_pandas:
            # 收集衍生指标（这些指标依赖于之前计算的列�?            derived_columns_dict = {}
            derived_columns_dict['BIAS_5'] = (close - result['SMA_5']) / result['SMA_5'] * 100
            derived_columns_dict['BIAS_10'] = (close - result['SMA_10']) / result['SMA_10'] * 100
            derived_columns_dict['BIAS_20'] = (close - result['SMA_20']) / result['SMA_20'] * 100
            derived_columns_dict['BIAS_60'] = (close - result['SMA_60']) / result['SMA_60'] * 100
            derived_columns_dict['Price_Change_1d'] = close.pct_change(1) * 100
            derived_columns_dict['Price_Change_5d'] = close.pct_change(5) * 100
            derived_columns_dict['Price_Change_10d'] = close.pct_change(10) * 100
            derived_columns_dict['Price_Change_20d'] = close.pct_change(20) * 100
            derived_columns_dict['Volatility_5'] = close.pct_change().rolling(5).std() * np.sqrt(252) * 100
            derived_columns_dict['Volatility_10'] = close.pct_change().rolling(10).std() * np.sqrt(252) * 100
            derived_columns_dict['Volatility_20'] = close.pct_change().rolling(20).std() * np.sqrt(252) * 100
            derived_columns_dict['Relative_Strength_MA20'] = close / result['SMA_20']
            derived_columns_dict['Relative_Strength_MA50'] = close / result['SMA_50']
            derived_columns_dict['Volume_Price_Ratio'] = volume / close
            derived_columns_dict['Volume_Change_1d'] = volume.pct_change(1) * 100
            derived_columns_dict['MA_Cross_5_20'] = (result['SMA_5'] > result['SMA_20']).astype(int)
            derived_columns_dict['MA_Cross_10_20'] = (result['SMA_10'] > result['SMA_20']).astype(int)
            derived_columns_dict['EMA_Cross_12_26'] = (result['EMA_12'] > result['EMA_26']).astype(int)
            derived_columns_dict['MACD_Cross'] = (result['MACD_Line'] > result['MACD_Signal']).astype(int)
            derived_columns_dict['RSI_Overbought_70'] = (result['RSI_14'] > 70).astype(int)
            derived_columns_dict['RSI_Oversold_30'] = (result['RSI_14'] < 30).astype(int)
            derived_columns_dict['BB_Position'] = (close - result['BB_Lower']) / (result['BB_Upper'] - result['BB_Lower'])
            derived_columns_dict['BB_Squeeze'] = (result['BB_Width'] < result['BB_Width'].rolling(20).mean() * 0.5).astype(int)
            derived_columns_dict['Price_Position_20'] = (close - result['MIN_20']) / (result['MAX_20'] - result['MIN_20'])
            derived_columns_dict['Price_Position_50'] = (close - result['MIN_50']) / (result['MAX_50'] - result['MIN_50'])
            derived_columns_dict['STOCH_J'] = 3 * result['STOCH_K'] - 2 * result['STOCH_D']
            derived_columns_dict['Volume_Ratio_5'] = volume / result['VOL_SMA_5']
            derived_columns_dict['Volume_Ratio_20'] = volume / result['VOL_SMA_20']
            # 一次性合并衍生指标列
            derived_df = pd.DataFrame(derived_columns_dict, index=result.index)
            result = pd.concat([result, derived_df], axis=1)
        else:
            # Polars: 批量添加衍生指标（使用pl.col()引用DataFrame中的列）
            result = result.with_columns([
                # 乖离�?                ((pl.col('收盘�?) - pl.col('SMA_5')) / pl.col('SMA_5') * 100).alias('BIAS_5'),
                ((pl.col('收盘�?) - pl.col('SMA_10')) / pl.col('SMA_10') * 100).alias('BIAS_10'),
                ((pl.col('收盘�?) - pl.col('SMA_20')) / pl.col('SMA_20') * 100).alias('BIAS_20'),
                ((pl.col('收盘�?) - pl.col('SMA_60')) / pl.col('SMA_60') * 100).alias('BIAS_60'),
                # 价格变化
                (pl.col('收盘�?).pct_change(1) * 100).alias('Price_Change_1d'),
                (pl.col('收盘�?).pct_change(5) * 100).alias('Price_Change_5d'),
                (pl.col('收盘�?).pct_change(10) * 100).alias('Price_Change_10d'),
                (pl.col('收盘�?).pct_change(20) * 100).alias('Price_Change_20d'),
                # 波动�?                (pl.col('收盘�?).pct_change().rolling_std(5) * np.sqrt(252) * 100).alias('Volatility_5'),
                (pl.col('收盘�?).pct_change().rolling_std(10) * np.sqrt(252) * 100).alias('Volatility_10'),
                (pl.col('收盘�?).pct_change().rolling_std(20) * np.sqrt(252) * 100).alias('Volatility_20'),
                # 相对强度
                (pl.col('收盘�?) / pl.col('SMA_20')).alias('Relative_Strength_MA20'),
                (pl.col('收盘�?) / pl.col('SMA_50')).alias('Relative_Strength_MA50'),
                # 量价�?                (pl.col('总量') / pl.col('收盘�?)).alias('Volume_Price_Ratio'),
                (pl.col('总量').pct_change(1) * 100).alias('Volume_Change_1d'),
                # MA交叉信号
                ((pl.col('SMA_5') > pl.col('SMA_20')).cast(pl.Int32)).alias('MA_Cross_5_20'),
                ((pl.col('SMA_10') > pl.col('SMA_20')).cast(pl.Int32)).alias('MA_Cross_10_20'),
                ((pl.col('EMA_12') > pl.col('EMA_26')).cast(pl.Int32)).alias('EMA_Cross_12_26'),
                # MACD信号
                ((pl.col('MACD_Line') > pl.col('MACD_Signal')).cast(pl.Int32)).alias('MACD_Cross'),
                # RSI超买超卖
                ((pl.col('RSI_14') > 70).cast(pl.Int32)).alias('RSI_Overbought_70'),
                ((pl.col('RSI_14') < 30).cast(pl.Int32)).alias('RSI_Oversold_30'),
                # 布林带位置（bb_lower等是Series，需要先添加到DataFrame或使用其他方式）
                # 注意：bb_lower等变量在Polars分支中需要重新获�?                # 价格位置
                ((pl.col('收盘�?) - pl.col('MIN_20')) / (pl.col('MAX_20') - pl.col('MIN_20'))).alias('Price_Position_20'),
                ((pl.col('收盘�?) - pl.col('MIN_50')) / (pl.col('MAX_50') - pl.col('MIN_50'))).alias('Price_Position_50'),
                # KDJ J�?                ((3 * pl.col('STOCH_K') - 2 * pl.col('STOCH_D'))).alias('STOCH_J'),
                # 成交量比�?                (pl.col('总量') / pl.col('VOL_SMA_5')).alias('Volume_Ratio_5'),
                (pl.col('总量') / pl.col('VOL_SMA_20')).alias('Volume_Ratio_20'),
                # 布林带位置和布林带挤压（合并到同一次with_columns调用�?                ((pl.col('收盘�?) - pl.col('BB_Lower')) / (pl.col('BB_Upper') - pl.col('BB_Lower'))).alias('BB_Position'),
                ((pl.col('BB_Width') < pl.col('BB_Width').rolling_mean(20) * 0.5).cast(pl.Int32)).alias('BB_Squeeze')
            ])
        
        # Polars优化：最后统一rechunk，优化内存布局，并清理临时变量
        if not is_pandas:
            result = result.rechunk()
            # 强制垃圾回收，释放中间计算产生的内存
            gc.collect()
        
        return result
