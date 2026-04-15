# 메인 윈도우 — 4개 카메라 영상 + 실시간 PatchCore 검사 결과 표시
import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QGridLayout, QLabel, QStatusBar,
    QComboBox, QPushButton,
    QHBoxLayout, QVBoxLayout,
    QSlider
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

from app.camera.camera_manager import CameraManager
from app.inspection.inspector import Inspector
from app.inspection.inspection_thread import InspectionThread
from app.utils.image_saver import ImageSaver


# 제품 종류 목록
PRODUCT_LIST = [
    "T68-MCR",
    "제품2", "제품3", "제품4", "제품5",
    "제품6", "제품7", "제품8", "제품9", "제품10"
]

# 모델 체크포인트 경로
CKPT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "models" / "patchcore_screw"
    / "Patchcore" / "MVTecAD" / "screw"
    / "v0" / "weights" / "lightning" / "model.ckpt"
)


class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스.
    4개 카메라 영상 표시 + 실시간 PatchCore 검사 결과 오버레이.
    """

    def __init__(self, camera_manager: CameraManager):
        super().__init__()
        self.camera_manager   = camera_manager
        self.image_saver      = ImageSaver(base_dir="data/raw")
        self.inspector        = None
        self.inspection_thread = None

        # 검사 활성화 여부 플래그
        self.inspection_enabled = False

        self._init_ui()
        self._init_inspector()
        self._init_timer()

    # ── 초기화 ───────────────────────────────────────

    def _init_ui(self):
        """UI 레이아웃을 구성합니다."""
        self.setWindowTitle("Vision Inspection System")
        self.setMinimumSize(1280, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── 상단 컨트롤 바 ──────────────────────────
        control_bar = QHBoxLayout()

        # 제품 선택
        self.product_combo = QComboBox()
        self.product_combo.addItems(PRODUCT_LIST)
        self.product_combo.setFixedWidth(160)
        self.product_combo.currentTextChanged.connect(self._on_product_changed)

        # 캡처 버튼
        self.capture_btn = QPushButton("📷  캡처  [Space]")
        self.capture_btn.setFixedHeight(34)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d7d46; color: white;
                border-radius: 4px; font-size: 13px; padding: 0 12px;
            }
            QPushButton:hover   { background-color: #3a9e5a; }
            QPushButton:pressed { background-color: #1f5c33; }
        """)
        self.capture_btn.clicked.connect(self._capture_all)

        # 검사 ON/OFF 버튼
        self.inspect_btn = QPushButton("🔍  검사 시작")
        self.inspect_btn.setFixedHeight(34)
        self.inspect_btn.setCheckable(True)
        self.inspect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5276; color: white;
                border-radius: 4px; font-size: 13px; padding: 0 12px;
            }
            QPushButton:checked { background-color: #922b21; }
            QPushButton:hover   { background-color: #2471a3; }
        """)
        self.inspect_btn.clicked.connect(self._toggle_inspection)

        # 저장 카운트
        self.count_label = QLabel("저장: 0장")
        self.count_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        # 검사 대상 카메라 선택
        cam_label = QLabel("검사 카메라:")
        self.cam_combo = QComboBox()
        self.cam_combo.setFixedWidth(100)

        control_bar.addWidget(QLabel("제품:"))
        control_bar.addWidget(self.product_combo)
        control_bar.addSpacing(8)
        control_bar.addWidget(self.capture_btn)
        control_bar.addSpacing(8)
        control_bar.addWidget(cam_label)
        control_bar.addWidget(self.cam_combo)
        control_bar.addSpacing(8)
        control_bar.addWidget(self.inspect_btn)
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
                color: #888888; font-size: 14px;
            """)
            cam_name = self.camera_manager.cameras[i].name
            label.setText(f"{cam_name}\n신호 없음")
            grid_layout.addWidget(label, row, col)
            self.cam_labels.append(label)

        main_layout.addLayout(grid_layout)

        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("초기화 완료 — Space: 캡처 / 검사 시작 버튼으로 AI 검사 활성화")

    def _init_inspector(self):
        """PatchCore 모델을 로드하고 검사 스레드를 초기화합니다."""
        if not CKPT_PATH.exists():
            self.status_bar.showMessage(
                f"[경고] 모델 파일 없음: {CKPT_PATH}"
            )
            return

        self.inspector = Inspector(ckpt_path=str(CKPT_PATH), threshold=None)
        if self.inspector.load():
            self.inspection_thread = InspectionThread(self.inspector)
            self.inspection_thread.start()

            # 검사 카메라 콤보박스 채우기
            for cam in self.camera_manager.cameras:
                self.cam_combo.addItem(cam.name)

            self.status_bar.showMessage(
                f"모델 로드 완료 — 임계값: {self.inspector.threshold:.2f}"
            )
        else:
            self.status_bar.showMessage("[오류] 모델 로드 실패")

    def _init_timer(self):
        """33ms 간격으로 화면 갱신 타이머 시작."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frames)
        self.timer.start(33)

    # ── 이벤트 핸들러 ────────────────────────────────

    def keyPressEvent(self, event):
        """스페이스바: 캡처 저장."""
        if event.key() == Qt.Key_Space:
            self._capture_all()

    def _on_product_changed(self, product_name: str):
        """제품 변경 시 저장 수 갱신."""
        count = self.image_saver.get_total_count(product_name)
        self.count_label.setText(f"저장: {count}장")

    def _toggle_inspection(self, checked: bool):
        """검사 ON/OFF 토글."""
        self.inspection_enabled = checked
        if checked:
            self.inspect_btn.setText("🔴  검사 중지")
            self.status_bar.showMessage("AI 검사 실행 중...")
        else:
            self.inspect_btn.setText("🔍  검사 시작")
            self.status_bar.showMessage("AI 검사 중지됨")

    def _capture_all(self):
        """4대 카메라 프레임을 모두 저장합니다."""
        product = self.product_combo.currentText()
        frames  = self.camera_manager.get_all_frames()
        saved   = 0

        for i, frame in enumerate(frames):
            if frame is not None:
                cam_name = self.camera_manager.cameras[i].name
                self.image_saver.save(
                    frame=frame,
                    camera_name=cam_name,
                    product_type=product
                )
                saved += 1

        total = self.image_saver.get_total_count(product)
        self.count_label.setText(f"저장: {total}장")
        self.status_bar.showMessage(
            f"✅ {product} — {saved}장 저장 완료 (누적: {total}장)"
        )

    # ── 프레임 갱신 ──────────────────────────────────

    def _update_frames(self):
        """타이머에 의해 주기적으로 호출 — 카메라 프레임 + 검사 결과 갱신."""
        frames = self.camera_manager.get_all_frames()

        # 검사 대상 카메라 인덱스
        inspect_idx = self.cam_combo.currentIndex()

        for i, frame in enumerate(frames):
            cam = self.camera_manager.cameras[i]

            if frame is None:
                self.cam_labels[i].setPixmap(QPixmap())
                status = "초기화 중..." if cam.is_connected else "No Signal"
                self.cam_labels[i].setText(f"{cam.name}\n{status}")
                continue

            display_frame = frame.copy()

            # 검사 활성화 + 해당 카메라인 경우 추론 요청 및 결과 오버레이
            if self.inspection_enabled and i == inspect_idx:
                # 새 프레임을 검사 스레드에 전달
                if self.inspection_thread:
                    self.inspection_thread.update_frame(frame)

                # 가장 최근 결과 가져와서 오버레이
                result = self.inspection_thread.get_result() \
                    if self.inspection_thread else None

                if result is not None:
                    display_frame = self.inspector.overlay_result(
                        display_frame, result
                    )
                    # 상태바에 실시간 판정 결과 표시
                    self.status_bar.showMessage(
                        f"[{cam.name}] {result.label}  "
                        f"Score: {result.anomaly_score:.2f}  "
                        f"Threshold: {result.threshold:.2f}"
                    )

            # 프레임을 QLabel에 표시
            pixmap = self._convert_frame_to_pixmap(display_frame)
            self.cam_labels[i].setPixmap(
                pixmap.scaled(
                    self.cam_labels[i].size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
            self.cam_labels[i].setText("")

    @staticmethod
    def _convert_frame_to_pixmap(frame: np.ndarray) -> QPixmap:
        """OpenCV BGR 프레임을 QPixmap으로 변환합니다."""
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)

    def closeEvent(self, event):
        """창 닫기 시 모든 스레드를 안전하게 종료합니다."""
        self.timer.stop()
        if self.inspection_thread:
            self.inspection_thread.stop()
        self.camera_manager.stop_all()
        event.accept()