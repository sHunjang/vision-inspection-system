# 실시간 검사 탭 — 4대 카메라 동시 검사 및 통합 판정
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

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
    """4대 카메라 동시 검사 및 통합 판정 탭."""

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
        self._last_final       = None  # 마지막 통합 판정 결과

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # ── 상단 컨트롤 바 ──────────────────────────
        ctrl = QHBoxLayout()

        self.product_combo = QComboBox()
        self.product_combo.addItems(PRODUCT_LIST)
        self.product_combo.setFixedWidth(150)

        self.capture_btn = QPushButton("📷 캡처 [Space]")
        self.capture_btn.setFixedHeight(34)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e8449; color: white;
                border-radius: 4px; padding: 0 12px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.capture_btn.clicked.connect(self.capture_all)

        self.inspect_btn = QPushButton("🔍 검사 시작")
        self.inspect_btn.setFixedHeight(34)
        self.inspect_btn.setCheckable(True)
        self.inspect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5276; color: white;
                border-radius: 4px; padding: 0 12px;
            }
            QPushButton:checked { background-color: #922b21; }
            QPushButton:hover   { background-color: #2471a3; }
        """)
        self.inspect_btn.clicked.connect(self._toggle_inspection)

        self.count_label = QLabel("저장: 0장")
        self.count_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        ctrl.addWidget(QLabel("제품:"))
        ctrl.addWidget(self.product_combo)
        ctrl.addSpacing(8)
        ctrl.addWidget(self.capture_btn)
        ctrl.addSpacing(4)
        ctrl.addWidget(self.inspect_btn)
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

        # ── 최종 통합 판정 패널 ──────────────────────
        self.final_panel = QLabel("검사 대기 중")
        self.final_panel.setFixedHeight(70)
        self.final_panel.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.final_panel.setFont(font)
        self.final_panel.setStyleSheet("""
            background-color: #2c3e50;
            color: #aaaaaa;
            border-radius: 6px;
            font-size: 20px;
        """)
        main_layout.addWidget(self.final_panel)

    # ── 외부 호출 메서드 ─────────────────────────────

    def update_frames(self):
        """QTimer에서 호출 — 프레임 갱신 및 검사 결과 표시."""
        frames = self.camera_manager.get_all_frames()

        # 검사 활성화 시 4대 동시 추론 요청
        if self.inspection_enabled and self.inspection_thread:
            self.inspection_thread.update_frames(frames)

        # 개별 결과 가져오기
        results = self.inspection_thread.get_results() \
            if self.inspection_thread else [None] * 4

        for i, frame in enumerate(frames):
            cam = self.camera_manager.cameras[i]

            if frame is None:
                self.cam_labels[i].setPixmap(QPixmap())
                self.cam_labels[i].setText(
                    f"{cam.name}\n{'초기화 중...' if cam.is_connected else 'No Signal'}"
                )
                continue

            display = frame.copy()

            # 개별 카메라 결과 오버레이
            if self.inspection_enabled and results[i] is not None:
                display = self.inspector.overlay_result(display, results[i])

            pixmap = self._to_pixmap(display)
            self.cam_labels[i].setPixmap(
                pixmap.scaled(
                    self.cam_labels[i].size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
            self.cam_labels[i].setText("")

        # 통합 판정 패널 갱신
        if self.inspection_enabled and self.inspection_thread:
            final = self.inspection_thread.get_final_result()
            self._update_final_panel(final)

            # 판정 결과 변경 시 DB 저장
            if self._should_log(final):
                self._save_to_db(final)
                self._last_final = final

    def capture_all(self):
        """4대 카메라 캡처 저장."""
        product = self.product_combo.currentText()
        frames  = self.camera_manager.get_all_frames()
        saved   = 0
        for i, frame in enumerate(frames):
            if frame is not None:
                self.image_saver.save(
                    frame        = frame,
                    camera_name  = self.camera_manager.cameras[i].name,
                    product_type = product,
                )
                saved += 1
        total = self.image_saver.get_total_count(product)
        self.count_label.setText(f"저장: {total}장")

    # ── 내부 헬퍼 ────────────────────────────────────

    def _toggle_inspection(self, checked: bool):
        """검사 ON/OFF."""
        self.inspection_enabled = checked
        self.inspect_btn.setText(
            "🔴 검사 중지" if checked else "🔍 검사 시작"
        )
        if not checked:
            # 검사 중지 시 판정 패널 초기화
            self.final_panel.setText("검사 대기 중")
            self.final_panel.setStyleSheet("""
                background-color: #2c3e50;
                color: #aaaaaa;
                border-radius: 6px;
            """)
            # 카메라 테두리 초기화
            for lbl in self.cam_labels:
                lbl.setStyleSheet("""
                    background-color: #1a1a1a;
                    border: 1px solid #444;
                    color: #888; font-size: 13px;
                """)

    def _update_final_panel(self, final: dict):
        """통합 판정 패널을 갱신합니다."""
        if not final["scores"]:
            return

        if final["is_defective"]:
            # 불량 — 어떤 카메라에서 불량인지 표시
            defect_info = ", ".join(final["defect_cameras"])
            text    = f"❌  DEFECT  |  불량 카메라: {defect_info}  |  Max Score: {final['max_score']:.2f}"
            bg, fg  = "#922b21", "#f1948a"
        else:
            scores_text = "  ".join(
                [f"{k}: {v:.1f}" for k, v in final["scores"].items()]
            )
            text    = f"✅  OK  |  {scores_text}"
            bg, fg  = "#1e8449", "#82e0aa"

        self.final_panel.setText(text)
        self.final_panel.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border-radius: 6px;
            padding: 0 12px;
        """)

        # 불량 카메라 테두리 강조
        for i, cam in enumerate(self.camera_manager.cameras):
            if cam.name in final["defect_cameras"]:
                self.cam_labels[i].setStyleSheet("""
                    background-color: #1a1a1a;
                    border: 3px solid #e74c3c;
                    color: #888; font-size: 13px;
                """)
            else:
                self.cam_labels[i].setStyleSheet("""
                    background-color: #1a1a1a;
                    border: 3px solid #2ecc71;
                    color: #888; font-size: 13px;
                """)

    def _should_log(self, final: dict) -> bool:
        """이전 판정과 결과가 다를 때만 DB 저장."""
        if self._last_final is None:
            return bool(final["scores"])
        return final["is_defective"] != self._last_final["is_defective"]

    def _save_to_db(self, final: dict):
        """통합 판정 결과를 DB에 저장합니다."""
        product = self.product_combo.currentText()
        for cam_name, score in final["scores"].items():
            self.db_manager.insert_log(
                product   = product,
                camera    = cam_name,
                result    = final["label"],
                score     = score,
                threshold = self.inspector.threshold,
            )

    @staticmethod
    def _to_pixmap(frame: np.ndarray) -> QPixmap:
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QPixmap.fromImage(
            QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.capture_all()