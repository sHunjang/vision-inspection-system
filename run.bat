@echo off
chcp 65001 > nul

REM conda 초기화
call conda activate vis-inspection 2>nul
if %errorlevel% neq 0 (
    echo [오류] vis-inspection 환경을 찾을 수 없습니다.
    echo install.bat 을 먼저 실행해주세요.
    pause
    exit /b 1
)

REM 앱 실행
cd /d %~dp0
python -m app.main

REM 비정상 종료 시 오류 메시지 표시
if %errorlevel% neq 0 (
    echo.
    echo [오류] 앱이 비정상 종료되었습니다.
    echo 오류 내용을 캡처하여 담당자에게 문의하세요.
    pause
)