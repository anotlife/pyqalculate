# PyQalculate — Python 移植开发计划

> **项目目标**：将 libqalculate (C++) 移植为纯 Python 实现，提供 CLI 和 GUI 应用。
>
> **路径选择**：纯 Python 组合方案（无 C++ 编译依赖），使用成熟 Python 库替代各组件。
>
> **本文档供后续 Agent 参考，请按阶段顺序执行。**

---

## 1. 项目概览

### 1.1 目标

将 libqalculate v5.11.0 的核心功能移植为纯 Python 库 `pyqalculate`，并构建：
- **库 (pyqalculate)**：可 pip install 的 Python 包
- **CLI (pyqalc)**：命令行计算器，兼容 qalc 语法
- **GUI (pyqalculate-gui)**：桌面图形界面计算器

### 1.2 不做什么（v1.0 范围外）

- 不做 Web 界面
- 不做 Jupyter 集成（可后续扩展）
- 不做 100% 功能对齐（优先核心功能，边缘功能后续迭代）
- 不做性能优化到 C++ 水平（目标是"可用"而非"极速"）

### 1.3 参考源码位置

```
D:\1\1tmp\libqalculate\          ← libqalculate C++ 源码
D:\1\1tmp\libqalculate\libqalculate\  ← 核心库源码（63 个文件）
D:\1\1tmp\libqalculate\data\           ← XML 定义文件（单位、函数、变量等）
D:\1\1tmp\libqalculate\src\qalc.cc     ← CLI 参考实现（10,671 行）
```

---

## 2. 技术栈

| 组件 | 库 | 用途 |
|------|-----|------|
| 符号计算 | **SymPy** + **SymEngine** | 代数化简、微积分、方程求解、因式分解 |
| 任意精度 | **gmpy2** + **mpmath** | GMP/MPFR 级精度数值计算 |
| 单位系统 | **Pint** | 426+ 单位换算 |
| 货币 | **requests** + 汇率 API | 实时汇率获取 |
| 日历 | **convertdate** | 31 种日历系统（覆盖 libqalculate 的 11 种） |
| 绘图 | **Matplotlib** | 函数绘图（替代 Gnuplot） |
| 特殊函数 | **SciPy.special** | Bessel、Gamma、erf 等 |
| 表达式解析 | **自定义 Parser** | libqalculate 兼容语法 |
| CLI | **cmd** / **readline** | 命令行交互 |
| GUI | **PyQt6** 或 **tkinter** | 桌面图形界面 |
| 测试 | **pytest** | 单元测试 + 集成测试 |
| 打包 | **setuptools** + **pyproject.toml** | pip install |

---

## 3. 架构设计

