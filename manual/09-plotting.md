# 第9章 绘图系统

> **验证状态**: ✅ 已验证  
> **来源**: `pyqalculate/plot.py` (543 行)

---

## 9.1 概述

PyQalculate 使用 matplotlib 进行函数绘图 [来源: plot.py:73]

**绘图器类**: `Plotter`

---

## 9.2 基本用法

### 通过 Calculator API

```python
calc = Calculator()
calc.load_definitions()

# 标准绘图
result = calc.calculate_and_print('plot(sin(x), -10, 10, "sin.png")')

# 参数方程
result = calc.calculate_and_print('plot_parametric(cos(t), sin(t), "circle.png")')

# 隐函数
result = calc.calculate_and_print('plot_implicit(x^2 + y^2 - 1, "circle_implicit.png")')
```

### 通过 Plotter 类

```python
from pyqalculate.plot import Plotter

plotter = Plotter()

# 标准绘图
plotter.plot("sin(x)", x_min=-10, x_max=10, filename="sin.png")

# 多函数绘图
plotter.plot_multi(["sin(x)", "cos(x)"], x_min=-10, x_max=10, filename="trig.png")

# 参数方程
plotter.plot_parametric("cos(t)", "sin(t)", filename="circle.png")

# 隐函数
plotter.plot_implicit("x^2 + y^2 - 1", filename="circle.png")
```

---

## 9.3 Plotter 方法

[来源: plot.py:73-543]

| 方法 | 行号 | 说明 |
|------|------|------|
| `plot(expr, params, x_min, x_max, num_points, filename)` | 88 | 绘制单个表达式 |
| `plot_multi(exprs, params, ..., colors)` | 149 | 绘制多个表达式 |
| `plot_data(x_values, y_values, params, filename)` | 216 | 绘制原始 x/y 数据 |
| `generate_data(expr, x_min, x_max, num_points)` | 253 | 生成数据点（不渲染） |
| `plot_parametric(x_expr, y_expr, ...)` | 311 | 绘制参数方程 x(t), y(t) |
| `plot_implicit(expr_str, ...)` | 361 | 绘制隐函数 f(x,y)=0 |

---

## 9.4 plot — 标准绘图

```python
result = plotter.plot(
    expr="sin(x)",           # 表达式
    params=None,             # PlotParameters
    x_min=-10,               # X 最小值
    x_max=10,                # X 最大值
    num_points=1000,         # 数据点数
    filename="output.png"    # 输出文件
)
```

**返回**: 文件路径

[来源: plot.py:88-148]

---

## 9.5 plot_multi — 多函数绘图

```python
result = plotter.plot_multi(
    exprs=["sin(x)", "cos(x)"],  # 表达式列表
    params=None,
    x_min=-10,
    x_max=10,
    num_points=1000,
    filename="trig.png",
    colors=["blue", "red"]       # 颜色列表
)
```

[来源: plot.py:149-215]

---

## 9.6 plot_data — 数据绘图

```python
result = plotter.plot_data(
    x_values=[1, 2, 3, 4, 5],
    y_values=[1, 4, 9, 16, 25],
    params=None,
    filename="data.png"
)
```

[来源: plot.py:216-252]

---

## 9.7 generate_data — 生成数据

```python
data = plotter.generate_data(
    expr="x^2",
    x_min=-5,
    x_max=5,
    num_points=100
)
```

**返回**: `PlotData` 对象（含 `x_values` 和 `y_values` 属性）

[来源: plot.py:253-310]

---

## 9.8 plot_parametric — 参数方程绘图

```python
result = plotter.plot_parametric(
    x_expr="cos(t)",         # x(t) 表达式
    y_expr="sin(t)",         # y(t) 表达式
    params=None,
    t_min=0,                 # t 最小值
    t_max=6.28,              # t 最大值
    num_points=1000,
    filename="circle.png"
)
```

**示例**:
- 圆: `cos(t)`, `sin(t)`
- 心形线: `(1+cos(t))*cos(t)`, `(1+cos(t))*sin(t)`
- 螺旋线: `t*cos(t)`, `t*sin(t)`

[来源: plot.py:311-360]

---

## 9.9 plot_implicit — 隐函数绘图

```python
result = plotter.plot_implicit(
    expr_str="x^2 + y^2 - 1",  # f(x,y) = 0
    x_range=(-2.0, 2.0),
    y_range=(-2.0, 2.0),
    filename="circle.png"
)
```

**原理**: 使用 matplotlib 的等高线功能 (`contour`) 绘制 f(x,y) = 0 的等高线 [来源: plot.py:361-419]

**示例**:
- 圆: `x^2 + y^2 - 1`
- 椭圆: `x^2/4 + y^2 - 1`
- 双曲线: `x^2 - y^2 - 1`

