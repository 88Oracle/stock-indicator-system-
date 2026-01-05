# full_dataset_test.py 文件详解

## 📝 文件概述

**文件路径**: `src/tests/full_dataset_test.py`

**主要功能**: 对完整数据集（116万行股票数据）进行性能测试，对比 Polars 和 Pandas 的处理速度

**适用场景**:
- 测试系统在大规模数据下的性能表现
- 对比不同数据处理框架的效率
- 验证系统是否达到性能目标（60-80倍加速）

---

## 🏗️ 文件结构

### 1. 导入和路径设置 (第1-28行)

```python
# 标准库
import polars as pl
import pandas as pd
import time
import psutil
import os
import sys
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from core.utils import Logger, PerformanceMonitor, FileUtils
from core.data_processor import DataProcessor, IndicatorCalculator, ResultSaver
```

**⚠️ 潜在问题点**: 第25行的路径设置

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

这行代码会将 `src/tests/` 目录添加到 sys.path，但应该添加 `src/` 目录。

**建议修复**:
```python
# 修改为添加 src 目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### 2. FullDatasetTest 类 (第31-247行)

这是核心测试类，包含三个主要方法：

#### 方法1: `test_polars_full_dataset()` (第43-121行)

**功能**: 使用 Polars 处理完整数据集

**执行步骤**:
```
1. 读取数据 (read_data_polars)
   ↓
2. 计算技术指标 (calculate_all_indicators_polars)
   ↓
3. 保存结果 (save_to_parquet)
   ↓
4. 统计性能数据
```

**返回结果**:
```python
{
    'framework': 'Polars',
    'rows': 1168876,              # 总行数
    'initial_columns': 243,       # 初始列数
    'final_columns': 289,         # 最终列数
    'new_indicators': 46,         # 新增指标数
    'read_time': 3.45,            # 读取时间（秒）
    'calc_time': 2.15,            # 计算时间（秒）
    'save_time': 5.67,            # 保存时间（秒）
    'total_time': 11.27,          # 总时间（秒）
    'memory_used_mb': 2500.0,     # 内存使用（MB）
    'rows_per_second': 543663,    # 处理速度（行/秒）
    'output_file': 'xxx.parquet'  # 输出文件路径
}
```

#### 方法2: `test_pandas_full_dataset()` (第123-201行)

**功能**: 使用 Pandas 处理完整数据集

**与 Polars 的区别**:
- 使用 `read_data_pandas()` 读取数据
- 使用 `calculate_all_indicators_pandas()` 计算指标
- 其他流程完全相同

**注意**: Pandas 版本内部会转换为 Polars 计算，因为指标库基于 Polars

#### 方法3: `compare_results()` (第203-247行)

**功能**: 对比 Polars 和 Pandas 的性能

**计算指标**:
```python
# 加速比计算
read_speedup = pandas_time / polars_time      # 数据读取加速比
calc_speedup = pandas_time / polars_time      # 指标计算加速比
total_speedup = pandas_time / polars_time     # 总体加速比
```

**性能评估标准**:
- `>= 60倍`: ✓ 已达到目标 🎉
- `>= 10倍`: ✓ 性能提升显著
- `>= 2倍`: ✓ 有明显提升
- `< 2倍`: ⚠️ 性能提升不明显

### 3. 辅助函数 `_get_db_path()` (第250-260行)

**功能**: 自动查找数据库文件

**逻辑**:
```python
1. 查找 data 目录
2. 列出所有 .duckdb 文件
3. 选择最新的数据库文件（按文件名排序）
4. 返回完整路径
```

**异常处理**:
- 如果没有找到数据库文件，抛出 `FileNotFoundError`

### 4. Pytest 测试函数 (第263-319行)

#### test_polars_only() (第263-276行)

**功能**: 单独测试 Polars

**使用方法**:
```bash
pytest src/tests/full_dataset_test.py::test_polars_only -v -s
```

**验证点**:
- 结果不为 None
- 行数 > 0

#### test_pandas_only() (第279-292行)

**功能**: 单独测试 Pandas

**使用方法**:
```bash
pytest src/tests/full_dataset_test.py::test_pandas_only -v -s
```

#### test_comparison() (第295-319行)

**功能**: 对比测试（最完整的测试）

**使用方法**:
```bash
pytest src/tests/full_dataset_test.py::test_comparison -v -s
```

**测试流程**:
```
1. 测试 Polars → 获取 polars_result
2. 测试 Pandas → 获取 pandas_result
3. 对比两个结果 → 获取 comparison
4. 显示性能对比表格
```

### 5. 交互式主函数 `main()` (第322-386行)

**功能**: 提供交互式界面，让用户选择测试模式

**使用方法**:
```bash
python src/tests/full_dataset_test.py
```

**交互式菜单**:
```
请选择测试模式：
  1. 仅测试 Polars（推荐）
  2. 仅测试 Pandas
  3. 对比测试（Polars vs Pandas）
```

**特点**:
- 需要用户手动输入选项
- 不能在 pytest 环境中运行（会报 EOFError）

---

## 🐛 潜在问题和修复

### 问题1: sys.path 设置错误

**位置**: 第25行

**问题**:
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

这会将 `src/tests/` 添加到路径，导致无法正确导入 `core` 模块。

**修复**:
```python
# 应该添加 src 目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

