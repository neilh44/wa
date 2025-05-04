#!/bin/bash

# Script to create and populate backend code files
echo "Creating and populating backend code files..."

# Navigate to the backend directory
cd whatsapp-supabase-backend || { echo "Backend directory not found!"; exit 1; }

# Create requirements.txt
cat > requirements.txt << 'EOL'
fastapi==0.104.0
uvicorn==0.23.2
python-dotenv==1.0.0
pydantic==2.4.2
supabase==2.0.0
python-multipart==0.0.6
selenium==4.15.2
webdriver-manager==4.0.1
loguru==0.7.2
python-jose==3.3.0
passlib==1.7.4
httpx==0.25.1
bcrypt==4.0.1
pytest==7.4.3
EOL

# Create .env.example
cat > .env.example << 'EOL'
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Application Settings
APP_SECRET_KEY=your_app_secret_key
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# WhatsApp Settings
WHATSAPP_DATA_DIR=./whatsapp_data
EOL

# Create config.py
cat > app/config.py << 'EOL'
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

class Settings(BaseModel):
    # App settings
    app_name: str = "WhatsApp to Supabase"
    app_debug: bool = os.getenv("APP_DEBUG", "False").lower() == "true"
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    secret_key: str = os.getenv("APP_SECRET_KEY", "your-secret-key-here")
    
    # JWT Settings
    jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "your-jwt-secret")
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7  # 1 week
    
    # Supabase settings
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    
    # WhatsApp settings
    whatsapp_data_dir: str = os.getenv("WHATSAPP_DATA_DIR", "./whatsapp_data")

settings = Settings()
EOL

# Create main.py
cat > app/main.py << 'EOL'
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import settings
from app.api import auth, files, whatsapp, storage
from app.utils.security import get_current_user

app = FastAPI(
    title=settings.app_name,
    description="API for WhatsApp to Supabase file upload automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(files.router, prefix="/api/files", tags=["Files"], dependencies=[Depends(get_current_user)])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"], dependencies=[Depends(get_current_user)])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"], dependencies=[Depends(get_current_user)])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to WhatsApp to Supabase API"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug
    )
EOL

# Create logger.py
cat > app/utils/logger.py << 'EOL'
import sys
import os
from loguru import logger

# Configure logger
log_file_path = os.path.join("logs", "app.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO")  # Add stderr handler
logger.add(
    log_file_path, 
    rotation="10 MB", 
    retention="7 days", 
    level="DEBUG"
)

def get_logger():
    return logger
EOL

# Create security.py
cat > app/utils/security.py << 'EOL'
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional
from app.config import settings
from app.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against a provided password."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expires_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        # Get user from database (implementation depends on your storage)
        from app.services.auth_service import get_user_by_id
        user = get_user_by_id(user_id)
        
        if user is None:
            raise credentials_exception
            
        return user
    except JWTError:
        raise credentials_exception
EOL

# Create user.py model
cat > app/models/user.py << 'EOL'
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class UserBase(BaseModel):
    email: EmailStr
    username: str
    
class UserCreate(UserBase):
    password: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class User(UserBase):
    id: UUID = Field(default_factory=uuid4)
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_admin: bool
    created_at: datetime
    
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
EOL

# Create file.py model
cat > app/models/file.py << 'EOL'
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
EOL

# Create session.py model
cat > app/models/session.py << 'EOL'
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
EOL

# Create auth service
cat > app/services/auth_service.py << 'EOL'
from typing import Optional
from uuid import UUID
import os
from app.models.user import User, UserCreate, UserLogin, Token
from app.utils.security import hash_password, verify_password, create_access_token
from datetime import timedelta
from app.config import settings
from supabase import create_client, Client
from app.utils.logger import get_logger

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

def register_user(user_data: UserCreate) -> User:
    """Register a new user."""
    # Check if user already exists
    user_query = supabase.table("users").select("*").eq("email", user_data.email).execute()
    
    if user_query.data:
        raise ValueError("User with this email already exists")
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    
    user_dict = user_data.dict()
    user_dict.pop("password")  # Don't store plain password
    user_dict["hashed_password"] = hashed_password
    
    # Insert into Supabase
    result = supabase.table("users").insert(user_dict).execute()
    
    if not result.data:
        logger.error("Failed to create user")
        raise Exception("Failed to create user")
    
    return User(**result.data[0])

def authenticate_user(user_login: UserLogin) -> Optional[User]:
    """Authenticate a user and return user if credentials are valid."""
    user_query = supabase.table("users").select("*").eq("email", user_login.email).execute()
    
    if not user_query.data:
        return None
    
    user_data = user_query.data[0]
    
    if not verify_password(user_login.password, user_data.get("hashed_password", "")):
        return None
    
    return User(**user_data)

