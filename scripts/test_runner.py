"""PyQalculate Test Runner - runs all test suites and saves results.

Executes three test categories:
1. Unit tests (pytest)
2. Comparison tests (run_pyqalculate_tests.py)
3. Plot tests (run_plot_tests.py)

Results are saved to the tests/output/ directory.
"""
import os
import subprocess
import sys
from datetime import datetime


def run_command(cmd, output_file, label, cwd=None):
    """Run a command with LIVE streaming output, also saving to file."""
    import re
    print(f'  Running {label}...')
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # pytest writes to stderr
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=cwd or os.path.dirname(os.path.abspath(__file__)),
            bufsize=1,  # line-buffered
        )

        output_lines = []
        assert process.stdout is not None
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in process.stdout:
                print(line, end='')  # LIVE in terminal
                f.write(line)        # save to file
                output_lines.append(line)

        process.wait()
        combined = ''.join(output_lines)

        if process.returncode == 0:
            summary_match = re.search(r'(\d+ passed(?:,\s*\d+ \w+)*\s+in\s+[\d.]+s)', combined)
            if summary_match:
                print(f'    [PASS] {label} -- {summary_match.group(1)}')
            else:
                print(f'    [PASS] {label}')
        else:
            print(f'    [FAIL] {label} (exit code {process.returncode})')
            failed_tests = re.findall(r'FAILED\s+(\S+)', combined)
            for t in failed_tests:
                print(f'      FAILED {t}')
            print(f'    Full output: {output_file}')
        return process.returncode == 0
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

    # Determine paths
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(scripts_dir)
    output_dir = os.path.join(project_dir, 'tests', 'output')
    os.makedirs(output_dir, exist_ok=True)
    print(f'Results directory: {output_dir}')
    print()

    python = sys.executable
    results = {}

    # 1. Unit tests (pytest) — must run from project root to find tests/
    print('[1/3] Unit tests (pytest)...')
    results['unit'] = run_command(
        [python, '-m', 'pytest', 'tests/unit', '-v', '--tb=short'],
        os.path.join(output_dir, 'unit_tests.txt'),
        'Unit Tests',
        cwd=project_dir,
    )

    # 2. Comparison tests — runs from project root
    print('[2/3] Comparison tests...')
    results['comparison'] = run_command(
        [python, 'tests/comparison/run.py'],
        os.path.join(output_dir, 'comparison.txt'),
        'Comparison Tests',
        cwd=project_dir,
    )

    # 3. Plot tests — runs from project root
    print('[3/3] Plot tests...')
    subprocess.run([python, "-m", "pip", "install", "matplotlib", "-q"], check=False)
    results['plot'] = run_command(
        [python, 'tests/plot/run.py'],
        os.path.join(output_dir, 'plot_tests.txt'),
        'Plot Tests',
        cwd=project_dir,
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
