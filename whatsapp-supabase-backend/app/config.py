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
