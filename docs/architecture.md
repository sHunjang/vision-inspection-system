# 프로젝트 아키텍처 문서

## 프로젝트 개요
- **프로젝트명**: Vision AI 기반 양/불량 검사 시스템
- **목적**: 생산 라인에서 카메라 4대를 이용해 외관 불량을 자동 검출
- **버전**: MVP v1.0
- **배포 방식**: 런처 스크립트 (install.bat / run.bat)

---

## 시스템 구성도
```bash
[카메라 4대]  →  [CameraThread x4]  →  [CameraManager]
전/후/좌/우      멀티스레드 캡처         프레임 통합 관리
MJPG 압축                                    ↓
[MainWindow]
PyQt5 탭 구조
QTimer 33ms 갱신
↓
┌──────────────┼──────────────┐
[검사 탭]      [수집 탭]      [이력 탭]
↓
[InspectionThread x4]
4대 동시 PatchCore 추론
↓
[통합 판정 결과]
하나라도 DEFECT → 최종 DEFECT
↓
[DBManager]
SQLite 검사 이력 저장
```

---

## 모듈별 역할

| 모듈 | 경로 | 역할 | 상태 |
|---|---|---|---|
| 카메라 스레드 | `app/camera/camera_thread.py` | 단일 카메라 캡처 스레드 | ✅ 완료 |
| 카메라 매니저 | `app/camera/camera_manager.py` | 4대 카메라 병렬 초기화 및 통합 관리 | ✅ 완료 |
| 메인 윈도우 | `app/gui/main_window.py` | PyQt5 탭 구조 메인 윈도우 | ✅ 완료 |
| 검사 탭 | `app/gui/inspection_tab.py` | 4대 동시 검사 및 통합 판정 UI | ✅ 완료 |
| 수집 탭 | `app/gui/collection_tab.py` | 양품/불량 데이터 수집 UI | ✅ 완료 |
| 이력 탭 | `app/gui/history_tab.py` | 검사 이력 조회 및 통계 | ✅ 완료 |
| 검사 스레드 | `app/inspection/inspection_thread.py` | 4대 카메라 동시 PatchCore 추론 | ✅ 완료 |
| 검사 엔진 | `app/inspection/inspector.py` | 모델 로드, 추론, 결과 오버레이 | ✅ 완료 |
| DB 매니저 | `app/database/db_manager.py` | SQLite 검사 이력 저장·조회 | ✅ 완료 |
| 이미지 저장 | `app/utils/image_saver.py` | 제품·카메라·라벨별 이미지 저장 | ✅ 완료 |
| 경로 유틸 | `app/utils/path_utils.py` | 개발/배포 환경 경로 처리 | ✅ 완료 |
| 앱 진입점 | `app/main.py` | 앱 초기화 및 실행 | ✅ 완료 |

---

## 카메라 모듈 상세 구조
```bash
CameraManager (병렬 초기화)
├── CameraThread (index=0, name="Front")
│   ├── _open_camera()    # MJPG 포맷으로 카메라 연결
│   ├── _capture_loop()   # 별도 스레드에서 프레임 지속 캡처
│   ├── get_frame()       # 최신 프레임 반환 (Lock 보호)
│   └── stop()            # 스레드 종료 및 자원 해제
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

## AI 검사 엔진 구조
```bash
[카메라 프레임 4장]
↓
[InspectionThread]
├── CameraInspectionThread (Front) → PatchCore 추론
├── CameraInspectionThread (Back)  → PatchCore 추론
├── CameraInspectionThread (Left)  → PatchCore 추론
└── CameraInspectionThread (Right) → PatchCore 추론
↓
[get_final_result()]
├── 4방향 중 하나라도 DEFECT → 최종 DEFECT
└── 4방향 모두 OK            → 최종 OK
```

### PatchCore 추론 흐름

```bash
OpenCV 프레임 (BGR)
↓
BGR → RGB 변환
↓
Resize (256x256) + Normalize (ImageNet 기준)
↓
model.model() 직접 호출 (raw distance 획득)
↓
raw_score vs image_threshold (30.48) 비교
↓
양품 (OK) / 불량 (DEFECT) 판정
```

### 모델 정보 (MVTec screw 기준)

| 항목 | 값 |
|---|---|
| 모델 | PatchCore |
| 백본 | wide_resnet50_2 |
| 추출 레이어 | layer2, layer3 |
| image_AUROC | 0.9656 |
| pixel_AUROC | 0.9895 |
| 임계값 | 30.4784 |

---

## GUI 구조
```bash
MainWindow (QMainWindow)
├── QTabWidget
│   ├── 탭 1: InspectionTab    — 실시간 4대 동시 검사
│   │   ├── QGridLayout (2x2)  — 카메라 영상
│   │   └── 통합 판정 패널      — OK/DEFECT 크게 표시
│   ├── 탭 2: CollectionTab    — 데이터 수집
│   │   ├── 카메라 프리뷰
│   │   ├── 양품/불량 캡처 버튼
│   │   └── 수집 진행 현황
│   └── 탭 3: HistoryTab       — 검사 이력 조회
│       ├── 필터 (제품/결과)
│       ├── 이력 테이블
│       └── 불량률 통계
└── QStatusBar
```

### OpenCV → PyQt5 이미지 변환 흐름
```bash
cap.read()           → numpy 배열 (BGR)
cv2.cvtColor()       → numpy 배열 (RGB)
QImage()             → QImage 객체
QPixmap.fromImage()  → QPixmap 객체
QLabel.setPixmap()   → 화면 표시
```

---

## 데이터 구조
```bash
data/
├── raw/                          # 수집한 원본 이미지
│   └── {제품명}/
│       ├── good/{카메라}/{날짜}/  # 양품
│       └── defect/{불량유형}/{카메라}/{날짜}/  # 불량
├── custom/                       # 학습용 데이터셋 (MVTec 형식)
│   └── {제품명}/
│       ├── train/good/
│       └── test/{good, 불량유형}/
├── mvtec/                        # MVTec AD 오픈 데이터셋
└── inspection.db                 # 검사 이력 SQLite DB
```

### DB 스키마 (inspection_log)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | INTEGER | 자동 증가 기본키 |
| timestamp | TEXT | 검사 일시 |
| product | TEXT | 제품 종류 |
| camera | TEXT | 카메라 이름 |
| result | TEXT | OK / DEFECT |
| score | REAL | 이상 점수 |
| threshold | REAL | 판정 임계값 |

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
| AI 프레임워크 | PyTorch + Anomalib (PatchCore) |
| 영상처리 | OpenCV 4.x |
| 데이터베이스 | SQLite3 |
| 배포 방식 | 런처 스크립트 (install.bat / run.bat) |
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

## v2.0 개선 예정

- OCR 기반 라벨 텍스트 정확성 검사 (PaddleOCR 연동)
- YOLOv8 부품 존재 여부 탐지 (볼트, 라벨 탐지)
- 실제 T68-MCR 데이터 수집 및 재학습
- 10종 제품별 개별 모델 관리
- 검사 결과 리포트 PDF 출력
- 불량 이미지 자동 저장 기능