@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title PyQalculate v2.1.2
cd /d "%~dp0"

echo.
echo ========================================
echo   PyQalculate v2.1.2 - Python Calculator
echo ========================================
echo.

:: Check Python exists
echo [1/2] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo Python is not installed!
    echo Please install Python 3.8 or later.
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo Found %%i

:: Check virtual environment
echo [2/2] Checking virtual environment...
if not exist ".venv" (
    echo Creating virtual environment...
    echo.

    echo Creating .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create .venv!
        pause
        exit /b 1
    )

    echo Installing dependencies...
    call .venv\Scripts\activate.bat
    pip install -e . -q
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )

    echo Installing extras (matplotlib, sympy, gmpy2)...
    pip install matplotlib sympy gmpy2 -q

    echo.
    echo Setup complete!
) else (
    echo Virtual environment found.
    call .venv\Scripts\activate.bat
)

echo.

:MENU
echo ========================================
echo           Main Menu
echo ========================================
echo   [1] CLI Mode     - Command line calculator
echo   [2] GUI Mode     - Graphical calculator
echo   [3] Run Tests    - Run all test suites
echo   [4] Run Demo     - Run all demos
echo   [0] Exit
echo ========================================
echo.

set /p choice=Select [0-4]: 

if "%choice%"=="1" goto CLI
if "%choice%"=="2" goto GUI
if "%choice%"=="3" goto TEST
if "%choice%"=="4" goto DEMO
if "%choice%"=="0" goto EXIT

echo Invalid choice!
echo.
goto MENU

:CLI
echo.
echo Starting CLI Mode...
echo Type 'quit' to exit the calculator.
echo.
python cli.py
echo.
pause
goto MENU

:GUI
echo.
echo Starting GUI Mode...
python gui.py
echo.
pause
goto MENU

:TEST
echo.
python test_runner.py
echo.
pause
goto MENU

:DEMO
echo.
python demo.py
echo.
pause
goto MENU

:EXIT
echo.
echo Goodbye!
echo.
pause
endlocal
exit /b 0
