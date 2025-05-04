import sys
import os
from loguru import logger

# Configure logger
log_file_path = os.path.join("logs", "app.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO")  # Add stderr handler
logger.add(
    log_file_path, 
    rotation="10 MB", 
    retention="7 days", 
    level="DEBUG"
)

def get_logger():
    return logger
