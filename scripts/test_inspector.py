# Inspector 단독 동작 확인 스크립트
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from pathlib import Path
from app.inspection.inspector import Inspector


def load_image(path: Path) -> np.ndarray:
    """한글 경로 문제를 피하기 위해 numpy로 이미지를 읽습니다."""
    img_array = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(img_array, cv2.IMREAD_COLOR)


def test_inspector():
    root_dir  = Path(__file__).resolve().parent.parent
    ckpt_path = (
        root_dir
        / "models" / "patchcore_screw"
        / "Patchcore" / "MVTecAD" / "screw"
        / "v0" / "weights" / "lightning" / "model.ckpt"
    )

    good_img_path   = root_dir / "data/mvtec/screw/test/good/000.png"
    defect_img_path = root_dir / "data/mvtec/screw/test/scratch_head/000.png"

    # ── 이미지 로드 확인 ─────────────────────────────
    print("[디버그] 이미지 로드 확인")
    good_frame   = load_image(good_img_path)
    defect_frame = load_image(defect_img_path)

    if good_frame is None:
        print(f"  [오류] 양품 이미지 로드 실패: {good_img_path}")
        return
    if defect_frame is None:
        print(f"  [오류] 불량 이미지 로드 실패: {defect_img_path}")
        return

    print(f"  양품 이미지: {good_frame.shape}")
    print(f"  불량 이미지: {defect_frame.shape}")

    # ── 모델 로드 ────────────────────────────────────
    # threshold=None → 모델 학습 시 자동 결정된 임계값 사용
    inspector = Inspector(ckpt_path=str(ckpt_path), threshold=None)
    if not inspector.load():
        print("모델 로드 실패")
        return

    # ── 양품 테스트 ──────────────────────────────────
    print("\n[테스트 1] 양품 이미지")
    good_result = inspector.predict(good_frame)
    print(f"  판정    : {good_result.label}")
    print(f"  이상 점수: {good_result.anomaly_score:.4f}")
    print(f"  임계값  : {good_result.threshold:.4f}")

    # ── 불량 테스트 ──────────────────────────────────
    print("\n[테스트 2] 불량 이미지 (scratch_head)")
    defect_result = inspector.predict(defect_frame)
    print(f"  판정    : {defect_result.label}")
    print(f"  이상 점수: {defect_result.anomaly_score:.4f}")
    print(f"  임계값  : {defect_result.threshold:.4f}")

    # ── 결과 화면 표시 ───────────────────────────────
    good_overlay   = inspector.overlay_result(good_frame, good_result)
    defect_overlay = inspector.overlay_result(defect_frame, defect_result)

    # 화면에 맞게 크기 축소 (1024x1024 → 512x512)
    good_overlay   = cv2.resize(good_overlay,   (512, 512))
    defect_overlay = cv2.resize(defect_overlay, (512, 512))

    cv2.imshow("Good Sample", good_overlay)
    cv2.imshow("Defect Sample", defect_overlay)

    print("\n아무 키나 누르면 종료됩니다.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_inspector()