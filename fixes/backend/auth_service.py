from typing import Optional
from uuid import UUID
import os
from app.models.user import User, UserCreate, UserLogin, Token
from app.utils.security import hash_password, verify_password, create_access_token
from datetime import timedelta
from app.config import settings
from supabase import create_client, Client
from app.utils.logger import get_logger
import httpx

logger = get_logger()

# Add error handling for Supabase connection
try:
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

def register_user(user_data: UserCreate) -> User:
    """Register a new user."""
    if not supabase:
        logger.error("Supabase client not initialized")
        raise Exception("Database connection error")
    
    try:
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
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        raise

def authenticate_user(user_login: UserLogin) -> Optional[User]:
    """Authenticate a user and return user if credentials are valid."""
    if not supabase:
        logger.error("Supabase client not initialized")
        raise Exception("Database connection error")
    
    try:
        user_query = supabase.table("users").select("*").eq("email", user_login.email).execute()
        
        if not user_query.data:
            logger.warning(f"No user found with email: {user_login.email}")
            return None
        
        user_data = user_query.data[0]
        
        if not verify_password(user_login.password, user_data.get("hashed_password", "")):
            logger.warning(f"Invalid password for user: {user_login.email}")
            return None
        
        return User(**user_data)
    except Exception as e:
        logger.error(f"Error in authenticate_user: {e}")
        raise

def create_user_token(user: User) -> Token:
    """Create a JWT token for the user."""
    try:
        access_token_expires = timedelta(minutes=settings.jwt_expires_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token)
    except Exception as e:
        logger.error(f"Error in create_user_token: {e}")
        raise

def get_user_by_id(user_id: str) -> Optional[User]:
    """Get a user by ID."""
    if not supabase:
        logger.error("Supabase client not initialized")
        raise Exception("Database connection error")
    
    try:
        user_query = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not user_query.data:
            return None
        
        return User(**user_query.data[0])
    except Exception as e:
        logger.error(f"Error in get_user_by_id: {e}")
        raise
