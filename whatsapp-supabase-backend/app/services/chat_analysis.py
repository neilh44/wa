from datetime import datetime, timedelta
import re
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from app.utils.logger import get_logger

logger = get_logger()

class ChatAnalyzer:
    """Analyzes WhatsApp chats and extracts relevant information."""
    
    def __init__(self, driver):
        """
        Initialize chat analyzer.
        
        Args:
            driver: Selenium WebDriver instance with WhatsApp web loaded
        """
        self.driver = driver
    
    def extract_active_chats(self) -> Dict[str, Any]:
        """
        Extract information about active chats from WhatsApp Web.
        Returns a dict of phone numbers with last activity timestamps.
        """
        active_chats = {}
        
        if not self.driver:
            return active_chats
        
        try:
            # Find chat list
            chat_list = self.driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
            
            for chat in chat_list:
                try:
                    # Get chat title (usually contains phone number or name)
                    title_element = chat.find_element(By.CSS_SELECTOR, "span[data-testid='chat-title']")
                    title = title_element.text.strip()
                    
                    # Try to extract timestamp
                    timestamp_element = chat.find_element(By.CSS_SELECTOR, "span[data-testid='chat-timestamp']")
                    timestamp_text = timestamp_element.text.strip()
                    
                    # Parse timestamp (simplified)
                    # Current time as fallback
                    chat_time = datetime.now()
                    
                    # Try to parse common timestamp formats
                    if ":" in timestamp_text:  # Today timestamps like "14:22"
                        hour, minute = map(int, timestamp_text.split(':'))
                        chat_time = chat_time.replace(hour=hour, minute=minute)
                    elif "yesterday" in timestamp_text.lower():
                        chat_time = chat_time - timedelta(days=1)
                    
                    # Extract phone number if possible
                    phone_match = re.search(r'\+(\d+)', title)
                    phone = phone_match.group(1) if phone_match else title
                    
                    active_chats[phone] = {
                        'title': title,
                        'last_activity': chat_time
                    }
                    
                except Exception as e:
                    logger.debug(f"Error processing chat: {str(e)}")
                    continue
                    
            return active_chats
            
        except Exception as e:
            logger.error(f"Error extracting active chats: {str(e)}")
            return active_chats
    
    def get_chat_content(self, chat_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get content from a specific chat.
        
        Args:
            chat_id: ID or title of the chat to extract
            limit: Maximum number of messages to extract
            
        Returns:
            Dictionary with chat messages and metadata
        """
        # This is a placeholder function - actual implementation would require
        # selecting the chat and extracting messages
        
        return {
            "chat_id": chat_id,
            "messages": [],
            "metadata": {
                "total_messages": 0,
                "participants": []
            }
        }