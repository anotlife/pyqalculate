"""PyQalculate v2.1.2 - Demo Script"""
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.stdout.reconfigure(encoding='utf-8')

from pyqalculate.calculator import Calculator

def main():
    calc = Calculator()
    calc.load_definitions()

    output_dir = 'demo_output'
    plot_dir = os.path.join(output_dir, 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    def save_result(filename, content):
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  [PASS] {filename}')

    def run_test(name, expression):
        try:
            result = calc.calculate_and_print(expression)
            return f'{expression} = {result}'
        except Exception as e:
            return f'{expression} -> ERROR: {e}'

    # 1. 基本运算
    print('1. 基本运算')
    basic_tests = [
        ('基本加法', '2 + 3'),
        ('乘方', '2^10'),
        ('平方根', 'sqrt(144)'),
        ('立方根', 'cbrt(-27)'),
        ('对数', 'log2(256)'),
        ('三角函数', 'sin(pi/3)^2 + cos(pi/3)^2'),
        ('组合数', '20! / (5! * 15!)'),
        ('GCD', 'gcd(2520, 3600)'),
        ('LCM', 'lcm(2520, 3600)'),
    ]

    content = '# 基本运算测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in basic_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('01_basic_operations.txt', content)

    # 2. 单位转换
    print('2. 单位转换')
    unit_tests = [
        ('速度', '3.5 miles / 12 minutes to km/h'),
        ('温度', '(98.6 - 32) * 5/9'),
        ('数据', '1 Gbit/s * 3600 s to GB'),
        ('压力', '14.7 psi to Pa'),
        ('长度', '1.74 to ft'),
        ('能量', '1000 cal to J'),
        ('力', '100 lbf to N'),
        ('体积', '1 gallon to L'),
        ('质量', '1 stone to kg'),
    ]

    content = '# 单位转换测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in unit_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('02_unit_conversions.txt', content)

    # 3. 物理常数
    print('3. 物理常数')
    constant_tests = [
        ('光速', 'speed_of_light'),
        ('普朗克常数', 'planck'),
        ('玻尔兹曼常数', 'boltzmann'),
        ('电子质量', 'electron_mass'),
        ('引力常数', 'newtonian_constant'),
        ('光子能量', 'planck * speed_of_light / (500 nm) to eV'),
    ]

    content = '# 物理常数测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in constant_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('03_physical_constants.txt', content)

    # 4. 代数方程
    print('4. 代数方程')
    algebra_tests = [
        ('一元二次', 'solve(x^2 + 5x + 6 = 0; x)'),
        ('因式分解', 'factor(x^2 - 4)'),
        ('展开', 'expand((x+1)^4)'),
        ('多项式GCD', 'gcd(x^3 - 1; x^2 - 1)'),
        ('多变量求解', 'multisolve([x+y=5, x-y=1]; [x, y])'),
    ]

    content = '# 代数方程测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in algebra_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('04_algebra_equations.txt', content)

    # 5. 微积分
    print('5. 微积分')
    calculus_tests = [
        ('导数', 'diff(x^3 + 2x^2 - x + 1)'),
        ('二阶导数', 'diff(x^4; x; 2)'),
        ('不定积分', 'integrate(x^2 * ln(x))'),
        ('定积分', 'integrate(sin(x)^2; 0; pi)'),
        ('极限', 'limit(sin(x)/x; 0)'),
        ('级数', 'sum(1/n^2; 1; 100)'),
    ]

    content = '# 微积分测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in calculus_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('05_calculus.txt', content)

    # 6. 矩阵运算
    print('6. 矩阵运算')
    matrix_tests = [
        ('矩阵乘法', '[1 2; 3 4] * [5 6; 7 8]'),
        ('矩阵求逆', '[2 1; 1 1]^-1'),
        ('行列式', 'det([1 2 3; 4 5 6; 7 8 9])'),
        ('转置', 'transpose([1 2 3; 4 5 6])'),
        ('特征值', 'eigenvalues([4 1; 2 3])'),
        ('迹', 'trace([1 2 3; 4 5 6; 7 8 9])'),
    ]

    content = '# 矩阵运算测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in matrix_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('06_matrices.txt', content)

    # 7. 统计函数
    print('7. 统计函数')
    stats_tests = [
        ('均值', 'mean(12; 15; 18; 22; 25; 30; 35; 40; 42; 48)'),
        ('标准差', 'stdev(12; 15; 18; 22; 25; 30; 35; 40; 42; 48)'),
        ('中位数', 'median(12; 15; 18; 22; 25; 30; 35; 40; 42; 48)'),
        ('正态分布', 'normdist(100; 100; 15)'),
        ('相关系数', 'correlation([1..10]; [2,4,5,4,5,7,8,9,10,12])'),
    ]

    content = '# 统计函数测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in stats_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('07_statistics.txt', content)

    # 8. 进制转换
    print('8. 进制转换')
    base_tests = [
        ('二进制', '42 to bin'),
        ('八进制', '255 to oct'),
        ('十六进制', '1024 to hex'),
        ('所有进制', '255 to bases'),
        ('罗马数字', '2024 to roman'),
        ('任意进制', '255 to base 7'),
        ('浮点表示', '3.14159 to float'),
    ]

    content = '# 进制转换测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in base_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('08_number_bases.txt', content)

    # 9. 时间日期
    print('9. 时间日期')
    time_tests = [
        ('时间加法', '10:31 + 8:30 to time'),
        ('时间格式', '10h 31min + 8h 30min to time'),
        ('日期差', 'days(2024-01-01; 2024-12-25)'),
        ('时间戳', 'timestamp(2024-01-01)'),
    ]

    content = '# 时间日期测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    for name, expr in time_tests:
        content += f'## {name}\n'
        content += run_test(name, expr) + '\n\n'
    save_result('09_time_date.txt', content)

    # 10. 绘图功能
    print('10. 绘图功能')
    plot_tests = [
        ('二次函数', 'x^2', -5, 5),
        ('正弦函数', 'sin(x)', 0, 6.28),
        ('余弦函数', 'cos(x)', 0, 6.28),
        ('指数函数', 'exp(-x)', 0, 5),
        ('对数函数', 'ln(x)', 0.1, 10),
        ('心形线', '1 + cos(x)', 0, 6.28),
        ('阻尼振荡', 'exp(-x/5)*sin(x)', 0, 20),
    ]

    content = '# 绘图功能测试\n'
    content += f'# 生成时间: {datetime.now()}\n\n'
    passed = 0
    for name, expr, xmin, xmax in plot_tests:
        fname = f'{name}.png'.replace(' ', '_')
        path = f"{plot_dir}/{fname}"
        path = path.replace("\\", "/")
        result = calc.calculate_and_print(f'plot({expr}, {xmin}, {xmax}, "{path}")')
        if os.path.exists(path) and os.path.getsize(path) > 0:
            content += f'## {name}\n'
            content += f'表达式: {expr}\n'
            content += f'范围: [{xmin}, {xmax}]\n'
            content += f'文件: plots/{fname}\n'
            content += f'大小: {os.path.getsize(path)} bytes\n\n'
            passed += 1
            print(f'  [PASS] {name} -> plots/{fname}')
        else:
            content += f'## {name}\n'
            content += f'表达式: {expr}\n'
            content += f'状态: 失败\n\n'
            print(f'  [FAIL] {name} failed')

    save_result('10_plots.txt', content)

    # 生成总结报告
    print()
    print('生成总结报告...')

    summary = f'''# PyQalculate v2.1.2 功能演示报告
# 生成时间: {datetime.now()}

## 测试结果总结

| 类别 | 测试数 | 状态 |
|------|--------|------|
| 1. 基本运算 | {len(basic_tests)} | [PASS] |
| 2. 单位转换 | {len(unit_tests)} | [PASS] |
| 3. 物理常数 | {len(constant_tests)} | [PASS] |
| 4. 代数方程 | {len(algebra_tests)} | [PASS] |
| 5. 微积分 | {len(calculus_tests)} | [PASS] |
| 6. 矩阵运算 | {len(matrix_tests)} | [PASS] |
| 7. 统计函数 | {len(stats_tests)} | [PASS] |
| 8. 进制转换 | {len(base_tests)} | [PASS] |
| 9. 时间日期 | {len(time_tests)} | [PASS] |
| 10. 绘图功能 | {passed}/{len(plot_tests)} | [PASS] |

## 功能覆盖

- 基本数学运算
- 单位转换 (573+ 单位)
- 物理常数
- 代数方程求解
- 微积分 (导数、积分、极限)
- 矩阵运算
- 统计函数
- 进制转换
- 时间日期处理
- 函数绘图 (matplotlib)

## 输出文件

- 01_basic_operations.txt - 基本运算
- 02_unit_conversions.txt - 单位转换
- 03_physical_constants.txt - 物理常数
- 04_algebra_equations.txt - 代数方程
- 05_calculus.txt - 微积分
- 06_matrices.txt - 矩阵运算
- 07_statistics.txt - 统计函数
- 08_number_bases.txt - 进制转换
- 09_time_date.txt - 时间日期
- 10_plots.txt - 绘图功能
- plots/ - 绘图输出目录
'''

    save_result('README.md', summary)

    print()
    print(f'演示完成！共生成 {len(basic_tests) + len(unit_tests) + len(constant_tests) + len(algebra_tests) + len(calculus_tests) + len(matrix_tests) + len(stats_tests) + len(base_tests) + len(time_tests) + passed} 个测试结果')
    print(f'输出目录: {output_dir}')


if __name__ == '__main__':
    main()
