# 📈 高性能股票技术指标计算系统

基于 **Polars** + **DuckDB** 的高性能股票技术指标计算系统，支持110+种技术指标，性能相对Pandas提升20-40倍。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Polars](https://img.shields.io/badge/Polars-1.36+-orange.svg)](https://pola.rs/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ 主要特性

- 🚀 **超高性能**: 相对Pandas提升20-40倍，116万行数据仅需3秒
- 📊 **丰富指标**: 支持110+种技术指标，涵盖趋势、动量、波动率、成交量等13大类
- 💡 **智能优化**: 自动列裁剪、快速压缩、零拷贝操作
- 🔧 **易于使用**: 简洁API，默认优化，无需配置
- 📚 **文档完整**: 详细的使用指南、性能报告、API文档
- ✅ **测试完善**: 200+测试用例，100%指标覆盖

---

## 🎯 性能数据

### 实测性能（116万行 × 14列数据）

| 阶段 | 优化前 | 优化后 | 提升 |
|-----|--------|--------|------|
| **数据读取** | 2.32秒 | 0.15秒 | **快15.5倍** ⚡ |
| **指标计算** | 0.47秒 | 0.47秒 | 持平 |
| **结果保存** | 3.78秒 | 2.50秒 | **快1.5倍** |
| **总耗时** | **6.57秒** | **3.12秒** | **快52%** 🚀 |

### 相对Pandas提升

- 小数据集（10万行）: **快5.4倍**
- 大数据集（116万行）: **快20-40倍**
- 内存使用: 减少92%

---

## 📦 快速开始

### 1. 环境要求

- Python 3.10+
- Windows / Linux / macOS

### 2. 安装依赖

```bash
# 克隆项目
git clone https://gitee.com/你的用户名/stock-indicator-system.git
cd stock-indicator-system

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 准备数据

```bash
# 导入CSV数据到DuckDB
python src/scripts/import_data.py

# 检查数据
python src/scripts/check_database.py
```

### 4. 运行示例

```python
from src.core.data_processor import DataProcessor, IndicatorCalculator, ResultSaver

# 初始化（自动启用所有优化）
processor = DataProcessor("data/stock_data.duckdb")

# 读取数据（只读14核心列，快15倍）
df = processor.read_data_polars(limit=10000)

# 计算所有110个指标
df_with_indicators = IndicatorCalculator.calculate_all_indicators_polars(df)

# 快速保存（zstd压缩，快1.5倍）
ResultSaver.save_to_parquet(df_with_indicators, "output/indicators/result.parquet")

print(f"✓ 计算完成！原始列: {len(df.columns)}, 新增指标: {len(df_with_indicators.columns) - len(df.columns)}")
```

---

## 📊 支持的指标

### 指标总览（110个）

| 类别 | 数量 | 主要指标 |
|-----|------|---------|
| 趋势类 | 21个 | SMA, EMA, WMA, HMA, DEMA, TEMA, KAMA, ALMA, ZLEMA, FRAMA |
| 动量类 | 8个 | RSI, ROC, Momentum, Stochastic RSI, TSI |
| 震荡类 | 12个 | MACD, Stochastic, CCI, Aroon, Ultimate Osc, Fisher Transform |
| 波动率类 | 10个 | Bollinger Bands, ATR, Keltner, Donchian, Historical Volatility |
| 成交量类 | 9个 | OBV, VWAP, MFI, CMF, FI, Volume Oscillator |
| 统计类 | 8个 | Z-Score, Percentile, Skewness, Kurtosis, Correlation, Sharpe |
| 风险管理类 | 5个 | Maximum Drawdown, Sortino Ratio, Calmar Ratio, Win Rate |
| 形态识别类 | 6个 | Doji, Hammer, Engulfing, Shooting Star, Morning Star |
| 市场结构类 | 4个 | Market Structure, Order Blocks, Fair Value Gaps |
| 其他 | 27个 | ADX, Ichimoku, Supertrend, Parabolic SAR, ZigZag |

**完整清单**: [指标分类清单.md](docs/指标分类清单.md)

---

## 🛠️ 技术栈

### 核心技术

- **[Polars](https://pola.rs/)** - 下一代DataFrame库，基于Rust，性能是Pandas的10-100倍
- **[DuckDB](https://duckdb.org/)** - 嵌入式分析型数据库，SQL支持，列式存储
- **[PyArrow](https://arrow.apache.org/docs/python/)** - Apache Arrow，零拷贝数据传输
- **[Python](https://www.python.org/)** 3.10+ - 现代Python特性

### 性能优化技术

1. **列裁剪（Column Pruning）**: 从243列 → 14列，减少94%数据量
2. **快速压缩算法**: zstd level 1，比默认快34%
3. **零拷贝操作**: 列别名代替数据复制
4. **Arrow格式传输**: DuckDB ↔ Polars零拷贝
5. **向量化计算**: Polars SIMD加速

---

## 📖 文档

### 核心文档

- **[快速开始](docs/快速开始指南.md)** - 5分钟上手
- **[性能优化指南](docs/性能优化指南.md)** - 详细优化说明
- **[快速优化成果报告](docs/快速优化成果报告.md)** - 优化成果总结
- **[指标参考手册](docs/指标参考手册.md)** - 所有指标详解
- **[项目结构](README_项目结构.md)** - 代码组织说明

### 测试文档

- **[测试说明](tests/README.md)** - 测试套件介绍
- **[性能测试报告](docs/性能测试报告.md)** - 详细性能数据

---

## 🔧 高级用法

### 1. 自定义核心列

```python
# 如果需要更多列用于特殊指标
processor = DataProcessor("data/stock_data.duckdb", use_essential_columns=False)
df = processor.read_data_polars()  # 读取全部243列
```

### 2. CSV直接读取

```python
# 跳过DuckDB，直接从CSV读取（首次处理时使用）
df = processor.read_csv_direct("data/通达信数据_20251229.csv", limit=100000)
```

### 3. 批量处理

```python
from src.batch_processor import BatchProcessor

# 批量处理所有股票
processor = BatchProcessor("data/stock_data.duckdb", output_dir="output/indicators")
processor.process_all_stocks(
    batch_size=10,      # 每批处理10只股票
    parallel=True       # 并行处理
)
```

### 4. 性能测试

```bash
# 运行快速性能测试（10万行）
python tests/performance/quick_performance_test.py

# 运行完整数据集测试（116万行）
python tests/performance/test_full_dataset.py
```

---

## 📈 项目结构

```
stock-indicator-system/
├── src/                      # 源代码
│   ├── core/                 # 核心模块
│   │   ├── data_processor.py # 数据处理器
│   │   ├── indicators.py     # 指标计算（110个）
│   │   └── utils.py          # 工具函数
│   ├── config/               # 配置文件
│   ├── scripts/              # 工具脚本
│   └── main.py               # 主程序
├── tests/                    # 测试代码
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   ├── indicators/           # 指标测试（分批）
│   └── performance/          # 性能测试
├── docs/                     # 文档
│   ├── 性能优化指南.md
│   ├── 快速优化成果报告.md
│   ├── 指标参考手册.md
│   └── 性能测试报告.md
├── data/                     # 数据目录
│   └── stock_data.duckdb     # DuckDB数据库
├── output/                   # 输出目录
├── requirements.txt          # Python依赖
├── .gitignore               # Git忽略规则
└── README.md                # 本文件
```

**详细说明**: [项目结构文档](README_项目结构.md)

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定类型测试
pytest tests/unit/ -v              # 单元测试
pytest tests/indicators/ -v        # 指标测试
pytest tests/performance/ -v       # 性能测试

# 测试覆盖率
pytest tests/ --cov=src/core --cov-report=html
```

### 测试统计

- **测试文件**: 17个
- **测试用例**: 200+
- **指标覆盖**: 100%（110/110）
- **代码覆盖**: 95%+

---

## 🎨 使用示例

### 示例1: 计算单只股票指标

```python
from src.core.data_processor import DataProcessor, IndicatorCalculator

processor = DataProcessor("data/stock_data.duckdb")

# 获取股票代码列表
codes = processor.get_stock_codes(limit=10)
print(f"共有 {len(codes)} 只股票")

# 读取单只股票数据
stock_code = codes[0]
df = processor.get_stock_data_polars(stock_code)

# 计算所有指标
df_with_indicators = IndicatorCalculator.calculate_all_indicators_polars(df)

# 查看结果
print(df_with_indicators.tail(5))
```

### 示例2: 性能对比测试

```python
import time

# 优化前（读取全部列）
processor_old = DataProcessor("data/stock_data.duckdb", use_essential_columns=False)
start = time.time()
df_old = processor_old.read_data_polars(limit=100000)
time_old = time.time() - start

# 优化后（只读14列）
processor_new = DataProcessor("data/stock_data.duckdb")
start = time.time()
df_new = processor_new.read_data_polars(limit=100000)
time_new = time.time() - start

print(f"优化前: {time_old:.3f}秒 ({len(df_old.columns)}列)")
print(f"优化后: {time_new:.3f}秒 ({len(df_new.columns)}列)")
print(f"性能提升: {time_old/time_new:.2f}倍")
```

### 示例3: 导出不同格式

```python
from src.core.data_processor import ResultSaver

# 保存为Parquet（推荐，快速压缩）
ResultSaver.save_to_parquet(df, "output/result.parquet")

# 保存为CSV（通用格式）
ResultSaver.save_to_csv(df, "output/result.csv")

# 保存到DuckDB
ResultSaver.save_to_duckdb(df, "output/results.duckdb", "indicators")
```

---

## 🤝 贡献指南

欢迎贡献代码、报告问题、提出建议！

### 贡献流程

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加新功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

### 提交信息规范

使用以下前缀：

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `perf:` 性能优化
- `test:` 测试相关
- `refactor:` 重构
- `style:` 代码格式

---

## 📝 更新日志

### v1.0 (2026-01-01)

- ✅ 完成性能优化，总体提升52%
- ✅ 数据读取快15.94倍（列裁剪）
- ✅ 结果保存快1.52倍（快速压缩）
- ✅ 支持110个技术指标
- ✅ 添加CSV直接读取功能
- ✅ 完善文档和测试

### 未来计划

- 🔜 LazyFrame延迟执行（+10-20%）
- 🔜 批量向量化计算（+20-30%）
- 🔜 GPU加速支持（cuDF）
- 🔜 实时数据流处理
- 🔜 Web可视化界面

---

## ⚠️ 常见问题

### Q1: 为什么选择Polars而不是Pandas？

**A**: Polars基于Rust编写，性能是Pandas的10-100倍。它使用：
- 列式存储架构（Apache Arrow）
- 自动并行化
- 零拷贝操作
- 延迟执行优化

### Q2: 数据文件太大无法上传GitHub？

**A**: 正常现象。大文件（>100MB）已在`.gitignore`中忽略。用户需要自行准备数据文件，或从网盘下载。

### Q3: 如何添加自定义指标？

**A**: 参考 [开发指南](docs/开发指南.md)，在`src/core/indicators.py`中添加新方法。

### Q4: 支持实时数据吗？

**A**: 目前支持历史数据分析。实时数据流处理在开发计划中。

---

## 📄 许可证

本项目采用 **MIT License** 开源协议。详见 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2026 Stock Indicator System Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🌟 致谢

感谢以下开源项目：

- [Polars](https://pola.rs/) - 高性能DataFrame库
- [DuckDB](https://duckdb.org/) - 嵌入式分析数据库
- [Apache Arrow](https://arrow.apache.org/) - 列式内存格式
- [TA-Lib](https://ta-lib.org/) - 技术分析库（灵感来源）

---

## 📞 联系方式

- **Issues**: [提交问题](https://gitee.com/你的用户名/stock-indicator-system/issues)
- **Email**: your-email@example.com
- **文档**: [完整文档](docs/)

---

## 🎯 项目状态

![GitHub last commit](https://img.shields.io/github/last-commit/你的用户名/stock-indicator-system)
![GitHub issues](https://img.shields.io/github/issues/你的用户名/stock-indicator-system)
![GitHub stars](https://img.shields.io/github/stars/你的用户名/stock-indicator-system)

**开发状态**: 🟢 活跃开发中

**功能完成度**:
- [x] 核心功能（100%）
- [x] 性能优化（100%）
- [x] 文档完善（100%）
- [ ] LazyFrame支持（0%）
- [ ] GPU加速（0%）
- [ ] Web界面（0%）

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个Star！**

Made with ❤️ by Stock Indicator System Contributors

</div>
