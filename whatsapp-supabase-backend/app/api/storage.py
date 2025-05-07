from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from app.models.user import User
from app.services.storage_service import StorageService
from app.utils.security import get_current_user
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=Dict[str, List[Dict[str, Any]]])
async def get_storage_files(
    current_user: User = Depends(get_current_user)
):
    storage_service = StorageService(current_user.id)
    return {"files": storage_service.get_files()}

@router.get("/missing", response_model=Dict[str, List[Dict[str, Any]]])
async def get_missing_files(
    current_user: User = Depends(get_current_user)
):
    storage_service = StorageService(current_user.id)
    return {"files": storage_service.get_missing_files()}

@router.post("/upload/{file_id}", status_code=status.HTTP_200_OK)
async def upload_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        storage_service = StorageService(current_user.id)
        return storage_service.upload_file(file_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))