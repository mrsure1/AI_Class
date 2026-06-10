@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Instagram AI Auto Studio Launcher
echo ===================================================
echo.

:: 1. 파이썬 설치 여부 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않거나 PATH 환경변수에 등록되지 않았습니다.
    echo Python 3.9 이상을 설치하고 다시 실행해 주세요.
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    pause
    exit /b 1
)

:: 2. 가상환경 생성
if not exist .venv (
    echo [.venv 가상환경이 없습니다. 새로 생성합니다...]
    echo [.venv virtual environment not found. Creating a new one...]
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [오류] 가상환경 생성에 실패했습니다.
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. 가상환경 활성화 및 패키지 설치
echo [가상환경 활성화 및 패키지 설치 확인 중...]
echo [Activating virtual environment & Installing dependencies...]
call .venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [오류] 가상환경 활성화 실패
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [pip 업그레이드 중...]
python -m pip install --upgrade pip >nul 2>&1

echo [requirements.txt 의존성 패키지 설치 중...]
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [오류] 라이브러리 설치 실패. requirements.txt를 확인해 주세요.
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. 환경 변수 파일 검사
if not exist .env (
    echo.
    echo ===================================================
    echo   [경고] '.env' 설정 파일이 존재하지 않습니다.
    echo   '.env.template'을 기반으로 '.env' 파일을 복사합니다.
    echo   메모장으로 열린 '.env' 파일에 API Key와 인스타 계정을 기입해주세요.
    echo ===================================================
    copy .env.template .env >nul
    
    start notepad.exe .env
    echo.
    echo [.env 파일을 작성하고 저장한 뒤, 아무 키나 누르면 대시보드가 시작됩니다.]
    pause
)

:: 5. 브라우저로 대시보드 자동 열기
echo [웹 브라우저로 대시보드를 엽니다...]
start http://127.0.0.1:8000

:: 6. 대시보드 웹 서버 실행
echo [FastAPI 웹 서버를 가동합니다...]
python dashboard.py
if %errorlevel% neq 0 (
    echo [오류] 웹 서버 실행 중 오류가 발생했습니다.
    echo [ERROR] Web server crashed.
    pause
    exit /b 1
)

pause
