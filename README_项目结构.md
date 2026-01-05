# 项目结构说明

**项目名称**: 股票技术指标计算系统
**当前版本**: v4.0
**指标总数**: 110个技术指标（基础48 + 早期15 + A-H批次47）
**最后更新**: 2026-01-01

---

## 📁 目录结构

```
project/
├── data/                        # 数据文件
│   ├── stock_data.duckdb       # DuckDB数据库
│   └── 通达信数据_*.csv         # 原始CSV数据
│
├── src/                         # 源代码
│   ├── core/                    # 核心模块
│   │   ├── __init__.py         # 模块导出
│   │   ├── data_processor.py   # 数据处理器
│   │   ├── indicators.py       # 技术指标计算（110个指标）
│   │   └── utils.py            # 工具函数
│   │
│   ├── config/                  # 配置文件
│   │   ├── __init__.py
│   │   └── column_mapping.py   # 列名映射配置
│   │
│   ├── scripts/                 # 独立工具脚本
│   │   ├── __init__.py
│   │   ├── import_data.py      # 数据导入（CSV → DuckDB）
│   │   ├── check_database.py   # 数据库检查工具
│   │   ├── analyze_dataset.py  # 数据集分析工具
│   │   └── visualize_performance.py  # 性能可视化
│   │
│   ├── batch_processor.py       # 批量处理器
│   ├── cli.py                   # 命令行接口
│   └── main.py                  # 主程序入口
│
├── tests/                       # 测试文件（重新组织）
│   ├── README.md                # 测试说明文档
│   │
│   ├── unit/                    # 单元测试
│   │   ├── test_indicators_simple.py    # 基础指标测试
│   │   ├── test_new_indicators.py       # 新指标测试
│   │   └── test_batch_processor.py      # 批处理器测试
│   │
│   ├── integration/             # 集成测试
│   │   ├── test_all_new_indicators.py   # 所有新指标集成测试
│   │   └── test_integration_new_indicators.py  # 指标集成测试
│   │
│   ├── indicators/              # 指标测试（按批次分类）
│   │   ├── test_statistical_indicators.py      # A批：统计指标（8个）
│   │   ├── test_moving_averages_extended.py    # B批：移动平均扩展（8个）
│   │   ├── test_oscillators_extended.py        # C批：震荡指标补充（6个）
│   │   ├── test_volatility_extended.py         # D批：波动率指标（5个）
│   │   ├── test_risk_indicators.py             # E批：风险管理（5个）
│   │   ├── test_pattern_indicators.py          # F批：形态识别（6个）
│   │   ├── test_advanced_trend_indicators.py   # G批：高级趋势（5个）
│   │   └── test_market_structure_indicators.py # H批：市场结构（4个）
│   │
│   ├── performance/             # 性能测试
│   │   ├── performance_test.py           # 基准性能测试
│   │   ├── performance_test_real.py      # 真实数据性能测试
│   │   ├── test_full_dataset.py          # 完整数据集测试（pytest）
│   │   └── full_dataset_test.py          # 完整数据集测试（交互式）
│   │
│   └── utils/                   # 工具测试
│       ├── count_all_indicators.py       # 指标数量统计
│       └── verify_indicators_accuracy.py # 指标准确性验证
│
├── docs/                        # 文档
│   ├── 指标实现总结_A至H批次.md    # 完整批次实现总结（主文档）
│   ├── 指标清单_全集.md            # 200+指标清单
│   ├── 指标扩展计划.md             # 未来扩展计划
│   ├── 指标准确性说明.md           # 指标准确性说明
│   ├── 指标参考手册.md             # 指标使用手册
│   ├── 性能测试报告.md             # 性能测试报告
│   ├── full_dataset_test_解读.md  # 完整数据集测试解读
│   └── full_dataset_test_修复记录.md  # 测试修复记录
│
├── output/                      # 统一输出目录
│   ├── test_results/           # 测试结果
│   └── indicators/             # 指标计算结果
│
├── .venv/                       # Python虚拟环境
├── .claude/                     # Claude Code配置
├── .idea/                       # IDE配置
├── .pytest_cache/               # Pytest缓存
│
├── README.md                    # 项目主zm文档
├── README_项目结构.md           # 本文件
└── requirements.txt             # Python依赖
```

