# 프로젝트 회고록 (Retrospective)

> 각 Phase 완료 후 배운 점, 어려웠던 점, 다음에 개선할 점을 기록합니다.

---

## Phase 1 — 환경 구축 및 프로젝트 기반 세팅

### 이번 Phase에서 한 일
- GitHub 저장소 생성 및 Git Flow 브랜치 전략 수립 (`main` / `develop` / `feature/*`)
- conda 가상환경 구성 (Python 3.10, vis-inspection)
- 핵심 라이브러리 설치 (PyQt5, OpenCV, PyTorch, YOLOv8, PyInstaller)
- GPU 환경 확인 (RTX 5060 / CUDA 12.8 / PyTorch 2.x)
- 프로젝트 폴더 구조 설계 및 생성
- 프로젝트 문서 3종 초안 작성 (architecture, tech-decisions, troubleshooting)

### 배운 점
- Git Flow 브랜치 전략의 흐름: `feature/*` → `develop` → (추후) `main`
- Conventional Commits 커밋 메시지 형식 (`feat:`, `chore:`, `docs:` 등)
- 빈 폴더를 Git으로 추적하려면 `.gitkeep` 파일이 필요하다

---

## Phase 2 — 카메라 모듈 개발

### 이번 Phase에서 한 일
- 카메라 인덱스 탐색 스크립트 작성 (`scripts/check_cameras.py`)
- 단일 카메라 동작 확인 스크립트 작성 (`scripts/test_single_camera.py`)
- 멀티스레드 카메라 캡처 모듈 구현 (`app/camera/camera_thread.py`)
- 카메라 통합 매니저 구현 (`app/camera/camera_manager.py`)
- PyQt5 메인 윈도우 구현 — 2x2 그리드 실시간 카메라 뷰어 (`app/gui/main_window.py`)
- USB 대역폭 문제 해결 (MJPG 포맷 적용)
- 카메라 병렬 초기화 구현으로 시작 시간 단축

### 배운 점
- 스레드(Thread)의 개념과 필요성 — 카메라 4대를 동시에 처리하려면 멀티스레드가 필수
- Lock의 역할 — 여러 스레드가 동시에 같은 데이터에 접근할 때 충돌 방지
- OpenCV → PyQt5 이미지 변환 흐름 (BGR → RGB → QImage → QPixmap)
- QTimer를 이용한 GUI 주기적 갱신 방식 (33ms = 약 30fps)
- USB 대역폭 개념 — 카메라 포맷(YUY2 vs MJPG)이 전송량에 미치는 영향
- daemon 스레드 — 메인 프로그램 종료 시 자동으로 함께 종료되는 스레드

---

## 전체 프로젝트 회고

> 모든 Phase 완료 후 작성 예정

### 프로젝트를 통해 성장한 점

### 실제 현장 적용 시 보완할 점

### 다음 버전(v2.0)에서 추가 예정 기능