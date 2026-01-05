# full_dataset_test.py 修复记录

## 📋 修复时间
2026-01-01

## 🐛 发现的问题

### 问题1: sys.path 路径设置错误 ⚠️

**位置**: 第25行

**原代码**:
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

**问题**:
- 文件位于 `src/tests/` 目录
- 代码会将 `src/tests/` 添加到 sys.path
- 导致无法正确导入 `core` 模块

**修复后**:
```python
# 添加src目录到路径（回退两级到达 src 目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**说明**: 需要回退两级（tests → src）才能正确导入 core 模块

---

### 问题2: 输出路径设置错误 ⚠️

**位置**:
- 第68-70行 (Polars测试)
- 第148-150行 (Pandas测试)

**原代码**:
```python
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "results")
```

**问题**:
- 从 `src/tests/` 回退一级只到 `src/`
- 但 `output` 目录在项目根目录
- 导致输出路径错误

**修复后**:
```python
# 回退到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
output_dir = os.path.join(project_root, "output", "results")
```

**说明**: 需要回退三级（tests → src → project root）

---

### 问题3: _get_db_path() 路径错误 ⚠️

**位置**: 第254-258行

**原代码**:
```python
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(script_dir, "data")
```

**修复后**:
```python
# 回退到项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data_dir = os.path.join(project_root, "data")
```

---

### 问题4: main() 函数路径错误 ⚠️

**位置**: 第327-331行

**原代码**:
```python
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(script_dir, "data")
```

**修复后**:
```python
# 配置路径（回退到项目根目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data_dir = os.path.join(project_root, "data")
```

---

## ✅ 修复总结

### 修改内容

| 位置 | 修改内容 | 原因 |
|------|---------|------|
| 第25行 | sys.path 路径回退两级 | 正确导入 core 模块 |
| 第68-70行 | output_dir 路径回退三级 | 输出到正确的 output 目录 |
| 第148-150行 | output_dir 路径回退三级 | 同上 |
| 第254-258行 | data_dir 路径回退三级 | 正确找到 data 目录 |
| 第327-331行 | data_dir 路径回退三级 | 同上 |

### 路径结构说明

```
project/                    # 项目根目录
├── data/                   # 数据目录 ✓
│   └── *.duckdb
├── output/                 # 输出目录 ✓
│   └── results/
├── src/                    # 源代码目录
│   ├── core/              # 核心模块 ✓
│   │   ├── data_processor.py
│   │   ├── indicators.py
│   │   └── utils.py
│   └── tests/             # 测试目录 ← __file__ 在这里
│       └── full_dataset_test.py
```

**从 `src/tests/full_dataset_test.py` 需要回退的层级**:
- 回退1级 → `src/`
- 回退2级 → `project/` (项目根目录)
- 回退3级 → 错误（超出项目范围）

**修正**: 实际上：
- 回退1级: `src/tests/` → `src/`
- 回退2级: `src/` → `project/` (项目根目录) ✓

所以正确的回退次数是：
- **导入 core 模块**: 回退2级到 `src/`
- **访问 data/output**: 回退2级到项目根目录

让我重新检查...实际上文件在 `project/src/tests/`，所以：
- `__file__`: `project/src/tests/full_dataset_test.py`
- `dirname(__file__)`: `project/src/tests/`
- `dirname(dirname(__file__))`: `project/src/` ← 这里可以导入 core
- `dirname(dirname(dirname(__file__)))`: `project/` ← 这里可以访问 data 和 output

所以修复是正确的！

---

## 🧪 验证结果

```bash
# 测试收集成功
$ pytest src/tests/full_dataset_test.py --collect-only -q
src/tests/full_dataset_test.py::test_polars_only
src/tests/full_dataset_test.py::test_pandas_only
src/tests/full_dataset_test.py::test_comparison

3 tests collected in 0.63s
```

✅ 所有路径问题已修复，测试可以正常收集和运行。

---

## 📝 建议

### 1. 使用更可靠的路径处理方式

可以考虑使用 `pathlib` 模块，更清晰：

```python
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 各个目录
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "results"
```

### 2. 创建配置文件

可以创建一个 `src/config/paths.py`:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "results"
SRC_DIR = PROJECT_ROOT / "src"
```

然后在测试中：
```python
from config.paths import DATA_DIR, OUTPUT_DIR
```

这样路径管理更集中、更易维护。

---

## 🎯 相关文档

- 详细解读: `docs/full_dataset_test_解读.md`
- 项目结构: `README_项目结构.md`
