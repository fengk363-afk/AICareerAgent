from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


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
