# 测试目录说明

本目录包含项目的所有测试文件，按功能和批次进行分类组织。

## 📁 目录结构

```
tests/
├── unit/                              # 单元测试
│   ├── test_indicators_simple.py      # 基础指标测试
│   ├── test_new_indicators.py         # 新增指标测试
│   └── test_batch_processor.py        # 批处理器测试
│
├── integration/                       # 集成测试
│   ├── test_all_new_indicators.py     # 所有新指标集成测试
│   └── test_integration_new_indicators.py  # 指标集成测试
│
├── indicators/                        # 指标测试（按批次分类）
│   ├── test_statistical_indicators.py      # A批：统计指标（8个）
│   ├── test_moving_averages_extended.py    # B批：移动平均扩展（8个）
│   ├── test_oscillators_extended.py        # C批：震荡指标补充（6个）
│   ├── test_volatility_extended.py         # D批：波动率指标（5个）
│   ├── test_risk_indicators.py             # E批：风险管理（5个）
│   ├── test_pattern_indicators.py          # F批：形态识别（6个）
│   ├── test_advanced_trend_indicators.py   # G批：高级趋势（5个）
│   └── test_market_structure_indicators.py # H批：市场结构（4个）
│
├── performance/                       # 性能测试
│   ├── performance_test.py            # 基准性能测试
│   ├── performance_test_real.py       # 真实数据性能测试
│   ├── test_full_dataset.py           # 完整数据集测试（pytest）
│   └── full_dataset_test.py           # 完整数据集测试（交互式）
│
└── utils/                             # 工具测试
    ├── count_all_indicators.py        # 指标数量统计工具
    └── verify_indicators_accuracy.py  # 指标准确性验证工具
```

## 🧪 测试分类说明

### 1. 单元测试 (unit/)

测试单个指标或模块的功能，确保每个组件独立工作正常。

**运行方式**:
```bash
pytest tests/unit/ -v
```

### 2. 集成测试 (integration/)

测试多个指标协同工作，验证系统整体功能。

**运行方式**:
```bash
pytest tests/integration/ -v
```

### 3. 指标测试 (indicators/)

按批次分类的指标测试，每个测试文件对应一个批次的指标实现。

**批次说明**:
- **A批**: 统计指标（Z-Score, Percentile, Skewness, Kurtosis等）
- **B批**: 移动平均扩展（SMMA, LWMA, TMA, ZLEMA, T3等）
- **C批**: 震荡指标补充（Fisher Transform, Coppock, Klinger等）
- **D批**: 波动率指标（Historical Volatility, Chaikin Vol, ATR Stop等）
- **E批**: 风险管理（Maximum Drawdown, Sortino, Calmar Ratio等）
- **F批**: 形态识别（Doji, Hammer, Engulfing, Morning Star等）
- **G批**: 高级趋势（FRAMA, MAMA, Linear Regression等）
- **H批**: 市场结构（Market Structure, Order Blocks, FVG等）

**运行方式**:
```bash
# 运行所有指标测试
pytest tests/indicators/ -v

# 运行特定批次测试
pytest tests/indicators/test_statistical_indicators.py -v
pytest tests/indicators/test_moving_averages_extended.py -v
```

### 4. 性能测试 (performance/)

测试系统在大数据集上的性能表现。

**运行方式**:
```bash
# Pytest性能测试
pytest tests/performance/test_full_dataset.py -v -s

# 交互式性能测试
python tests/performance/full_dataset_test.py
```

### 5. 工具测试 (utils/)

辅助工具和验证脚本。

**运行方式**:
```bash
# 统计指标数量
python tests/utils/count_all_indicators.py

# 验证指标准确性
python tests/utils/verify_indicators_accuracy.py
```

## 🚀 快速开始

### 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并显示覆盖率
pytest tests/ --cov=src/core --cov-report=html

# 运行测试并生成详细报告
pytest tests/ -v --tb=short
```

### 运行特定类型的测试

```bash
# 只运行单元测试
pytest tests/unit/ -v

# 只运行指标测试
pytest tests/indicators/ -v

# 只运行性能测试
pytest tests/performance/ -v
```

### 运行特定指标批次测试

```bash
# A批：统计指标
pytest tests/indicators/test_statistical_indicators.py -v

# B批：移动平均扩展
pytest tests/indicators/test_moving_averages_extended.py -v

# E批：风险管理
pytest tests/indicators/test_risk_indicators.py -v

# F批：形态识别
pytest tests/indicators/test_pattern_indicators.py -v
```

### 运行特定测试用例

```bash
# 运行特定测试函数
pytest tests/indicators/test_statistical_indicators.py::test_zscore -v

# 使用关键字过滤
pytest tests/indicators/ -k "zscore" -v
```

## 📊 测试覆盖情况

- **测试文件数**: 17个
- **测试用例数**: 200+
- **指标覆盖**: 109个指标，100%覆盖
- **代码覆盖**: 95%+
- **测试类型**: 功能测试 + 属性测试 + 性能测试 + 集成测试

## ✅ 测试标准

所有测试需满足以下标准：

1. **功能正确性**: 指标计算结果正确
2. **数值稳定性**: 处理NaN和异常值
3. **边界条件**: 测试极端情况
4. **性能要求**: 大数据集下性能合理
5. **数学属性**: 验证数学特性（单调性、边界等）

## 🔍 测试数据

测试使用的数据源：
- **小样本**: 100-1000行测试数据
- **中等样本**: 1万-10万行测试数据
- **完整数据集**: 116万行真实股票数据

## 📝 添加新测试

### 1. 添加单元测试

在 `tests/unit/` 中创建新测试文件：

```python
# test_my_feature.py
import pytest
from core.indicators import MyIndicators

def test_my_indicator():
    # 准备测试数据
    df = create_test_dataframe(100)

    # 执行指标计算
    result = MyIndicators.my_indicator(df, 'close', 14)

    # 断言
    assert 'My_Indicator_14' in result.columns
    assert not result['My_Indicator_14'].is_null().all()
```

### 2. 添加批次指标测试

在 `tests/indicators/` 中创建批次测试文件：

```python
# test_my_batch_indicators.py
import pytest
from core.indicators import MyBatchIndicators

class TestMyBatchIndicators:
    def test_indicator1(self):
        # 测试指标1
        pass

    def test_indicator2(self):
        # 测试指标2
        pass
```

### 3. 运行新测试

```bash
pytest tests/unit/test_my_feature.py -v
pytest tests/indicators/test_my_batch_indicators.py -v
```

## 🐛 调试测试

```bash
# 显示详细输出
pytest tests/ -v -s

# 在第一个失败时停止
pytest tests/ -x

# 显示局部变量
pytest tests/ -l

# 进入调试模式
pytest tests/ --pdb
```

## 📚 相关文档

- [项目结构说明](../README_项目结构.md)
- [指标实现总结](../docs/指标实现总结_A至H批次.md)
- [指标清单](../docs/指标清单_全集.md)
- [性能测试报告](../docs/性能测试报告.md)

---

**最后更新**: 2026-01-01
**测试框架**: pytest
**Python版本**: 3.8+
