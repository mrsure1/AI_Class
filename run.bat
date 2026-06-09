@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ===================================================
echo   인스타그램 AI 오토 스튜디오 시작 스크립트
echo ===================================================
echo.

:: 1. 파이썬 설치 여부 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [오류] 시스템에 Python이 설치되어 있지 않거나 PATH 설정이 안 되어 있습니다.
    echo Python 3.9 이상 버전을 설치하신 후 다시 실행해주세요.
    pause
    exit /b 1
)

:: 2. 가상환경 설정
if not exist .venv (
    echo [.venv 가상환경이 존재하지 않습니다. 새로 생성합니다...]
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [오류] 가상환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
)

:: 3. 가상환경 활성화 및 라이브러리 설치
echo [가상환경 활성화 및 라이브러리 설치 확인 중...]
call .venv\Scripts\activate.bat

echo [pip 업그레이드 중...]
python -m pip install --upgrade pip >nul 2>&1

echo [requirements.txt 의존성 패키지 설치 중...]
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [오류] 라이브러리 설치에 실패했습니다. requirements.txt를 확인해주세요.
    pause
    exit /b 1
)

:: 4. 환경 변수 파일 검사
if not exist .env (
    echo.
    echo ===================================================
    echo   [경고] '.env' 설정 파일이 존재하지 않습니다.
    echo   '.env.template'을 기반으로 '.env' 파일을 복사합니다.
    echo   반드시 새로 만들어진 '.env' 파일에 API Key와 계정 정보를 입력해주세요.
    echo ===================================================
    copy .env.template .env >nul
    
    :: 메모장으로 .env 파일 열어주기
    start notepad.exe .env
    echo.
    echo [.env 파일을 메모장으로 열었습니다. 설정을 마치고 저장한 후 이 창으로 돌아와 아무 키나 눌러주세요.]
    pause
)

:: 5. 브라우저로 대시보드 자동 열기
echo [웹 브라우저를 통해 대시보드를 엽니다...]
start http://127.0.0.1:8000

:: 6. 대시보드 웹 서버 실행
echo [FastAPI 웹 서버를 가동합니다...]
python dashboard.py

pause
