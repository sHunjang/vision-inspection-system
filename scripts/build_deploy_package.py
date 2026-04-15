# 배포 패키지를 생성하는 스크립트
# 소스코드 + 모델 + 런처 스크립트를 하나의 폴더로 묶습니다.
import shutil
import os
from pathlib import Path
from datetime import datetime

ROOT_DIR   = Path(__file__).resolve().parent.parent
DEPLOY_DIR = ROOT_DIR / f"vision-inspection-deploy"


def build():
    print("=" * 50)
    print("배포 패키지 생성")
    print(f"출력: {DEPLOY_DIR}")
    print("=" * 50)

    # 기존 배포 폴더 초기화
    if DEPLOY_DIR.exists():
        shutil.rmtree(DEPLOY_DIR)
    DEPLOY_DIR.mkdir()

    # 1. 소스 코드 복사 (app/)
    print("\n[1/5] 소스 코드 복사...")
    shutil.copytree(ROOT_DIR / "app",     DEPLOY_DIR / "app")
    shutil.copytree(ROOT_DIR / "configs", DEPLOY_DIR / "configs")
    print("  app/, configs/ 복사 완료")

    # 2. 모델 파일 복사 (.ckpt 만)
    print("\n[2/5] 모델 파일 복사...")
    models_dst = DEPLOY_DIR / "models"
    ckpt_files = [
        f for f in (ROOT_DIR / "models").rglob("*.ckpt")
        if "latest" not in f.parts
    ]
    for ckpt in ckpt_files:
        relative = ckpt.relative_to(ROOT_DIR / "models")
        dst      = models_dst / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ckpt, dst)
        print(f"  복사: {relative}")

    # 3. 런처 스크립트 복사
    print("\n[3/5] 런처 스크립트 복사...")
    for bat in ["install.bat", "run.bat", "update_model.bat"]:
        src = ROOT_DIR / bat
        if src.exists():
            shutil.copy2(src, DEPLOY_DIR / bat)
            print(f"  복사: {bat}")

    # 4. requirements 복사
    print("\n[4/5] requirements 복사...")
    req_src = ROOT_DIR / "requirements_deploy.txt"
    if req_src.exists():
        shutil.copy2(req_src, DEPLOY_DIR / "requirements.txt")
    else:
        shutil.copy2(ROOT_DIR / "requirements.txt", DEPLOY_DIR / "requirements.txt")
    print("  requirements.txt 복사 완료")

    # 5. README 복사
    print("\n[5/5] README 복사...")
    readme = ROOT_DIR / "README.txt"
    if readme.exists():
        shutil.copy2(readme, DEPLOY_DIR / "README.txt")

    # 빈 data 폴더 생성
    (DEPLOY_DIR / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (DEPLOY_DIR / "data" / "custom").mkdir(parents=True, exist_ok=True)

    # 결과 출력
    total_size = sum(
        f.stat().st_size
        for f in DEPLOY_DIR.rglob("*")
        if f.is_file()
    )
    print(f"\n{'='*50}")
    print(f"✅ 배포 패키지 생성 완료!")
    print(f"   경로: {DEPLOY_DIR}")
    print(f"   크기: {total_size / 1024 / 1024:.1f} MB")
    print(f"{'='*50}")


if __name__ == "__main__":
    build()