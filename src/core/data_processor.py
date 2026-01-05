"""
数据处理模块
功能：整合数据读取和指标计算

"""

import polars as pl
import pandas as pd
import duckdb
import time
import os
import sys
import io
from typing import Union, List, Dict, Any, Optional

# 导入自定义模块
from .utils import PerformanceMonitor, Logger, DataValidator, print_dataframe_info
from .indicators import (
    TrendIndicators, MomentumIndicators, VolatilityIndicators,
    VolumeIndicators, OscillatorIndicators, PriceIndicators,
    ExtraIndicators
)


class DataProcessor:
    """数据处理器类"""

    # 定义核心必要列（用于指标计算）- 从243列减少到12核心列
    # 注意：根据实际数据库列名调整
    ESSENTIAL_COLUMNS = [
        '日期', '代码', '名称',      # 基础信息
        '现价', '今开', '最高', '最低',  # OHLC价格（关键）
        '昨收',                      # 用于计算涨跌
        '总量', '总金额',            # 成交量和成交额
        '涨幅%', '振幅%',            # 基础指标
        '换手%', '量比'              # 辅助指标
    ]

    # 列名映射：标准名->数据库列名
    COLUMN_MAPPING = {
        '收盘价': '现价',   # 收盘价在数据库中叫"现价"
        '开盘价': '今开',   # 开盘价在数据库中叫"今开"
    }

    def __init__(self, db_path: str, use_essential_columns: bool = True):
        """
        初始化数据处理器

        参数:
        db_path: DuckDB 数据库路径
        use_essential_columns: 是否只读取核心列（默认True，性能优化）
        """
        self.db_path = db_path
        self.conn = None
        self.use_essential_columns = use_essential_columns

        # 检查数据库是否存在
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    def connect(self):
        """连接数据库"""
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path, read_only=True)
            Logger.success(f"已连接到数据库: {self.db_path}")

    def disconnect(self):
        """断开数据库连接"""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            Logger.info("已断开数据库连接")

    def read_data_polars(self, query: Optional[str] = None, limit: Optional[int] = None) -> pl.DataFrame:
        """
        使用 Polars 读取数据

        参数:
        query: SQL 查询语句（可选，默认读取全部数据）
        limit: 限制返回的行数（可选）

        返回:
        pl.DataFrame: Polars DataFrame
        """
        self.connect()

        if query is None:
            # 性能优化：只读取必要的列（从243列→15列，减少94%数据量）
            if self.use_essential_columns:
                columns_str = ", ".join([f'"{col}"' for col in self.ESSENTIAL_COLUMNS])
                query = f"SELECT {columns_str} FROM stock_data"
                Logger.info(f"[性能优化] 只读取 {len(self.ESSENTIAL_COLUMNS)} 个核心列")
            else:
                query = "SELECT * FROM stock_data"
                Logger.warning("[性能警告] 正在读取全部243列，这会降低性能")

            if limit:
                query += f" LIMIT {limit}"

        Logger.info(f"执行查询: {query[:100]}...")

        with PerformanceMonitor("Polars 读取数据"):
            # 使用 arrow 作为中间格式（更快）
            result = self.conn.execute(query).fetch_arrow_table()
            df = pl.from_arrow(result)

        Logger.success(f"读取完成: {len(df)} 行, {len(df.columns)} 列")

        # 添加列名别名（为了兼容指标计算代码）
        df = self._add_column_aliases(df)

        return df

    def read_data_pandas(self, query: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """
        使用 Pandas 读取数据

        参数:
        query: SQL 查询语句（可选，默认读取全部数据）
        limit: 限制返回的行数（可选）

        返回:
        pd.DataFrame: Pandas DataFrame
        """
        self.connect()

        if query is None:
            # 性能优化：只读取必要的列
            if self.use_essential_columns:
                columns_str = ", ".join([f'"{col}"' for col in self.ESSENTIAL_COLUMNS])
                query = f"SELECT {columns_str} FROM stock_data"
                Logger.info(f"[性能优化] 只读取 {len(self.ESSENTIAL_COLUMNS)} 个核心列")
            else:
                query = "SELECT * FROM stock_data"
                Logger.warning("[性能警告] 正在读取全部243列，这会降低性能")

            if limit:
                query += f" LIMIT {limit}"

        Logger.info(f"执行查询: {query[:100]}...")

        with PerformanceMonitor("Pandas 读取数据"):
            df = self.conn.execute(query).fetchdf()

        Logger.success(f"读取完成: {len(df)} 行, {len(df.columns)} 列")

        return df

    def get_stock_codes(self, limit: Optional[int] = None) -> List[str]:
        """
        获取所有股票代码

        参数:
        limit: 限制返回的股票数量（可选）

        返回:
        list: 股票代码列表
        """
        self.connect()

        query = "SELECT DISTINCT 代码 FROM stock_data ORDER BY 代码"
        if limit:
            query += f" LIMIT {limit}"

        result = self.conn.execute(query).fetchall()
        codes = [row[0] for row in result]

        Logger.info(f"获取到 {len(codes)} 个股票代码")

        return codes

    def get_stock_list(self, limit: Optional[int] = None) -> List[tuple]:
        """
        获取股票代码和名称列表

        参数:
        limit: 限制返回的股票数量（可选）

        返回:
        list: [(代码, 名称), ...] 列表
        """
        self.connect()

        query = """
        SELECT DISTINCT 代码, 名称
        FROM stock_data
        ORDER BY 代码
        """
        if limit:
            query += f" LIMIT {limit}"

        result = self.conn.execute(query).fetchall()

        Logger.info(f"获取到 {len(result)} 个股票")

        return result

    def get_stock_data_polars(self, stock_code: str) -> pl.DataFrame:
        """
        获取单个股票的数据（Polars）

        参数:
        stock_code: 股票代码

        返回:
        pl.DataFrame: 该股票的数据
        """
        # 性能优化：只读取必要的列
        if self.use_essential_columns:
            columns_str = ", ".join([f'"{col}"' for col in self.ESSENTIAL_COLUMNS])
            query = f"SELECT {columns_str} FROM stock_data WHERE \"代码\" = '{stock_code}' ORDER BY \"日期\""
        else:
            query = f"SELECT * FROM stock_data WHERE \"代码\" = '{stock_code}' ORDER BY \"日期\""
        return self.read_data_polars(query)

    def get_stock_data_pandas(self, stock_code: str) -> pd.DataFrame:
        """
        获取单个股票的数据（Pandas）

        参数:
        stock_code: 股票代码

        返回:
        pd.DataFrame: 该股票的数据
        """
        # 性能优化：只读取必要的列
        if self.use_essential_columns:
            columns_str = ", ".join([f'"{col}"' for col in self.ESSENTIAL_COLUMNS])
            query = f"SELECT {columns_str} FROM stock_data WHERE \"代码\" = '{stock_code}' ORDER BY \"日期\""
        else:
            query = f"SELECT * FROM stock_data WHERE \"代码\" = '{stock_code}' ORDER BY \"日期\""
        return self.read_data_pandas(query)

    def read_csv_direct(self, csv_path: Optional[str] = None, limit: Optional[int] = None) -> pl.DataFrame:
        """
        直接从CSV读取数据（跳过DuckDB，性能提升最大）

        参数:
        csv_path: CSV文件路径（可选，默认使用项目data目录中的文件）
        limit: 限制返回的行数（可选）

        返回:
        pl.DataFrame: Polars DataFrame

        性能优势：
        - 省去CSV→DuckDB→Arrow→Polars的转换开销
        - 预期比DuckDB读取快50%以上
        """
        # 默认CSV路径
        if csv_path is None:
            data_dir = os.path.dirname(self.db_path)
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and '通达信' in f]
            if not csv_files:
                raise FileNotFoundError(f"在 {data_dir} 目录下未找到CSV文件")
            csv_path = os.path.join(data_dir, sorted(csv_files)[-1])

        Logger.info(f"[性能优化] 直接从CSV读取: {os.path.basename(csv_path)}")

        with PerformanceMonitor("直接读取 CSV"):
            # 选择要读取的列
            columns_to_read = self.ESSENTIAL_COLUMNS if self.use_essential_columns else None

            if columns_to_read:
                Logger.info(f"[性能优化] 只读取 {len(columns_to_read)} 个核心列")

            # 使用Polars高性能读取CSV
            df = pl.read_csv(
                csv_path,
                columns=columns_to_read,   # 只读必要列
                n_rows=limit,              # 限制行数
                low_memory=False,          # 使用更多内存换速度
                rechunk=True,              # 优化内存布局
                encoding='utf8',           # 明确编码
                try_parse_dates=True       # 自动解析日期
            )

        Logger.success(f"读取完成: {len(df)} 行, {len(df.columns)} 列")

        # 添加列名别名
        df = self._add_column_aliases(df)

        return df

    def _add_column_aliases(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        添加列名别名，用于兼容指标计算代码

        参数:
        df: 原始DataFrame

        返回:
        pl.DataFrame: 添加了别名列的DataFrame
        """
        # 如果"现价"存在但"收盘价"不存在，创建别名
        if '现价' in df.columns and '收盘价' not in df.columns:
            df = df.with_columns(pl.col('现价').alias('收盘价'))

        # 如果"今开"存在但"开盘价"不存在，创建别名
        if '今开' in df.columns and '开盘价' not in df.columns:
            df = df.with_columns(pl.col('今开').alias('开盘价'))

        return df


class IndicatorCalculator:
    """指标计算器类"""

    @staticmethod
    def calculate_all_indicators_polars(df: pl.DataFrame) -> pl.DataFrame:
        """
        使用 Polars 计算所有技术指标

        参数:
        df: Polars DataFrame

        返回:
        pl.DataFrame: 添加了所有指标的 DataFrame
        """
        Logger.section("开始计算技术指标 (Polars)")

        with PerformanceMonitor("计算所有指标"):
            # 1. 趋势指标
            Logger.info("计算趋势指标...")
            df = TrendIndicators.sma(df, '收盘价', 5)
            df = TrendIndicators.sma(df, '收盘价', 10)
            df = TrendIndicators.sma(df, '收盘价', 20)
            df = TrendIndicators.sma(df, '收盘价', 50)
            df = TrendIndicators.sma(df, '收盘价', 100)
            df = TrendIndicators.sma(df, '收盘价', 200)

            df = TrendIndicators.ema(df, '收盘价', 5)
            df = TrendIndicators.ema(df, '收盘价', 10)
            df = TrendIndicators.ema(df, '收盘价', 20)
            df = TrendIndicators.ema(df, '收盘价', 50)
            df = TrendIndicators.ema(df, '收盘价', 100)
            df = TrendIndicators.ema(df, '收盘价', 200)

            # 2. 动量指标
            Logger.info("计算动量指标...")
            df = MomentumIndicators.rsi(df, '收盘价', 7)
            df = MomentumIndicators.rsi(df, '收盘价', 14)
            df = MomentumIndicators.rsi(df, '收盘价', 21)
            df = MomentumIndicators.rsi(df, '收盘价', 30)

            df = MomentumIndicators.momentum(df, '收盘价', 5)
            df = MomentumIndicators.momentum(df, '收盘价', 10)
            df = MomentumIndicators.momentum(df, '收盘价', 20)

            df = MomentumIndicators.roc(df, '收盘价', 5)
            df = MomentumIndicators.roc(df, '收盘价', 10)
            df = MomentumIndicators.roc(df, '收盘价', 20)

            # 3. 波动率指标
            Logger.info("计算波动率指标...")
            df = VolatilityIndicators.bollinger_bands(df, '收盘价', 20, 2.0)

            # 检查是否有最高、最低价列
            if '最高' in df.columns and '最低' in df.columns:
                df = VolatilityIndicators.atr(df, '最高', '最低', '收盘价', 14)

            df = VolatilityIndicators.volatility(df, '收盘价', 5)
            df = VolatilityIndicators.volatility(df, '收盘价', 10)
            df = VolatilityIndicators.volatility(df, '收盘价', 20)

            # 4. 成交量指标
            Logger.info("计算成交量指标...")
            if '总量' in df.columns:
                df = VolumeIndicators.obv(df, '收盘价', '总量')
                df = VolumeIndicators.volume_sma(df, '总量', 5)
                df = VolumeIndicators.volume_sma(df, '总量', 10)
                df = VolumeIndicators.volume_sma(df, '总量', 20)

                # VWAP（如果有最高、最低价）
                if '最高' in df.columns and '最低' in df.columns:
                    df = VolumeIndicators.vwap(df, '最高', '最低', '收盘价', '总量')

            # 5. 震荡指标
            Logger.info("计算震荡指标...")
            df = OscillatorIndicators.macd(df, '收盘价', 12, 26, 9)

            if '最高' in df.columns and '最低' in df.columns:
                df = OscillatorIndicators.stochastic(df, '最高', '最低', '收盘价', 14, 3)
                df = OscillatorIndicators.cci(df, '最高', '最低', '收盘价', 20)

            # 6. 价格指标
            Logger.info("计算价格指标...")
            df = PriceIndicators.price_change(df, '收盘价', 1)
            df = PriceIndicators.price_change(df, '收盘价', 5)
            df = PriceIndicators.price_change(df, '收盘价', 10)

            df = PriceIndicators.price_change_pct(df, '收盘价', 1)
            df = PriceIndicators.price_change_pct(df, '收盘价', 5)
            df = PriceIndicators.price_change_pct(df, '收盘价', 10)

            # 7. 额外技术指标(新增17个)
            Logger.info("计算额外技术指标...")

            # ADX (需要高低收)
            if '最高' in df.columns and '最低' in df.columns:
                df = ExtraIndicators.adx(df, '最高', '最低', '收盘价', 14)

            # Envelopes (包络线)
            df = ExtraIndicators.envelopes(df, '收盘价', 20, 2.5)

            # Alligator (鳄鱼指标)
            df = ExtraIndicators.alligator(df, '收盘价')

            # Awesome Oscillator (需要高低价)
            if '最高' in df.columns and '最低' in df.columns:
                df = ExtraIndicators.awesome_oscillator(df, '最高', '最低')

            # Fractals (分形,需要高低价)
            if '最高' in df.columns and '最低' in df.columns:
                df = ExtraIndicators.fractals(df, '最高', '最低', 5)

            # Gator Oscillator (鳄鱼震荡)
            # 注意：这会重新计算Alligator,所以可能会有重复列
            # df = ExtraIndicators.gator_oscillator(df, '收盘价')

            # Schaff Trend Cycle
            df = ExtraIndicators.schaff_trend_cycle(df, '收盘价', 23, 50, 10)

            # Chaikin Oscillator (需要高低收和成交量)
            if '最高' in df.columns and '最低' in df.columns and '总量' in df.columns:
                df = ExtraIndicators.chaikin_oscillator(df, '最高', '最低', '收盘价', '总量')

            # Know Sure Thing (KST)
            df = ExtraIndicators.kst(df, '收盘价')

            # Bollinger %B (需要先有BB指标)
            df = ExtraIndicators.bollinger_pct_b(df, '收盘价', 20, 2.0)

            # ATR Bands (需要高低收)
            if '最高' in df.columns and '最低' in df.columns:
                df = ExtraIndicators.atr_bands(df, '最高', '最低', '收盘价', 14, 2.0)

            # Chandelier Exit (需要高低收)
            if '最高' in df.columns and '最低' in df.columns:
                df = ExtraIndicators.chandelier_exit(df, '最高', '最低', '收盘价', 22, 3.0)

            # KAMA (考夫曼自适应移动平均)
            df = ExtraIndicators.kama(df, '收盘价', 10, 2, 30)

            # DEMA (双重指数移动平均)
            df = ExtraIndicators.dema(df, '收盘价', 20)

            # TEMA (三重指数移动平均)
            df = ExtraIndicators.tema(df, '收盘价', 20)

            # ZigZag (之字转向,需要高低价)
            if '最高' in df.columns and '最低' in df.columns:
                df = ExtraIndicators.zigzag(df, '最高', '最低', 5.0)

        Logger.success(f"所有指标计算完成！共 {len(df.columns)} 列")

        return df

    @staticmethod
    def calculate_all_indicators_pandas(df: pd.DataFrame) -> pd.DataFrame:
        """
        使用 Pandas 计算所有技术指标

        参数:
        df: Pandas DataFrame

        返回:
        pd.DataFrame: 添加了所有指标的 DataFrame
        """
        Logger.section("开始计算技术指标 (Pandas)")

        with PerformanceMonitor("计算所有指标"):
            # 转换为 Polars 计算（因为我们的指标实现是基于 Polars 的）
            df_polars = pl.from_pandas(df)

            # 计算指标
            df_polars = IndicatorCalculator.calculate_all_indicators_polars(df_polars)

            # 转回 Pandas
            df = df_polars.to_pandas()

        Logger.success(f"所有指标计算完成！共 {len(df.columns)} 列")

        return df


class ResultSaver:
    """结果保存器类"""

    @staticmethod
    def save_to_csv(df: Union[pl.DataFrame, pd.DataFrame], file_path: str):
        """
        保存到 CSV 文件

        参数:
        df: DataFrame
        file_path: 文件路径
        """
        Logger.info(f"保存结果到: {file_path}")

        with PerformanceMonitor("保存到 CSV"):
            if isinstance(df, pl.DataFrame):
                df.write_csv(file_path)
            else:  # pandas
                df.to_csv(file_path, index=False)

        # 检查文件大小
        size_mb = os.path.getsize(file_path) / 1024 / 1024
        Logger.success(f"保存完成！文件大小: {size_mb:.2f} MB")

    @staticmethod
    def save_to_parquet(df: Union[pl.DataFrame, pd.DataFrame], file_path: str, fast_mode: bool = True):
        """
        保存到 Parquet 文件（更高效）

        参数:
        df: DataFrame
        file_path: 文件路径
        fast_mode: 是否使用快速模式（默认True，性能优化）
        """
        Logger.info(f"保存结果到: {file_path}")

        with PerformanceMonitor("保存到 Parquet"):
            if isinstance(df, pl.DataFrame):
                if fast_mode:
                    # 性能优化：使用zstd压缩，level=1最快，row_group_size减小
                    df.write_parquet(
                        file_path,
                        compression='zstd',      # zstd比snappy更快
                        compression_level=1,     # 最快压缩级别（默认3）
                        statistics=False,        # 跳过统计信息计算
                        row_group_size=10000     # 减小行组，加快写入
                    )
                    Logger.info("[性能优化] 使用快速Parquet保存模式 (zstd-level1)")
                else:
                    df.write_parquet(file_path)
            else:  # pandas
                if fast_mode:
                    df.to_parquet(
                        file_path,
                        index=False,
                        engine='pyarrow',
                        compression='zstd',
                        compression_level=1
                    )
                    Logger.info("[性能优化] 使用快速Parquet保存模式 (zstd-level1)")
                else:
                    df.to_parquet(file_path, index=False)

        # 检查文件大小
        size_mb = os.path.getsize(file_path) / 1024 / 1024
        Logger.success(f"保存完成！文件大小: {size_mb:.2f} MB")

    @staticmethod
    def save_to_duckdb(df: Union[pl.DataFrame, pd.DataFrame], db_path: str, table_name: str):
        """
        保存到 DuckDB 数据库

        参数:
        df: DataFrame
        db_path: 数据库路径
        table_name: 表名
        """
        Logger.info(f"保存结果到 DuckDB: {db_path} (表: {table_name})")

        with PerformanceMonitor("保存到 DuckDB"):
            conn = duckdb.connect(db_path)

            # 删除旧表（如果存在）
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")

            # 创建新表
            if isinstance(df, pl.DataFrame):
                conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            else:  # pandas
                conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

            conn.close()

        Logger.success(f"保存完成！表名: {table_name}")


# 测试代码
if __name__ == "__main__":
    Logger.section("数据处理模块测试")

    # 配置路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(script_dir, "data")

    # 查找数据库文件
    db_files = [f for f in os.listdir(data_dir) if f.endswith('.duckdb')]

    if not db_files:
        Logger.error("未找到数据库文件！请先运行 import_data.py")
        sys.exit(1)

    # 使用最新的数据库文件
    db_file = sorted(db_files)[-1]
    db_path = os.path.join(data_dir, db_file)

    Logger.info(f"使用数据库: {db_file}")

    try:
        # 创建数据处理器
        processor = DataProcessor(db_path)

        # 测试读取数据（只读取 1000 行用于测试）
        Logger.info("测试读取数据 (Polars)...")
        df_polars = processor.read_data_polars(limit=1000)
        print_dataframe_info(df_polars, "测试数据")

        # 测试获取股票代码
        Logger.info("获取股票代码...")
        codes = processor.get_stock_codes(limit=5)
        Logger.info(f"前5个股票代码: {codes}")

        # 测试单个股票数据读取
        if codes:
            test_code = codes[0]
            Logger.info(f"读取股票 {test_code} 的数据...")
            stock_df = processor.get_stock_data_polars(test_code)
            Logger.success(f"读取到 {len(stock_df)} 条数据")

            # 测试指标计算
            Logger.info("测试指标计算...")
            stock_df_with_indicators = IndicatorCalculator.calculate_all_indicators_polars(stock_df)

            Logger.info(f"计算前列数: {len(stock_df.columns)}")
            Logger.info(f"计算后列数: {len(stock_df_with_indicators.columns)}")
            Logger.info(f"新增指标数: {len(stock_df_with_indicators.columns) - len(stock_df.columns)}")

            # 显示部分结果
            Logger.info("\n结果示例（最后5行，前10列）:")
            print(stock_df_with_indicators.tail(5).select(stock_df_with_indicators.columns[:10]))

        # 断开连接
        processor.disconnect()

        Logger.section("所有测试完成！")

    except Exception as e:
        Logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
