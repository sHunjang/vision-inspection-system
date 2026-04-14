# 메인 윈도우 — 4개 카메라 영상을 2x2 그리드로 표시하는 PyQt5 GUI
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QGridLayout, QLabel, QStatusBar,
    QComboBox, QPushButton,
    QHBoxLayout, QVBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

from app.utils.image_saver import ImageSaver


# 제품 종류 목록 — 추후 configs/ 파일로 분리 예정
PRODUCT_LIST = [
    "T68-MCR",
    "제품2", "제품3", "제품4", "제품5",
    "제품6", "제품7", "제품8", "제품9", "제품10"
]


class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스.
    4개의 카메라 영상을 2x2 그리드로 실시간 표시하고
    스페이스바 또는 버튼으로 이미지를 저장.
    """

    def __init__(self, camera_manager):
        super().__init__()
        self.camera_manager = camera_manager
        self.image_saver = ImageSaver(base_dir="data/raw")

        self._init_ui()
        self._init_timer()

    def _init_ui(self):
        """UI 레이아웃을 구성."""
        self.setWindowTitle("Vision Inspection System — Camera View")
        self.setMinimumSize(1280, 780)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 전체 세로 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── 상단 컨트롤 바 ──────────────────────────
        control_bar = QHBoxLayout()

        # 제품 종류 선택 드롭다운
        lbl_product = QLabel("제품 종류:")
        self.product_combo = QComboBox()
        self.product_combo.addItems(PRODUCT_LIST)
        self.product_combo.setFixedWidth(160)
        # 제품 변경 시 저장 카운트 상태 갱신
        self.product_combo.currentTextChanged.connect(self._on_product_changed)

        # 캡처 버튼
        self.capture_btn = QPushButton("📷  캡처 저장  [Space]")
        self.capture_btn.setFixedHeight(36)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d7d46;
                color: white;
                border-radius: 4px;
                font-size: 13px;
                padding: 0 16px;
            }
            QPushButton:hover   { background-color: #3a9e5a; }
            QPushButton:pressed { background-color: #1f5c33; }
        """)
        self.capture_btn.clicked.connect(self._capture_all)

        # 저장 카운트 표시 라벨
        self.count_label = QLabel("저장: 0장")
        self.count_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        control_bar.addWidget(lbl_product)
        control_bar.addWidget(self.product_combo)
        control_bar.addSpacing(12)
        control_bar.addWidget(self.capture_btn)
        control_bar.addSpacing(12)
        control_bar.addWidget(self.count_label)
        control_bar.addStretch()

        main_layout.addLayout(control_bar)

        # ── 카메라 2x2 그리드 ────────────────────────
        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)

        self.cam_labels = []
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for i, (row, col) in enumerate(positions):
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                background-color: #1a1a1a;
                border: 1px solid #444444;
                color: #888888;
                font-size: 14px;
            """)
            cam_name = self.camera_manager.cameras[i].name
            label.setText(f"{cam_name}\n신호 없음")
            grid_layout.addWidget(label, row, col)
            self.cam_labels.append(label)

        main_layout.addLayout(grid_layout)

        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "카메라 초기화 완료 — Space: 전체 캡처 저장"
        )

    def _init_timer(self):
        """33ms 간격(약 30fps)으로 화면 갱신 타이머 시작."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frames)
        self.timer.start(33)

    # ── 이벤트 핸들러 ────────────────────────────────

    def keyPressEvent(self, event):
        """스페이스바 입력 시 전체 카메라 캡처 저장."""
        if event.key() == Qt.Key_Space:
            self._capture_all()

    def _on_product_changed(self, product_name: str):
        """제품 종류 변경 시 해당 제품의 기존 저장 수 표시."""
        count = self.image_saver.get_total_count(product_name)
        self.count_label.setText(f"저장: {count}장")
        self.status_bar.showMessage(
            f"제품 변경: {product_name} — 기존 저장 {count}장"
        )

    def _capture_all(self):
        """현재 4대 카메라 프레임을 모두 저장."""
        product = self.product_combo.currentText()
        frames = self.camera_manager.get_all_frames()
        saved_paths = []

        for i, frame in enumerate(frames):
            if frame is not None:
                cam_name = self.camera_manager.cameras[i].name
                filepath = self.image_saver.save(
                    frame=frame,
                    camera_name=cam_name,
                    product_type=product
                )
                saved_paths.append(filepath)
                print(f"[저장] {filepath}")

        # 상태바 및 카운트 갱신
        total = self.image_saver.get_total_count(product)
        if saved_paths:
            self.count_label.setText(f"저장: {total}장")
            self.status_bar.showMessage(
                f"✅ {product} — {len(saved_paths)}장 저장 완료  "
                f"(총 누적: {total}장)"
            )
        else:
            self.status_bar.showMessage("⚠️  저장할 프레임이 없습니다.")

    # ── 프레임 갱신 ──────────────────────────────────

    def _update_frames(self):
        """타이머에 의해 주기적으로 호출 — 모든 카메라 프레임을 갱신."""
        frames = self.camera_manager.get_all_frames()

        for i, frame in enumerate(frames):
            cam = self.camera_manager.cameras[i]

            if frame is not None:
                pixmap = self._convert_frame_to_pixmap(frame)
                self.cam_labels[i].setPixmap(
                    pixmap.scaled(
                        self.cam_labels[i].size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
                self.cam_labels[i].setText("")
            else:
                self.cam_labels[i].setPixmap(QPixmap())
                if cam.is_connected:
                    self.cam_labels[i].setText(f"{cam.name}\n초기화 중...")
                else:
                    self.cam_labels[i].setText(f"{cam.name}\nNo Signal")

    @staticmethod
    def _convert_frame_to_pixmap(frame: np.ndarray) -> QPixmap:
        """
        OpenCV 프레임(numpy BGR)을 PyQt5 QPixmap으로 변환.
        OpenCV는 BGR, Qt는 RGB 순서를 사용하므로 반드시 변환 필요.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_image = QImage(
            rgb_frame.data, w, h,
            bytes_per_line,
            QImage.Format_RGB888
        )
        return QPixmap.fromImage(q_image)

    def closeEvent(self, event):
        """창 닫기 시 타이머와 카메라를 안전하게 종료."""
        self.timer.stop()
        self.camera_manager.stop_all()
        event.accept()