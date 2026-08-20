from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────

class UserRegister(BaseModel):
    """手机号注册"""
    phone: str = Field(..., min_length=11, max_length=11, pattern=r'^1[3-9]\d{9}$')
    password: str = Field(..., min_length=6, max_length=50)
    verify_code: Optional[str] = None  # 验证码（预留接口，暂不验证）
    full_name: Optional[str] = Field(None, max_length=50)


class UserLogin(BaseModel):
    """手机号登录"""
    phone: str = Field(..., min_length=11, max_length=11, pattern=r'^1[3-9]\d{9}$')
    password: str = Field(..., min_length=6, max_length=50)


class SendCodeRequest(BaseModel):
    """发送验证码"""
    phone: str = Field(..., min_length=11, max_length=11, pattern=r'^1[3-9]\d{9}$')


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    phone: str


class UserResponse(BaseModel):
    id: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Resume Version ────────────────────────────────────────────

class ResumeVersionCreate(BaseModel):
    resume_profile_id: str
    version_name: str
    original_filename: str
    notes: Optional[str] = None


class ResumeVersionResponse(BaseModel):
    id: str
    resume_profile_id: str
    version_name: str
    original_filename: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Career Preference ─────────────────────────────────────────

class CareerPreferenceCreate(BaseModel):
    target_industry: Optional[str] = None
    target_role: Optional[str] = None
    target_location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    preferred_companies: Optional[List[str]] = None
    notes: Optional[str] = None


class CareerPreferenceResponse(BaseModel):
    id: int
    target_industry: Optional[str] = None
    target_role: Optional[str] = None
    target_location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    preferred_companies: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── User Profile ──────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    id: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
