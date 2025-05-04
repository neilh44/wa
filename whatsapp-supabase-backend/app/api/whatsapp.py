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
