"""
工具函数模块
功能：提供通用的工具函数和类

"""

import polars as pl
import pandas as pd
import time
import os
import sys
import io
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
import psutil


# 设置UTF-8编码（仅在非测试环境下）
try:
    # 检查是否在 pytest 环境中运行
    if 'pytest' not in sys.modules and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except Exception:
    pass  # 如果设置失败，使用默认编码


class DataValidator:
    """数据验证工具类"""

    @staticmethod
    def check_null_values(df: Union[pl.DataFrame, pd.DataFrame], column: str) -> Dict[str, Any]:
        """
        检查指定列的空值情况

        参数:
        df: Polars 或 Pandas DataFrame
        column: 列名

        返回:
        dict: 包含空值统计信息
        """
        if isinstance(df, pl.DataFrame):
            total_rows = len(df)
            null_count = df[column].null_count()
        else:  # pandas
            total_rows = len(df)
            null_count = df[column].isna().sum()

        null_percentage = (null_count / total_rows) * 100 if total_rows > 0 else 0

        return {
            'column': column,
            'total_rows': total_rows,
            'null_count': null_count,
            'null_percentage': null_percentage,
            'has_null': null_count > 0
        }

    @staticmethod
    def check_all_nulls(df: Union[pl.DataFrame, pd.DataFrame]) -> pd.DataFrame:
        """
        检查所有列的空值情况

        参数:
        df: Polars 或 Pandas DataFrame

        返回:
        pd.DataFrame: 空值统计表
        """
        results = []

        if isinstance(df, pl.DataFrame):
            for col in df.columns:
                total_rows = len(df)
                null_count = df[col].null_count()
                null_percentage = (null_count / total_rows) * 100 if total_rows > 0 else 0

                results.append({
                    'column': col,
                    'null_count': null_count,
                    'null_percentage': f"{null_percentage:.2f}%",
                    'non_null_count': total_rows - null_count
                })
        else:  # pandas
            for col in df.columns:
                total_rows = len(df)
                null_count = df[col].isna().sum()
                null_percentage = (null_count / total_rows) * 100 if total_rows > 0 else 0

                results.append({
                    'column': col,
                    'null_count': null_count,
                    'null_percentage': f"{null_percentage:.2f}%",
                    'non_null_count': total_rows - null_count
                })

        return pd.DataFrame(results)

    @staticmethod
    def validate_dataframe(df: Union[pl.DataFrame, pd.DataFrame]) -> Dict[str, Any]:
        """
        验证 DataFrame 的基本信息

        参数:
        df: Polars 或 Pandas DataFrame

        返回:
        dict: 包含验证信息
        """
        df_type = "Polars" if isinstance(df, pl.DataFrame) else "Pandas"

        if isinstance(df, pl.DataFrame):
            info = {
                'type': df_type,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns,
                'dtypes': {col: str(df[col].dtype) for col in df.columns},
                'memory_usage_mb': df.estimated_size() / 1024 / 1024
            }
        else:  # pandas
            info = {
                'type': df_type,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'dtypes': {col: str(df[col].dtype) for col in df.columns},
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            }

        return info

    @staticmethod
    def compare_dataframes(df1: Union[pl.DataFrame, pd.DataFrame],
                          df2: Union[pl.DataFrame, pd.DataFrame],
                          tolerance: float = 1e-6) -> Dict[str, Any]:
        """
        比较两个 DataFrame 的差异

        参数:
        df1: 第一个 DataFrame
        df2: 第二个 DataFrame
        tolerance: 数值比较的容差

        返回:
        dict: 包含比较结果
        """
        # 转换为 Pandas 以便比较
        if isinstance(df1, pl.DataFrame):
            df1 = df1.to_pandas()
        if isinstance(df2, pl.DataFrame):
            df2 = df2.to_pandas()

        results = {
            'shape_match': df1.shape == df2.shape,
            'df1_shape': df1.shape,
            'df2_shape': df2.shape,
            'columns_match': set(df1.columns) == set(df2.columns),
            'df1_columns': df1.columns.tolist(),
            'df2_columns': df2.columns.tolist(),
            'differences': []
        }

        # 比较共同列的数值
        common_cols = set(df1.columns) & set(df2.columns)
        for col in common_cols:
            if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                # 数值列比较
                diff = (df1[col] - df2[col]).abs()
                max_diff = diff.max()
                mean_diff = diff.mean()

                if max_diff > tolerance:
                    results['differences'].append({
                        'column': col,
                        'max_diff': max_diff,
                        'mean_diff': mean_diff,
                        'diff_count': (diff > tolerance).sum()
                    })

        results['all_match'] = len(results['differences']) == 0 and results['shape_match'] and results['columns_match']

        return results


