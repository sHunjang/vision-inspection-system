# 실시간 검사 탭 위젯
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel,
    QHBoxLayout, QVBoxLayout,
    QComboBox, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

from app.camera.camera_manager import CameraManager
from app.inspection.inspection_thread import InspectionThread
from app.inspection.inspector import Inspector
from app.database.db_manager import DBManager
from app.utils.image_saver import ImageSaver

PRODUCT_LIST = [
    "T68-MCR",
    "제품2", "제품3", "제품4", "제품5",
    "제품6", "제품7", "제품8", "제품9", "제품10"
]


class InspectionTab(QWidget):
    """실시간 카메라 영상 및 검사 결과를 표시하는 탭."""

    def __init__(
        self,
        camera_manager: CameraManager,
        inspection_thread: InspectionThread,
        inspector: Inspector,
        db_manager: DBManager,
        image_saver: ImageSaver,
        parent=None
    ):
        super().__init__(parent)
        self.camera_manager    = camera_manager
        self.inspection_thread = inspection_thread
        self.inspector         = inspector
        self.db_manager        = db_manager
        self.image_saver       = image_saver
        self.inspection_enabled = False

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # ── 컨트롤 바 ────────────────────────────────
        ctrl = QHBoxLayout()

        self.product_combo = QComboBox()
        self.product_combo.addItems(PRODUCT_LIST)
        self.product_combo.setFixedWidth(150)

        self.cam_combo = QComboBox()
        self.cam_combo.setFixedWidth(100)
        for cam in self.camera_manager.cameras:
            self.cam_combo.addItem(cam.name)

        self.capture_btn = QPushButton("📷 캡처 [Space]")
        self.capture_btn.setFixedHeight(32)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e8449; color: white;
                border-radius: 4px; padding: 0 10px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.capture_btn.clicked.connect(self.capture_all)

        self.inspect_btn = QPushButton("🔍 검사 시작")
        self.inspect_btn.setFixedHeight(32)
        self.inspect_btn.setCheckable(True)
        self.inspect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5276; color: white;
                border-radius: 4px; padding: 0 10px;
            }
            QPushButton:checked { background-color: #922b21; }
            QPushButton:hover   { background-color: #2471a3; }
        """)
        self.inspect_btn.clicked.connect(self._toggle_inspection)

        self.count_label = QLabel("저장: 0장")
        self.count_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        # 실시간 판정 결과 표시 라벨
        self.result_label = QLabel("대기 중")
        self.result_label.setFixedHeight(32)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            background-color: #2c3e50;
            color: #aaaaaa;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            padding: 0 16px;
        """)

        ctrl.addWidget(QLabel("제품:"))
        ctrl.addWidget(self.product_combo)
        ctrl.addSpacing(8)
        ctrl.addWidget(QLabel("검사:"))
        ctrl.addWidget(self.cam_combo)
        ctrl.addSpacing(8)
        ctrl.addWidget(self.capture_btn)
        ctrl.addSpacing(4)
        ctrl.addWidget(self.inspect_btn)
        ctrl.addSpacing(12)
        ctrl.addWidget(self.result_label)
        ctrl.addSpacing(12)
        ctrl.addWidget(self.count_label)
        ctrl.addStretch()

        main_layout.addLayout(ctrl)

        # ── 카메라 2x2 그리드 ────────────────────────
        grid = QGridLayout()
        grid.setSpacing(4)
        self.cam_labels = []

        for i, (row, col) in enumerate([(0,0),(0,1),(1,0),(1,1)]):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
                background-color: #1a1a1a;
                border: 1px solid #444;
                color: #888; font-size: 13px;
            """)
            lbl.setText(f"{self.camera_manager.cameras[i].name}\n신호 없음")
            grid.addWidget(lbl, row, col)
            self.cam_labels.append(lbl)

        main_layout.addLayout(grid)

    # ── 외부에서 호출되는 메서드 ─────────────────────

    def update_frames(self):
        """QTimer에서 호출 — 프레임 갱신 및 검사 결과 표시."""
        frames      = self.camera_manager.get_all_frames()
        inspect_idx = self.cam_combo.currentIndex()

        for i, frame in enumerate(frames):
            cam = self.camera_manager.cameras[i]

            if frame is None:
                self.cam_labels[i].setPixmap(QPixmap())
                self.cam_labels[i].setText(
                    f"{cam.name}\n{'초기화 중...' if cam.is_connected else 'No Signal'}"
                )
                continue

            display = frame.copy()

            # 검사 활성화된 카메라에 추론 적용
            if self.inspection_enabled and i == inspect_idx:
                if self.inspection_thread:
                    self.inspection_thread.update_frame(frame)
                result = self.inspection_thread.get_result() \
                    if self.inspection_thread else None

                if result is not None:
                    display = self.inspector.overlay_result(display, result)
                    self._update_result_label(result)

                    # DB에 결과 저장 (매 프레임이 아닌 결과 변경 시만)
                    if not hasattr(self, '_last_result_id') or \
                       self._should_log(result):
                        self.db_manager.insert_log(
                            product  = self.product_combo.currentText(),
                            camera   = cam.name,
                            result   = result.label,
                            score    = result.anomaly_score,
                            threshold= result.threshold,
                        )
                        self._last_score = result.anomaly_score

            # QLabel에 표시
            pixmap = self._to_pixmap(display)
            self.cam_labels[i].setPixmap(
                pixmap.scaled(
                    self.cam_labels[i].size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
            self.cam_labels[i].setText("")

    def capture_all(self):
        """4대 카메라 캡처 저장."""
        product = self.product_combo.currentText()
        frames  = self.camera_manager.get_all_frames()
        saved   = 0
        for i, frame in enumerate(frames):
            if frame is not None:
                self.image_saver.save(
                    frame=frame,
                    camera_name=self.camera_manager.cameras[i].name,
                    product_type=product
                )
                saved += 1
        total = self.image_saver.get_total_count(product)
        self.count_label.setText(f"저장: {total}장")

    # ── 내부 헬퍼 ────────────────────────────────────

    def _toggle_inspection(self, checked: bool):
        self.inspection_enabled = checked
        self.inspect_btn.setText(
            "🔴 검사 중지" if checked else "🔍 검사 시작"
        )
        if not checked:
            self.result_label.setText("대기 중")
            self.result_label.setStyleSheet("""
                background-color: #2c3e50; color: #aaaaaa;
                border-radius: 4px; font-size: 14px;
                font-weight: bold; padding: 0 16px;
            """)

    def _update_result_label(self, result):
        """판정 결과 라벨을 갱신합니다."""
        if result.is_defective:
            bg, fg = "#922b21", "#f1948a"
        else:
            bg, fg = "#1e8449", "#82e0aa"

        self.result_label.setText(
            f"{result.label}  Score: {result.anomaly_score:.2f}"
        )
        self.result_label.setStyleSheet(f"""
            background-color: {bg}; color: {fg};
            border-radius: 4px; font-size: 14px;
            font-weight: bold; padding: 0 16px;
        """)

    def _should_log(self, result) -> bool:
        """이전 결과와 score 차이가 클 때만 DB 저장 (과도한 저장 방지)."""
        prev = getattr(self, '_last_score', None)
        if prev is None:
            return True
        return abs(result.anomaly_score - prev) > 1.0

    @staticmethod
    def _to_pixmap(frame: np.ndarray) -> QPixmap:
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QPixmap.fromImage(
            QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        )