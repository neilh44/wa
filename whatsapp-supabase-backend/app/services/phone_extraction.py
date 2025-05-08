import re
from datetime import datetime
from typing import Dict, Any, Optional

from app.utils.logger import get_logger

logger = get_logger()

class PhoneExtractor:
    """Handles extracting phone numbers from WhatsApp filenames and matching with active chats."""
    
    def extract_phone_number(self, filename_or_path: str, file_date: datetime, active_chats: Dict[str, Any]) -> str:
        """
        Try to extract phone number from filename, path, or match with active chats.
        
        Args:
            filename_or_path: The WhatsApp filename or full path to analyze
            file_date: Timestamp of the file
            active_chats: Dictionary of active chats with timestamps
            
        Returns:
            Extracted phone number or "unknown"
        """
        logger.debug(f"Attempting to extract phone number from: {filename_or_path}")
        
        # Define all WhatsApp folder patterns
        whatsapp_folder_patterns = [
            r'(\d+)@s\.whatsapp\.net',  # Regular contacts
            r'(\d+)@status'             # Status updates
        ]
        
        # Try each folder pattern
        for pattern in whatsapp_folder_patterns:
            folder_match = re.search(pattern, filename_or_path)
            if folder_match:
                phone_number = folder_match.group(1)
                logger.info(f"Extracted phone number {phone_number} from pattern {pattern} in path: {filename_or_path}")
                return phone_number
                
        # Log that we couldn't find a match in folder pattern
        logger.debug(f"No WhatsApp folder pattern match for: {filename_or_path}")
        
        # Next try common filename patterns
        phone_patterns = [
            r'from \+(\d+)',
            r'from \((\d+)\)',
            r'from (\d{10,})',
            r'(\d{10,})\.', 
            r'WhatsApp.*?(\d{10,})',
        ]
        
        for pattern in phone_patterns:
            matches = re.search(pattern, filename_or_path)
            if matches:
                phone_number = matches.group(1)
                logger.info(f"Extracted phone number {phone_number} from filename pattern {pattern} in: {filename_or_path}")
                return phone_number
                
        # Log that we couldn't find a match in filename pattern
        logger.debug(f"No filename pattern match for: {filename_or_path}")
        
        # Try to match with active chats based on time
        phone_number = self._match_with_active_chats(filename_or_path, file_date, active_chats)
        if phone_number:
            return phone_number
        
        # Log all possible patterns we tried
        logger.warning(f"Failed to extract phone number from path: {filename_or_path}")
        logger.warning(f"Tried patterns: {whatsapp_folder_patterns + phone_patterns}")
        logger.warning(f"Also tried matching with {len(active_chats) if active_chats else 0} active chats")
        
        # Default fallback
        return "unknown"
    
    def _match_with_active_chats(self, filename: str, file_date: datetime, active_chats: Dict[str, Any]) -> Optional[str]:
        """Match file with active chats based on time proximity."""
        if not active_chats:
            logger.debug(f"No active chats available for matching with: {filename}")
            return None
            
        # Try to extract date from filename
        date_match = re.search(r'(\d{8})|\d{6}|\d{4}-\d{2}-\d{2}', filename)
        
        # Find the closest chat by timestamp
        closest_chat = None
        closest_diff = float('inf')
        
        for phone, chat_info in active_chats.items():
            if 'last_activity' in chat_info:
                chat_time = chat_info['last_activity']
                time_diff = abs((chat_time - file_date).total_seconds())
                logger.debug(f"Time diff for {filename} with {phone}: {time_diff}s")
                
                if time_diff < closest_diff:
                    closest_diff = time_diff
                    closest_chat = phone
        
        # Use a wider time window (12 hours instead of 1 hour)
        if closest_chat and closest_diff < 43200:  # 12 hours
            logger.info(f"Matched file {filename} with chat {closest_chat} (time diff: {closest_diff}s)")
            return closest_chat
        else:
            logger.debug(f"No matching chat found within 12-hour window for: {filename}")
            if closest_chat:
                logger.debug(f"Closest chat was {closest_chat} with time diff: {closest_diff}s")
            
        return None