---

## 📦 核心模块说明

### 1. core/ - 核心模块

#### data_processor.py (数据处理器)

```python
class DataProcessor:
    """数据读取和管理"""
    - 连接DuckDB数据库
    - 读取Polars/Pandas格式数据
    - 获取股票代码和列表
    - Arrow格式数据传输

class IndicatorCalculator:
    """指标计算器"""
    - 计算所有110种技术指标
    - 支持批量计算
    - 自动处理NaN值

class ResultSaver:
    """结果保存"""
    - 保存为CSV格式
    - 保存为Parquet格式（推荐）
    - 自动创建输出目录
```

#### indicators.py (技术指标计算 - 110个指标)

**基础指标类** (48个):
```python
class TrendIndicators:
    """趋势指标 (13个)"""
    # SMA, EMA, WMA, HMA, DEMA, TEMA, KAMA, VWMA等

class MomentumIndicators:
    """动量指标 (9个)"""
    # RSI, Stochastic RSI, Williams %R, CMO, ROC等

class VolatilityIndicators:
    """波动率指标 (15个)"""
    # Bollinger Bands, ATR, Keltner Channels, Donchian等

class VolumeIndicators:
    """成交量指标 (10个)"""
    # OBV, VWAP, MFI, CMF, ADL等

class OscillatorIndicators:
    """震荡指标 (12个)"""
    # MACD, Stochastic, CCI, Ultimate Osc, Awesome Osc等

class PriceIndicators:
    """价格指标 (3个)"""
    # Price Change, Price Rate of Change等
```

**早期新增指标** (15个):
```python
# 分散在基础类和扩展类中
- HMA, TRIX, CCI, VWMA (基础类扩展)
- Keltner Channels, Donchian Channel (通道类)
- CMF, FI (资金流类)
- VWAP_STD, Volume Oscillator (成交量类)
- Aroon, Ultimate Oscillator, Stochastic RSI, TSI, TR% (振荡/动量类)
```

**A-H批次新增指标** (47个):
```python
class StatisticalIndicators:
    """统计指标 (8个 - A批)"""
    # Z-Score, Percentile, Skewness, Kurtosis
    # Correlation, Rolling Correlation, Beta, Sharpe Ratio

class AdvancedTrendIndicators:
    """高级趋势指标 (13个 - B批+G批)"""
    # B批: SMMA, LWMA, TMA, ZLEMA, T3, ALMA, JMA, McGinley
    # G批: FRAMA, MAMA, Linear Regression, Time Series Forecast, Projection Bands

class AdvancedOscillatorIndicators:
    """高级震荡指标 (6个 - C批)"""
    # Fisher Transform, Inverse Fisher Transform
    # Coppock Curve, Klinger Oscillator, PPO, Squeeze Momentum

class AdvancedVolatilityIndicators:
    """高级波动率指标 (5个 - D批)"""
    # Historical Volatility, Chaikin Volatility
    # ATR Trailing Stop, Normalized ATR, Parkinson Volatility

class RiskIndicators:
    """风险管理指标 (5个 - E批)"""
    # Maximum Drawdown, Sortino Ratio, Calmar Ratio
    # Win Rate, Profit Factor

class PatternIndicators:
    """形态识别指标 (6个 - F批)"""
    # Doji, Hammer, Engulfing
    # Shooting Star, Morning Star, Three White Soldiers

class MarketStructureIndicators:
    """市场结构指标 (4个 - H批)"""
    # Market Structure, Order Blocks
    # Fair Value Gaps, Liquidity Levels
```

#### utils.py (工具函数)

