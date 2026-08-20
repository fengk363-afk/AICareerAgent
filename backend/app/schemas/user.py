from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
