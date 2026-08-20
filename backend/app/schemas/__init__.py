from pydantic import BaseModel
from typing import Optional, List


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class APIEndpoint(BaseModel):
    method: str
    path: str
    description: str
    params: Optional[dict] = None
    body: Optional[dict] = None
    response: Optional[dict] = None
