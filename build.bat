@echo off
echo ================================
echo Vision Inspection System 빌드
echo ================================

echo.
echo [1/4] PyInstaller 빌드...
pyinstaller vision_inspection.spec --clean
if %errorlevel% neq 0 (
    echo [오류] 빌드 실패
    pause
    exit /b 1
)

echo.
echo [2/4] 배포용 모델 파일 추출...
python scripts/prepare_model_for_deploy.py

echo.
echo [3/4] 모델 파일 복사...
xcopy /E /I /Y deploy_models dist\VisionInspection\models

echo.
echo [4/4] 데이터 폴더 생성...
if not exist dist\VisionInspection\data\raw mkdir dist\VisionInspection\data\raw
if not exist dist\VisionInspection\data\custom mkdir dist\VisionInspection\data\custom

echo.
echo ================================
echo ✅ 빌드 완료!
echo ================================
pause