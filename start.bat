@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title PyQalculate v3.0.0
cd /d "%~dp0"

echo.
echo ========================================
echo   PyQalculate v3.0.0 - Python Calculator
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
:: Check if venv exists AND is valid
set VENV_VALID=0
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import sys; print('ok')" >nul 2>&1
    if not errorlevel 1 set VENV_VALID=1
)

if %VENV_VALID%==0 (
    :: Venv missing or broken - recreate
    if exist ".venv" (
        echo Virtual environment is incomplete. Recreating...
        rmdir /s /q ".venv"
    )
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Please ensure Python is installed and accessible.
        pause
        exit /b 1
    )
    
    echo Installing dependencies...
    call .venv\Scripts\activate.bat
    pip install -e . -q
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        echo Retrying...
        pip install -e . -q
    )
    
    echo Installing optional dependencies...
    pip install matplotlib sympy gmpy2 -q
    
    echo Virtual environment created successfully.
) else (
    echo Virtual environment found.
    call .venv\Scripts\activate.bat
    
    :: Verify key packages are installed
    python -c "import sympy" >nul 2>&1
    if errorlevel 1 (
        echo Some dependencies are missing. Installing...
        pip install -e . -q
    )
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
.venv\Scripts\python.exe scripts\cli.py
echo.
pause
goto MENU

:GUI
echo.
echo Starting GUI Mode...
.venv\Scripts\python.exe scripts\gui.py
echo.
pause
goto MENU

:TEST
echo.
.venv\Scripts\python.exe scripts\test_runner.py
echo.
pause
goto MENU

:DEMO
echo.
.venv\Scripts\python.exe scripts\demo.py
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
