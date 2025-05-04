from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
from app.models.user import User
from app.services.storage_service import StorageService
from app.utils.security import get_current_user
from uuid import UUID

router = APIRouter()

@router.post("/{file_id}", status_code=status.HTTP_200_OK)
async def upload_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        storage_service = StorageService(current_user.id)
        return storage_service.upload_file(file_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", status_code=status.HTTP_200_OK)
async def get_storage_files(
    phone_number: str = None,
    current_user: User = Depends(get_current_user)
):
    try:
        storage_service = StorageService(current_user.id)
        return storage_service.get_files(phone_number)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))