```python
class Logger:
    """日志工具"""
    # 统一日志输出
    # 支持不同日志级别

class PerformanceMonitor:
    """性能监控"""
    # 计算执行时间
    # 监控内存使用
    # 生成性能报告

class DataValidator:
    """数据验证"""
    # 验证数据完整性
    # 检查数据质量

class FileUtils:
    """文件操作"""
    # 安全文件读写
    # 路径处理
```

### 2. config/ - 配置模块

#### column_mapping.py (列名映射)

```python
COLUMN_MAPPING = {
    'date': '日期',
    'open': '开盘价',
    'high': '最高价',
    'low': '最低价',
    'close': '收盘价',
    'volume': '成交量',
    'amount': '成交额'
}
```

用于兼容不同数据源的列名差异。

### 3. scripts/ - 工具脚本

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| import_data.py | CSV导入DuckDB | `python src/scripts/import_data.py` |
| check_database.py | 检查数据库 | `python src/scripts/check_database.py` |
| analyze_dataset.py | 分析数据集 | `python src/scripts/analyze_dataset.py` |
| visualize_performance.py | 性能可视化 | `python src/scripts/visualize_performance.py` |

### 4. tests/ - 测试模块

测试目录已按功能和批次重新组织，详见 [tests/README.md](../tests/README.md)

**测试统计**:
- 测试文件: 17个
- 测试用例: 200+
- 指标覆盖: 110个指标，100%覆盖
- 代码覆盖: 95%+

---

## 🚀 使用方法

### 1. 运行主程序

```bash
cd D:\shixun\project
python src/main.py
```

根据提示选择：
- **选项1**: 快速测试（1000行）
- **选项2**: 单只股票测试
- **选项3**: 完整处理（116万行）

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定类型测试
pytest tests/unit/ -v              # 单元测试
pytest tests/indicators/ -v        # 指标测试
pytest tests/performance/ -v       # 性能测试

# 运行特定批次测试
pytest tests/indicators/test_statistical_indicators.py -v  # A批
pytest tests/indicators/test_moving_averages_extended.py -v  # B批
pytest tests/indicators/test_risk_indicators.py -v  # E批

# 测试覆盖率
pytest tests/ --cov=src/core --cov-report=html
```

### 3. 使用工具脚本

```bash
# 导入数据
python src/scripts/import_data.py

# 检查数据库
python src/scripts/check_database.py

# 分析数据集
python src/scripts/analyze_dataset.py

# 可视化性能
python src/scripts/visualize_performance.py

# 统计指标数量
python tests/utils/count_all_indicators.py

# 验证指标准确性
python tests/utils/verify_indicators_accuracy.py
```

---

## 💻 代码示例

### 示例1: 基本使用

```python
# 导入核心模块
from core import DataProcessor, IndicatorCalculator, Logger
from core.indicators import TrendIndicators, MomentumIndicators

# 初始化数据处理器
processor = DataProcessor("data/stock_data.duckdb")
df = processor.read_data_polars(limit=1000)

# 计算基础指标
df = TrendIndicators.sma(df, '收盘价', 20)
df = MomentumIndicators.rsi(df, '收盘价', 14)

# 记录日志
Logger.info("处理完成")
```

### 示例2: 使用新增指标

```python
from core.indicators import (
    StatisticalIndicators,
    AdvancedTrendIndicators,
    RiskIndicators,
    PatternIndicators
)

# A批: 统计指标
df = StatisticalIndicators.zscore(df, 'close', 20)
df = StatisticalIndicators.sharpe_ratio(df, 'returns', 252)

# B批: 高级移动平均
df = AdvancedTrendIndicators.alma(df, 'close', 9, 0.85, 6.0)
df = AdvancedTrendIndicators.zlema(df, 'close', 20)

# E批: 风险管理
df = RiskIndicators.maximum_drawdown(df, 'value')
df = RiskIndicators.sortino_ratio(df, 'returns', 252)

# F批: 形态识别
df = PatternIndicators.hammer(df, 'open', 'high', 'low', 'close')
df = PatternIndicators.engulfing(df, 'open', 'close')
```

### 示例3: 批量计算所有指标

```python
from core import IndicatorCalculator

# 初始化计算器
calculator = IndicatorCalculator()

