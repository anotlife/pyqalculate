@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title PyQalculate v2.1.2
cd /d "%~dp0"

set "VENV_DIR=..\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PY_CMD="

echo.
echo ========================================
echo   PyQalculate v2.1.2 - Python Calculator
echo ========================================
echo.

:: Check Python exists
echo [1/2] Checking Python...
call :FIND_PYTHON
if not defined PY_CMD (
    echo.
    echo Python 3.10 or later is not installed or not on PATH!
    echo Please install Python 3.10+.
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('%PY_CMD% --version 2^>^&1') do echo Found %%i

:: Check virtual environment
echo [2/2] Checking virtual environment...
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Existing virtual environment uses an unsupported Python version.
        echo Recreating virtual environment...
        rmdir /s /q "%VENV_DIR%"
    )
)

if not exist "%VENV_PY%" (
    echo Creating virtual environment...
    echo.

    echo Creating .venv...
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create .venv!
        pause
        exit /b 1
    )

    call :INSTALL_DEPS || goto SETUP_FAILED

    echo.
    echo Setup complete!
) else (
    echo Virtual environment found.
    call :CHECK_DEPS || goto SETUP_FAILED
)

call "%VENV_DIR%\Scripts\activate.bat"
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
"%VENV_PY%" -m pyqalc
echo.
pause
goto MENU

:GUI
echo.
echo Starting GUI Mode...
"%VENV_PY%" -m pyqalculate_gui
echo.
pause
goto MENU

:TEST
echo.
"%VENV_PY%" test_runner.py
echo.
pause
goto MENU

:DEMO
echo.
"%VENV_PY%" demo.py
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

:CHECK_DEPS
echo Verifying installed packages...
"%VENV_PY%" -c "import pyqalculate, pyqalc, pyqalculate_gui, sympy, gmpy2, matplotlib" >nul 2>&1
if errorlevel 1 (
    echo Virtual environment exists, but dependencies are incomplete.
    echo Repairing virtual environment...
    call :INSTALL_DEPS
    if errorlevel 1 exit /b 1
) else (
    echo Dependencies ready.
)
exit /b 0

:INSTALL_DEPS
echo Installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel -q
if errorlevel 1 (
    echo Failed to upgrade pip/setuptools/wheel!
    exit /b 1
)

"%VENV_PY%" -m pip install -e .. -q
if errorlevel 1 (
    echo Failed to install project dependencies!
    exit /b 1
)

echo Installing extras: matplotlib, sympy, gmpy2...
"%VENV_PY%" -m pip install matplotlib sympy gmpy2 -q
if errorlevel 1 (
    echo Failed to install optional dependencies!
    exit /b 1
)
exit /b 0

:SETUP_FAILED
echo.
echo Setup failed. Please check the error above and run this launcher again.
pause
endlocal
exit /b 1

:FIND_PYTHON
call :TRY_PY "py -3.12"
if defined PY_CMD exit /b 0
call :TRY_PY "py -3.13"
if defined PY_CMD exit /b 0
call :TRY_PY "py -3.14"
if defined PY_CMD exit /b 0
call :TRY_PY "py -3"
if defined PY_CMD exit /b 0
call :TRY_PY "python"
exit /b 0

:TRY_PY
%~1 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 set "PY_CMD=%~1"
exit /b 0
