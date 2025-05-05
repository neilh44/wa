#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime
from uuid import UUID

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Import the WhatsApp service
from app.services.whatsapp_service import WhatsAppService
from app.utils.logger import get_logger

logger = get_logger()

def debug_qr_code():
    """Debug QR code extraction"""
    logger.info("Starting QR code debugging...")
    
    # Create a test user ID
    test_user_id = UUID('00000000-0000-0000-0000-000000000001')
    
    # Initialize the WhatsApp service
    whatsapp_service = WhatsAppService(test_user_id)
    
    # Initialize a session and get QR code data
    logger.info("Initializing WhatsApp session...")
    result = whatsapp_service.initialize_session()
    
    # Print the result
    logger.info(f"Session initialization result: {json.dumps(result, indent=2)}")
    
    # Close the session
    whatsapp_service.close_session()
    
    return result

if __name__ == "__main__":
    debug_qr_code()
