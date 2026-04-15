# 단일 카메라 캡처 동작을 확인하는 테스트 스크립트
import cv2

def test_camera(index=0):
    """
    지정한 인덱스의 카메라를 열어 영상을 화면에 표시
    'q'키를 누르면 중료
    """
    
    # 카메라 열기
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print(f"카메라 {index}번을 열 수 없음..")
        return 
    
    print(f"카메라 {index}번 시작 - 'q' 키를 누르면 종료..")
    
    while True:
        # 프레임 한 장 읽기
        # ret: 읽기 성공 여부 (True/False)
        # frame: 읽어온 이미지 (numpy 배열)
        ret, frame = cap.read()
        
        if not ret:
            print(f"프레임을 읽을 수 없음..")
            break
        
        # 화면에 카메라 번호 텍스트 표시
        cv2.putText(
            frame,                        # 텍스트를 그릴 이미지
            f"Camera {index}",            # 표시할 텍스트
            (10, 30),                     # 텍스트 위치 (x, y)
            cv2.FONT_HERSHEY_SIMPLEX,     # 폰트 종류
            1.0,                          # 폰트 크기
            (0, 255, 0),                  # 색상 (BGR 형식 — 초록색)
            2                             # 텍스트 두께
        )
        
        # 창에 프레임 표시
        cv2.imshow(f"Camera {index} Test", frame)
        
        # 키 입력 대기 (1ms) - 'q' 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 자원 해제 (반드시 해야 함)
    cap.release()
    cv2.destroyAllWindows()
    print("카메라 종료 완료.")


if __name__ == "__main__":
    test_camera(index=0)