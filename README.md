# Vision Inspection System

> 생산 라인 비전 AI 기반 양/불량 자동 검사 시스템 (MVP)

## 개요

4대의 카메라(전/후/좌/우)로 제품을 촬영하여 외관 및 형상 불량을 자동으로 검출하는 시스템입니다.

## 기술 스택

- **언어**: Python 3.10
- **GUI**: PyQt5
- **AI**: PyTorch + YOLOv8
- **패키징**: PyInstaller

## 개발 환경 설정

```bash
# 가상환경 생성
conda create -n vis-inspection python=3.10 -y
conda activate vis-inspection

# 라이브러리 설치
pip install -r requirements.txt
```

## 프로젝트 구조
```bash
app/          # 핵심 애플리케이션 코드
data/         # 학습 데이터
models/       # AI 모델 파일
docs/         # 프로젝트 문서
```

## 문서

- [아키텍처 문서](docs/architecture.md)
- [기술 선택 근거](docs/tech-decisions.md)
- [트러블슈팅](docs/troubleshooting.md)