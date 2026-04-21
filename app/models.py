from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, HttpUrl


class MetadataRequest(BaseModel):
    url: HttpUrl


class MetadataRecord(BaseModel):
    url: str
    status_code: int
    headers: Dict[str, str]
    cookies: Dict[str, str]
    page_source: str
    fetched_at: datetime


class AcceptedResponse(BaseModel):
    message: str
    url: str
