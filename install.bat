@echo off
chcp 65001 > nul
echo ================================================
echo  Vision Inspection System - 설치 프로그램
echo ================================================
echo.

REM Miniconda 설치 여부 확인
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] conda가 설치되어 있지 않습니다.
    echo.
    echo Miniconda를 먼저 설치해주세요:
    echo https://docs.conda.io/en/latest/miniconda.html
    echo.
    pause
    exit /b 1
)

echo [1/3] conda 환경 생성 중... (Python 3.10)
call conda create -n vis-inspection python=3.10 -y
if %errorlevel% neq 0 (
    echo [오류] conda 환경 생성 실패
    pause
    exit /b 1
)

echo.
echo [2/3] PyTorch CPU 버전 설치 중...
call conda activate vis-inspection
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
if %errorlevel% neq 0 (
    echo [오류] PyTorch 설치 실패
    pause
    exit /b 1
)

echo.
echo [3/3] 필수 라이브러리 설치 중...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [오류] 라이브러리 설치 실패
    pause
    exit /b 1
)

echo.
echo ================================================
echo  설치 완료!
echo  run.bat 을 실행하여 프로그램을 시작하세요.
echo ================================================
pause