class DateUtils:
    """日期处理工具类"""

    @staticmethod
    def parse_date_column(df: Union[pl.DataFrame, pd.DataFrame],
                         column: str,
                         date_format: Optional[str] = None) -> Union[pl.DataFrame, pd.DataFrame]:
        """
        解析日期列

        参数:
        df: Polars 或 Pandas DataFrame
        column: 日期列名
        date_format: 日期格式（可选）

        返回:
        DataFrame: 处理后的 DataFrame
        """
        if isinstance(df, pl.DataFrame):
            if date_format:
                df = df.with_columns(
                    pl.col(column).str.strptime(pl.Date, date_format).alias(column)
                )
            else:
                df = df.with_columns(
                    pl.col(column).str.strptime(pl.Date, "%Y-%m-%d").alias(column)
                )
        else:  # pandas
            df[column] = pd.to_datetime(df[column], format=date_format)

        return df

    @staticmethod
    def get_date_range(df: Union[pl.DataFrame, pd.DataFrame],
                      date_column: str) -> Dict[str, Any]:
        """
        获取日期范围

        参数:
        df: Polars 或 Pandas DataFrame
        date_column: 日期列名

        返回:
        dict: 包含日期范围信息
        """
        if isinstance(df, pl.DataFrame):
            min_date = df[date_column].min()
            max_date = df[date_column].max()
            unique_dates = df[date_column].n_unique()
        else:  # pandas
            min_date = df[date_column].min()
            max_date = df[date_column].max()
            unique_dates = df[date_column].nunique()

        return {
            'min_date': str(min_date),
            'max_date': str(max_date),
            'unique_dates': unique_dates,
            'date_range_days': (max_date - min_date).days if hasattr(max_date - min_date, 'days') else None
        }

    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        格式化时间戳

        参数:
        timestamp: 时间戳
        format_str: 格式字符串

        返回:
        str: 格式化后的日期时间字符串
        """
        return datetime.fromtimestamp(timestamp).strftime(format_str)


class PerformanceMonitor:
    """性能监控工具类"""

    def __init__(self, task_name: str = "Task"):
        """
        初始化性能监控器

        参数:
        task_name: 任务名称
        """
        self.task_name = task_name
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process()

    def start(self):
        """开始监控"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        print(f"\n{'='*80}")
        print(f"[{self.task_name}] 开始执行...")
        print(f"{'='*80}")
        print(f"开始时间: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"初始内存: {self.start_memory:.2f} MB")

    def end(self):
        """结束监控"""
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        elapsed_time = self.end_time - self.start_time
        memory_used = self.end_memory - self.start_memory

        print(f"\n{'='*80}")
        print(f"[{self.task_name}] 执行完成！")
        print(f"{'='*80}")
        print(f"结束时间: {datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"执行时间: {elapsed_time:.2f} 秒")
        print(f"最终内存: {self.end_memory:.2f} MB")
        print(f"内存增量: {memory_used:+.2f} MB")
        print(f"{'='*80}\n")

        return {
            'task_name': self.task_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'elapsed_time': elapsed_time,
            'start_memory_mb': self.start_memory,
            'end_memory_mb': self.end_memory,
            'memory_used_mb': memory_used
        }

    def __enter__(self):
        """支持 with 语句"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句"""
        self.end()


class FileUtils:
    """文件操作工具类"""

    @staticmethod
    def ensure_dir(directory: str):
        """
        确保目录存在，如果不存在则创建

        参数:
        directory: 目录路径
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
            # 使用 Logger 避免编码问题
            if 'pytest' not in sys.modules:
                print(f"✓ 创建目录: {directory}")

    @staticmethod
    def get_file_size(file_path: str) -> Dict[str, Any]:
        """
        获取文件大小信息

        参数:
        file_path: 文件路径

        返回:
        dict: 文件大小信息
        """
        if not os.path.exists(file_path):
            return {'exists': False}

        size_bytes = os.path.getsize(file_path)
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        size_gb = size_mb / 1024

        return {
            'exists': True,
            'path': file_path,
            'size_bytes': size_bytes,
            'size_kb': f"{size_kb:.2f} KB",
            'size_mb': f"{size_mb:.2f} MB",
            'size_gb': f"{size_gb:.2f} GB",
            'readable_size': FileUtils.format_size(size_bytes)
        }

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        格式化文件大小

        参数:
        size_bytes: 字节数

        返回:
        str: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def list_files(directory: str, extension: Optional[str] = None) -> List[str]:
        """
        列出目录中的文件

        参数:
        directory: 目录路径
        extension: 文件扩展名（可选，如 '.csv'）

        返回:
        list: 文件路径列表
        """
        if not os.path.exists(directory):
            return []

        files = []
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                if extension is None or file.endswith(extension):
                    files.append(file_path)

        return sorted(files)


class Logger:
    """简单的日志工具类"""

    @staticmethod
    def info(message: str):
        """打印信息日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [INFO] {message}")

    @staticmethod
    def warning(message: str):
        """打印警告日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 在 pytest 环境下避免使用特殊字符
        symbol = "WARNING" if 'pytest' in sys.modules else "⚠️ "
        print(f"[{timestamp}] [WARNING] {symbol} {message}")

    @staticmethod
    def error(message: str):
        """打印错误日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 在 pytest 环境下避免使用特殊字符
        symbol = "ERROR" if 'pytest' in sys.modules else "❌"
        print(f"[{timestamp}] [ERROR] {symbol} {message}")

    @staticmethod
    def success(message: str):
        """打印成功日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 在 pytest 环境下避免使用特殊字符
        symbol = "OK" if 'pytest' in sys.modules else "✓"
        print(f"[{timestamp}] [SUCCESS] {symbol} {message}")

    @staticmethod
    def section(title: str, width: int = 80):
        """打印分节标题"""
        print("\n" + "=" * width)
        print(f"{title:^{width}}")
        print("=" * width + "\n")


# 便捷函数
def format_number(num: Union[int, float], decimals: int = 2) -> str:
    """
    格式化数字，添加千位分隔符

    参数:
    num: 数字
    decimals: 小数位数

    返回:
    str: 格式化后的数字字符串
    """
    if isinstance(num, int):
        return f"{num:,}"
    else:
        return f"{num:,.{decimals}f}"


def print_dataframe_info(df: Union[pl.DataFrame, pd.DataFrame], name: str = "DataFrame"):
    """
    打印 DataFrame 的基本信息

    参数:
    df: Polars 或 Pandas DataFrame
    name: DataFrame 名称
    """
    validator = DataValidator()
    info = validator.validate_dataframe(df)

    Logger.section(f"{name} 信息")
    print(f"类型: {info['type']}")
    print(f"行数: {format_number(info['rows'])}")
    print(f"列数: {format_number(info['columns'])}")
    print(f"内存占用: {info['memory_usage_mb']:.2f} MB")
    print(f"\n前 5 列:")
    for i, col in enumerate(info['column_names'][:5], 1):
        print(f"  {i}. {col} ({info['dtypes'][col]})")

    if len(info['column_names']) > 5:
        print(f"  ... 还有 {len(info['column_names']) - 5} 列")


def benchmark(func, *args, runs: int = 1, **kwargs) -> Dict[str, Any]:
    """
    对函数进行性能基准测试

    参数:
    func: 要测试的函数
    *args: 函数参数
    runs: 运行次数
    **kwargs: 函数关键字参数

    返回:
    dict: 性能测试结果
    """
    times = []

    for i in range(runs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        times.append(end - start)

    return {
        'function': func.__name__,
        'runs': runs,
        'times': times,
        'min_time': min(times),
        'max_time': max(times),
        'avg_time': sum(times) / len(times),
        'total_time': sum(times)
    }


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("工具函数模块测试")
    print("=" * 80)

    # 测试性能监控器
    with PerformanceMonitor("测试任务") as monitor:
        time.sleep(1)
        print("执行一些操作...")

    # 测试文件工具
    print("\n测试文件工具:")
    FileUtils.ensure_dir("test_output")

    # 测试日志工具
    print("\n测试日志工具:")
    Logger.info("这是一条信息日志")
    Logger.warning("这是一条警告日志")
    Logger.error("这是一条错误日志")
    Logger.success("这是一条成功日志")

    # 测试数字格式化
    print("\n测试数字格式化:")
    print(f"整数: {format_number(1234567)}")
    print(f"小数: {format_number(1234567.89, decimals=3)}")

    print("\n" + "=" * 80)
    print("✓ 所有测试完成！")
    print("=" * 80)
