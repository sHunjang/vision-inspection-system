# PatchCore 모델 로드 및 실시간 추론 수행 검사 엔진 모듈
import cv2
import numpy as np
import torch

from pathlib import Path
from anomalib.models import Patchcore


class InspectionResult:
    """
    단일 이미지 검사 결과를 담는 데이터 클래스.
    GUI에서 이 객체를 받아 화면에 표시합니다.
    """

    def __init__(
        self,
        is_defective: bool,
        anomaly_score: float,
        anomaly_map: np.ndarray,
        threshold: float,
    ):
        self.is_defective  = is_defective
        self.anomaly_score = anomaly_score
        self.anomaly_map   = anomaly_map
        self.threshold     = threshold

    @property
    def label(self) -> str:
        """판정 결과를 문자열로 반환합니다."""
        return "DEFECT" if self.is_defective else "OK"

    @property
    def color(self) -> tuple:
        """판정 결과에 따른 BGR 색상을 반환합니다."""
        return (0, 0, 255) if self.is_defective else (0, 255, 0)


class Inspector:
    """
    PatchCore 모델을 로드하고 이미지 추론을 수행하는 검사 엔진.

    사용 예:
        inspector = Inspector(ckpt_path="models/.../model.ckpt")
        inspector.load()
        result = inspector.predict(frame)
    """

    def __init__(self, ckpt_path: str, threshold: float = None):
        """
        ckpt_path : 학습된 모델 체크포인트 경로
        threshold : 이상 점수 임계값
                    None이면 모델 학습 시 자동 결정된 값 사용
        """
        self.ckpt_path       = Path(ckpt_path)
        self._threshold_override = threshold  # None이면 모델 내장값 사용
        self.threshold       = threshold or 0.0
        self.model           = None
        self.device          = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 모델 내장 전처리기 사용 — 별도 transform 불필요
        self.pre_processor   = None

    def load(self) -> bool:
        """저장된 체크포인트에서 모델을 로드합니다."""
        if not self.ckpt_path.exists():
            print(f"[오류] 모델 파일을 찾을 수 없습니다: {self.ckpt_path}")
            return False

        # CUDA 가용 여부 재확인 — 패키징 환경에서도 안전하게 처리
        if self.device.type == "cuda" and not torch.cuda.is_available():
            print("[경고] CUDA를 사용할 수 없습니다. CPU로 전환합니다.")
            self.device = torch.device("cpu")

        print(f"[모델 로드] {self.ckpt_path}")
        print(f"[디바이스] {self.device}")

        self.model = Patchcore.load_from_checkpoint(
            checkpoint_path=str(self.ckpt_path),
            map_location=self.device,   # ← 이미 device를 지정하므로 안전
            weights_only=False,
        )
        self.model.eval()
        self.model.to(self.device)

        pp = self.model.post_processor
        if self._threshold_override is None:
            self.threshold = float(pp.image_threshold)
        else:
            self.threshold = self._threshold_override

        self.score_min = float(pp.image_min)
        self.score_max = float(pp.image_max)

        print(f"[임계값] {self.threshold:.4f}")
        print(f"[Score 범위] min={self.score_min:.4f} / max={self.score_max:.4f}")
        print("[모델 로드] 완료 ✅")
        return True

    def predict(self, frame: np.ndarray) -> InspectionResult:
        """
        OpenCV 프레임을 입력받아 검사 결과를 반환합니다.
        frame: OpenCV BGR 이미지 (numpy 배열)
        """
        if self.model is None:
            raise RuntimeError("모델이 로드되지 않음. load()를 먼저 호출하세요.")

        # BGR → RGB 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # numpy → tensor 변환 및 전처리
        import torchvision.transforms.functional as TF
        input_tensor = TF.to_tensor(rgb_frame)
        input_tensor = TF.resize(input_tensor, [256, 256])
        input_tensor = TF.normalize(
            input_tensor,
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        input_tensor = input_tensor.unsqueeze(0).to(self.device)

        # model.model() 직접 호출 → 정규화 전 raw distance 값 획득
        # model.forward()는 이미 정규화된 0~1 값만 반환하므로 사용 불가
        with torch.no_grad():
            raw_output = self.model.model(input_tensor)

        # raw pred_score: 이미지 단위 이상 점수 (raw distance)
        raw_score   = float(raw_output.pred_score.item())

        # anomaly_map: 픽셀 단위 이상 맵 (raw distance)
        anomaly_map = raw_output.anomaly_map

        if anomaly_map is not None:
            anomaly_map_np = anomaly_map.squeeze().cpu().numpy()
            anomaly_map_resized = cv2.resize(
                anomaly_map_np,
                (frame.shape[1], frame.shape[0])
            )
        else:
            anomaly_map_resized = np.zeros(
                (frame.shape[0], frame.shape[1]), dtype=np.float32
            )

        # print(f"  [디버그] raw_score: {raw_score:.4f} / threshold: {self.threshold:.4f}")

        # 임계값 기준 양/불량 판정
        is_defective = raw_score > self.threshold

        return InspectionResult(
            is_defective  = is_defective,
            anomaly_score = raw_score,
            anomaly_map   = anomaly_map_resized,
            threshold     = self.threshold,
        )

    def overlay_result(self, frame: np.ndarray, result: InspectionResult) -> np.ndarray:
        """검사 결과를 원본 프레임에 오버레이하여 반환합니다."""
        if frame is None or frame.size == 0:
            print("[경고] overlay_result: 유효하지 않은 프레임")
            return np.zeros((480, 640, 3), dtype=np.uint8)

        overlay = frame.copy()
        h, w    = overlay.shape[:2]

        # 히트맵 오버레이 (불량일 때만)
        if result.anomaly_map is not None and result.is_defective:
            heatmap_norm = cv2.normalize(
                result.anomaly_map, None, 0, 255, cv2.NORM_MINMAX
            ).astype(np.uint8)
            heatmap_colored = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
            heatmap_colored = cv2.resize(heatmap_colored, (w, h))
            overlay = cv2.addWeighted(overlay, 0.6, heatmap_colored, 0.4, 0)

        # 판정 결과 박스
        cv2.rectangle(overlay, (0, 0), (w, 64), (0, 0, 0), -1)
        cv2.rectangle(overlay, (0, 0), (w, 64), result.color, 2)

        # 판정 레이블
        cv2.putText(
            overlay, result.label,
            (10, 38),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2,
            result.color, 2
        )

        # 이상 점수 및 임계값
        score_text = (
            f"Score: {result.anomaly_score:.2f}  "
            f"Threshold: {result.threshold:.2f}"
        )
        cv2.putText(
            overlay, score_text,
            (10, 58),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45,
            (200, 200, 200), 1
        )

        return overlay