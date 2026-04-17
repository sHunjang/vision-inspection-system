# Vision Inspection System

> 생산 라인 비전 AI 기반 양/불량 자동 검사 시스템 (MVP v1.0)

## 개요

4대의 카메라(전/후/좌/우)로 제품을 동시 촬영하여 외관 불량을 자동으로 검출하는 시스템입니다.
PatchCore 이상 탐지 모델을 사용하여 양품 데이터만으로 학습이 가능합니다.

## 주요 기능

- 4대 카메라 동시 실시간 영상 표시
- PatchCore 기반 이상 탐지 (양품 데이터만으로 학습)
- 4방향 동시 검사 및 통합 판정
- 데이터 수집 탭 (양품/불량 분류 저장, 연속 촬영)
- 검사 이력 SQLite DB 저장 및 조회
- 불량 카메라 빨간 테두리 강조 표시

## 기술 스택

- **언어**: Python 3.10
- **GUI**: PyQt5
- **AI**: PyTorch + Anomalib (PatchCore)
- **영상처리**: OpenCV
- **DB**: SQLite
- **배포**: 런처 스크립트 (install.bat / run.bat)

## 설치 및 실행

### 개발 환경

```bash
conda create -n vis-inspection python=3.10 -y
conda activate vis-inspection
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python -m app.main
```

### 배포 환경
1. install.bat 실행 (최초 1회)
2. run.bat 실행

## 모델 학습

```bash
# MVTec 데이터로 테스트 학습
python scripts/train_patchcore.py

# 실제 수집 데이터로 학습
python scripts/prepare_dataset.py T68-MCR
python scripts/train_patchcore.py T68-MCR
```

## 프로젝트 문서

- [아키텍처 문서](docs/architecture.md)
- [기술 선택 근거](docs/tech-decisions.md)
- [트러블슈팅](docs/troubleshooting.md)
- [회고록](docs/retrospective.md)