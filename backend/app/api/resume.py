import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import ResumeProfile, ResumeVersion
from app.agents.engine import engine
from app.schemas.models import ResumeProfileResponse
from app.api.auth import get_token
from app.core.auth_utils import decode_access_token

router = APIRouter()

# 上传目录：限制在项目根目录的 uploads/ 下
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _safe_upload_path(filename: str) -> Path:
    """生成安全的上传路径，防止路径穿越"""
    safe_name = Path(filename).name  # 只取文件名，去掉路径部分
    return UPLOAD_DIR / safe_name


def _is_within_uploads(path: Path) -> bool:
    """校验路径是否在 uploads 目录内"""
    try:
        path.resolve().relative_to(UPLOAD_DIR.resolve())
        return True
    except ValueError:
        return False


@router.post("/upload", response_model=ResumeProfileResponse)
async def upload_resume(
    file: UploadFile = File(...),
    version_name: Optional[str] = None,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF 简历，创建新版本"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式")

    content = await file.read()

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user_id = int(payload.get("sub"))

    # 保存文件到 uploads 目录
    upload_path = _safe_upload_path(file.filename)
    with open(upload_path, "wb") as f:
        f.write(content)

    result = await engine.upload_resume(user_id, content, file.filename)

    # 查询真实 ORM 对象，设置 file_path 并持久化
    profile_result = await db.execute(
        select(ResumeProfile).where(ResumeProfile.id == result.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.file_path = str(upload_path)
        await db.commit()
        await db.refresh(profile)

    version = ResumeVersion(
        id=str(uuid.uuid4()),
        resume_profile_id=result.id,
        version_name=version_name or f"v{len(result.skills or [])}skills",
        original_filename=file.filename,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return result


@router.get("/profiles", response_model=list[ResumeProfileResponse])
async def list_profiles(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的简历画像"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user_id = int(payload.get("sub"))
    result = await db.execute(
        select(ResumeProfile)
        .where(ResumeProfile.user_id == user_id)
        .order_by(ResumeProfile.created_at.desc())
    )
    return [ResumeProfileResponse.model_validate(p) for p in result.scalars().all()]


@router.get("/profiles/{profile_id}", response_model=ResumeProfileResponse)
async def get_profile(
    profile_id: str,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
):
    """查询简历画像（需归属当前用户）"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user_id = int(payload.get("sub"))
    result = await db.execute(
        select(ResumeProfile)
        .where(ResumeProfile.id == profile_id, ResumeProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="简历画像不存在")
    return ResumeProfileResponse.model_validate(profile)


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
):
    """删除简历画像及对应 PDF 文件"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user_id = int(payload.get("sub"))
    result = await db.execute(
        select(ResumeProfile)
        .where(ResumeProfile.id == profile_id, ResumeProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="简历画像不存在")

    # 删除 PDF 文件（带路径安全校验）
    if profile.file_path:
        file_path = Path(profile.file_path)
        if _is_within_uploads(file_path):
            if file_path.exists():
                file_path.unlink()

    await db.delete(profile)
    await db.commit()
    return {"message": "删除成功"}
