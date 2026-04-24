# 검사 이력 조회 탭 위젯
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLabel,
    QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from app.database.db_manager import DBManager

PRODUCT_LIST = [
    "전체", "T68-MCR",
    "제품2", "제품3", "제품4", "제품5",
    "제품6", "제품7", "제품8", "제품9", "제품10"
]


class HistoryTab(QWidget):
    """검사 이력을 조회하는 탭."""

    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── 필터 바 ──────────────────────────────────
        filter_bar = QHBoxLayout()

        self.product_filter = QComboBox()
        self.product_filter.addItems(PRODUCT_LIST)
        self.product_filter.setFixedWidth(140)

        self.result_filter = QComboBox()
        self.result_filter.addItems(["전체", "OK", "DEFECT"])
        self.result_filter.setFixedWidth(100)

        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setFixedHeight(30)
        refresh_btn.clicked.connect(self.refresh)

        # 통계 라벨
        self.stats_label = QLabel("총: 0건 | OK: 0 | DEFECT: 0 | 불량률: 0.0%")
        self.stats_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        filter_bar.addWidget(QLabel("제품:"))
        filter_bar.addWidget(self.product_filter)
        filter_bar.addSpacing(8)
        filter_bar.addWidget(QLabel("결과:"))
        filter_bar.addWidget(self.result_filter)
        filter_bar.addSpacing(8)
        filter_bar.addWidget(refresh_btn)
        filter_bar.addSpacing(16)
        filter_bar.addWidget(self.stats_label)
        filter_bar.addStretch()

        layout.addLayout(filter_bar)

        # ── 이력 테이블 ──────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "일시", "제품", "카메라", "결과", "Score", "Threshold"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch  # 일시 컬럼을 넓게
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #333; }
            QTableWidget::item:alternate { background-color: #333; }
        """)

        layout.addWidget(self.table)

        # 필터 변경 시 자동 새로고침
        self.product_filter.currentTextChanged.connect(self.refresh)
        self.result_filter.currentTextChanged.connect(self.refresh)

    def refresh(self):
        """DB에서 이력을 불러와 테이블을 갱신합니다."""
        product = self.product_filter.currentText()
        result  = self.result_filter.currentText()

        product = None if product == "전체" else product
        result  = None if result  == "전체" else result

        logs  = self.db_manager.get_logs(limit=200, product=product, result=result)
        stats = self.db_manager.get_stats(product=product)

        # 통계 갱신
        self.stats_label.setText(
            f"총: {stats['total']}건 | "
            f"OK: {stats['ok_count']} | "
            f"DEFECT: {stats['defect_count']} | "
            f"불량률: {stats['defect_rate']:.1f}%"
        )

        # 테이블 갱신
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            values = [
                str(log["id"]),
                log["timestamp"],
                log["product"],
                log["camera"],
                log["result"],
                f"{log['score']:.2f}",
                f"{log['threshold']:.2f}",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)

                # 결과에 따라 색상 구분
                if col == 4:  # 결과 컬럼
                    if val == "DEFECT":
                        item.setForeground(QColor("#e74c3c"))
                    else:
                        item.setForeground(QColor("#2ecc71"))

                self.table.setItem(row, col, item)