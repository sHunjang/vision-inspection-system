# PyInstaller 패키징 환경과 일반 실행 환경 파일 경로 반환 유틸 모듈
import os
import sys
from pathlib import Path


def get_base_dir() -> Path:
    """
    실행 환경에 따라 프로젝트 루트 경로 반환
    
    일반 실행: 프로젝트 루트 디렉토리
    PyInstaller: 압축 해제된 임시 디렉토리 (_MEIPASS)
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우
        # sys._MEIPASS: PyInstaller가 임시로 파일을 풀어놓는 경우
        return Path(sys._MEIPASS)
    else:
        # 일반 Python 실행의 경우
        return Path(__file__).resolve().parent.parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    리소스 파일의 절대 경로를 반환
    
    relative_path: 프로젝트 루트 기준 상대 경로
        ex: "models/patchcore_screw/.../model.ckpt"
    """
    return get_base_dir() / relative_path


def get_data_dir() -> Path:
    """
    데이터 저장 경로 반환
    패키징 환경에서 실행 파일 옆에 data/ 폴더 사용
    """
    if getattr(sys, 'frozen', False):
        # 패키징된 경우: 실행 파일이 있는 폴더 기준
        return Path(sys.executable).parent / "data"
    else:
        # 일반 실행: 프로젝트 루트 기준
        return get_base_dir() / "data"


def get_model_path(model_name: str) -> Path:
    """
    모델 파일 경로 반환
    패키징 환경에서 실행 파일 옆에 models/ 폴더 사용
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / "models" / model_name
    else: 
        return get_base_dir() / "models" / model_name