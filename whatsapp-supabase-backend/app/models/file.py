from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class FileBase(BaseModel):
    filename: str
    phone_number: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    
class FileCreate(FileBase):
    pass
    
class File(FileBase):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    storage_path: str
    uploaded: bool = False
    upload_attempts: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class FileResponse(FileBase):
    id: UUID
    storage_path: str
    uploaded: bool
    created_at: datetime
