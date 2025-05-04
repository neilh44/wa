from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class SessionType(str, Enum):
    WHATSAPP = "whatsapp"
    
class SessionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ERROR = "error"

class SessionBase(BaseModel):
    user_id: UUID
    session_type: SessionType
    device_name: Optional[str] = None
    
class SessionCreate(SessionBase):
    pass
    
class Session(SessionBase):
    id: UUID = Field(default_factory=uuid4)
    status: SessionStatus = SessionStatus.INACTIVE
    session_data: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class SessionResponse(SessionBase):
    id: UUID
    status: SessionStatus
    expires_at: Optional[datetime]
    created_at: datetime