---

## 9.10 plot_subplot — 子图绘图

[来源: plot.py:420-474]

```python
result = plotter.plot_subplot(
    subplot_specs=[
        {"type": "plot", "args": {"expr": "sin(x)", "x_min": -10, "x_max": 10}},
        {"type": "plot", "args": {"expr": "cos(x)", "x_min": -10, "x_max": 10}},
    ],
    rows=1,
    cols=2,
    filename="subplot.png"
)
```

每个 subplot spec 支持以下 `type`:
- `"plot"`: 标准函数绘图
- `"parametric"`: 参数方程绘图
- `"implicit"`: 隐函数绘图

---

## 9.11 PlotParameters — 绘图参数

```python
@dataclass
class PlotParameters:
    title: str = ""          # 标题
    x_label: str = ""        # X 轴标签
    y_label: str = ""        # Y 轴标签
    filename: str = ""       # 输出文件名
    filetype: PlotFileType = PlotFileType.AUTO  # 输出格式
    font: str = ""           # 字体
    color: str = "blue"      # 颜色
    grid: bool = True        # 显示网格
    x_axis_with: bool = True # X 轴是否与 Y 轴交叉
    x_min: float = 0.0       # X 最小值（auto_x_min=True 时自动计算）
    x_max: float = 0.0       # X 最大值（auto_x_max=True 时自动计算）
    y_min: float = 0.0       # Y 最小值（auto_y_min=True 时自动计算）
    y_max: float = 0.0       # Y 最大值（auto_y_max=True 时自动计算）
    auto_x_min: bool = True  # 自动 X 最小值
    auto_x_max: bool = True  # 自动 X 最大值
    auto_y_min: bool = True  # 自动 Y 最小值
    auto_y_max: bool = True  # 自动 Y 最大值
    logarithmic_x: bool = False  # X 轴对数
    logarithmic_y: bool = False  # Y 轴对数
```

[来源: types.py:748-769]

---

## 9.12 PlotDataParameters — 数据系列参数

[来源: types.py:772-783]

```python
@dataclass
class PlotDataParameters:
    """Parameters for a single data series in a plot."""
    title: str = ""                         # 系列标题
    style: PlotStyle = PlotStyle.LINES      # 绘图样式
    smoothing: PlotSmoothing = PlotSmoothing.NONE  # 平滑方式
    test_continuous: bool = False           # 检测连续性
    force_continuous: bool = False          # 强制连续
    y_axis2: bool = False                   # 使用右侧 Y 轴
    x_axis2: bool = False                   # 使用顶部 X 轴
    color: str = ""                         # 颜色（空字符串使用调色板自动分配）
    width: int = -1                         # 线宽（-1 为默认）
```

---

## 9.13 安全表达式求值

绘图使用受限命名空间，只包含数学函数，不执行任意代码 [来源: plot.py:25-37]

```python
# 安全的命名空间
_SAFE_NAMESPACE = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "exp": math.exp, "log": math.log, "sqrt": math.sqrt,
    "pi": math.pi, "e": math.e,
    # ... 只有数学函数
}
```

---

## 9.14 输出格式

支持的输出格式 [来源: types.py:510]:

| 格式 | 说明 |
|------|------|
| PNG | 默认格式 |
| SVG | 矢量图 |
| PDF | PDF 文档 |
| EPS | PostScript |
| PS | PostScript |
| LATEX | LaTeX (PGF/TikZ) |
| FIG | XFig |
| AUTO | 自动检测 |

---

## 9.15 使用示例

### 基本函数

```python
# 正弦函数
plotter.plot("sin(x)", x_min=-2*3.14, x_max=2*3.14, filename="sin.png")

# 二次函数
plotter.plot("x^2", x_min=-5, x_max=5, filename="quadratic.png")

# 指数函数
plotter.plot("exp(x)", x_min=-2, x_max=2, filename="exp.png")
```

### 多函数对比

```python
plotter.plot_multi(
    ["sin(x)", "cos(x)", "tan(x)"],
    x_min=-3.14, x_max=3.14,
    filename="trig_comparison.png"
)
```

### 参数方程

```python
# 圆
plotter.plot_parametric("cos(t)", "sin(t)", t_min=0, t_max=6.28, filename="circle.png")

# 心形线
plotter.plot_parametric(
    "(1+cos(t))*cos(t)", "(1+cos(t))*sin(t)",
    t_min=0, t_max=6.28, filename="heart.png"
)
```

### 隐函数

```python
# 单位圆
plotter.plot_implicit("x^2 + y^2 - 1", filename="circle_implicit.png")

# 椭圆
plotter.plot_implicit("x^2/4 + y^2 - 1", filename="ellipse.png")
```
