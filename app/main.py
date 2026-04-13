# 애플리케이션 진입점 - 카메라 매니저와 GUI를 초기화하고 실행
import sys
from PyQt5.QtWidgets import QApplication

from app.camera.camera_manager import CameraManager
from app.gui.main_window import MainWindow


def main():
    # PyQt5 앱 객체 생성 (모든 PyQt5 앱은 반드시 QApplication이 있어야 함.)
    app = QApplication(sys.argv)
    
    # 카메라 매니저 초기화 및 전체 카메라 시작
    manager = CameraManager()
    manager.start_all()
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow(camera_manager=manager)
    window.show()
    
    # 앱 이벤트 루스 실행 (창이 닫힐 때까지 여기서 대기)
    sys.exit(app.exec_())
    
    
if __name__ == "__main__":
    main()