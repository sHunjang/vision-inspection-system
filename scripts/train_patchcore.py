# PatchCore 모델 학습 스크립트
# MVTec screw 데이터셋으로 학습하고 모델을 저장합니다.
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from anomalib.data import MVTecAD
from anomalib.models import Patchcore
from anomalib.engine import Engine


def train():
    # ── 경로 설정 ────────────────────────────────────
    root_dir   = Path(__file__).resolve().parent.parent
    data_dir   = root_dir / "data" / "mvtec"
    output_dir = root_dir / "models" / "patchcore_screw"

    print("=" * 50)
    print("Patchcore 모델 학습 시작")
    print(f"데이터 경로: {data_dir}")
    print(f"저장 경로  : {output_dir}")
    print("=" * 50)

    # ── 데이터셋 설정 ────────────────────────────────
    # Anomalib 2.x: image_size 파라미터 제거됨
    datamodule = MVTecAD(
        root=str(data_dir),      # 데이터 루트 경로
        category="screw",        # 카테고리
        train_batch_size=32,     # 학습 배치 크기
        eval_batch_size=32,      # 평가 배치 크기
        num_workers=4,           # 데이터 로딩 병렬 수
    )

    # ── 모델 설정 ────────────────────────────────────
    # PatchCore: ResNet 백본으로 특징 추출 후 메모리 뱅크 구축
    model = Patchcore(
        backbone="wide_resnet50_2",   # 특징 추출 백본
        layers=["layer2", "layer3"],  # 특징 추출 레이어
        coreset_sampling_ratio=0.1,   # 메모리 뱅크 샘플링 비율
    )

    # ── 학습 엔진 설정 ───────────────────────────────
    engine = Engine(
        max_epochs=1,                      # PatchCore는 1 에폭으로 충분
        accelerator="gpu",                 # RTX 5060 GPU 사용
        devices=1,
        default_root_dir=str(output_dir),  # 결과 저장 경로
    )

    # ── 학습 실행 ────────────────────────────────────
    print("\n학습 시작...")
    engine.fit(model=model, datamodule=datamodule)

    # ── 평가 실행 ────────────────────────────────────
    print("\n평가 시작...")
    results = engine.test(model=model, datamodule=datamodule)
    print("\n평가 결과:")
    print(results)

    print("\n✅ 학습 완료!")
    print(f"모델 저장 위치: {output_dir}")


if __name__ == "__main__":
    train()