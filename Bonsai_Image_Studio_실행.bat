@echo off
chcp 65001 > nul
title Bonsai Image Studio 실행기
echo ==========================================================
echo   Bonsai Image Studio 서버 및 화면을 기동하는 중입니다...
echo   (최초 실행 시 모델 로드에 약 1분~1분 30초 정도 소요됩니다.)
echo ==========================================================
echo.

:: 1. 백그라운드로 uvicorn API 서버 실행 (C:\tools\image 디렉토리에서)
echo [1/2] 로컬 이미지 생성 AI 백엔드 서버를 켜고 있습니다...
start /min "Bonsai Backend Server" powershell -Command "cd C:\tools\image; powershell -ExecutionPolicy Bypass -File .\scripts\serve.ps1 -BackendOnly"

:: 2. 5초 대기 후 웹 브라우저 실행
echo [2/2] 5초 후에 이미지 생성 웹페이지를 브라우저로 엽니다...
timeout /t 5 > nul

:: 현재 배치 파일이 있는 경로의 image_generator.html 파일을 기본 브라우저로 열기
start "" "%~dp0image_generator.html"

echo.
echo ==========================================================
echo   ✔ 모든 실행 과정이 시작되었습니다!
echo   이 검은색 창(배치 파일)은 닫으셔도 괜찮습니다.
echo   단, 최소화되어 실행 중인 백그라운드 파워쉘 창은 끄지 말아주세요.
echo ==========================================================
timeout /t 7
