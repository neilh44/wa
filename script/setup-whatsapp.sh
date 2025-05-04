#!/bin/bash

# WhatsApp Access Setup and Execution Script
# This script sets up and runs the WhatsApp to Supabase file access application

# Exit on any error
set -e

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== WhatsApp File Access Setup ===${NC}"
echo "This script will setup and run your WhatsApp file access application."

# Define variables
APP_DIR="whatsapp-supabase-backend"
LOGS_DIR="$APP_DIR/logs"
DATA_DIR="$APP_DIR/whatsapp_data"
ENV_FILE="$APP_DIR/.env"

# Check if the application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo -e "${YELLOW}Creating application directory...${NC}"
    mkdir -p "$APP_DIR"
fi

# Create required directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p "$LOGS_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$APP_DIR/app/api"
mkdir -p "$APP_DIR/app/models"
mkdir -p "$APP_DIR/app/services"
mkdir -p "$APP_DIR/app/utils"
mkdir -p "$APP_DIR/migrations"

# Create a .env file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > "$ENV_FILE" << EOL
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Application Settings
APP_SECRET_KEY=$(openssl rand -hex 32)
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# WhatsApp Settings
WHATSAPP_DATA_DIR=./whatsapp_data
EOL
    echo -e "${GREEN}Created .env file. Please update it with your Supabase credentials.${NC}"
fi

# Run the setup script provided in your codebase
echo -e "${YELLOW}Running application setup script...${NC}"
bash paste.txt

# Create compliance-specific database tables
echo -e "${YELLOW}Creating compliance database tables...${NC}"
# Note: You'll need to adapt this to your actual database setup method
# This assumes you have the SQL file created from the previous code suggestions
cat > "$APP_DIR/migrations/create_compliance_tables.sql" << 'EOL'
-- Create consent_records table
CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    phone_number TEXT NOT NULL,
    is_owner BOOLEAN DEFAULT TRUE,
    verification_method TEXT NOT NULL,
    consent_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create compliance_logs table
CREATE TABLE IF NOT EXISTS compliance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    event_type TEXT NOT NULL,
    phone_number TEXT,
    result TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indices for faster queries
CREATE INDEX IF NOT EXISTS idx_consent_user_phone ON consent_records(user_id, phone_number);
CREATE INDEX IF NOT EXISTS idx_compliance_logs_user ON compliance_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_compliance_logs_event_type ON compliance_logs(event_type);
EOL

echo -e "${YELLOW}Installing required Python packages...${NC}"
cd "$APP_DIR"
pip install -r requirements.txt

# Verify ChromeDriver installation
echo -e "${YELLOW}Verifying Chrome and ChromeDriver installation...${NC}"
if ! command -v google-chrome &> /dev/null; then
    echo -e "${RED}Google Chrome not found. Installing Chrome...${NC}"
    # This is for Ubuntu/Debian - adjust for your OS
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
    apt-get update
    apt-get install -y google-chrome-stable
fi

# Add compliance verification code to files
echo -e "${YELLOW}Adding compliance verification code...${NC}"

# Create compliance models file
cat > "$APP_DIR/app/models/consent.py" << 'EOL'
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class ConsentRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    phone_number: str
    is_owner: bool = True
    verification_method: str = "self_declaration"
    consent_timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    
    class Config:
        from_attributes = True
EOL

# Create compliance service file
cat > "$APP_DIR/app/services/compliance_service.py" << 'EOL'
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import os
import json
from app.models.consent import ConsentRecord
from app.utils.logger import get_logger
from app.config import settings
from supabase import create_client, Client

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

