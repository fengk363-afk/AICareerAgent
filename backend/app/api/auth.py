import random
import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import User
from app.core.auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from app.schemas.auth import (
    UserRegister, UserLogin, SendCodeRequest,
    TokenResponse, UserResponse, UserProfileResponse,
)

router = APIRouter()
security = HTTPBearer()


def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """从 HTTPBearer 中提取 token 字符串"""
    return credentials.credentials

# 内存存储验证码（生产环境应使用 Redis）
_verify_codes: dict[str, tuple[str, float]] = {}


@router.post("/send-code", summary="发送验证码")
async def send_verify_code(data: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    """发送短信验证码（预留接口，实际发送逻辑待接入短信服务）"""
    # 检查手机号是否已注册
    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()
    if user and not user.is_active:
        raise HTTPException(status_code=400, detail="该手机号已被禁用")

    # 生成 6 位验证码
    code = str(random.randint(100000, 999999))
    _verify_codes[data.phone] = (code, time.time())

    return {"message": "演示验证码已生成", "phone": data.phone, "code": code}


@router.post("/register", response_model=UserResponse, summary="手机号注册")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """手机号注册"""
    # 检查手机号是否已注册
    result = await db.execute(select(User).where(User.phone == data.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    # 验证验证码
    stored = _verify_codes.get(data.phone)
    if not stored or stored[0] != data.verify_code or time.time() - stored[1] > 300:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    # 创建用户
    user = User(
        phone=data.phone,
        username=data.phone,  # 兼容旧逻辑
        email=f"{data.phone}@phone.local",  # 手机号用户自动生成邮箱占位
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        phone=user.phone,
        full_name=user.full_name,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse, summary="手机号登录")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """手机号密码登录"""
    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
        )
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
        )

    token = create_access_token({"sub": str(user.id), "phone": user.phone})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        phone=user.phone,
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user(token: str = Depends(get_token), db: AsyncSession = Depends(get_db)):
    """获取当前登录用户信息"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserResponse(
        id=str(user.id),
        phone=user.phone,
        full_name=user.full_name,
        created_at=user.created_at,
    )


@router.put("/me", response_model=UserResponse, summary="更新用户资料")
async def update_profile(
    data: dict,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
):
    """更新用户资料"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if "full_name" in data:
        user.full_name = data["full_name"]
    if "phone" in data:
        existing = await db.execute(select(User).where(User.phone == data["phone"], User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该手机号已被使用")
        user.phone = data["phone"]
    if "bio" in data:
        user.bio = data["bio"]

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        phone=user.phone,
        full_name=user.full_name,
        created_at=user.created_at,
    )


@router.post("/logout", summary="退出登录")
async def logout(token: str = Depends(get_token)):
    """退出登录（前端清除 token 即可）"""
    return {"message": "已退出登录"}
