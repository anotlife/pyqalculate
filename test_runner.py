"""PyQalculate Test Runner - runs all test suites and saves results.

Executes three test categories:
1. Unit tests (pytest)
2. Comparison tests (run_pyqalculate_tests.py)
3. Plot tests (run_plot_tests.py)

Results are saved to the test_results/ directory.
"""
import os
import subprocess
import sys
from datetime import datetime


def run_command(cmd, output_file, label):
    """Run a command and capture output to file."""
    print(f'  Running {label}...')
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write('\n--- STDERR ---\n')
                f.write(result.stderr)
        if result.returncode == 0:
            print(f'    [PASS] {label}')
        else:
            print(f'    [FAIL] {label} (exit code {result.returncode})')
            print(f'           See {output_file}')
        return result.returncode == 0
    except Exception as e:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f'ERROR: {e}\n')
        print(f'    [ERROR] {label} - {e}')
        return False


def main():
    """Run all tests and save results."""
    print('=' * 50)
    print('  PyQalculate Test Runner')
    print('=' * 50)
    print()

    output_dir = 'test_results'
    os.makedirs(output_dir, exist_ok=True)
    print(f'Results directory: {output_dir}/')
    print()

    python = sys.executable
    results = {}

    # 1. Unit tests (pytest)
    print('[1/3] Unit tests (pytest)...')
    results['unit'] = run_command(
        [python, '-m', 'pytest', 'tests', '-v', '--tb=short'],
        os.path.join(output_dir, 'unit_tests.txt'),
        'Unit Tests',
    )

    # 2. Comparison tests
    print('[2/3] Comparison tests...')
    results['comparison'] = run_command(
        [python, 'run_pyqalculate_tests.py'],
        os.path.join(output_dir, 'comparison.txt'),
        'Comparison Tests',
    )

    # 3. Plot tests
    print('[3/3] Plot tests...')
    results['plot'] = run_command(
        [python, 'run_plot_tests.py'],
        os.path.join(output_dir, 'plot_tests.txt'),
        'Plot Tests',
    )

    # Summary
    print()
    print('=' * 50)
    print('  Summary')
    print('=' * 50)
    for name, passed in results.items():
        status = 'PASS' if passed else 'FAIL'
        print(f'  {name:15s} [{status}]')

    all_passed = all(results.values())
    print()
    if all_passed:
        print('All tests passed!')
    else:
        print('Some tests failed. Check test_results/ for details.')

    print(f'\nResults saved to: {output_dir}/')
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