# 计算所有110个指标
df_with_indicators = calculator.calculate_all_indicators_polars(df)

# 查看添加的指标列
print(f"原始列数: {len(df.columns)}")
print(f"添加指标后: {len(df_with_indicators.columns)}")
print(f"新增指标: {len(df_with_indicators.columns) - len(df.columns)}")
```

---

## 📊 数据流程

```
CSV文件 (通达信数据)
    ↓
  import_data.py (数据导入)
    ↓
DuckDB数据库 (stock_data.duckdb)
    ↓
  DataProcessor.read_data_polars() (Arrow格式传输)
    ↓
Polars DataFrame (高性能数据帧)
    ↓
  IndicatorCalculator.calculate_all_indicators_polars()
    ↓
添加110种技术指标的DataFrame
    ↓
  ResultSaver.save_to_parquet() (压缩存储)
    ↓
Parquet结果文件 (output/indicators/)
```

---

## ⚡ 性能优化

### 1. 数据读取优化
- ✅ Arrow格式零拷贝传输（DuckDB ↔ Polars）
- ✅ 列式存储，按需读取
- ✅ 支持流式处理大数据集

### 2. 计算优化
- ✅ Polars向量化计算（比Pandas快10-100倍）
- ✅ 并行计算支持
- ✅ 延迟执行（Lazy Evaluation）

### 3. 内存优化
- ✅ 自动内存监控
- ✅ 增量计算
- ✅ 及时释放中间结果

### 4. 存储优化
- ✅ Parquet格式压缩（压缩率70-90%）
- ✅ 列式存储，查询高效
- ✅ 支持分区存储

**性能数据**:
- 116万行数据处理: ~10秒
- 内存占用: <2GB
- 结果文件: Parquet格式，压缩后~50MB

---

## 🔧 开发指南

### 添加新指标

**步骤1**: 在 `src/core/indicators.py` 中添加新方法

```python
class StatisticalIndicators:
    @staticmethod
    def my_new_indicator(df: pl.DataFrame, column: str, period: int) -> pl.DataFrame:
        """
        我的新指标

        Args:
            df: Polars DataFrame
            column: 价格列名
            period: 计算周期

        Returns:
            添加了新指标的DataFrame
        """
        # 实现指标计算（使用Polars向量化操作）
        result = df.with_columns([
            # 你的计算逻辑
            pl.col(column).rolling_mean(period).alias(f'MyIndicator_{period}')
        ])
        return result
```

**步骤2**: 在 `tests/` 中添加测试

```python
# tests/unit/test_my_indicator.py
import pytest
from core.indicators import StatisticalIndicators

def test_my_new_indicator():
    # 准备测试数据
    df = create_test_data(100)

    # 执行指标计算
    result = StatisticalIndicators.my_new_indicator(df, 'close', 14)

    # 断言
    assert 'MyIndicator_14' in result.columns
    assert not result['MyIndicator_14'].is_null().all()
```

**步骤3**: 运行测试

```bash
pytest tests/unit/test_my_indicator.py -v
```

### 添加新测试

在相应的测试目录中创建测试文件：
- `tests/unit/` - 单元测试
- `tests/integration/` - 集成测试
- `tests/indicators/` - 指标批次测试

### 代码规范

1. **类型注解**: 使用类型提示
2. **文档字符串**: 完整的docstring
3. **向量化**: 优先使用Polars向量化操作
4. **错误处理**: 处理NaN值和边界条件
5. **测试覆盖**: 每个新功能都要有测试

---

## 📚 文档说明

### 主要文档

| 文档 | 说明 | 位置 |
|------|------|------|
| README.md | 项目主文档 | 根目录 |
| README_项目结构.md | 项目结构说明（本文件） | 根目录 |
| 指标实现总结_A至H批次.md | A-H批次实现总结 | docs/ |
| 指标分类清单.md | 系统全部110个指标清单 | docs/ |
| 指标清单_全集.md | 200+可实现指标清单 | docs/ |
| 指标准确性说明.md | 指标准确性说明 | docs/ |
| 指标参考手册.md | 详细使用手册 | docs/ |
| 性能测试报告.md | 性能测试报告 | docs/ |
| tests/README.md | 测试说明文档 | tests/ |

### 文档导航

```
开始使用项目
    → README.md (项目概述)
    → README_项目结构.md (本文件 - 详细结构)

