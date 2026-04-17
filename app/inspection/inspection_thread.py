# 4대 카메라를 동시에 별도 스레드에서 추론하는 모듈
import threading
import numpy as np
from app.inspection.inspector import Inspector, InspectionResult


class CameraInspectionThread:
    """단일 카메라 전용 추론 스레드."""

    def __init__(self, inspector: Inspector, cam_name: str):
        self.inspector   = inspector
        self.cam_name    = cam_name
        self._frame      = None
        self._result     = None
        self._lock       = threading.Lock()
        self._event      = threading.Event()
        self._is_running = False
        self._thread     = None

    def start(self):
        self._is_running = True
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name=f"Inspection-{self.cam_name}"
        )
        self._thread.start()

    def _loop(self):
        while self._is_running:
            triggered = self._event.wait(timeout=1.0)
            if not triggered:
                continue

            with self._lock:
                frame = self._frame.copy() if self._frame is not None else None
                self._event.clear()

            if frame is None:
                continue

            try:
                result = self.inspector.predict(frame)
                with self._lock:
                    self._result = result
            except Exception as e:
                print(f"[오류] {self.cam_name} 추론 중 예외: {e}")

    def update_frame(self, frame: np.ndarray):
        with self._lock:
            self._frame = frame.copy() if frame is not None else None
        self._event.set()

    def get_result(self) -> InspectionResult:
        with self._lock:
            return self._result

    def stop(self):
        self._is_running = False
        self._event.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)


class InspectionThread:
    """
    4대 카메라를 동시에 추론하고 통합 판정을 내리는 매니저 클래스.
    """

    def __init__(self, inspector: Inspector, cam_names: list = None):
        self.inspector = inspector
        self.cam_names = cam_names or ["Front", "Back", "Left", "Right"]

        # 카메라 1대당 스레드 1개
        self._threads = [
            CameraInspectionThread(inspector, name)
            for name in self.cam_names
        ]

    def start(self):
        for t in self._threads:
            t.start()
        print(f"[시작] 검사 스레드 {len(self._threads)}대 시작")

    def update_frames(self, frames: list):
        """4개 프레임을 각 스레드에 전달합니다."""
        for i, frame in enumerate(frames):
            if i < len(self._threads) and frame is not None:
                self._threads[i].update_frame(frame)

    def get_results(self) -> list:
        """4개 카메라의 개별 결과를 반환합니다."""
        return [t.get_result() for t in self._threads]

    def get_final_result(self) -> dict:
        """4개 결과를 통합하여 최종 판정을 반환합니다."""
        results     = self.get_results()
        defect_cams = []
        scores      = {}
        max_score   = 0.0

        for i, result in enumerate(results):
            if result is None:
                continue
            cam_name = self.cam_names[i]
            scores[cam_name] = result.anomaly_score
            max_score = max(max_score, result.anomaly_score)

            if result.is_defective:
                defect_cams.append(cam_name)

        is_defective = len(defect_cams) > 0

        return {
            "is_defective"  : is_defective,
            "label"         : "DEFECT" if is_defective else "OK",
            "color"         : (0, 0, 255) if is_defective else (0, 255, 0),
            "defect_cameras": defect_cams,
            "max_score"     : max_score,
            "scores"        : scores,
        }

    def stop(self):
        for t in self._threads:
            t.stop()
        print("[종료] 검사 스레드 종료")