from fastapi import APIRouter, HTTPException, Depends, status, Request, Body, Response
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.models.user import User
from app.services.whatsapp_service import WhatsAppService
from app.utils.security import get_current_user
from app.utils.logger import get_logger
from uuid import UUID

logger = get_logger()
router = APIRouter()

class SessionRequest(BaseModel):
    phone_number: Optional[str] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    auth_token: Optional[str] = None
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    version: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    device: Optional[Dict[str, Any]] = None

@router.post("/session", status_code=status.HTTP_201_CREATED)
async def create_session(
    session_request: Optional[SessionRequest] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    # Allow for direct JSON body for flexibility
    body: Dict[str, Any] = Body(None)
):
    """Create a new WhatsApp session.
    
    This endpoint supports both Pydantic model validation and direct JSON body
    to accommodate various client implementations.
    """
    try:
        # Get client IP for security logging
        client_ip = request.client.host if request and hasattr(request, 'client') else None
        
        # Handle both validated model and direct JSON body
        if session_request is None and body:
            # Try to create a SessionRequest from body
            try:
                session_request = SessionRequest(**body)
            except Exception as e:
                logger.warning(f"Invalid session request body: {e}")
                # Continue with partial data for backward compatibility
                session_request = SessionRequest(
                    phone_number=body.get("phone_number", "unknown")
                )
        
        # Default to a simpler request if we still don't have one
        if session_request is None:
            session_request = SessionRequest(phone_number="unknown")
            
        # Initialize WhatsApp service
        whatsapp_service = WhatsAppService(current_user.id)
        
        # Log request type 
        logger.info(f"Creating WhatsApp session for user {current_user.id} with phone {session_request.phone_number}")
        
        # Try enhanced initialization if phone number is provided
        if session_request.phone_number and session_request.phone_number != "unknown":
            try:
                session_data = whatsapp_service.secure_session_initialization(
                    session_request.phone_number, 
                    client_ip
                )
                return session_data
            except AttributeError as e:
                # Fallback to regular initialization
                logger.warning(f"Falling back to regular initialization: {e}")
                session_data = whatsapp_service.initialize_session()
                return session_data
        else:
            # Use basic initialization
            session_data = whatsapp_service.initialize_session()
            return session_data
            
    except Exception as e:
        logger.error(f"Error creating WhatsApp session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e),
            headers={"X-Error-Type": type(e).__name__}
        )

@router.get("/session/{session_id}", status_code=status.HTTP_200_OK)
async def check_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Check the status of a WhatsApp session."""
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        session_status = whatsapp_service.check_session_status(session_id)
        
        # Try to get QR code data if available but not authenticated
        if session_status.get("status") != "authenticated":
            try:
                # Get current session data from database
                session_data = whatsapp_service._get_session_data(session_id)
                if session_data and session_data.get("qr_data"):
                    session_status["qr_data"] = session_data.get("qr_data")
                    session_status["qr_available"] = True
            except Exception as qr_error:
                logger.warning(f"Error retrieving QR data: {qr_error}")
                
        return session_status
    except Exception as e:
        logger.error(f"Error checking session {session_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/session/qr/{session_id}", status_code=status.HTTP_200_OK)
async def get_session_qr(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        qr_image = whatsapp_service.get_session_qr(session_id)
        return Response(content=qr_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/download", status_code=status.HTTP_200_OK)
async def download_files(current_user: User = Depends(get_current_user)):
    """Download files from WhatsApp."""
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        return {"files": whatsapp_service.download_files()}
    except Exception as e:
        logger.error(f"Error downloading files: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/session/{session_id}", status_code=status.HTTP_200_OK)
async def close_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Close a WhatsApp session."""
    try:
        whatsapp_service = WhatsAppService(current_user.id)
        whatsapp_service.close_session()
        return {"message": "Session closed successfully"}
    except Exception as e:
        logger.error(f"Error closing session {session_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
