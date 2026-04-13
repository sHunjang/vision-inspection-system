# 프로젝트 아키텍처 문서

## 프로젝트 개요
- **프로젝트명**: Vision AI 기반 양/불량 검사 시스템
- **목적**: 생산 라인에서 카메라 4대를 이용해 외관·형상 불량을 자동 검출
- **버전**: MVP (데모)
- **최초 작성일**: 2025-xx-xx

---

## 시스템 구성도
```bash
[카메라 4대] → [캡처 모듈] → [AI 검사 엔진] → [판정 결과]
전/후/좌/우      멀티스레드      YOLOv8           양품/불량
↓
[GUI 대시보드]
[검사 이력 DB]
```

---

## 모듈별 역할

| 모듈 | 경로 | 역할 |
|---|---|---|
| 카메라 모듈 | `app/camera/` | 4채널 카메라 연결 및 프레임 캡처 |
| 검사 엔진 | `app/inspection/` | AI 모델 추론 및 불량 판정 |
| GUI | `app/gui/` | PyQt5 기반 사용자 화면 |
| 데이터베이스 | `app/database/` | SQLite 검사 이력 관리 |
| 유틸리티 | `app/utils/` | 공통 함수, 경로 처리 등 |

---

## 개발 환경

| 항목 | 내용 |
|---|---|
| OS | Windows 10/11 |
| Python | 3.10 |
| 가상환경 | conda (vis-inspection) |
| GPU | NVIDIA GeForce RTX 5060 |
| CUDA | 12.8 |
| GUI 프레임워크 | PyQt5 |
| AI 프레임워크 | PyTorch 2.x + Ultralytics YOLOv8 |
| 패키징 | PyInstaller |

---

## 브랜치 전략 (Git Flow)

| 브랜치 | 용도 |
|---|---|
| `main` | 최종 배포 버전 |
| `develop` | 개발 통합 브랜치 |
| `feature/*` | 기능 단위 개발 |
| `release/*` | 배포 준비 |
| `hotfix/*` | 긴급 수정 |

---

## 향후 업데이트 예정
- 카메라 모듈 상세 설계 (Phase 2)
- AI 모델 구조 상세 (Phase 4)
- DB 스키마 (Phase 6)