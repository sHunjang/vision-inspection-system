# 캡처 이미지를 날짜·제품종류·양불량별로 저장하는 유틸리티 모듈
import os
import cv2
from datetime import datetime


class ImageSaver:
    """
    카메라에서 캡처한 이미지를 지정된 경로에 저장하는 클래스.

    저장 구조:
        data/raw/{product_type}/{label}/{camera_name}/{날짜}/{시각}_{카운트}.jpg

        양품: data/raw/T68-MCR/good/Front/2025-01-01/143022_001.jpg
        불량: data/raw/T68-MCR/defect/label_missing/Front/2025-01-01/143022_001.jpg
    """

    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir      = base_dir
        self.capture_count = 0

    def save(
        self,
        frame,
        camera_name: str,
        product_type: str = "unknown",
        label: str = "good",          # "good" 또는 "defect"
        defect_type: str = None,      # 불량 유형 (label_missing, bolt_missing 등)
    ) -> str:
        """
        프레임을 파일로 저장합니다.

        frame        : OpenCV 이미지 (numpy 배열)
        camera_name  : 카메라 이름
        product_type : 제품 종류
        label        : "good" 또는 "defect"
        defect_type  : 불량 유형 (label이 "defect"일 때만 사용)
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 저장 경로 구성
        if label == "good":
            save_dir = os.path.join(
                self.base_dir, product_type, "good", camera_name, today
            )
        else:
            dtype = defect_type if defect_type else "unknown_defect"
            save_dir = os.path.join(
                self.base_dir, product_type, "defect", dtype, camera_name, today
            )

        os.makedirs(save_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%H%M%S")
        self.capture_count += 1
        filename = f"{timestamp}_{self.capture_count:03d}.jpg"
        filepath = os.path.join(save_dir, filename)

        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return filepath

    def get_total_count(self, product_type: str, label: str = None) -> int:
        """
        특정 제품의 저장된 총 이미지 수를 반환합니다.
        label: "good", "defect", None(전체)
        """
        if label:
            target_dir = os.path.join(self.base_dir, product_type, label)
        else:
            target_dir = os.path.join(self.base_dir, product_type)

        if not os.path.exists(target_dir):
            return 0

        count = 0
        for root, dirs, files in os.walk(target_dir):
            count += sum(1 for f in files if f.endswith(".jpg"))
        return count