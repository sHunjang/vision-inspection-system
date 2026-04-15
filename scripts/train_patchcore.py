# PatchCore 모델 학습 스크립트
# MVTec 형식 데이터셋으로 학습합니다.
# 사용법:
#   python scripts/train_patchcore.py              → MVTec screw (기본)
#   python scripts/train_patchcore.py T68-MCR      → 실제 수집 데이터
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from anomalib.data import MVTecAD
from anomalib.models import Patchcore
from anomalib.engine import Engine


def train(product: str = None):
    root_dir = Path(__file__).resolve().parent.parent

    if product:
        # 실제 수집 데이터 사용
        data_dir    = root_dir / "data" / "custom"
        category    = product
        output_dir  = root_dir / "models" / f"patchcore_{product.lower().replace('-', '_')}"
    else:
        # 기본값: MVTec screw 데이터셋
        data_dir    = root_dir / "data" / "mvtec"
        category    = "screw"
        output_dir  = root_dir / "models" / "patchcore_screw"

    print("=" * 50)
    print("Patchcore 모델 학습 시작")
    print(f"데이터 경로: {data_dir}")
    print(f"카테고리  : {category}")
    print(f"저장 경로 : {output_dir}")
    print("=" * 50)

    datamodule = MVTecAD(
        root             = str(data_dir),
        category         = category,
        train_batch_size = 32,
        eval_batch_size  = 32,
        num_workers      = 4,
    )

    model = Patchcore(
        backbone               = "wide_resnet50_2",
        layers                 = ["layer2", "layer3"],
        coreset_sampling_ratio = 0.1,
    )

    engine = Engine(
        max_epochs        = 1,
        accelerator       = "gpu",
        devices           = 1,
        default_root_dir  = str(output_dir),
    )

    print("\n학습 시작...")
    engine.fit(model=model, datamodule=datamodule)

    print("\n평가 시작...")
    results = engine.test(model=model, datamodule=datamodule)
    print("\n평가 결과:")
    print(results)

    print("\n✅ 학습 완료!")
    print(f"모델 저장 위치: {output_dir}")


if __name__ == "__main__":
    # 커맨드라인 인자로 제품명 지정 가능
    # 예: python scripts/train_patchcore.py T68-MCR
    product = sys.argv[1] if len(sys.argv) > 1 else None
    train(product=product)