from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    status: str
    storage_key: str
    created_at: datetime | None = None
    extracted_data: dict | None = None
    class Config: from_attributes = True
