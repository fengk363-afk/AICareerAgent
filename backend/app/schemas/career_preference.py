from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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
