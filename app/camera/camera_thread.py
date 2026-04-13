# 카메라 1대를 독립적인 스레드로 실행하는 모듈
# 각 카메라마다 이 클래스의 인스턴스를 하나씩 생성해서 사용

import cv2
import threading
import time

class CameraThread:
    """
    단일 카메라를 별도 스레드에서 지속적으로 읽어
    항상 최신 프레임을 유지하는 클래스
    
    ex:
        cam = CameraThread(index=0, name="Front")
        cam.start()
        frame = cam.get_frame()
        cam.stop()
    """
    
    def __init__(self, index: int, name: str = ""):
        """
        index: 카메라 인덱스 번호 (0, 1, 2, ..)
        name: 카메라 이름 (전면, 후면 등 - 화면 표시용)
        """
        
        self.index = index
        self.name = name if name else f"Camera {index}"
        
        self.cap = None             # OpenCV VideoCapture 객체
        self.frame = None           # 가장 최근에 읽은 프레임
        self.is_running = False     # 스레드 실행 상태 플래그
        self._thread = None         # 실제 스레드 객체
        
        # Lock: 두 곳에서 동시에 frame에 접근할 때 충돌 방지
        # (스레드가 쓰는 동안 메인이 읽으면 깨진 이미지가 나올 수 있음)
        self._lock = threading.Lock()
        
        # 연결 상태 플래그 추가 - GUI에서 상태 표시에 활용
        self.is_connected = False
    
    
    def start(self) -> bool:
        """카메라를 열고 캡처 스레드를 시작"""
        # 기존 직접 open 방식 제거 → _open_camera()로 통일
        # 이렇게 해야 MJPG 설정이 처음부터 적용됨
        if not self._open_camera():
            return False

        self.is_running = True

        # daemon=True: 메인 프로그램 종료 시 스레드도 자동 종료
        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name=f"Thread-{self.name}"
        )
        self._thread.start()
        return True


    def _open_camera(self) -> bool:
        """카메라 연결 시도. 성공하면 True 반환"""
        if self.cap is not None:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        
        if self.cap.isOpened():
            # C920 카메라 장점 == 카메라 자체에서 MJPG(압축) 포맷을 지원 -> USB로 전송되는 데이터량이 대폭 감소
            # MJOG - 비압축(YUY2) 대비 MJPG == 데이터량이 약 1/10 수준
            # MJPG 압축 포맷 설정 - USB 대역폭을 대폭 절약
            # fourcc: 영상 압축 방식을 4글자 코드로 지정하는 방법
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # 버퍼 크기를 1로 설정 - 항상 최신 프레임만 유지
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 실제로 적용된 설정값 확인 출력
            actual_w   = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h   = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            print(f"[연결] {self.name} → {actual_w}x{actual_h} @ {actual_fps}fps (MJPG)")

            
            self.is_connected = True
            
            print(f"[연결] {self.name} 카메라 연결 성공")
            return True
        
        self.is_connected = False
        return False


    def _capture_loop(self):
        """
        스레드에서 실행되는 캡처 루프.
        is_running = False 가 될 때까지 프레임을 계속 읽음
        """
        
        while self.is_running:
            # 카메라가 열려있지 않으면 연결 시도
            if self.cap is None or not self.cap.isOpened():
                if not self._open_camera():
                    print(f"[재시도] {self.name} 3초 후 재연결 시도...")
                    time.sleep(3)
                    continue
            
            ret, frame = self.cap.read()
            
            if ret:
                # Lock을 걸고 frame 업데이트 (다른 곳에서 동시 접근 방지)
                with self._lock:
                    self.frame = frame
            
            else:
                # 프레임 읽기 실패 - 연결 끊김으로 간주
                print(f"[경고] {self.name} 프레임 읽기 실패 - 재연결 시도")
                self.is_connected = False
                with self._lock:
                    self.frame = None
                self.cap.release()
                time.sleep(1)
    
    def get_frame(self):
        """
        현재 저장된 최신 프레임을 반환
        아직 프레임이 없으면 None을 반환
        """
        
        with self._lock:
            # copy()로 복사본 반환 - 원본을 보호하기 위해
            return self.frame.copy() if self.frame is not None else None
    
    def stop(self):
        """캡처 스레드를 중지하고 카메라 자원을 해제"""
        self.is_running = False
        
        if self._thread is not None:
            self._thread.join(timeout=2.0)      # 스레드가 끝날 때까지 최대 2초 대기
        
        if self.cap is not None:
            self.cap.release()
        
        print(f"[종료] {self.name} 캡처 스레드 종료")