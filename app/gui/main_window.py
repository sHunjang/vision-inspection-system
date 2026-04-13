# 메인 윈도우 — 4개 카메라 영상을 2x2 그리드로 표시하는 PyQt5 GUI
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QGridLayout, QLabel, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스.
    4개의 카메라 영상을 2x2 그리드 레이아웃으로 실시간 표시.
    """

    def __init__(self, camera_manager):
        """
        camera_manager: CameraManager 인스턴스 (이미 start_all() 호출된 상태)
        """
        super().__init__()
        self.camera_manager = camera_manager

        self._init_ui()      # UI 구성
        self._init_timer()   # 화면 갱신 타이머 시작

    def _init_ui(self):
        """UI 레이아웃을 구성."""
        self.setWindowTitle("Vision Inspection System — Camera View")
        self.setMinimumSize(1280, 720)

        # 중앙 위젯 및 2x2 그리드 레이아웃
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        grid_layout.setSpacing(4)         # 영상 간 간격
        grid_layout.setContentsMargins(8, 8, 8, 8)

        # 카메라 영상을 표시할 QLabel 4개 생성
        # QLabel은 이미지를 표시하는 가장 기본적인 PyQt5 위젯입니다
        self.cam_labels = []
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (행, 열)

        for i, (row, col) in enumerate(positions):
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                background-color: #1a1a1a;
                border: 1px solid #444444;
                color: #888888;
                font-size: 14px;
            """)
            # 카메라 이름 가져오기
            cam_name = self.camera_manager.cameras[i].name
            label.setText(f"{cam_name}\n신호 없음")

            # 그리드에 추가 (행, 열 위치)
            grid_layout.addWidget(label, row, col)
            self.cam_labels.append(label)

        # 상태바 — 하단에 간단한 정보를 표시
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("카메라 초기화 완료 — 실시간 영상 표시 중")

    def _init_timer(self):
        """
        QTimer: 일정 간격으로 화면 갱신 함수를 호출.
        33ms 간격 = 약 30FPS
        """
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frames)
        self.timer.start(33)  # 33ms마다 _update_frames 호출

    def _update_frames(self):
        """타이머에 의해 주기적으로 호출 — 모든 카메라 프레임을 갱신."""
        frames = self.camera_manager.get_all_frames()

        for i, frame in enumerate(frames):
            cam = self.camera_manager.cameras[i]
            
            if frame is not None:
                # OpenCV 프레임을 QPixmap으로 변환하여 QLabel에 표시
                pixmap = self._convert_frame_to_pixmap(frame)
                
                # QLabel 크기에 맞게 비율 유지하며 축소
                self.cam_labels[i].setPixmap(
                    pixmap.scaled(
                        self.cam_labels[i].size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
                
                # 텍스트 제거 (영상이 표시될 때는 텍스트 불필요)
                self.cam_labels[i].setText("")
            else:
                # 프레임이 없음 - 연결 상태에 따라 메시지 구분
                self.cam_labels[i].setPixmap(QPixmap())
                
                if cam.is_connected:
                    # 연결은 됐지만 아직 첫 프레임 못 받은 상태
                    self.cam_labels[i].setText(f"{cam.name}\n초기화 중..")
                else:
                    self.cam_labels[i].setText(f"{cam.name}\nNo Signal")

    @staticmethod
    def _convert_frame_to_pixmap(frame: np.ndarray) -> QPixmap:
        """
        OpenCV 프레임(numpy BGR)을 PyQt5 QPixmap으로 변환.

        OpenCV는 BGR 순서, Qt는 RGB 순서를 사용하기 때문에
        반드시 색상 채널을 변환해야 .
        """
        # BGR → RGB 색상 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        # numpy 배열 → QImage → QPixmap 순서로 변환
        q_image = QImage(
            rgb_frame.data,       # 이미지 데이터
            w, h,                 # 가로, 세로 크기
            bytes_per_line,       # 한 행의 바이트 수
            QImage.Format_RGB888  # RGB 형식
        )
        return QPixmap.fromImage(q_image)

    def closeEvent(self, event):
        """
        창 닫기 버튼(X) 클릭 시 호출.
        타이머와 카메라를 안전하게 종료.
        """
        self.timer.stop()
        self.camera_manager.stop_all()
        event.accept()