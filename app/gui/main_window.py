# 메인 윈도우 — 탭 구조로 전체 UI 통합
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar
)
from PyQt5.QtCore import QTimer

from app.camera.camera_manager import CameraManager
from app.inspection.inspector import Inspector
from app.inspection.inspection_thread import InspectionThread
from app.database.db_manager import DBManager
from app.utils.image_saver import ImageSaver
from app.gui.inspection_tab import InspectionTab
from app.gui.history_tab import HistoryTab
from app.gui.collection_tab import CollectionTab

from app.utils.path_utils import get_model_path
from app.utils.path_utils import get_data_dir


CKPT_PATH = get_model_path(
    "patchcore_screw/Patchcore/MVTecAD/screw/v0/weights/lightning/model.ckpt"
)


class MainWindow(QMainWindow):
    """탭 구조의 메인 윈도우."""

    def __init__(self, camera_manager: CameraManager):
        super().__init__()
        
        data_dir = get_data_dir()
        
        self.camera_manager = camera_manager

        # 공유 객체 초기화
        self.db_manager   = DBManager(db_path=str(data_dir / "inspection.db"))
        self.image_saver  = ImageSaver(base_dir=str(data_dir / "raw"))
        self.inspector    = None
        self.insp_thread  = None

        self._init_inspector()
        self._init_ui()
        self._init_timer()

    def _init_inspector(self):
        """PatchCore 모델 로드."""
        if not CKPT_PATH.exists():
            print(f"[경고] 모델 파일 없음: {CKPT_PATH}")
            return

        self.inspector = Inspector(ckpt_path=str(CKPT_PATH), threshold=None)
        if self.inspector.load():
            # 카메라 이름 목록 전달 → 4대 동시 추론 스레드 생성
            cam_names = [cam.name for cam in self.camera_manager.cameras]
            self.insp_thread = InspectionThread(
                inspector  = self.inspector,
                cam_names  = cam_names
            )
            self.insp_thread.start()
            print("[모델] 로드 완료")

        self.inspector = Inspector(ckpt_path=str(CKPT_PATH), threshold=None)
        if self.inspector.load():
            self.insp_thread = InspectionThread(self.inspector)
            self.insp_thread.start()
            print("[모델] 로드 완료")

    def _init_ui(self):
        """탭 구조 UI 초기화."""
        self.setWindowTitle("Vision Inspection System")
        self.setMinimumSize(1280, 820)

        # 탭 위젯
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabBar::tab { min-width: 120px; padding: 6px 16px; }
            QTabBar::tab:selected { font-weight: bold; }
        """)

        # 탭 1: 실시간 검사
        self.inspection_tab = InspectionTab(
            camera_manager    = self.camera_manager,
            inspection_thread = self.insp_thread,
            inspector         = self.inspector,
            db_manager        = self.db_manager,
            image_saver       = self.image_saver,
        )
        tab_widget.addTab(self.inspection_tab, "🔍  실시간 검사")

        # 탭 2: 데이터 수집 (기존 탭 2 앞에 추가)
        self.collection_tab = CollectionTab(
            camera_manager = self.camera_manager,
            image_saver    = self.image_saver,
        )
        tab_widget.addTab(self.collection_tab, "📸  데이터 수집")

        # 탭 3: 검사 이력
        self.history_tab = HistoryTab(db_manager=self.db_manager)
        tab_widget.addTab(self.history_tab, "📋  검사 이력")

        # 탭 전환 시 이력 자동 새로고침
        tab_widget.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(tab_widget)

        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        threshold_info = (
            f"임계값: {self.inspector.threshold:.2f}"
            if self.inspector else "모델 없음"
        )
        self.status_bar.showMessage(
            f"Vision Inspection System 준비 완료 — {threshold_info}"
        )

    def _init_timer(self):
        """33ms 간격 화면 갱신 타이머."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(33)

    def _update(self):
        """타이머 콜백 — 현재 탭만 갱신."""
        self.inspection_tab.update_frames()

    def _on_tab_changed(self, index: int):
        """탭 전환 시 이력 탭 새로고침."""
        if index == 2:
            self.history_tab.refresh()

    def keyPressEvent(self, event):
        """스페이스바: 캡처."""
        from PyQt5.QtCore import Qt
        if event.key() == Qt.Key_Space:
            self.inspection_tab.capture_all()

    def closeEvent(self, event):
        """종료 시 모든 스레드 안전하게 종료."""
        self.timer.stop()
        if self.insp_thread:
            self.insp_thread.stop()
        self.camera_manager.stop_all()
        event.accept()