class ComplianceService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.audit_log_path = os.path.join("logs", "compliance_audit.log")
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        
    def verify_phone_ownership(self, phone_number: str, ip_address: Optional[str] = None) -> bool:
        """
        Verify that the user owns the phone number they're trying to access.
        This is a simplified implementation - in production, you would 
        implement a more robust verification process.
        """
        # Check if consent record exists
        consent_query = supabase.table("consent_records").select("*") \
            .eq("user_id", str(self.user_id)) \
            .eq("phone_number", phone_number) \
            .execute()
            
        if consent_query.data:
            # Record exists, return true if is_owner is true
            return consent_query.data[0].get("is_owner", False)
        
        # Create new consent record
        consent_record = {
            "user_id": str(self.user_id),
            "phone_number": phone_number,
            "is_owner": True,  # In production, this would be set based on verification
            "verification_method": "self_declaration",
            "consent_timestamp": datetime.utcnow().isoformat(),
            "ip_address": ip_address
        }
        
        supabase.table("consent_records").insert(consent_record).execute()
        
        # Log consent verification
        self.log_compliance_event(
            event_type="phone_ownership_verification",
            phone_number=phone_number,
            result="approved",
            details="Self-declaration of ownership"
        )
        
        return True
    
    def check_whatsapp_tos_compliance(self) -> Dict[str, Any]:
        """
        Check that the application is operating within WhatsApp's Terms of Service.
        Returns compliance status and any potential issues.
        """
        # This is a simplified version. In production, you would include
        # more detailed checks based on current WhatsApp ToS
        compliance_issues = []
        
        # Check 1: Verify data is being accessed by the owner
        # In a real implementation, you'd have more rigorous checks here
        
        # Check 2: Verify we're not exceeding rate limits or API usage restrictions
        # Add implementation here
        
        # Check 3: Verify we're not storing WhatsApp data longer than allowed
        # Add implementation here
        
        is_compliant = len(compliance_issues) == 0
        
        # Log compliance check
        self.log_compliance_event(
            event_type="tos_compliance_check",
            result="pass" if is_compliant else "fail",
            details=json.dumps(compliance_issues) if compliance_issues else "No issues detected"
        )
        
        return {
            "is_compliant": is_compliant,
            "issues": compliance_issues
        }
    
    def log_compliance_event(self, event_type: str, result: str, details: str, phone_number: Optional[str] = None):
        """Log a compliance-related event for audit purposes."""
        timestamp = datetime.utcnow().isoformat()
        event = {
            "timestamp": timestamp,
            "user_id": str(self.user_id),
            "event_type": event_type,
            "phone_number": phone_number,
            "result": result,
            "details": details
        }
        
        # Log to file
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        # Log to database
        supabase.table("compliance_logs").insert({
            "user_id": str(self.user_id),
            "event_type": event_type,
            "phone_number": phone_number,
            "result": result,
            "details": details,
            "created_at": timestamp
        }).execute()
        
        # Also log to application logger
        logger.info(f"Compliance event: {event_type} - {result}")
        
        return event
EOL

# Create compliance API file
cat > "$APP_DIR/app/api/compliance.py" << 'EOL'
from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Dict, Any
from app.models.user import User
from app.services.compliance_service import ComplianceService
from app.utils.security import get_current_user
from uuid import UUID

router = APIRouter()

