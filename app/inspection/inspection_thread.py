# 별도 스레드에서 PatchCore 추론 수행 모듈
# GUI 스레드와 분리하여 화면 버벅임 없이 실시간 검사 수행
import threading
import numpy as np

from app.inspection.inspector import Inspector, InspectionResult


class InspectionThread:
    """
    Inspector를 별도 스레드에서 실행하는 래퍼 클래스.
    
    카메라 프레임을 받아 추론하고 결과 저장
    GUI == get_result()로 최신 결과만 가져감
    
    ex:
        insp_thread = InspectionThread(inspector)
        insp_thread.start()
        insp_thread.update_frame(frame)     # 새 프레임 전달
        result = insp_thread.get_result()   # 최신 결과 조회
        insp_thread.stop()
    """
    
    def __init__(self, inspector: Inspector):
        self.inspector = inspector
        self._frame = None      # 추론할 최신 프레임
        self._result = None     # 가잔 최근 추론 결과
        self._lock = threading.Lock()
        self._event = threading.Event()     # 새 프레임 도착 신호
        self._is_running = False
        self._thread = None
    
    
    def start(self):
        """추론 스레드 시작 함수"""
        
        self._is_running = True
        self._thread = threading.Thread(
            target=self._inference_loop,
            daemon=True,
            name="Thread-Inspection"
        )
        self._thread.start()
        print("[시작] 검사 스레드 시작")
    
    
    def _inference_loop(self):
        """
        새로운 프레임이 들어올 때마다 추론을 수행하는 루프
        Event 사용으로 프레임이 없을 때는 대기
        """
        while self._is_running:
            # 새로운 프레임 도착까지 대기 (최대 1초)
            triggered = self._event.wait(timeout=1.0)
            
            if not triggered:
                continue
            
            # 프레임 가져오기
            with self._lock:
                frame = self._frame.copy() if self._frame is not None else None
                self._event.clear()     # 이벤트 초기화
            
            if frame is None:
                continue
            
            
            # 추론 수행
            try:
                result = self.inspector.predict(frame)
                
                with self._lock:
                    self._result = result
            
            except Exception as e:
                print(f"[오류] 추론 중 예외 발생: {e}")
    
    
    def update_frame(self, frame: np.ndarray):
        """
        새로운 프레임을 전달하고 추론 요청
        GUI의 QTimer에서 호출됨.
        """
        with self._lock:
            self._frame = frame.copy() if frame is not None else None    
        self._event.set()       # 새로운 프레임 도착 신호
        
    
    def get_result(self) -> InspectionResult:
        """가장 최근 추론 결과 반환"""
        with self._lock:
            return self._result
    
    
    def stop(self):
        """추론 스레드 종료"""
        self._is_running = False
        self._event.set()   # 대기 중인 스레드 깨우기
        
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        
        print("[종료] 검사 스레드 종료")