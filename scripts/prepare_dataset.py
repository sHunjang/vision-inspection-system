# 수집된 원본 이미지를 Anomalib MVTec 형식의 학습 데이터셋으로 변환하는 스크립트
# 실행 전 data/raw/ 폴더에 이미지가 수집되어 있어야 함

"""
변환 결과:
    data/raw/{product}/good/**/*.jpg
        -> data/custom/{product}/train/good/*.jpg  (80%)
        -> data/custom/{product}/test/good/*.jpg   (20%)
    
    data/raw/{product}/defect/{defect_type}/**/*.jpg
        -> data/custom/{product}/defect/{defect_type}/**/*.jpg
        -> data/custom/{product}/text/{defect_type}/*.jpg
"""

import os
import sys
import shutil
import random
from pathlib import Path

# 프로젝트 루트 기준 경로
ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
CUSTOM_DIR = ROOT_DIR / "data" / "custom"

# 양품 데이터 train/test 분할 비율
TRAIN_RATIO = 0.8


def collect_images(folder: Path) -> list:
    """
    지정 폴더 하위의 모든 .jpg / .png 등 파일 경로를 재귀적으로 수집
    """
    images = []
    
    for ext in ("*.jpg", "*.png", "*.jpeg"):
        images.extend(folder.rglob(ext))
    return sorted(images)


def copy_images(src_list: list, dst_dir: Path, prefix: str = ""):
    """
    이미지 목록을 dst_dir에 복사
    파일명 충돌 방지를 위해 순번을 할당
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    for i, src in enumerate(src_list):
        ext = src.suffix
        filename = f"{prefix}{i:04d}{ext}"
        dst = dst_dir / filename
        shutil.copy2(src, dst)


def prepare_product(product: str):
    """
    단일 제품의 raw 이미지를 MVTec 형식으로 변환
    """
    raw_product_dir = RAW_DIR / product
    
    if not raw_product_dir.exists():
        print(f"  [건너뜀] {product} - 수집 데이터 없음")
        return
    
    print(f"\n{'='*50}")
    print(f"  제품: {product}")
    print(f"{'='*50}")
    
    
    # 양품 처리
    good_dir = raw_product_dir / "good"
    
    if good_dir.exists():
        good_images = collect_images(good_dir)
        total = len(good_images)
        
        if total == 0:
            print(" [양품] 이미지 없음")
        else:
            # 무작위 셔플 후 train/test 분할
            random.shuffle(good_images)
            split_idx = int(total * TRAIN_RATIO)
            train_images = good_images[:split_idx]
            test_images = good_images[split_idx:]
            
            # 복사
            train_dst = CUSTOM_DIR / product / "train" / "good"
            test_dst = CUSTOM_DIR / product / "test" / "good"
            
            copy_images(train_images, train_dst, prefix="good_train_")
            copy_images(test_images, test_dst, prefix="good_test_")
            
            print(f"  [양품] 전체 {total}장")
            print(f"         → train/good : {len(train_images)}장")
            print(f"         → test/good  : {len(test_images)}장")
    else:
        print("[양품] 폴더 없음")
    
    
    # 불량 처리
    defect_dir = raw_product_dir / "defect"
    
    if defect_dir.exists():
        defect_types = [d for d in defect_dir.iterdir() if d.is_dir()]
    
        if not defect_types:
            print("[불량] 불량 유형 폴더 없음")
        else:
            for dtype_dir in sorted(defect_types):
                defect_images = collect_images(dtype_dir)
                
                if not defect_images:
                    continue
                
                # 불량은 전량 test 폴더로
                dst = CUSTOM_DIR / product / "test" / dtype_dir.name
                copy_images(defect_images, dst, prefix=f"{dtype_dir.name}_")
                
                print(f"[불량] {dtype_dir.name}: {len(defect_images)}장 -> test/{dtype_dir.name}/")
    
    else:
        print("[불량] 폴더 없음 (양품만으로도 학습 가능)")
    
    
    # 결과 요약
    custom_product = CUSTOM_DIR / product
    
    print(f"\n 저장 경로: {custom_product}")
    _print_structure(custom_product)


def _print_structure(base: Path, indent: int = 0):
    """폴더 구조와 이미지 수를 출력"""
    if not base.exists():
        return
    
    for item in sorted(base.iterdir()):
        prefix = "  " * indent + "├── "
        
        if item.is_dir():
            count = len(list(item.rglob("*.jpg"))) + len(list(item.rglob("*.png")))
            print(f"{prefix}{item.name} / {count}장")
            _print_structure(item, indent + 1)


def main():
    print("=" * 50)
    print("데이터셋 구성")
    print(f"원본 경로 : {RAW_DIR}")
    print(f"출력 경로 : {CUSTOM_DIR}")
    print(f"Train 비율: {int(TRAIN_RATIO*100)}% / Test 비율: {int((1-TRAIN_RATIO)*100)}%")
    print("=" * 50)
    
    # 특정 제품 지정 또는 전체 처리
    if len(sys.argv) > 1:
        # 예: python scripts/prepare_dataset.py T68-MCR
        products = sys.argv[1:]
    else:
        # 인자 없으면 data/raw/ 하위 전체 제품 처리
        if not RAW_DIR.exists():
            print(f"[오류] 원본 데이터 폴더 없음: {RAW_DIR}")
            return
        
        products = [d.name for d in RAW_DIR.iterdir() if d.is_dir()]
    
    if not products:
        print("[오류] 처리할 제품 없음")
        return
    
    print(f"\n처리 대상 제품: {products}")
    
    
    # 기존 custom 폴더 초기화 여부 확인
    if CUSTOM_DIR.exists():
        print(f"\n[주의] 기존 데이터셋 폴더가 존재합니다: {CUSTOM_DIR}")
        answer = input("기존 데이터를 삭제하고 새로 생성하시겠습니까? (y/n): ".strip().lower())
        
        if answer == 'y':
            shutil.rmtree(CUSTOM_DIR)
            print(" 기존 데이터셋 삭제 완료")
        else:
            print(" 기존 데이터 유지 - 덮어쓰기 방식으로 진행")
    
    for product in products:
        prepare_product(product)
    
    print(f"\n{'=' * 50}")
    print("데이터셋 변환 완료")
    print(f" 학습 시 root='{CUSTOM_DIR}'로 지정하세요.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    random.seed(42)     # 재현 가능한 분할을 위해 시드 고정
    main()