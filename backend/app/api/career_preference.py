from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import CareerPreference
from app.schemas.career_preference import CareerPreferenceCreate, CareerPreferenceResponse

router = APIRouter()


@router.get("/", response_model=Optional[CareerPreferenceResponse])
async def get_preference(db: AsyncSession = Depends(get_db)):
    """获取当前用户求职偏好"""
    result = await db.execute(select(CareerPreference).limit(1))
    pref = result.scalar_one_or_none()
    if pref:
        return CareerPreferenceResponse.model_validate(pref)
    return None


@router.post("/", response_model=CareerPreferenceResponse)
async def create_preference(data: CareerPreferenceCreate, db: AsyncSession = Depends(get_db)):
    """创建或更新求职偏好"""
    # 检查是否已存在
    result = await db.execute(select(CareerPreference).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        # 更新
        for key, value in data.model_dump().items():
            if value is not None:
                setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return CareerPreferenceResponse.model_validate(existing)
    else:
        # 创建
        pref = CareerPreference(**data.model_dump())
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
        return CareerPreferenceResponse.model_validate(pref)


@router.put("/", response_model=CareerPreferenceResponse)
async def update_preference(data: CareerPreferenceCreate, db: AsyncSession = Depends(get_db)):
    """更新求职偏好"""
    result = await db.execute(select(CareerPreference).limit(1))
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(status_code=404, detail="偏好不存在")

    for key, value in data.model_dump().items():
        if value is not None:
            setattr(pref, key, value)

    await db.commit()
    await db.refresh(pref)
    return CareerPreferenceResponse.model_validate(pref)
