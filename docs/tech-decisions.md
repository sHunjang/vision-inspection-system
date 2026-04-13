# 기술 선택 근거 문서

## GUI 프레임워크: PyQt5

- **선택 이유**: PyInstaller와의 호환성이 안정적이며, 국내 레퍼런스가 풍부함
- **대안**: PyQt6 (더 현대적이나 패키징 이슈 가능성)
- **결정일**: 2025-xx-xx

---

## AI 프레임워크: PyTorch + Ultralytics YOLOv8

- **선택 이유**: 오픈소스, 실시간 객체 탐지에 최적화, 전이학습 지원
- **대안**: TensorFlow, OpenCV DNN
- **결정일**: 2025-xx-xx

---

## 데이터베이스: SQLite (예정)

- **선택 이유**: 별도 서버 불필요, 단독 실행 파일에 포함 가능
- **대안**: MySQL, PostgreSQL
- **결정일**: Phase 6에서 확정 예정

---

## 패키징: PyInstaller

- **선택 이유**: Python 앱을 Windows .exe로 변환, 무료 오픈소스
- **대안**: cx_Freeze, Nuitka
- **결정일**: 2025-xx-xx

---

## GPU: NVIDIA GeForce RTX 5060 / CUDA 12.8

- **선택 이유**: 사내 보유 장비, PyTorch CUDA 버전으로 추론 가속 가능
- **결정일**: 2025-xx-xx