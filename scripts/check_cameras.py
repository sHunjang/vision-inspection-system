# 연결된 카메라 인덱스를 자동으로 탐색하는 스크립트
import cv2

def find_available_cameras(max_index=10):
    """
    0번부터 max_index번까지 카메라 연결을 시도하여
    실제로 작동하는 카메라 인덱스 목록 반환
    """
    
    available = []  # 사용 가능한 카메라 인덱스를 담을 리스트
    
    print("카메라 탐색 시작..")
    
    for index in range(max_index):
        
        # 해당 인덱스로 카메라 열기 시도
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)    # CAP_DSHOW: Windows 전용 드라이버
        
        if cap.isOpened():
            
            # 실제로 프레임을 읽을 수 있는지 추가 확인
            ret, frame = cap.read()
            
            if ret:
                
                # 카메라 해상도 정보도 같이 출력
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                print(f"[발견] 카메라 인덱스 {index} -> 해상도: {width} x {height}")
                
                available.append(index)
            
            cap.release()   # 카메라 자원 반환 (열었으면 반드시 닫아야 함)
    
    return available

if __name__ == "__main__":
    cameras = find_available_cameras()

    print(f"\n총 {len(cameras)}대의 카메라를 발견했습니다.")
    print(f"사용 가능한 인덱스: {cameras}")

    if len(cameras) < 4:
        print("\n⚠️  경고: 4대 미만입니다. 연결 상태를 확인해주세요.")
    else:
        print("\n✅ 4대 이상 확인됨. 다음 단계로 진행 가능합니다.")