了解指标
    → docs/指标实现总结_A至H批次.md (A-H批次47个指标详解)
    → docs/指标分类清单.md (系统全部110个指标清单)
    → docs/指标清单_全集.md (200+指标完整清单)
    → docs/指标参考手册.md (使用手册)

编写测试
    → tests/README.md (测试说明)
    → tests/indicators/ (批次测试示例)

性能优化
    → docs/性能测试报告.md (性能数据)
    → tests/performance/ (性能测试代码)
```

---

## ⚠️ 注意事项

### 1. 导入路径
所有模块使用相对导入：
```python
from core import DataProcessor
from core.indicators import TrendIndicators
```

### 2. 编码问题
- pytest环境下自动处理中文编码
- 文件保存使用UTF-8编码

### 3. 数据库连接
```python
# 使用完毕后断开连接
processor = DataProcessor("data/stock_data.duckdb")
# ... 处理数据 ...
processor.close()  # 断开连接
```

### 4. 内存管理
```python
# 大数据处理时启用内存监控
from core.utils import PerformanceMonitor

with PerformanceMonitor("指标计算"):
    df_result = calculator.calculate_all_indicators_polars(df)
```

### 5. 测试数据
- 小样本测试: 100-1000行
- 完整测试: 116万行真实数据
- 使用 `limit` 参数控制数据量

---

## 🔄 维护建议

### 日常维护

1. **定期测试**
   ```bash
   pytest tests/ -v --cov=src/core
   ```

2. **性能监控**
   ```bash
   python tests/performance/performance_test_real.py
   ```

3. **代码检查**
   ```bash
   # 使用pylint或flake8
   pylint src/core/
   ```

4. **清理缓存**
   ```bash
   # 清理pytest缓存
   rm -rf .pytest_cache __pycache__

   # 清理临时输出
   rm -rf output/test_results/*
   ```

### 开发建议

1. ✅ 核心模块保持稳定，避免频繁修改
2. ✅ 新功能优先作为独立脚本开发
3. ✅ 所有变更都要添加对应的测试
4. ✅ 提交前运行完整测试套件
5. ✅ 保持文档与代码同步更新

### 版本管理

- **v1.0**: 初始版本，48个基础指标
- **v1.5**: 早期扩展，63个指标（+15个）
- **v2.0**: BCD批次，82个指标（+19个）
- **v3.0**: EFGH批次，102个指标（+20个）
- **v4.0**: A批+项目重组，110个指标（+8个，当前版本）

---

## 📈 项目统计

### 代码统计
- **核心代码**: ~3,700行（indicators.py 163KB）
- **测试代码**: ~1,500行
- **文档**: ~4,000行
- **总计**: ~9,200行

### 指标统计
- **总指标数**: 110个（基础48 + 早期15 + A-H批次47）
- **指标类别**: 13大类
- **测试覆盖**: 100%
- **代码覆盖**: 95%+

### 性能统计
- **116万行处理**: ~10秒
- **内存占用**: <2GB
- **速度提升**: 比Pandas快10-100倍
- **存储压缩**: 压缩率70-90%

---

## 🎯 快速链接

- **开始使用**: [README.md](README.md)
- **指标总结**: [docs/指标实现总结_A至H批次.md](docs/指标实现总结_A至H批次.md)
- **指标清单**: [docs/指标分类清单.md](docs/指标分类清单.md)
- **测试说明**: [tests/README.md](tests/README.md)
- **完整清单**: [docs/指标清单_全集.md](docs/指标清单_全集.md)

---

**最后更新**: 2026-01-01
**版本**: v4.0
**维护者**: Claude Code
**项目**: 股票技术指标计算系统
