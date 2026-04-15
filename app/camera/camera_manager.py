# 여러 대의 카메라를 통합 관리하는 매니저 모듈
# CameraThread 인스턴스들을 생성/시작/종료/조회하는 역할

import threading

from app.camera.camera_thread import CameraThread


# 카메라 설정 - 인데긋와 이름을 여기서 중앙 관리
# 실제 현장에서 카메라 위치가 바뀌면 이 부분만 수정하면 됨
CAMERA_CONFIG = [
    {"index": 0, "name": "Front"},
    {"index": 1, "name": "Back"},
    {"index": 2, "name": "Left"},
    {"index": 3, "name": "Right"},
]


class CameraManager:
    """
    여러 대의 CameraThread를 생성하고 관리하는 클래스
    
    ex:
        manager = CameraManager()
        manager.start_all()
        frames = manager.get_all_frames()
        manager.stop_all()
    """
    
    def __init__(self, config: list = None):
        """
        config: 카메라 설정 리스트. None이면 기본값(CAMERA_CONFIG) 사용
        """
        
        self.config = config if config else CAMERA_CONFIG
        self.cameras: list[CameraThread] = []   # CameraThread 인스턴스 목록


    def start_all(self) -> bool:    
        """모든 카메라 스레드를 시작"""
        
        print("=" * 50)
        print("카메라 초기화 시작 (병렬)")
        print("=" * 50)
        
        
        for cam_info in self.config:
            cam = CameraThread(
                index=cam_info["index"],
                name=cam_info["name"],
            )
            self.cameras.append(cam)
            
        # 각 카메라를 별도 스레드에서 동시에 start()
        init_threads = []
        results = [False] * len(self.cameras)
        
        def _start_camera(cam, idx):
            results[idx] = cam.start()
        
        for i, cam in enumerate(self.cameras):
            t = threading.Thread(
                target=_start_camera,
                args=(cam, i),
                daemon=True
            )
            init_threads.append(t)
            t.start()
        
        # 모든 초기화 스레드가 끝날 때까지 대기 (최대 10초)
        for t in init_threads:
            t.join(timeout=10)
        
        success_count = sum(results)
        print(f"\n{success_count}/{len(self.config)}대 카메라 시작 완료")
        return success_count == len(self.config)


    def get_all_frames(self) -> list:
        """
        모든 카메라의 최신 프레임을 리스트로 반환
        반환값: [frame0, frame1, frame2, frame3]
                프레임이 없는 카메라는 None으로 채워짐.
        """
        return [cam.get_frame() for cam in self.cameras]


    def get_frame(self, index: int):
        """특정 인덱스의 카메라 프레임만 반환"""
        if 0 <= index < len(self.cameras):
            return self.cameras[index].get_frame()
        return None
    
    
    def stop_all(self):
        """모든 카메라 스레드 종료"""
        print("\n카메라 종료 중..")
        for cam in self.cameras:
            cam.stop()
        
        self.cameras.clear()
        print("모든 카메라 종료 완료")