def create_user_token(user: User) -> Token:
    """Create a JWT token for the user."""
    access_token_expires = timedelta(minutes=settings.jwt_expires_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token)

def get_user_by_id(user_id: str) -> Optional[User]:
    """Get a user by ID."""
    user_query = supabase.table("users").select("*").eq("id", user_id).execute()
    
    if not user_query.data:
        return None
    
    return User(**user_query.data[0])
EOL

# Create whatsapp service
cat > app/services/whatsapp_service.py << 'EOL'
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from app.utils.logger import get_logger
from app.models.session import Session, SessionStatus
from app.config import settings
from supabase import create_client, Client

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

class WhatsAppService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.data_dir = os.path.join(settings.whatsapp_data_dir, str(user_id))
        os.makedirs(self.data_dir, exist_ok=True)
        self.driver = None
        self.session_id = None
    
    def initialize_session(self) -> Dict[str, Any]:
        """Initialize a WhatsApp session and return QR code data."""
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
        
        # Initialize the Chrome driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Open WhatsApp Web
        self.driver.get("https://web.whatsapp.com/")
        
        # Create a new session record
        session_data = {
            "user_id": str(self.user_id),
            "session_type": "whatsapp",
            "device_name": "Chrome",
            "status": SessionStatus.INACTIVE,
            "session_data": {}
        }
        
        # Save to database
        result = supabase.table("sessions").insert(session_data).execute()
        self.session_id = result.data[0]["id"] if result.data else None
        
        # Wait for QR code
        try:
            qr_code_element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
            )
            # In a real app, you'd extract QR code data from the canvas
            # This is a simplified version
            qr_data = {"qr_available": True, "session_id": self.session_id}
            return qr_data
        except Exception as e:
            logger.error(f"QR code not found: {e}")
            return {"qr_available": False, "error": str(e)}
    
    def check_session_status(self, session_id: UUID) -> Dict[str, Any]:
        """Check if the session is authenticated."""
        # Query session from database
        session_query = supabase.table("sessions").select("*").eq("id", str(session_id)).execute()
        
        if not session_query.data:
            return {"status": "not_found"}
        
        session_data = session_query.data[0]
        
        # If driver is not initialized, initialize it
        if not self.driver:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
            
            # Initialize the Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Open WhatsApp Web
            self.driver.get("https://web.whatsapp.com/")
        
        try:
            # Check if logged in by looking for a common element that appears after login
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-icon='chat']"))
            )
            
            # Update session status in database
            supabase.table("sessions").update({
                "status": SessionStatus.ACTIVE,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(session_id)).execute()
            
            return {"status": "authenticated"}
        except:
            return {"status": "not_authenticated"}
    
    def download_files(self) -> List[Dict[str, Any]]:
        """Download files from WhatsApp and return file info."""
        # This is a simplified implementation
        # In a real app, you'd need to monitor for new messages and download files
        
        # Placeholder for downloaded files
        downloaded_files = []
        
        # Update files in database
        for file_info in downloaded_files:
            file_data = {
                "user_id": str(self.user_id),
                "filename": file_info["filename"],
                "phone_number": file_info["phone_number"],
                "size": file_info["size"],
                "mime_type": file_info["mime_type"],
                "storage_path": file_info["local_path"],
                "uploaded": False
            }
            
            supabase.table("files").insert(file_data).execute()
        
        return downloaded_files
    
    def close_session(self):
        """Close the WhatsApp session."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        if self.session_id:
            # Update session status in database
            supabase.table("sessions").update({
                "status": SessionStatus.INACTIVE,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(self.session_id)).execute()
EOL

# Create storage service
cat > app/services/storage_service.py << 'EOL'
import os
from typing import Dict, List, Any, Optional
from uuid import UUID
from app.utils.logger import get_logger
from app.config import settings
from supabase import create_client, Client
from datetime import datetime

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

class StorageService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
    
    def upload_file(self, file_id: UUID) -> Dict[str, Any]:
        """Upload a file to Supabase Storage."""
        # Get file info from database
        file_query = supabase.table("files").select("*").eq("id", str(file_id)).execute()
        
        if not file_query.data:
            logger.error(f"File not found: {file_id}")
            return {"success": False, "error": "File not found"}
        
        file_data = file_query.data[0]
        local_path = file_data["storage_path"]
        
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return {"success": False, "error": "Local file not found"}
        
        try:
            # Organize by phone number in storage
            phone_number = file_data["phone_number"].replace("+", "").replace(" ", "")
            storage_path = f"{phone_number}/{file_data['filename']}"
            
            # Upload to Supabase Storage
            with open(local_path, "rb") as f:
                file_content = f.read()
                
            result = supabase.storage.from_("whatsapp_files").upload(
                storage_path,
                file_content,
                {"content-type": file_data.get("mime_type", "application/octet-stream")}
            )
            
            # Update file status in database
            supabase.table("files").update({
                "uploaded": True,
                "storage_path": storage_path,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(file_id)).execute()
            
            return {"success": True, "storage_path": storage_path}
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            
            # Update upload attempts
            supabase.table("files").update({
                "upload_attempts": file_data.get("upload_attempts", 0) + 1,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(file_id)).execute()
            
            return {"success": False, "error": str(e)}
    
    def get_files(self, phone_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get files from Supabase Storage, optionally filtered by phone number."""
        query = supabase.table("files").select("*").eq("user_id", str(self.user_id))
        
        if phone_number:
            query = query.eq("phone_number", phone_number)
        
        result = query.execute()
        return result.data if result.data else []
    
    def get_missing_files(self) -> List[Dict[str, Any]]:
        """Get files that have not been uploaded successfully."""
        result = supabase.table("files") \
            .select("*") \
            .eq("user_id", str(self.user_id)) \
            .eq("uploaded", False) \
            .execute()
        
        return result.data if result.data else []
EOL

# Create file service
cat > app/services/file_service.py << 'EOL'
from typing import Dict, List, Any, Optional
from uuid import UUID
from app.utils.logger import get_logger
from app.models.file import File, FileCreate
from app.services.storage_service import StorageService
from app.config import settings
from supabase import create_client, Client
from datetime import datetime

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

class FileService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.storage_service = StorageService(user_id)
    
    def get_user_files(self, phone_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all files for a user, optionally filtered by phone number."""
        return self.storage_service.get_files(phone_number)
    
    def sync_missing_files(self) -> Dict[str, Any]:
        """Synchronize missing files by uploading them to storage."""
        missing_files = self.storage_service.get_missing_files()
        
        if not missing_files:
            return {"message": "No missing files found", "files_synced": 0}
        
        files_synced = 0
        
        for file in missing_files:
            result = self.storage_service.upload_file(UUID(file["id"]))
            
            if result["success"]:
                files_synced += 1
        
        return {
            "message": f"Synced {files_synced} out of {len(missing_files)} files",
            "files_synced": files_synced,
            "total_missing": len(missing_files)
        }
    
    def create_file_record(self, file_data: FileCreate) -> File:
        """Create a new file record."""
        file_dict = file_data.dict()
        file_dict["user_id"] = str(self.user_id)
        file_dict["uploaded"] = False
        
        result = supabase.table("files").insert(file_dict).execute()
        
        if not result.data:
            logger.error("Failed to create file record")
            raise Exception("Failed to create file record")
        
        return File(**result.data[0])
EOL

# Create auth api
cat > app/api/auth.py << 'EOL'
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import register_user, authenticate_user, create_user_token
from app.utils.security import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    try:
        user = register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_login = UserLogin(email=form_data.username, password=form_data.password)
    user = authenticate_user(user_login)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return create_user_token(user)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return current_user
EOL

# Create files api
cat > app/api/files.py << 'EOL'
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from app.models.file import FileResponse, FileCreate
from app.models.user import User
from app.services.file_service import FileService
from app.utils.security import get_current_user
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[FileResponse])
async def get_files(
    phone_number: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    file_service = FileService(current_user.id)
    return file_service.get_user_files(phone_number)

@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    file_data: FileCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        file_service = FileService(current_user.id)
        return file_service.create_file_record(file_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_files(current_user: User = Depends(get_current_user)):
    try:
        file_service = FileService(current_user.id)
        return file_service.sync_missing_files()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
EOL

#!/bin/bash

# Fix for whatsapp.py file
cat > app/api/whatsapp.py << 'EOL'
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
from app.models.user import User
from app.services.whatsapp_service import WhatsAppService
from app.utils.security import get_current_user
from uuid import UUID

router = APIRouter()

@router.post("/session", status_code=status.HTTP_201_CREATED)
async def create_session(current_user: User = Depends(get_current_user)):
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        return whatsapp_service.initialize_session()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/session/{session_id}", status_code=status.HTTP_200_OK)
async def check_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        return whatsapp_service.check_session_status(session_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/download", status_code=status.HTTP_200_OK)
async def download_files(current_user: User = Depends(get_current_user)):
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        return {"files": whatsapp_service.download_files()}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/session/{session_id}", status_code=status.HTTP_200_OK)
async def close_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        whatsapp_service.close_session()
        return {"message": "Session closed successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
EOL

# Fix Dockerfile
cat > Dockerfile << 'EOL'
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs whatsapp_data

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOL

# Create logs directory
mkdir -p logs

echo "Fixed backend code files successfully!"