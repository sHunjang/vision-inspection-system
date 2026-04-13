# 프로젝트 회고록 (Retrospective)

> 각 Phase 완료 후 배운 점, 어려웠던 점, 다음에 개선할 점을 기록합니다.

---

## Phase 1 — 환경 구축 및 프로젝트 기반 세팅

- **완료일**: 2025-xx-xx
- **소요 시간**: 약 30분

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

## 전체 프로젝트 회고

> 모든 Phase 완료 후 작성 예정

### 프로젝트를 통해 성장한 점

### 실제 현장 적용 시 보완할 점

### 다음 버전(v2.0)에서 추가 예정 기능