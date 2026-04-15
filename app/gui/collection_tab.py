# 데이터 수집 전용 탭 위젯
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGroupBox,
    QProgressBar, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

from app.camera.camera_manager import CameraManager
from app.utils.image_saver import ImageSaver

PRODUCT_LIST = [
    "T68-MCR",
    "제품2", "제품3", "제품4", "제품5",
    "제품6", "제품7", "제품8", "제품9", "제품10"
]

DEFECT_TYPES = [
    "label_missing",
    "label_misplace",
    "bolt_missing",
    "bolt_defect",
    "scratch",
    "contamination",
    "other",
]

TARGET_GOOD   = 200
TARGET_DEFECT = 50


class CollectionTab(QWidget):
    """학습 데이터 수집 전용 탭."""

    def __init__(self, camera_manager: CameraManager, image_saver: ImageSaver, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.image_saver    = image_saver
        self.auto_timer     = QTimer()
        self.preview_timer  = QTimer()

        self._init_ui()

        # UI 완성 후 시그널 연결
        self.auto_timer.timeout.connect(self._auto_capture)
        self.preview_timer.timeout.connect(self._update_preview)
        self.preview_timer.start(33)

        self._refresh_stats()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ── 왼쪽: 카메라 프리뷰 ──────────────────────
        left = QVBoxLayout()

        cam_bar = QHBoxLayout()
        cam_bar.addWidget(QLabel("프리뷰 카메라:"))
        self.preview_combo = QComboBox()
        self.preview_combo.setFixedWidth(120)
        for cam in self.camera_manager.cameras:
            self.preview_combo.addItem(cam.name)
        cam_bar.addWidget(self.preview_combo)
        cam_bar.addStretch()
        left.addLayout(cam_bar)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setStyleSheet("""
            background-color: #1a1a1a;
            border: 2px solid #444;
            color: #888; font-size: 14px;
        """)
        self.preview_label.setText("카메라 프리뷰")
        left.addWidget(self.preview_label)

        main_layout.addLayout(left, stretch=3)

        # ── 오른쪽: 수집 설정 패널 ──────────────────
        right = QVBoxLayout()
        right.setSpacing(10)

        # 제품 선택
        product_group  = QGroupBox("제품 설정")
        product_layout = QVBoxLayout(product_group)
        prod_row       = QHBoxLayout()
        prod_row.addWidget(QLabel("제품 종류:"))
        self.product_combo = QComboBox()
        self.product_combo.addItems(PRODUCT_LIST)
        prod_row.addWidget(self.product_combo)
        product_layout.addLayout(prod_row)
        right.addWidget(product_group)

        # 양품 수집
        good_group  = QGroupBox("양품 수집")
        good_group.setStyleSheet("QGroupBox { color: #2ecc71; font-weight: bold; }")
        good_layout = QVBoxLayout(good_group)

        self.good_progress = QProgressBar()
        self.good_progress.setMaximum(TARGET_GOOD)
        self.good_progress.setStyleSheet("""
            QProgressBar { border: 1px solid #444; border-radius: 4px; }
            QProgressBar::chunk { background-color: #2ecc71; }
        """)
        self.good_count_label = QLabel(f"0 / {TARGET_GOOD}장")
        self.good_count_label.setAlignment(Qt.AlignCenter)

        self.good_capture_btn = QPushButton("✅  양품 캡처  [F1]")
        self.good_capture_btn.setFixedHeight(44)
        self.good_capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e8449; color: white;
                border-radius: 6px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover   { background-color: #27ae60; }
            QPushButton:pressed { background-color: #145a32; }
        """)
        self.good_capture_btn.clicked.connect(self._capture_good)

        good_layout.addWidget(self.good_progress)
        good_layout.addWidget(self.good_count_label)
        good_layout.addWidget(self.good_capture_btn)
        right.addWidget(good_group)

        # 불량 수집
        defect_group  = QGroupBox("불량 수집")
        defect_group.setStyleSheet("QGroupBox { color: #e74c3c; font-weight: bold; }")
        defect_layout = QVBoxLayout(defect_group)

        dtype_row = QHBoxLayout()
        dtype_row.addWidget(QLabel("불량 유형:"))
        self.defect_type_combo = QComboBox()
        self.defect_type_combo.addItems(DEFECT_TYPES)
        dtype_row.addWidget(self.defect_type_combo)
        defect_layout.addLayout(dtype_row)

        self.defect_progress = QProgressBar()
        self.defect_progress.setMaximum(TARGET_DEFECT)
        self.defect_progress.setStyleSheet("""
            QProgressBar { border: 1px solid #444; border-radius: 4px; }
            QProgressBar::chunk { background-color: #e74c3c; }
        """)
        self.defect_count_label = QLabel(f"0 / {TARGET_DEFECT}장")
        self.defect_count_label.setAlignment(Qt.AlignCenter)

        self.defect_capture_btn = QPushButton("❌  불량 캡처  [F2]")
        self.defect_capture_btn.setFixedHeight(44)
        self.defect_capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #922b21; color: white;
                border-radius: 6px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover   { background-color: #c0392b; }
            QPushButton:pressed { background-color: #641e16; }
        """)
        self.defect_capture_btn.clicked.connect(self._capture_defect)

        defect_layout.addWidget(self.defect_progress)
        defect_layout.addWidget(self.defect_count_label)
        defect_layout.addWidget(self.defect_capture_btn)
        right.addWidget(defect_group)

        # 연속 촬영
        auto_group  = QGroupBox("연속 촬영")
        auto_layout = QVBoxLayout(auto_group)

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("촬영 간격:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(500, 5000)
        self.interval_spin.setSingleStep(500)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSuffix(" ms")
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()
        auto_layout.addLayout(interval_row)

        self.auto_good_check   = QCheckBox("양품 연속 촬영")
        self.auto_defect_check = QCheckBox("불량 연속 촬영")
        auto_layout.addWidget(self.auto_good_check)
        auto_layout.addWidget(self.auto_defect_check)

        self.auto_btn = QPushButton("▶  연속 촬영 시작")
        self.auto_btn.setCheckable(True)
        self.auto_btn.setFixedHeight(34)
        self.auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5276; color: white;
                border-radius: 4px; font-size: 13px;
            }
            QPushButton:checked { background-color: #784212; }
            QPushButton:hover   { background-color: #2471a3; }
        """)
        self.auto_btn.clicked.connect(self._toggle_auto)
        auto_layout.addWidget(self.auto_btn)
        right.addWidget(auto_group)

        # 수집 현황
        stats_group  = QGroupBox("수집 현황")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("양품: 0장 | 불량: 0장 | 합계: 0장")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 13px; color: #aaaaaa;")
        stats_layout.addWidget(self.stats_label)
        right.addWidget(stats_group)

        right.addStretch()
        main_layout.addLayout(right, stretch=1)

        # 시그널 연결 — _init_ui() 마지막에 배치
        self.product_combo.currentTextChanged.connect(self._refresh_stats)

    def _capture_good(self):
        """양품 이미지를 4대 카메라에서 동시 저장합니다."""
        product = self.product_combo.currentText()
        for i, frame in enumerate(self.camera_manager.get_all_frames()):
            if frame is not None:
                self.image_saver.save(
                    frame        = frame,
                    camera_name  = self.camera_manager.cameras[i].name,
                    product_type = product,
                    label        = "good",
                )
        self._refresh_stats()

    def _capture_defect(self):
        """불량 이미지를 4대 카메라에서 동시 저장합니다."""
        product     = self.product_combo.currentText()
        defect_type = self.defect_type_combo.currentText()
        for i, frame in enumerate(self.camera_manager.get_all_frames()):
            if frame is not None:
                self.image_saver.save(
                    frame        = frame,
                    camera_name  = self.camera_manager.cameras[i].name,
                    product_type = product,
                    label        = "defect",
                    defect_type  = defect_type,
                )
        self._refresh_stats()

    def _auto_capture(self):
        """연속 촬영 타이머 콜백."""
        if self.auto_good_check.isChecked():
            self._capture_good()
        if self.auto_defect_check.isChecked():
            self._capture_defect()

    def _toggle_auto(self, checked: bool):
        """연속 촬영 ON/OFF."""
        if checked:
            self.auto_timer.start(self.interval_spin.value())
            self.auto_btn.setText("⏹  연속 촬영 중지")
        else:
            self.auto_timer.stop()
            self.auto_btn.setText("▶  연속 촬영 시작")

    def _refresh_stats(self):
        """수집 현황을 갱신합니다."""
        product      = self.product_combo.currentText()
        good_count   = self.image_saver.get_total_count(product, label="good")
        defect_count = self.image_saver.get_total_count(product, label="defect")
        total        = good_count + defect_count

        self.good_progress.setValue(min(good_count, TARGET_GOOD))
        self.good_count_label.setText(f"{good_count} / {TARGET_GOOD}장")
        self.defect_progress.setValue(min(defect_count, TARGET_DEFECT))
        self.defect_count_label.setText(f"{defect_count} / {TARGET_DEFECT}장")
        self.stats_label.setText(
            f"양품: {good_count}장 | 불량: {defect_count}장 | 합계: {total}장"
        )

    def _update_preview(self):
        """선택된 카메라의 프리뷰를 갱신합니다."""
        frame = self.camera_manager.get_frame(self.preview_combo.currentIndex())
        if frame is None:
            self.preview_label.setText("No Signal")
            return
        pixmap = self._to_pixmap(frame)
        self.preview_label.setPixmap(
            pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
        self.preview_label.setText("")

    def keyPressEvent(self, event):
        """F1: 양품 캡처 / F2: 불량 캡처."""
        if event.key() == Qt.Key_F1:
            self._capture_good()
        elif event.key() == Qt.Key_F2:
            self._capture_defect()

    @staticmethod
    def _to_pixmap(frame: np.ndarray) -> QPixmap:
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QPixmap.fromImage(
            QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        )