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
