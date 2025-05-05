#!/usr/bin/env python3
import os
import sys
import json
import time
from datetime import datetime
from uuid import UUID

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Import the WhatsApp service
from app.services.whatsapp_service import WhatsAppService
from app.utils.logger import get_logger

logger = get_logger()

def test_authentication():
    """Test WhatsApp authentication detection"""
    logger.info("Starting WhatsApp authentication testing...")
    
    # Create a test user ID - replace with your actual user ID from logs
    test_user_id = UUID('e4cb8a86-6474-454d-a740-3ae98266a509')  # Update with your user ID
    
    # Initialize the WhatsApp service
    whatsapp_service = WhatsAppService(test_user_id)
    
    # Initialize a session
    logger.info("Initializing WhatsApp session...")
    result = whatsapp_service.initialize_session()
    
    # Print the result
    logger.info(f"Session initialization result: {json.dumps(result, default=str)}")
    
    if 'session_id' in result:
        session_id = result['session_id']
        
        # Loop to check authentication status
        attempts = 0
        while attempts < 10:
            logger.info(f"Checking authentication status (attempt {attempts+1})...")
            status_result = whatsapp_service.check_session_status(session_id)
            logger.info(f"Authentication status: {json.dumps(status_result, default=str)}")
            
            if status_result.get('status') == 'authenticated':
                logger.info("Authentication successful!")
                break
            
            logger.info("Waiting for authentication...")
            time.sleep(5)
            attempts += 1
        
        # Close the session
        whatsapp_service.close_session()
    
    return result

if __name__ == "__main__":
    test_authentication()
