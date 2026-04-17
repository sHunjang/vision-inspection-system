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

## Phase 3 — 데이터 파이프라인

### 이번 Phase에서 한 일
- 이미지 캡처 저장 유틸리티 구현 (`app/utils/image_saver.py`)
- GUI에 제품 선택 드롭다운 및 캡처 버튼 추가
- 스페이스바로 4대 카메라 동시 캡처 저장 기능 구현
- MVTec AD 데이터셋 다운로드 및 구조 확인 (screw 카테고리)
- 오픈 데이터셋으로 전체 파이프라인 검증 방향 결정

### 배운 점
- 제조 현장에서 불량 데이터가 희소한 현실적 문제 인식
- 이상 탐지(Anomaly Detection) 방식이 양품 데이터만으로
  학습 가능한 이유 이해
- YOLOv8(부품 탐지) + PatchCore(외관 이상) 혼합 전략 수립
- 데이터 저장 시 제품·카메라·날짜별 폴더 구조의 중요성
- Git에서 대용량 파일(데이터셋, 모델)은 .gitignore로 제외해야 함

---

## Phase 4 — AI 모델 개발

### 이번 Phase에서 한 일
- Anomalib 2.3.3 설치 및 동작 확인
- PatchCore 학습 스크립트 작성 (`scripts/train_patchcore.py`)
- MVTec screw 데이터셋으로 PatchCore 학습 완료
- 학습 결과 평가 (image_AUROC: 0.9656 / pixel_AUROC: 0.9895)
- Anomalib 2.x API 변경 사항 트러블슈팅

### 배운 점
- PatchCore 동작 원리 — 양품 패치 특징을 메모리 뱅크에 저장하고
  새 이미지와 거리를 계산하는 방식
- AUROC 지표의 의미 — 1.0에 가까울수록 양/불량 구분 능력 우수
- pixel_F1Score가 낮아도 image_AUROC가 높으면 현장 적용 가능
- Anomalib 2.x에서 MVTec → MVTecAD, image_size 파라미터 제거 등
  API 변경 사항
- PatchCore는 1 에폭만으로 학습 완료 (메모리 뱅크 구축 방식이므로)

---

## Phase 5 — 검사 엔진

### 이번 Phase에서 한 일
- PatchCore 추론 엔진 구현 (`app/inspection/inspector.py`)
- 별도 추론 스레드 구현 (`app/inspection/inspection_thread.py`)
- PyQt5 GUI에 실시간 검사 결과 연동 (`app/gui/main_window.py`)
- 검사 ON/OFF 토글, 검사 카메라 선택 기능 추가

### 배운 점
- Anomalib 2.x의 `forward()` 는 정규화된 값만 반환 →
  `model.model()` 직접 호출로 raw distance 획득
- GUI 스레드와 추론 스레드 분리의 중요성
- threading.Event를 이용한 프레임 전달 방식

---

## Phase 6 — GUI 완성

### 이번 Phase에서 한 일
- SQLite 기반 검사 이력 DB 구현 (`app/database/db_manager.py`)
- 실시간 검사 탭 위젯 분리 (`app/gui/inspection_tab.py`)
- 검사 이력 조회 탭 구현 (`app/gui/history_tab.py`)
- 탭 구조 메인 윈도우로 전체 UI 재구성 (`app/gui/main_window.py`)
- 검사 결과 실시간 DB 저장 및 통계 표시

### 배운 점
- SQLite의 장점 — 별도 서버 없이 파일 하나로 DB 운용 가능
- PyQt5 QTabWidget으로 화면을 논리적으로 분리하는 방법
- os.makedirs vs os.mkdir 차이 (exist_ok 파라미터 지원 여부)
- GUI 스레드와 추론 스레드 분리 구조가 실제로 효과적임을 확인
- 데이터 수집 전용 탭 구현 (`app/gui/collection_tab.py`)
  - F1(양품) / F2(불량) 단축키 캡처
  - 불량 유형별 분류 저장
  - 연속 촬영 모드 (간격 설정 가능)
  - 수집 진행 현황 프로그레스바
  
---

## Phase 7 — 패키징 및 배포

### 이번 Phase에서 한 일
- PyInstaller 패키징 시도 → CUDA DLL 문제로 런처 방식으로 전환
- install.bat / run.bat / update_model.bat 런처 스크립트 작성
- 배포 패키지 자동 생성 스크립트 작성 (`scripts/build_deploy_package.py`)
- 모델 파일 추출 스크립트 작성 (`scripts/prepare_model_for_deploy.py`)
- 프로젝트 구조 정리 (불필요한 폴더/파일 제거)
- 4대 카메라 동시 검사 구조로 개선
- 통합 판정 패널 및 카메라별 테두리 강조 UI 추가
- main 브랜치 병합 및 v1.0.0, v1.0.1 태그 생성

---

## 전체 프로젝트 회고

> 모든 Phase 완료 후 작성 예정

### 프로젝트를 통해 성장한 점

### 실제 현장 적용 시 보완할 점

### 다음 버전(v2.0)에서 추가 예정 기능