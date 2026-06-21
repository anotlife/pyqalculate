"""PyQalculate v2.1.2 - Plot Test Script"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyqalculate.calculator import Calculator

def main():
    calc = Calculator()
    calc.load_definitions()

    output_dir = 'test_results'
    os.makedirs(output_dir, exist_ok=True)

    print(f'# 绘图测试 - {datetime.now()}\n')

    tests = [
        ('二次函数', 'x^2', -5, 5),
        ('正弦函数', 'sin(x)', 0, 6.28),
        ('余弦函数', 'cos(x)', 0, 6.28),
    ]

    passed = 0
    for name, expr, xmin, xmax in tests:
        fname = f'{name}.png'.replace(' ', '_')
        path = os.path.join(output_dir, fname)
        try:
            result = calc.calculate_and_print(f'plot({expr}, {xmin}, {xmax}, "{path}")')
            if os.path.exists(path) and os.path.getsize(path) > 0:
                print(f'✓ {name} -> {fname} ({os.path.getsize(path)} bytes)')
                passed += 1
            else:
                print(f'✗ {name} failed - no file created')
        except Exception as e:
            print(f'✗ {name} failed - {e}')

    print(f'\n绘图测试: {passed}/{len(tests)} 通过')


if __name__ == '__main__':
    main()
