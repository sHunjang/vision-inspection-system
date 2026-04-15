# 멀티스레드 카메라 매니저 동작 확인 스크립트
import cv2
import sys
import os


# 프로젝트 루트를 Python 경로에 추가 (app 모듈을 인식시키기 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from app.camera.camera_manager import CameraManager


def test_multi_camera():
    """4대 카메라를 2x2 그리드로 동시에 표시"""
    
    manager = CameraManager()
    
    if not manager.start_all():
        print("일부 카메라 시작에 실패..")
    
    
    print("\n화면 표시 시작 - 'q' 키를 눌러 종료")
    
    while True:
        frames = manager.get_all_frames()
        
        # None인 프레임은 검은 화면으로 표시
        display_frames = []
        
        for i, frame in enumerate(frames):
            if frame is None:
                import numpy as np
                
                frame = np.zeros((480, 640, 3), dtype="uint8")
                
                cv2.putText(frame, f"No Signal", (200, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
            
            # 카메라 이름 표시
            cam_name = manager.cameras[i].name
            
            cv2.putText(frame, cam_name, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            
            display_frames.append(frame)
        
        # 2x2 그리드로 합치기
        # 상단 행: 전 + 후
        # 하단 행: 좌 + 우
        import numpy as np
        
        top = cv2.hconcat([display_frames[0], display_frames[1]])
        bottom = cv2.hconcat([display_frames[2], display_frames[3]])
        grid = cv2.vconcat([top, bottom])
        
        # 전체 크기를 절반으로 줄여서 표시 (화면이 너무 크면 조정)
        grid_small = cv2.resize(grid, (1280, 960))
        cv2.imshow("4-Camera View", grid_small)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    manager.stop_all()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_multi_camera()