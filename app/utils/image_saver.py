# 캡처 이미지를 날짜/제품 종류별로 저장하는 유틸리티 모듈
import os
import cv2
from datetime import datetime


class ImageSaver:
    """
    카메라에서 캡처한 이미지를 지정된 경로에 저장하는 클래스.
    
    저장 구조:
        data/raw/{product_type}/{camera_name}/{날짜}/{시각}_{카운트}.jpg
        ex: data/raw/T68-MCR/Front/2026-04-01/090000_001.jpg
    """
    
    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = base_dir
        self.capture_count = 0      # 현재 세선의 총 캡처 횟수
        
    
    def save(self, frame, camera_name: str, product_type: str = "unknown") -> str:
        """
        프레임을 파일로 저장
        
        frame           : OpenCV 이미지 (numpy 배열)
        camera_name     : 카메라 이름 (Front, Back, Left, Right)
        product_type    : 제품 종류 이름 (ex: T68-MCR)
        
        Return:
            저장된 파일 경로 (문자열)
        """
        
        # 저장 폴더 경로: data/raw/T68-MCR/Front/2026-04-01
        today = datetime.now().strftime("%Y-%m-%d")
        
        save_dir = os.path.join(
            self.base_dir,
            product_type,
            camera_name,
            today
        )
        
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일명: 시각_순번.jpg (ex: 090000_001.jpg)
        timestamp = datetime.now().strftime("%H%M%S")
        self.capture_count += 1
        
        filename = f"{timestamp}_{self.capture_count:03d}.jpg"
        filepath = os.path.join(save_dir, filename)
        
        # 품질 95로 저장 (기본값 95 - 용량과 품질 균형)
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        return filepath
        
    
    def get_total_count(self, product_type: str) -> int:
        """
        특정 제품의 저장된 총 이미지 수를 반환
        진행 상황 파악에 활용
        """
        
        product_dir = os.path.join(self.base_dir, product_type)
        
        if not os.path.exists(product_dir):
            return 0
        
        count = 0
        
        # 하위 폴더까지 모두 탐색하여 .jpg 파일 수 집계
        for root, dirs, files in os.walk(product_dir):
            count += sum(1 for f in files if f.endswith(".jpg"))
        return count