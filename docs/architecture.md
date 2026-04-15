# 프로젝트 아키텍처 문서

## 프로젝트 개요
- **프로젝트명**: Vision AI 기반 양/불량 검사 시스템
- **목적**: 생산 라인에서 카메라 4대를 이용해 외관·형상 불량을 자동 검출
- **버전**: MVP (데모)

---

## 시스템 구성도
```bash
[카메라 4대] → [CameraThread x4] → [CameraManager] → [MainWindow]
전/후/좌/우     멀티스레드 캡처      프레임 통합 관리    PyQt5 2x2 그리드
MJPG 압축 포맷                          QTimer 30fps 갱신
↓
[AI 검사 엔진] (Phase 4~5)
[검사 이력 DB] (Phase 6)
```

---

## 모듈별 역할

| 모듈 | 경로 | 역할 | 상태 |
|---|---|---|---|
| 카메라 스레드 | `app/camera/camera_thread.py` | 단일 카메라 캡처 스레드 | ✅ 완료 |
| 카메라 매니저 | `app/camera/camera_manager.py` | 4대 카메라 통합 관리 | ✅ 완료 |
| 메인 윈도우 | `app/gui/main_window.py` | PyQt5 2x2 카메라 뷰어 | ✅ 완료 |
| 앱 진입점 | `app/main.py` | 앱 초기화 및 실행 | ✅ 완료 |
| 검사 스레드 | `app/inspection/inspection_thread.py` | 별도 스레드 PatchCore 추론 | ✅ 완료 |
| 검사 엔진 | `app/inspection/inspector.py` | 모델 로드 및 추론, 결과 오버레이 | ✅ 완료 |
| 데이터베이스 | `app/database/` | SQLite 검사 이력 관리 | 🔜 Phase 6 |
| 유틸리티 | `app/utils/` | 공통 함수, 경로 처리 등 | 🔜 Phase 6 |

---

## 카메라 모듈 상세 구조
```bash
CameraManager
├── CameraThread (index=0, name="Front")
│   ├── _open_camera()   # MJPG 포맷으로 카메라 연결
│   ├── _capture_loop()  # 별도 스레드에서 프레임 지속 캡처
│   ├── get_frame()      # 최신 프레임 반환 (Lock 보호)
│   └── stop()           # 스레드 종료 및 자원 해제
├── CameraThread (index=1, name="Back")
├── CameraThread (index=2, name="Left")
└── CameraThread (index=3, name="Right")
```

### 카메라 설정값
| 항목 | 값 | 이유 |
|---|---|---|
| 포맷 | MJPG | USB 대역폭 절약 (YUY2 대비 약 1/10) |
| 해상도 | 640 x 480 | C920 기본 해상도 |
| FPS | 30 | 실시간 검사 기준 |
| 버퍼 크기 | 1 | 항상 최신 프레임 유지 |
| 초기화 방식 | 병렬 (threading) | 시작 시간 단축 |

---

## GUI 구조
```bash
MainWindow (QMainWindow)
├── QGridLayout (2x2)
│   ├── QLabel — Front 카메라
│   ├── QLabel — Back 카메라
│   ├── QLabel — Left 카메라
│   └── QLabel — Right 카메라
├── QStatusBar — 상태 메시지 표시
└── QTimer (33ms) — 프레임 갱신 루프
```

### OpenCV → PyQt5 이미지 변환 흐름
cap.read()          → numpy 배열 (BGR)
cv2.cvtColor()      → numpy 배열 (RGB)
QImage()            → QImage 객체
QPixmap.fromImage() → QPixmap 객체
QLabel.setPixmap()  → 화면 표시

---

## 개발 환경

| 항목 | 내용 |
|---|---|
| OS | Windows 10/11 |
| Python | 3.10 |
| 가상환경 | conda (vis-inspection) |
| GPU | NVIDIA GeForce RTX 5060 |
| CUDA | 12.8 |
| PyTorch | 2.11.0+cu128 |
| GUI 프레임워크 | PyQt5 |
| AI 프레임워크 | PyTorch + Ultralytics YOLOv8 |
| 패키징 | PyInstaller |
| 카메라 | Logitech HD Pro Webcam C920 x4 |

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
- 데이터 수집·전처리 파이프라인 (Phase 3)
- AI 모델 구조 상세 (Phase 4)
- 검사 엔진 판정 로직 (Phase 5)
- DB 스키마 (Phase 6)