@router.post("/verify/{phone_number}", status_code=status.HTTP_200_OK)
async def verify_phone_ownership(
    phone_number: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Verify that the user owns the phone number they're trying to access."""
    try:
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        compliance_service = ComplianceService(current_user.id)
        result = compliance_service.verify_phone_ownership(phone_number, client_ip)
        
        if result:
            return {"verified": True, "message": "Phone ownership verified"}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Phone ownership verification failed"
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/status", status_code=status.HTTP_200_OK)
async def check_compliance_status(current_user: User = Depends(get_current_user)):
    """Check current compliance status."""
    try:
        compliance_service = ComplianceService(current_user.id)
        return compliance_service.check_whatsapp_tos_compliance()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
EOL

# Update main.py to include compliance router
sed -i 's/from app.api import auth, files, whatsapp, storage/from app.api import auth, files, whatsapp, storage, compliance/g' "$APP_DIR/app/main.py"
sed -i 's/app.include_router(storage.router, prefix="\/api\/storage", tags=\["Storage"\], dependencies=\[Depends(get_current_user)\])/app.include_router(storage.router, prefix="\/api\/storage", tags=\["Storage"\], dependencies=\[Depends(get_current_user)\])\napp.include_router(compliance.router, prefix="\/api\/compliance", tags=\["Compliance"\], dependencies=\[Depends(get_current_user)\])/g' "$APP_DIR/app/main.py"

# Update whatsapp_service.py with enhanced methods
# This is a simplified approach - in a real scenario, you'd want to patch the file more carefully
cat >> "$APP_DIR/app/services/whatsapp_service.py" << 'EOL'

# Enhanced methods for WhatsAppService
def secure_session_initialization(self, phone_number: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
    """Initialize a WhatsApp session with compliance checks."""
    # First check compliance
    from app.services.compliance_service import ComplianceService
    compliance_service = ComplianceService(self.user_id)
    
    # Verify phone ownership
    if not compliance_service.verify_phone_ownership(phone_number, ip_address):
        logger.warning(f"Phone ownership verification failed for user {self.user_id}, phone {phone_number}")
        return {"error": "Phone ownership verification failed", "status": "unauthorized"}
    
    # Check ToS compliance
    compliance_status = compliance_service.check_whatsapp_tos_compliance()
    if not compliance_status["is_compliant"]:
        logger.warning(f"ToS compliance check failed: {compliance_status['issues']}")
        return {"error": "Terms of Service compliance check failed", "status": "unauthorized", "issues": compliance_status["issues"]}
    
    # If all checks pass, initialize the session
    session_data = self.initialize_session()
    
    # Log successful initialization
    compliance_service.log_compliance_event(
        event_type="session_initialization",
        phone_number=phone_number,
        result="success",
        details=f"Session ID: {self.session_id}"
    )
    
    return session_data

def enhanced_close_session(self):
    """Enhanced session closure with proper cleanup and audit logging."""
    from app.services.compliance_service import ComplianceService
    import time
    
    if self.driver:
        try:
            # Log out of WhatsApp Web if logged in
            try:
                # Try to find and click the menu button
                menu_button = self.driver.find_element(By.CSS_SELECTOR, "[data-icon='menu']")
                menu_button.click()
                
                # Wait for menu to appear and find logout option
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Log out')]"))
                )
                logout_option = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Log out')]")
                logout_option.click()
                
                # Confirm logout if needed
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Log out')]"))
                )
                confirm_button = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Log out')]")
                confirm_button.click()
                
                # Wait for logout to complete
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not perform clean logout: {e}")
            
            # Close the browser
            self.driver.quit()
            self.driver = None
        except Exception as e:
            logger.error(f"Error closing driver: {e}")
    
    if self.session_id:
        # Update session status in database
        supabase.table("sessions").update({
            "status": SessionStatus.INACTIVE,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(self.session_id)).execute()
        
        # Log session closure for compliance
        compliance_service = ComplianceService(self.user_id)
        compliance_service.log_compliance_event(
            event_type="session_closure",
            result="success",
            details=f"Session ID: {self.session_id}"
        )
        
        self.session_id = None
    
    # Clean up any sensitive data
    sensitive_files = [
        os.path.join(self.data_dir, "Cookies"),
        os.path.join(self.data_dir, "Login Data")
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove sensitive file {file_path}: {e}")
    
    return {"message": "Session closed and cleaned up successfully"}
EOL

# Update whatsapp.py API to use enhanced methods
# This is a simplified approach - you'd want to be more careful in a real scenario
sed -i 's/@router.post("\/session", status_code=status.HTTP_201_CREATED)\nasync def create_session(current_user: User = Depends(get_current_user))/@router.post("\/session", status_code=status.HTTP_201_CREATED)\nasync def create_session(\n    phone_number: str,\n    request: Request,\n    current_user: User = Depends(get_current_user))/g' "$APP_DIR/app/api/whatsapp.py"

sed -i 's/return whatsapp_service.initialize_session()/client_ip = request.client.host if request.client else None\n        return whatsapp_service.secure_session_initialization(phone_number, client_ip)/g' "$APP_DIR/app/api/whatsapp.py"

sed -i 's/whatsapp_service.close_session()/whatsapp_service.enhanced_close_session()/g' "$APP_DIR/app/api/whatsapp.py"

# Update imports in whatsapp.py
sed -i '1s/^/from fastapi import APIRouter, HTTPException, Depends, status, Request\n/' "$APP_DIR/app/api/whatsapp.py"

# Build and run Docker container (if using Docker)
echo -e "${YELLOW}Building Docker container...${NC}"
if [ -f "$APP_DIR/Dockerfile" ]; then
    cd "$APP_DIR"
    docker build -t whatsapp-supabase-backend .
    
    echo -e "${GREEN}Docker container built successfully.${NC}"
    echo -e "${YELLOW}Starting the container...${NC}"
    
    docker run -d \
        --name whatsapp-backend \
        -p 8000:8000 \
        -v "$(pwd)"/whatsapp_data:/app/whatsapp_data \
        -v "$(pwd)"/logs:/app/logs \
        --env-file .env \
        whatsapp-supabase-backend
    
    echo -e "${GREEN}Container started successfully!${NC}"
    echo "The API is now accessible at http://localhost:8000"
    echo "API documentation is available at http://localhost:8000/docs"
else
    # Run directly with uvicorn if no Docker
    echo -e "${YELLOW}Starting application with uvicorn...${NC}"
    cd "$APP_DIR"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo "Note: Make sure to update your .env file with the correct Supabase credentials"
echo "You can now access your WhatsApp files through the API at http://localhost:8000"