```
pyqalculate/
├── pyqalculate/                  ← 核心库
│   ├── __init__.py
│   ├── calculator.py             ← 主计算器引擎（对应 Calculator.h）
│   ├── parser.py                 ← 表达式解析器（对应 Calculator-parse.cc）
│   ├── math_structure.py         ← 表达式树（对应 MathStructure.h）
│   ├── number.py                 ← 任意精度数值（对应 Number.h）
│   ├── function.py               ← 函数系统（对应 Function.h）
│   ├── builtin_functions.py      ← 内建函数注册（对应 BuiltinFunctions-*.cc）
│   ├── variable.py               ← 变量/常量（对应 Variable.h）
│   ├── unit.py                   ← 单位系统（对应 Unit.h）
│   ├── prefix.py                 ← 前缀系统（对应 Prefix.h）
│   ├── dataset.py                ← 数据集（对应 DataSet.h）
│   ├── datetime_ext.py           ← 日期时间扩展（对应 QalculateDateTime.cc）
│   ├── plot.py                   ← 绘图（对应 Calculator-plot.cc）
│   ├── definitions.py            ← 定义加载器（对应 Calculator-definitions.cc）
│   └── types.py                  ← 枚举、常量、选项（对应 includes.h）
│
├── pyqalculate_data/             ← 数据文件（从 libqalculate XML 转换）
│   ├── units.json
│   ├── functions.json
│   ├── variables.json
│   ├── currencies.json
│   ├── prefixes.json
│   ├── datasets.json
│   ├── elements.json
│   └── planets.json
│
├── pyqalc/                       ← CLI 应用
│   ├── __init__.py
│   └── cli.py                    ← 命令行界面（对应 src/qalc.cc）
│
├── pyqalculate_gui/              ← GUI 应用
│   ├── __init__.py
│   ├── main_window.py            ← 主窗口
│   ├── input_widget.py           ← 输入组件
│   ├── result_widget.py          ← 结果显示
│   ├── plot_widget.py            ← 绘图区域
│   └── settings_dialog.py        ← 设置对话框
│
├── tests/                        ← 测试
│   ├── test_parser.py
│   ├── test_calculator.py
│   ├── test_number.py
│   ├── test_units.py
│   ├── test_functions.py
│   ├── test_calculus.py
│   ├── test_algebra.py
│   ├── test_matrix.py
│   ├── test_statistics.py
│   ├── test_datetime.py
│   ├── test_plot.py
│   └── test_integration.py       ← 端到端测试
│
├── scripts/                      ← 工具脚本
│   └── convert_definitions.py    ← XML → JSON 转换
│
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 4. 开发阶段

### 阶段 0：项目初始化（1-2 天）

**目标**：搭建项目骨架，确保工具链可用。

**任务**：
1. 创建项目目录结构
2. 创建 `pyproject.toml`（依赖：sympy, gmpy2, pint, convertdate, matplotlib, scipy, requests）
3. 创建空的 `__init__.py` 和模块文件
4. 创建 `scripts/convert_definitions.py` — 读取 `data/*.xml.in`，转换为 `pyqalculate_data/*.json`
5. 运行转换脚本，生成所有 JSON 数据文件
6. 创建 `pytest.ini` 和基础测试框架

**验证**：
- `pip install -e .` 成功
- `pytest tests/` 通过（空测试）
- JSON 数据文件生成正确

**交付物**：
- 可编辑安装的项目骨架
- 转换后的 JSON 数据文件

---

### 阶段 1：核心数值引擎（3-5 天）

**目标**：实现任意精度数值计算。

**参考源码**：
- `libqalculate/Number.h` (18 KB)
- `libqalculate/Number.cc` (459 KB)

**任务**：
1. `number.py` — 封装 gmpy2.mpq (有理数) + gmpy2.mpfr (浮点数) + mpmath (复数)
2. 支持操作：+, -, *, /, ^, sqrt, cbrt, abs, floor, ceil, mod, factorial
3. 支持精确有理数和任意精度浮点数切换
4. 支持复数（实部 + 虚部）
5. 支持区间算术（上界 + 下界）
6. 支持无穷大和未定义值

**测试**：
```python
# 测试用例（对照 qalc 输出）
assert Number("sqrt(32)") == Number("4 * sqrt(2)")  # 精确模式
assert Number("(-27) ** (1/3)") == Number("1.5 + 2.598i")  # 主根
assert Number("5!").to_int() == 120
assert Number("gcd(2520, 3600)") == Number("360")
assert Number("lcm(2520, 3600)") == Number("25200")
```

**验证**：运行 `tests/test_number.py`，对照 `qalc` 输出。

---

### 阶段 2：表达式解析器（5-7 天）

**目标**：实现 libqalculate 兼容的表达式解析。

**参考源码**：
- `libqalculate/Calculator-parse.cc` (252 KB) — 主解析器
- `libqalculate/Calculator.cc` (105 KB) — 解析入口

**任务**：
1. `parser.py` — 自定义递归下降解析器
2. 支持的语法：
   - 数字：整数、浮点、科学计数法 (`5E3`)、分数 (`5/4`)
   - 运算符：`+`, `-`, `*`, `/`, `^`, `//`, `%`, `mod`
   - 括号：`(`, `)`
   - 函数调用：`sin(x)`, `sqrt(x)`, `log(x; 10)`
   - 变量：`x`, `pi`, `e`
   - 单位：`5 ft`, `3.5 miles`
   - 转换：`to m`, `to hex`, `to fraction`
   - 赋值：`x := 5`, `func() := x + 1`
   - 条件：`x where x > 0`
   - 未知数：`\x`, `"apple"`
   - 注释：`# this is a comment`
3. 输出：`MathStructure` 表达式树

**测试**：
```python
# 解析测试
m = parser.parse("sin(pi/2) + sqrt(32)")
assert m.type == STRUCT_ADDITION
assert m.children[0].type == STRUCT_FUNCTION  # sin()
assert m.children[1].type == STRUCT_POWER     # sqrt()

# 单位解析
m = parser.parse("5 ft to m")
assert m.has_unit_conversion()

# 赋值解析
m = parser.parse("x := 5")
assert m.type == STRUCT_FUNCTION  # save()
```

**验证**：运行 `tests/test_parser.py`，对照 qalc 的 `--terse` 输出。

---

### 阶段 3：表达式树与基础运算（5-7 天）

**目标**：实现 MathStructure 和基础求值。

**参考源码**：
- `libqalculate/MathStructure.h` (44 KB)
- `libqalculate/MathStructure.cc` (111 KB)
- `libqalculate/MathStructure-calculate.cc` (285 KB)
- `libqalculate/MathStructure-eval.cc` (117 KB)
- `libqalculate/MathStructure-print.cc` (227 KB)

**任务**：
1. `math_structure.py` — 表达式树节点类
   - 22 种节点类型（对应 `StructureType` 枚举）
   - 树操作：添加/删除子节点、遍历、克隆
2. `calculator.py` — 主计算器引擎
   - `calculate(expr)` → 求值
   - `parse(str)` → 解析
   - `format(mstruct)` → 格式化输出
3. 基础求值（委托 SymPy）：
   - 算术：`1 + 2*3 = 7`
   - 三角：`sin(pi/2) = 1`
   - 对数：`log2(256) = 8`
   - 组合：`20! / (5! * 15!) = 15504`
4. 输出格式化：
   - 精确模式：`sqrt(32) = 4 × √(2)`
   - 近似模式：`sqrt(32) ≈ 5.657`
   - 分数模式：`5/4 = 1 + 1/4`

**测试**：
```python
calc = Calculator()
assert calc.evaluate("1 + 2*3") == "7"
assert calc.evaluate("sin(pi/2)") == "1"
assert calc.evaluate("sqrt(32)", exact=True) == "4 * sqrt(2)"
assert calc.evaluate("sqrt(32)", exact=False) == "5.6568542"
assert calc.evaluate("137/12", fraction=True) == "11 + 5/12"
```

**验证**：对照 `01_basic_operations.txt` 中的 qalc 输出。

---

### 阶段 4：内建函数（5-7 天）

**目标**：实现 150+ 内建函数。

**参考源码**：
- `libqalculate/BuiltinFunctions.h` (34 KB)
- `libqalculate/BuiltinFunctions-number.cc` (114 KB)
- `libqalculate/BuiltinFunctions-trigonometry.cc` (75 KB)
- `libqalculate/BuiltinFunctions-explog.cc` (43 KB)
- `libqalculate/BuiltinFunctions-combinatorics.cc` (11 KB)
- `libqalculate/BuiltinFunctions-special.cc` (30 KB)
- `libqalculate/BuiltinFunctions-logical.cc` (22 KB)
- `libqalculate/BuiltinFunctions-calculus.cc` (39 KB)
- `libqalculate/BuiltinFunctions-algebra.cc` (59 KB)
- `libqalculate/BuiltinFunctions-matrixvector.cc` (77 KB)
- `libqalculate/BuiltinFunctions-statistics.cc` (15 KB)
- `libqalculate/BuiltinFunctions-datetime.cc` (14 KB)
- `libqalculate/BuiltinFunctions-util.cc` (110 KB)

**任务**：
1. `function.py` — 函数基类和参数验证
2. `builtin_functions.py` — 注册所有内建函数
3. 分类实现（优先级从高到低）：
   - **三角函数**（14 个）：sin, cos, tan, asin, acos, atan, atan2, sinh, cosh, tanh, asinh, acosh, atanh, sinc
   - **指数对数**（8 个）：exp, log, ln, log2, log10, exp2, exp10, sqrt, cbrt
   - **组合数学**（5 个）：factorial, binomial, multinomial, gamma, double_factorial
   - **数论**（10 个）：gcd, lcm, is_prime, next_prime, mod, rem, abs, round, floor, ceil
   - **代数**（8 个）：solve, multisolve, dsolve, factor, expand, coeff, degree, roots
   - **微积分**（4 个）：diff, integrate, limit, sum, product
   - **矩阵向量**（15 个）：det, inverse, transpose, cross, dot, hadamard, trace, adj, cofactor, rref, rank, norm, eigenvalues
   - **统计**（12 个）：mean, stdev, variance, median, mode, percentile, quartile, min, max, rand, correlation, covariance
   - **进制**（8 个）：bin, oct, hex, base, roman, float, floatError, bases
   - **日期时间**（10 个）：date, timestamp, stamptodate, days, weeks, months, years, now, today, lunarphase
   - **特殊函数**（10 个）：zeta, erf, erfc, besselj, bessely, airy, fresnels, fresnelc, gamma, beta
   - **逻辑位运算**（10 个）：and, or, xor, not, bitand, bitor, bitxor, bitnot, shift
   - **工具函数**（10 个）：if, for, sum, product, genvector, load, replace, tostring, length, concatenate

**测试**：每个类别对应一个测试文件，对照 qalc 输出验证。

---

### 阶段 5：单位换算系统（3-5 天）

**目标**：实现 426 种单位的换算。

**参考源码**：
- `libqalculate/Unit.h` (15 KB) + `Unit.cc` (56 KB)
- `libqalculate/Prefix.h` (13 KB) + `Prefix.cc` (13 KB)
- `libqalculate/Calculator-convert.cc` (95 KB)
- `data/units.xml.in` (5060 行, 426 单位)
- `data/currencies.xml.in` (1005 行, 312 货币)
- `data/prefixes.xml.in` (139 行, 34 前缀)

**任务**：
1. `unit.py` — 单位类（AliasUnit, CompositeUnit）
2. `prefix.py` — 前缀类（DecimalPrefix, BinaryPrefix）
3. 从 `pyqalculate_data/units.json` 加载所有单位定义
4. 实现链式转换：`ft → in → m`（通过别名链回溯到基本单位）
5. 实现自动最优单位：`optimal` 命令
6. 实现混合单位：`5 ft + 8.5 in`
7. 货币换算：通过 API 获取实时汇率
8. 前缀自动应用：`1000 m → 1 km`

**测试**：
```python
assert calc.evaluate("5 ft to m") == "1.524 m"
assert calc.evaluate("1.74 to ft") == "5 ft + 8.5039370 in"
assert calc.evaluate("50 Ohm * 2.5 A") == "125 V"
assert calc.evaluate("1 Gbit/s * 3600 s to GB") == "450 GB"
```

**验证**：对照 `02_unit_conversions.txt`。

---

### 阶段 6：代数与方程求解（3-5 天）

**目标**：实现符号代数操作。

**参考源码**：
- `libqalculate/MathStructure-isolatex.cc` (279 KB)
- `libqalculate/MathStructure-factor.cc` (115 KB)
- `libqalculate/MathStructure-gcd.cc` (58 KB)
- `libqalculate/MathStructure-polynomial.cc` (29 KB)
- `libqalculate/MathStructure-decompose.cc` (15 KB)

**任务**：
1. 委托 SymPy 实现：
   - `solve(expr, var)` — 方程求解
   - `multisolve([eq1, eq2, ...], [x, y, z])` — 方程组
   - `dsolve(ode, y, cond)` — 微分方程
   - `factor(expr)` — 因式分解
   - `expand(expr)` — 展开
   - `simplify(expr)` — 化简
   - `partial fraction` — 偏分式分解
2. 自定义实现（SymPy 不直接支持的）：
   - `assume` 系统（正数、负数、整数等假设）
   - 条件求解：`x^2 + 5x + 6 = 0 where x > -3`

**测试**：
```python
assert calc.evaluate("x^6 - 1 to factors") == "(x - 1)(x + 1)(x^2 - x + 1)(x^2 + x + 1)"
assert calc.evaluate("multisolve([x+y+z=6, 2x-y+z=3, x+2y-z=5], [x,y,z])") == "[13/7  17/7  12/7]"
assert calc.evaluate("1/(x^3 - x) to partial fraction") == "1/(2x + 2) + 1/(2x - 2) - 1/x"
```

**验证**：对照 `05_algebra_equations.txt`。

---

### 阶段 7：微积分（3-5 天）

**目标**：实现符号微分、积分、极限。

**参考源码**：
- `libqalculate/MathStructure-differentiate.cc` (28 KB)
- `libqalculate/MathStructure-integrate.cc` (290 KB)
- `libqalculate/MathStructure-limit.cc` (47 KB)

**任务**：
1. 委托 SymPy 实现：
   - `diff(expr)` — 符号微分
   - `diff(expr, x, n)` — n 阶偏微分
   - `integrate(expr)` — 不定积分
   - `integrate(expr, a, b)` — 定积分
   - `limit(expr, x, a)` — 极限
   - `sum(expr, i, a, b)` — 求和
   - `product(expr, i, a, b)` — 求积
2. 输出格式化：
   - 精确：`integrate(6x^2) = 2x^3 + C`
   - 近似：`integrate(e^(-x^2), -inf, inf) = sqrt(pi)`

**测试**：
```python
assert calc.evaluate("diff(sin(x^2) * exp(-x))") == "2*x*cos(x^2)*exp(-x) - sin(x^2)*exp(-x)"
assert calc.evaluate("integrate(6*x^2, 1, 5)") == "248"
assert calc.evaluate("limit((1 + 1/n)^n, n, oo)") == "E"
```

**验证**：对照 `06_calculus.txt`。

---

### 阶段 8：矩阵与向量（3-5 天）

**目标**：实现矩阵/向量操作。

**参考源码**：
- `libqalculate/MathStructure-matrixvector.cc` (49 KB)
- `libqalculate/BuiltinFunctions-matrixvector.cc` (77 KB)

**任务**：
1. 委托 SymPy.Matrix 实现：
   - 矩阵乘法、转置、求逆
   - 行列式、迹、秩
   - 特征值、特征向量
   - RREF（行最简形）
   - 点积、叉积、Hadamard 积
2. 自定义：
   - 矩阵语法：`[1 2 3; 4 5 6]`
   - 向量语法：`(1; 2; 3)` 或 `[1, 2, 3]`
   - 切片：`v(1)`, `m(2;3)`

**测试**：
```python
assert calc.evaluate("[1 2 3; 4 5 6; 7 8 9] * [1; 0; 1]") == "[4; 10; 16]"
assert calc.evaluate("det([2 1 0; 1 0 1; 0 1 2])") == "-4"
assert calc.evaluate("cross([1 2 3]; [4 5 6])") == "[-3  6  -3]"
```

**验证**：对照 `07_matrices_vectors.txt`。

---

### 阶段 9：统计与概率（2-3 天）

**目标**：实现统计函数。

**参考源码**：
- `libqalculate/BuiltinFunctions-statistics.cc` (15 KB)

**任务**：
1. 委托 SymPy + SciPy.stats 实现：
   - 描述统计：mean, stdev, variance, median, mode, quartile, percentile
   - 分布：normdist, tdist, fdist, chisqdist
   - 相关性：correlation, covariance
   - 假设检验：ttest, pttest
   - 回归：linear regression, polynomial regression

**测试**：
```python
assert calc.evaluate("mean(12; 15; 18; 22; 25; 30; 35; 40; 42; 48)") == "28.7"
assert calc.evaluate("stdev(12; 15; 18; 22; 25; 30; 35; 40; 42; 48)") ≈ 12.284
assert calc.evaluate("correlation([1;2;3;4;5;6;7;8;9;10]; [2;4;5;4;5;7;8;9;10;12])") ≈ 0.9719
```

**验证**：对照 `08_statistics.txt`。

---

### 阶段 10：日期时间（2-3 天）

**目标**：实现日期时间操作。

**参考源码**：
- `libqalculate/QalculateDateTime.cc` (93 KB)
- `libqalculate/BuiltinFunctions-datetime.cc` (14 KB)

**任务**：
1. `datetime_ext.py` — 日期时间扩展类
2. 委托 convertdate 实现日历转换（11+ 种日历）
3. 自定义：
   - 日期算术：`"2024-06-15" + 100 days`
   - 时间算术：`10:31 + 8:30 to time`
   - 时区转换：`now to utc+8`
   - 月相计算：`lunarphase(now)`
   - 时间戳：`timestamp(2024-01-01)`, `stamptodate(1704038400)`

**测试**：
```python
assert calc.evaluate("10:31 + 8:30 to time") == "19:01"
assert calc.evaluate("days(2024-01-01; 2024-12-25)") == "359"
assert calc.evaluate("timestamp(2024-01-01)") == "1704038400"
```

**验证**：对照 `09_time_date.txt`。

---

### 阶段 11：进制转换（2-3 天）

**目标**：实现数制转换。

**参考源码**：
- `libqalculate/BuiltinFunctions-number.cc` (114 KB)

**任务**：
1. 自定义实现：
   - 任意进制（2-36）：`255 to base 7 = 513`
   - 二进制/八进制/十六进制：`42 to bin = 0010 1010`
   - 浮点表示：`3.14159 to float`
   - 罗马数字：`2024 to roman = MMXXIV`
   - 所有进制：`255 to bases`
   - 位运算：`0xABCD AND 0xFF00`
   - 性别agesimal：`52.34 to sexa`

**测试**：
```python
assert calc.evaluate("255 to bases") == "0000 0000 1111 1111 = 0377 = 255 = 0xFF"
assert calc.evaluate("42 to bin") == "0010 1010"
assert calc.evaluate("2024 to roman") == "MMXXIV"
assert calc.evaluate("255 to base 7") == "513"
```

**验证**：对照 `10_number_bases.txt`。

---

### 阶段 12：绘图功能（2-3 天）

**目标**：实现函数绘图。

**参考源码**：
- `libqalculate/Calculator-plot.cc` (27 KB)

**任务**：
1. `plot.py` — 绘图模块
2. 委托 Matplotlib 实现：
   - 2D 函数绘图：`plot(x^2, -5, 5)`
   - 多函数叠加
   - 参数方程（通过生成数据点）
   - 极坐标
   - 保存为 PNG/SVG
3. 高级功能（作为绘图数据生成器）：
   - 傅里叶级数可视化
   - 阻尼振荡

**测试**：
```python
# 生成数据点测试
data = plot.generate_data("sin(x)", -6.28, 6.28, 1000)
assert len(data) == 1000
assert abs(data[500].y - sin(data[500].x)) < 0.001
```

**验证**：与 `plots/` 目录下的 PNG 对比。

---

### 阶段 13：不确定度与区间算术（2-3 天）

**目标**：实现误差传播。

**参考源码**：
- `libqalculate/Number.h` 中的区间部分
- `libqalculate/BuiltinFunctions-*.cc` 中的 Interval/Uncertainty 函数

**任务**：
1. 扩展 `number.py` 支持区间（上界 + 下界）
2. 支持语法：`5±0.1`, `interval(-3; 7)`
3. 误差传播：自动计算不确定度
4. 区间算术：`interval(-3; 7)^3`

**测试**：
```python
assert calc.evaluate("(5±0.1)*(3±0.2)^2/(2±0.05)") == "22.5±3.1"
assert calc.evaluate("interval(-3; 7)^3") == "interval(-52; 68)"
```

**验证**：对照 `04_uncertainty_interval.txt`。

---

### 阶段 14：物理常数与数据集（1-2 天）

**目标**：加载预定义常量和数据集。

**参考源码**：
- `libqalculate/Calculator-definitions.cc` (163 KB)
- `data/variables.xml.in` (971 行)
- `data/elements.xml.in` (1157 行)
- `data/planets.xml.in` (152 行)

**任务**：
1. `definitions.py` — 定义加载器
2. 从 JSON 加载 166 个变量/常量
3. 加载 118 个化学元素数据
4. 加载 10 个行星数据
5. 实现 `atom()`, `planet()` 函数

**测试**：
```python
assert calc.evaluate("speed_of_light") == "299792458 m/s"
assert calc.evaluate("planck * speed_of_light / (500 nm) to eV") ≈ "2.48 eV"
assert calc.evaluate("atom(Fe; weight)") ≈ "9.273e-26 kg"
```

**验证**：对照 `03_physical_constants.txt`。

---

### 阶段 15：CLI 应用（3-5 天）

**目标**：实现命令行计算器。

**参考源码**：
- `src/qalc.cc` (10,671 行)

**任务**：
1. `pyqalc/cli.py` — 命令行界面
2. 支持的功能：
   - 交互模式：`pyqalc` 进入交互式计算
   - 单次计算：`pyqalc "sin(pi/2)"`
   - 命令：`set`, `save`, `delete`, `assume`, `base`, `mode`, `help`
   - `to` 转换：`5 ft to m`, `42 to hex`
   - 历史记录
   - Tab 补全
   - 颜色输出
3. 命令行参数：
   - `-t` 简洁模式（只输出结果）
   - `-b BASE` 设置进制
   - `-s "option value"` 设置选项
   - `-e` 更新汇率
   - `-v` 版本

**测试**：
```bash
pyqalc "sin(pi/2)" → 1
pyqalc -t "5 ft to m" → 1.524 m
pyqalc "42 to hex" → 0x2A
```

**验证**：对照 `qalc` 的实际输出。

---

### 阶段 16：GUI 应用（5-7 天）

**目标**：实现桌面图形界面计算器。

**任务**：
1. `pyqalculate_gui/main_window.py` — 主窗口
   - 输入框（支持历史、补全）
   - 结果显示区域（支持数学公式渲染）
   - 绘图区域
   - 侧边栏（变量、函数、单位列表）
2. `pyqalculate_gui/input_widget.py` — 输入组件
3. `pyqalculate_gui/result_widget.py` — 结果显示
4. `pyqalculate_gui/plot_widget.py` — 绘图区域
5. `pyqalculate_gui/settings_dialog.py` — 设置对话框

**测试**：手动测试 GUI 功能。

**验证**：与 `qalculate-qt.exe` 对比功能。

---

### 阶段 17：集成测试与文档（3-5 天）

**目标**：全面测试和文档。

**任务**：
1. 创建 `tests/test_integration.py` — 端到端测试
   - 对照 `qalculate_output/` 中的所有结果文件
   - 逐行对比 qalc 输出
2. 创建 `README.md`
3. 创建使用文档
4. 性能基准测试
5. 修复发现的 bug

**验证**：所有测试通过，覆盖率 > 80%。

---

## 5. 测试策略

### 5.1 单元测试

每个模块对应一个测试文件：
- `test_number.py` — 数值引擎
- `test_parser.py` — 解析器
- `test_calculator.py` — 计算器引擎
- `test_units.py` — 单位换算
- `test_functions.py` — 内建函数
- `test_calculus.py` — 微积分
- `test_algebra.py` — 代数
- `test_matrix.py` — 矩阵
- `test_statistics.py` — 统计
- `test_datetime.py` — 日期时间
- `test_plot.py` — 绘图

### 5.2 集成测试

对照 `qalculate_output/` 目录中的 qalc 输出：
- `01_basic_operations.txt`
- `02_unit_conversions.txt`
- `03_physical_constants.txt`
- `04_uncertainty_interval.txt`
- `05_algebra_equations.txt`
- `06_calculus.txt`
- `07_matrices_vectors.txt`
- `08_statistics.txt`
- `09_time_date.txt`
- `10_number_bases.txt`

### 5.3 回归测试

使用 libqalculate 的测试文件：
- `tests/calculus.batch` (25 行)
- `tests/limits.batch` (407 行)
- `tests/matrixvector.batch` (299 行)
- `tests/stats.batch` (82 行)
- `tests/solver.batch` (118 行)
- `tests/units.batch` (34 行)

---

## 6. 交付物清单

| 交付物 | 说明 |
|--------|------|
| `pyqalculate/` | 核心库，可 `import pyqalculate` |
| `pyqalculate_data/` | JSON 数据文件 |
| `pyqalc/` | CLI 应用 |
| `pyqalculate_gui/` | GUI 应用 |
| `tests/` | 测试套件 |
| `pyproject.toml` | 包配置 |
| `README.md` | 使用文档 |
| `DEVELOPMENT_PLAN.md` | 本文件 |

---

## 7. 风险与注意事项

### 7.1 性能

- SymPy 纯 Python 模式比 C++ 慢 10-100×
- 解决方案：使用 SymEngine 后端（C++ 加速）
- 对于交互式使用（< 100ms 响应），80% 操作可接受

### 7.2 功能差异

- libqalculate 的解析器非常复杂（6,371 行），完整复现困难
- 解决方案：优先支持常用语法，边缘情况逐步完善
- 单位语法 `5 ft to m` 需要自定义解析器

### 7.3 依赖管理

- gmpy2 需要预编译的 wheel（Windows 上可用）
- SymEngine 可选但推荐（性能提升显著）
- convertdate 覆盖 31 种日历（比 libqalculate 的 11 种更多）

### 7.4 Windows 兼容性

- PyQt6 在 Windows 上原生支持
- gmpy2 有 Windows wheel
- 所有依赖都有 Windows wheel

---

## 8. 优先级排序（如果时间有限）

如果无法完成所有阶段，按以下优先级：

1. **阶段 1-3**（核心引擎 + 解析器 + 基础运算）— 最小可用版本
2. **阶段 4**（内建函数）— 功能丰富
3. **阶段 5-6**（单位 + 代数）— 实用工具
4. **阶段 7-8**（微积分 + 矩阵）— 高级功能
5. **阶段 9-11**（统计 + 日期 + 进制）— 补充功能
6. **阶段 12-14**（绘图 + 不确定度 + 常数）— 完整体验
7. **阶段 15-16**（CLI + GUI）— 用户界面
8. **阶段 17**（测试 + 文档）— 质量保证

---

## 9. 给下一个 Agent 的提示

### 开始前

1. 先运行 `pip install -e .` 确保项目骨架可安装
2. 运行 `scripts/convert_definitions.py` 生成 JSON 数据文件
3. 阅读 `D:\1\1tmp\libqalculate_output\libqalculate_analysis.md` 了解完整架构

### 开发时

1. 每完成一个阶段，运行对应的测试文件
2. 对照 `qalculate_output/` 中的结果验证输出
3. 使用 `qalc -t "expression"` 获取参考输出
4. 优先让功能正确，再优化性能

### 遇到问题

1. 解析器复杂度高 → 先实现核心语法，边缘情况标记 `TODO`
2. SymPy 输出格式不匹配 → 自定义 `StrPrinter` 调整格式
3. 性能问题 → 引入 SymEngine 后端
4. 单位换算精度 → 使用 gmpy2.mpfr 确保精度

### 代码风格

- 遵循 PEP 8
- 类型注解（type hints）
- docstring 用 Google 风格
- 测试用 pytest