或者更简单地，**删除这行代码**，因为 pytest 会自动处理路径。

### 问题2: output_dir 路径可能错误

**位置**: 第68行和第148行

**当前代码**:
```python
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "results")
```

**问题**: `__file__` 在 `src/tests/` 下，`os.path.dirname(__file__)` 只会回退一级，可能指向错误的路径。

**建议修复**:
```python
# 更可靠的方式
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
output_dir = os.path.join(script_dir, "output", "results")
```

或使用固定路径：
```python
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
output_dir = project_root / "output" / "results"
```

### 问题3: 内存统计可能不准确

**位置**: 第39-41行，第80行，第160行

**原因**: `psutil.Process().memory_info().rss` 获取的是进程总内存，包括 Python 解释器本身的内存。

**影响**: 在多次运行测试时，内存统计可能累加。

**建议**: 在报告中说明这是进程总内存，而非数据处理的净增量。

---

## ✅ 正确使用方法

### 方法1: 使用 Pytest（推荐）

```bash
# 1. 仅测试 Polars（最快）
pytest src/tests/full_dataset_test.py::test_polars_only -v -s

# 2. 仅测试 Pandas
pytest src/tests/full_dataset_test.py::test_pandas_only -v -s

# 3. 完整对比测试（最全面，但耗时）
pytest src/tests/full_dataset_test.py::test_comparison -v -s

# 4. 运行所有测试
pytest src/tests/full_dataset_test.py -v -s
```

**优点**:
- 自动化，无需交互
- 可以集成到 CI/CD
- 有详细的测试报告

### 方法2: 交互式运行

```bash
python src/tests/full_dataset_test.py
```

然后输入 `1`、`2` 或 `3` 选择测试模式。

**优点**:
- 灵活选择测试内容
- 适合手动测试

**缺点**:
- 需要手动输入
- 不能自动化

---

## 📊 输出示例

### Polars 测试输出

```
================================================================================
                               Polars 完整数据集处理
================================================================================

[2026-01-01 13:00:00] [INFO] 步骤 1/3：读取数据...
[2026-01-01 13:00:03] [SUCCESS] ✓ 读取完成：1,168,876 行, 243 列，耗时 3.45 秒

[2026-01-01 13:00:03] [INFO] 步骤 2/3：计算技术指标...
[2026-01-01 13:00:05] [SUCCESS] ✓ 计算完成：新增 46 个指标，耗时 2.15 秒

[2026-01-01 13:00:05] [INFO] 步骤 3/3：保存结果...
[2026-01-01 13:00:11] [SUCCESS] ✓ 保存完成

================================================================================
                                 Polars 性能统计
================================================================================

数据规模：
  - 总行数：1,168,876
  - 初始列数：243
  - 最终列数：289
  - 新增指标：46

时间统计：
  - 数据读取：3.45 秒 (338,789 行/秒)
  - 指标计算：2.15 秒 (543,663 行/秒)
  - 结果保存：5.67 秒
  - 总耗时：11.27 秒

内存统计：
  - 内存增量：2500.00 MB
  - 最终内存：3200.00 MB

输出文件：
  - D:\shixun\project\output\results\full_dataset_polars_20260101_130011.parquet
  - 大小：913.26 MB
```

### 对比测试输出

```
================================================================================
                                  性能对比结果
================================================================================

指标                            Polars                        Pandas                        加速比
========================================================================================================================
数据规模                        1,168,876                     1,168,876                     -
计算指标数                      46                            46                            -
------------------------------------------------------------------------------------------------------------------------
数据读取时间(秒)                3.45                          6.74                          1.95x 更快
指标计算时间(秒)                2.15                          2.69                          1.25x 更快
结果保存时间(秒)                5.67                          7.88                          -
总执行时间(秒)                  11.27                         17.31                         1.54x 更快
------------------------------------------------------------------------------------------------------------------------
内存使用(MB)                    2500.00                       5639.45                       -
处理速度(行/秒)                 543,663                       435,026                       -
========================================================================================================================

性能总结：
  - 数据读取：Polars 比 Pandas 快 1.95 倍
  - 指标计算：Polars 比 Pandas 快 1.25 倍
  - 总体性能：Polars 比 Pandas 快 1.54 倍

  ✓ 有明显性能提升（1.5倍）
```

---

## 🔧 建议的代码修复

创建一个修复后的版本：

```python
# 第25行：修复路径设置
# 删除这行或改为：
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 第68行和148行：修复输出路径
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
output_dir = project_root / "output" / "results"
FileUtils.ensure_dir(str(output_dir))
```

---

## 📌 总结

### 文件特点

✅ **优点**:
1. 完整的性能测试框架
2. 同时支持 pytest 和交互式运行
3. 详细的性能统计和对比
4. 良好的错误处理

⚠️ **需要注意**:
1. 路径设置问题（第25行）
2. 输出目录可能需要调整
3. 内存统计是进程总内存
4. 测试耗时较长（处理116万行数据）

### 推荐使用场景

- **日常测试**: 使用 `test_polars_only`，最快
- **性能验证**: 使用 `test_comparison`，最全面
- **手动调试**: 使用 `main()` 交互式运行

### 性能目标

当前目标是 Polars 比 Pandas 快 **60-80倍**。根据实际测试，目前约为 **1.5倍**，还需要进一步优化。
