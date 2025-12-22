@echo off
setlocal enabledelayedexpansion

:: 1. Move to the script's directory (backend folder) regardless of where it's called from
cd /d "%~dp0"

echo [INFO] Starting Backend UI...
echo Current Directory: %CD%

:: 2. Check Anaconda Default Path
set "ANACONDA_PYTHON=C:\Users\user\anaconda3\python.exe"
if exist "!ANACONDA_PYTHON!" (
    echo [Check] Found Anaconda Python at default location.
    "!ANACONDA_PYTHON!" app_ui.py
    if !ERRORLEVEL! EQU 0 goto :EOF
)

:: 3. Manual Fallback
echo.
echo ========================================================
echo [ERROR] Could not auto-detect Anaconda Python.
echo Please locate your 'python.exe' file manually.
echo (e.g. C:\Users\user\anaconda3\python.exe)
echo ========================================================
echo.
set /p PYTHON_PATH="Drag and drop your python.exe here (or press Enter to try system default): "

:: Remove quotes
set PYTHON_PATH=%PYTHON_PATH:"=%

if "%PYTHON_PATH%"=="" (
    echo [INFO] No path provided. Trying system 'python'...
    python app_ui.py
) else (
    echo [INFO] Using: "%PYTHON_PATH%"
    "%PYTHON_PATH%" app_ui.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAIL] Script execution failed.
    pause
) else (
    echo.
    echo [SUCCESS] UI closed.
    pause
)
