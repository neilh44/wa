"""
Debugging script for WhatsApp session endpoint.
This modifies the whatsapp.py API file to add detailed error logging.
"""
import os
import shutil
import re

# Backup the original file
api_file = "app/api/whatsapp.py"
backup_file = f"{api_file}.bak"

if not os.path.exists(backup_file):
    shutil.copy2(api_file, backup_file)
    print(f"Backed up {api_file} to {backup_file}")
else:
    print(f"Backup already exists at {backup_file}")

# Read the content of the file
with open(api_file, 'r') as f:
    content = f.read()

# Add imports if they don't exist
imports_to_add = [
    "import traceback",
    "import sys",
    "from fastapi.responses import JSONResponse"
]

for imp in imports_to_add:
    if imp not in content:
        content = imp + "\n" + content
        print(f"Added import: {imp}")

# Find and modify the create_session endpoint
create_session_pattern = r"@router\.post\(\"/session\".*?\)[\s\n]+async def create_session\(.*?\):.*?try:.*?except Exception as e:(.*?)(?=\n\n|\Z)"
replacement = """@router.post("/session", status_code=status.HTTP_201_CREATED)
async def create_session(
    phone_number: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    try:
        # Log request information
        client_ip = request.client.host if request.client else None
        logger.info(f"Creating WhatsApp session for user {current_user.id}, phone {phone_number}, IP {client_ip}")
        
        # Initialize the service
        whatsapp_service = WhatsAppService(current_user.id)
        
        # Call service with detailed logging
        try:
            session_data = whatsapp_service.secure_session_initialization(phone_number, client_ip)
            logger.info(f"Session initialized successfully: {session_data}")
            return session_data
        except AttributeError as attr_err:
            # Check if we're missing the secure_session_initialization method
            if "secure_session_initialization" in str(attr_err):
                logger.error("Method secure_session_initialization not found, using initialize_session instead")
                # Fall back to the old method
                session_data = whatsapp_service.initialize_session()
                logger.info(f"Session initialized with fallback method: {session_data}")
                return session_data
            else:
                raise
    except Exception as e:
        # Detailed error logging
        logger.error(f"Error creating WhatsApp session: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # More detailed information about the system
        logger.error(f"Python version: {sys.version}")
        logger.error(f"Platform: {sys.platform}")
        
        # Return a more detailed error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc().split("\\n")
            }
        )"""

if re.search(create_session_pattern, content, re.DOTALL):
    modified_content = re.sub(create_session_pattern, replacement, content, flags=re.DOTALL)
    
    # Write the modified content back to the file
    with open(api_file, 'w') as f:
        f.write(modified_content)
    
    print(f"Modified {api_file} to add detailed error logging")
else:
    print(f"Could not find the create_session function pattern in {api_file}")
    print("Manual modification will be required")

print("\nDebugging code has been added to the WhatsApp session API endpoint.")
print("After restarting the server, check the logs for detailed error information.")
