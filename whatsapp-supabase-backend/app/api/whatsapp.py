from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
from app.models.user import User
from app.services.whatsapp_service import WhatsAppService, supabase
from app.utils.security import get_current_user
from app.utils.logger import get_logger
from uuid import UUID

router = APIRouter()
logger = get_logger()

@router.post("/session", status_code=status.HTTP_201_CREATED)
async def create_session(current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Creating WhatsApp session for user {current_user.id} with phone unknown")
        whatsapp_service = WhatsAppService(current_user.id, supabase)  # Pass supabase
        return whatsapp_service.initialize_session()
    except Exception as e:
        logger.error(f"Error creating WhatsApp session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/session/{session_id}", status_code=status.HTTP_200_OK)
async def check_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        whatsapp_service = WhatsAppService(current_user.id, supabase)  # Add supabase
        result = whatsapp_service.check_session_status(session_id)
        return result
    except Exception as e:
        logger.error(f"Error checking WhatsApp session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/download", status_code=status.HTTP_200_OK)
async def download_files(current_user: User = Depends(get_current_user)):
    try:
        whatsapp_service = WhatsAppService(current_user.id, supabase)  # Add supabase
        return {"files": whatsapp_service.download_files()}
    except Exception as e:
        logger.error(f"Error downloading WhatsApp files: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/session/{session_id}", status_code=status.HTTP_200_OK)
async def close_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        whatsapp_service = WhatsAppService(current_user.id, supabase)  # Add supabase
        whatsapp_service.close_session()
        return {"message": "Session closed successfully"}
    except Exception as e:
        logger.error(f"Error closing WhatsApp session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/update-phone-numbers", status_code=status.HTTP_200_OK)
async def update_phone_numbers(current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Updating and organizing files by phone number for user {current_user.id}")
        whatsapp_service = WhatsAppService(current_user.id, supabase)
        result = whatsapp_service.update_file_phone_numbers()
        return result
    except Exception as e:
        logger.error(f"Error updating phone numbers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))