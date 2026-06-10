@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Instagram AI Auto Studio Launcher
echo ===================================================
echo.

:: 1. Check Python Installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ and try again.
    echo.
    pause
    exit /b 1
)

:: 2. Create Virtual Environment
if not exist .venv (
    echo [.venv virtual environment not found. Creating a new one...]
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Activate Virtual Environment & Install requirements
echo [Activating virtual environment...]
call .venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [Upgrading pip...]
python -m pip install --upgrade pip >nul 2>&1

echo [Installing requirements...]
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. Check configuration file
if not exist .env (
    echo.
    echo ===================================================
    echo   [WARNING] '.env' configuration file not found.
    echo   Copying '.env.template' to '.env'...
    echo   Please fill in your API Key and credentials in '.env'.
    echo ===================================================
    copy .env.template .env >nul
    
    start notepad.exe .env
    echo.
    echo [.env file opened in Notepad. Please edit, save, and press any key to continue...]
    pause
)

:: 5. Launch Web Server
echo [Starting FastAPI Web Server...]
python dashboard.py
if %errorlevel% neq 0 (
    echo [ERROR] Web server crashed.
    pause
    exit /b 1
)

pause
