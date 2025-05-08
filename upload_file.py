import os
import sys
import hashlib
import logging
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional
from supabase import create_client, Client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("whatsapp_media_upload")

# Supabase configuration - replace with your own or use environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
BUCKET_NAME = "whatsapp-files"  # Change this if your bucket name is different

def get_whatsapp_phone_from_path(file_path: str) -> Optional[str]:
    """Extract phone number from WhatsApp media path."""
    try:
        # Path format: .../Message/Media/PHONENUMBER@s.whatsapp.net/...
        parts = file_path.split('/')
        for i, part in enumerate(parts):
            if part == "Media" and i+1 < len(parts) and "@s.whatsapp.net" in parts[i+1]:
                phone_with_suffix = parts[i+1]
                phone_number = phone_with_suffix.split('@')[0]
                return phone_number
        return None
    except Exception as e:
        logger.warning(f"Failed to extract phone number from path: {str(e)}")
        return None

def calculate_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def upload_whatsapp_media(
    file_path: str, 
    user_id: str, 
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Upload a WhatsApp media file to Supabase Storage using service role key.
    
    Args:
        file_path: Path to WhatsApp media file
        user_id: User ID for path organization
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with upload result
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {"success": False, "error": "File not found"}
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Missing Supabase configuration")
        return {"success": False, "error": "Missing Supabase configuration"}
    
    # Extract phone number from path if possible
    phone_number = get_whatsapp_phone_from_path(file_path)
    if phone_number:
        logger.info(f"Extracted phone number from path: {phone_number}")
    else:
        logger.warning("Could not extract phone number from path")
    
    # Create Supabase client with service role key
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info(f"Connected to Supabase: {SUPABASE_URL}")
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        return {"success": False, "error": f"Failed to create Supabase client: {str(e)}"}
    
    # Extract file information
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_hash = calculate_file_hash(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        # Try to determine mime type based on file extension
        if filename.lower().endswith(('.jpg', '.jpeg')):
            mime_type = "image/jpeg"
        elif filename.lower().endswith('.png'):
            mime_type = "image/png"
        elif filename.lower().endswith('.gif'):
            mime_type = "image/gif"
        elif filename.lower().endswith(('.mp4', '.mov')):
            mime_type = "video/mp4"
        elif filename.lower().endswith('.pdf'):
            mime_type = "application/pdf"
        elif filename.lower().endswith('.mp3'):
            mime_type = "audio/mpeg"
        elif filename.lower().endswith('.ogg'):
            mime_type = "audio/ogg"
        else:
            mime_type = "application/octet-stream"
    
    logger.info(f"Uploading file: {filename} ({file_size} bytes, {mime_type})")
    
    # Generate destination path based on phone number
    if phone_number:
        # Clean phone number (remove + and spaces)
        clean_phone = phone_number.replace("+", "").replace(" ", "")
        destination_path = f"{clean_phone}/{filename}"
    else:
        # Use user_id based path
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        destination_path = f"{user_id}/{timestamp}_{filename}"
    
    logger.info(f"Destination path: {destination_path}")
    
    # Attempt to upload file with retries
    attempt = 0
    last_error = None
    
    while attempt <= max_retries:
        attempt += 1
        logger.info(f"Upload attempt {attempt}/{max_retries+1}")
        
        try:
            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Upload file to Supabase storage
            upload_result = supabase.storage.from_(BUCKET_NAME).upload(
                destination_path,
                file_content,
                {"content-type": mime_type}
            )
            
            # Check if upload was successful
            logger.info("Verifying upload...")
            try:
                # Try to get a URL for the file
                public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(destination_path)
                
                # Update database record
                try:
                    metadata = {
                        "mime_type": mime_type,
                        "user_id": user_id,
                        "local_path": file_path
                    }
                    
                    if phone_number:
                        metadata["phone_number"] = phone_number
                    
                    update_database_record(
                        supabase, 
                        file_hash, 
                        destination_path, 
                        public_url,
                        metadata
                    )
                except Exception as db_error:
                    logger.warning(f"Database update failed, but file was uploaded successfully: {str(db_error)}")
                
                return {
                    "success": True,
                    "path": destination_path,
                    "url": public_url,
                    "file_hash": file_hash,
                    "phone_number": phone_number
                }
            except Exception as verify_error:
                logger.error(f"Upload verification failed: {str(verify_error)}")
                last_error = f"Verification failed: {str(verify_error)}"
                # Continue to next retry
        
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            last_error = str(e)
            
            # Check for duplicate error
            if hasattr(e, 'json') and isinstance(e.json(), dict):
                error_data = e.json()
                if error_data.get('error') == 'Duplicate':
                    logger.info(f"File already exists at {destination_path}")
                    
                    # Try to get the URL for existing file
                    try:
                        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(destination_path)
                        
                        # Update database record for existing file
                        try:
                            metadata = {
                                "mime_type": mime_type,
                                "user_id": user_id,
                                "local_path": file_path
                            }
                            
                            if phone_number:
                                metadata["phone_number"] = phone_number
                            
                            update_database_record(
                                supabase, 
                                file_hash, 
                                destination_path, 
                                public_url,
                                metadata
                            )
                        except Exception as db_error:
                            logger.warning(f"Database update failed for existing file: {str(db_error)}")
                        
                        return {
                            "success": True,
                            "path": destination_path,
                            "url": public_url,
                            "file_hash": file_hash,
                            "status": "already_exists",
                            "phone_number": phone_number
                        }
                    except Exception as url_error:
                        logger.error(f"Failed to get URL for existing file: {str(url_error)}")
            
            # If the upload fails with a specific error, try with a different filename
            if attempt > 1:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}_{timestamp}{ext}"
                
                if phone_number:
                    clean_phone = phone_number.replace("+", "").replace(" ", "")
                    destination_path = f"{clean_phone}/{new_filename}"
                else:
                    destination_path = f"{user_id}/{new_filename}"
                    
                logger.info(f"Trying with alternative path: {destination_path}")
    
    # All attempts failed
    logger.error(f"All {max_retries + 1} upload attempts failed")
    return {
        "success": False, 
        "error": last_error,
        "phone_number": phone_number
    }

def update_database_record(
    supabase: Client, 
    file_hash: str, 
    storage_path: str, 
    storage_url: str, 
    metadata: Dict[str, Any]
) -> None:
    """Update or create a file record in the database."""
    try:
        # Check if files table exists
        table_exists = check_table_exists(supabase, "files")
        
        if not table_exists:
            logger.warning("Files table doesn't exist, creating it...")
            create_files_table(supabase)
        
        # Try to update existing record
        update_data = {
            "uploaded": True,
            "storage_path": storage_path,
            "storage_url": storage_url,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add additional metadata
        if "phone_number" in metadata and metadata["phone_number"]:
            update_data["phone_number"] = metadata["phone_number"]
            
        if "user_id" in metadata:
            update_data["user_id"] = metadata["user_id"]
            
        if "local_path" in metadata:
            update_data["local_path"] = metadata["local_path"]
            
        if "mime_type" in metadata:
            update_data["mime_type"] = metadata["mime_type"]
        
        # Try to update existing record
        result = supabase.table("files").update(update_data).eq("file_hash", file_hash).execute()
        
        # If no rows updated, create a new record
        if not result.data or len(result.data) == 0:
            logger.info(f"No existing record for file hash {file_hash}, creating new record")
            
            # Create new record
            file_data = {
                "file_hash": file_hash,
                "uploaded": True,
                "storage_path": storage_path,
                "storage_url": storage_url,
                "mime_type": metadata.get("mime_type", "application/octet-stream"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "upload_attempts": 1
            }
            
            # Add additional metadata
            if "phone_number" in metadata and metadata["phone_number"]:
                file_data["phone_number"] = metadata["phone_number"]
                
            if "user_id" in metadata:
                file_data["user_id"] = metadata["user_id"]
                
            if "local_path" in metadata:
                file_data["local_path"] = metadata["local_path"]
                
            # Insert new record
            supabase.table("files").insert(file_data).execute()
            
    except Exception as e:
        logger.error(f"Error updating database record: {str(e)}")
        raise

def check_table_exists(supabase: Client, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        # Try to get a single row from the table
        supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Error checking if table exists: {str(e)}")
        if "relation" in str(e) and "does not exist" in str(e):
            return False
        # For other errors, assume table exists to be safe
        return True

def create_files_table(supabase: Client) -> None:
    """Create the files table if it doesn't exist."""
    try:
        # SQL to create the files table
        sql = """
        CREATE TABLE IF NOT EXISTS files (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            file_hash text NOT NULL,
            uploaded boolean DEFAULT false,
            storage_path text,
            storage_url text,
            local_path text,
            mime_type text,
            phone_number text,
            user_id text,
            upload_attempts integer DEFAULT 0,
            created_at timestamp with time zone DEFAULT now(),
            updated_at timestamp with time zone DEFAULT now()
        );
        
        CREATE INDEX IF NOT EXISTS idx_files_file_hash ON files (file_hash);
        """
        
        # Execute the SQL
        supabase.rpc("execute_sql", {"query": sql}).execute()
        logger.info("Created files table")
    except Exception as e:
        logger.error(f"Error creating files table: {str(e)}")
        raise

def main():
    """Main function to run the WhatsApp media upload script."""
    if len(sys.argv) < 3:
        print("Usage: python upload_whatsapp_media.py <file_path> <user_id>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    user_id = sys.argv[2]
    
    # Check file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Upload file
    print(f"\nUploading WhatsApp media file: {file_path}")
    print(f"User ID: {user_id}")
    print("\n" + "=" * 50 + "\n")
    
    result = upload_whatsapp_media(file_path, user_id)
    
    print("\n" + "=" * 50 + "\n")
    if result["success"]:
        print("Upload successful!")
        print(f"File path: {result.get('path')}")
        print(f"Public URL: {result.get('url')}")
        print(f"File hash: {result.get('file_hash')}")
        if result.get('phone_number'):
            print(f"Phone number: {result.get('phone_number')}")
        if result.get('status') == 'already_exists':
            print("Note: File already existed in storage")
        sys.exit(0)
    else:
        print("Upload failed!")
        print(f"Error: {result.get('error')}")
        if result.get('phone_number'):
            print(f"Phone number: {result.get('phone_number')}")
        sys.exit(1)

if __name__ == "__main__":
    main()