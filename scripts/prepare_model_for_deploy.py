# 배포용 모델 파일만 추출하는 스크립트
# models/ 폴더에서 .ckpt 파일만 deploy_models/ 폴더로 복사합니다.
import shutil
from pathlib import Path

ROOT_DIR         = Path(__file__).resolve().parent.parent
MODELS_DIR       = ROOT_DIR / "models"
DEPLOY_DIR       = ROOT_DIR / "deploy_models"


def prepare():
    print("=" * 50)
    print("배포용 모델 파일 추출")
    print(f"원본: {MODELS_DIR}")
    print(f"출력: {DEPLOY_DIR}")
    print("=" * 50)

    # 기존 deploy_models 폴더 초기화
    if DEPLOY_DIR.exists():
        shutil.rmtree(DEPLOY_DIR)
    DEPLOY_DIR.mkdir()

    # models/ 하위의 모든 .ckpt 파일 탐색
    ckpt_files = [
        f for f in MODELS_DIR.rglob("*.ckpt")
        if "latest" not in f.parts
    ]

    if not ckpt_files:
        print("[오류] .ckpt 파일을 찾을 수 없습니다.")
        return

    for ckpt in ckpt_files:
        # 상대 경로 유지하며 복사
        # 예: models/patchcore_screw/Patchcore/MVTecAD/screw/v0/weights/lightning/model.ckpt
        #  → deploy_models/patchcore_screw/Patchcore/MVTecAD/screw/v0/weights/lightning/model.ckpt
        relative = ckpt.relative_to(MODELS_DIR)
        dst      = DEPLOY_DIR / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ckpt, dst)
        print(f"[복사] {relative}")

    print(f"\n✅ 완료 — {len(ckpt_files)}개 모델 파일 추출")
    print(f"   배포 시 deploy_models/ 폴더를 models/ 로 이름 바꿔서 포함하세요.")

    # 용량 비교
    original_size = sum(f.stat().st_size for f in MODELS_DIR.rglob("*") if f.is_file())
    deploy_size   = sum(f.stat().st_size for f in DEPLOY_DIR.rglob("*") if f.is_file())
    print(f"\n   원본 크기  : {original_size / 1024 / 1024:.1f} MB")
    print(f"   배포 크기  : {deploy_size   / 1024 / 1024:.1f} MB")
    print(f"   절약       : {(original_size - deploy_size) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    prepare()