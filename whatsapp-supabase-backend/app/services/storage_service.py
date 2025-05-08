import os
from typing import Dict, List, Any, Optional
from uuid import UUID
from app.utils.logger import get_logger
from app.config import settings
from supabase import create_client, Client
from datetime import datetime

logger = get_logger()

class StorageService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        # Create regular client for user-based operations
        self.client = create_client(settings.supabase_url, settings.supabase_key)
        # Create service role client for storage operations
        self.service_client = create_client(settings.supabase_url, settings.supabase_service_key)
        
        logger.debug(f"Initialized StorageService for user {user_id}")

    def upload_file(self, file_id: UUID) -> Dict[str, Any]:
        """Upload a file to Supabase Storage using service role."""
        
        # Get file info from database (using regular client is fine here)
        file_query = self.client.table("files").select("*").eq("id", str(file_id)).execute()
        
        if not file_query.data:
            logger.error(f"File not found: {file_id}")
            return {"success": False, "error": "File not found"}
        
        file_data = file_query.data[0]
        local_path = file_data.get("local_path") or file_data.get("storage_path")
        
        if not local_path or not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return {"success": False, "error": "Local file not found"}
        
        try:
            # Organize by phone number in storage
            phone_number = file_data.get("phone_number", "").replace("+", "").replace(" ", "")
            filename = file_data.get("filename") or os.path.basename(local_path)
            storage_path = f"{phone_number}/{filename}"
            
            # IMPORTANT: Check if file actually exists in storage using a more reliable method
            file_exists = False
            try:
                # First try to list the directory contents
                dirname = os.path.dirname(storage_path) or "/"
                basename = os.path.basename(storage_path)
                
                logger.info(f"Checking if file exists at {storage_path}")
                files = self.service_client.storage.from_("whatsapp-files").list(dirname)
                
                for file_item in files:
                    if file_item.get("name") == basename:
                        logger.info(f"File found in directory listing: {basename}")
                        file_exists = True
                        break
                        
                if not file_exists:
                    logger.info(f"File {basename} not found in {dirname}, will upload it")
            except Exception as e:
                logger.error(f"Error checking if file exists: {str(e)}")
                file_exists = False
            
            if file_exists:
                logger.info(f"File verified to exist at {storage_path}")
                
                # Update file status in database using service client
                self.service_client.table("files").update({
                    "uploaded": True,
                    "storage_path": storage_path,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(file_id)).execute()
                
                return {"success": True, "storage_path": storage_path, "status": "already_exists"}
                
            # If we get here, the file doesn't exist - upload it
            with open(local_path, "rb") as f:
                file_content = f.read()
                
            try:
                logger.info(f"Uploading file to {storage_path}")
                
                # Determine content type
                content_type = file_data.get("mime_type")
                if not content_type:
                    import mimetypes
                    content_type, _ = mimetypes.guess_type(local_path)
                    content_type = content_type or "application/octet-stream"
                
                # Upload the file
                result = self.service_client.storage.from_("whatsapp-files").upload(
                    storage_path,
                    file_content,
                    {"content-type": content_type}
                )
                
                # Verify upload was successful by checking again
                verification_successful = False
                try:
                    files = self.service_client.storage.from_("whatsapp-files").list(dirname)
                    for file_item in files:
                        if file_item.get("name") == basename:
                            verification_successful = True
                            break
                except Exception as ve:
                    logger.error(f"Error verifying upload: {str(ve)}")
                    
                if verification_successful:
                    logger.info(f"Upload verification successful for {storage_path}")
                    
                    # Get the public URL
                    url = self.service_client.storage.from_("whatsapp-files").get_public_url(storage_path)
                    
                    # Update file status in database
                    self.service_client.table("files").update({
                        "uploaded": True,
                        "storage_path": storage_path,
                        "storage_url": url,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", str(file_id)).execute()
                    
                    return {"success": True, "storage_path": storage_path, "url": url}
                else:
                    logger.error(f"Upload verification failed for {storage_path}")
                    return {"success": False, "error": "Upload verification failed"}
                    
            except Exception as e:
                # Handle duplicate error
                if hasattr(e, 'json') and isinstance(e.json(), dict):
                    error_data = e.json()
                    if error_data.get('error') == 'Duplicate':
                        logger.warning(f"Duplicate error for {storage_path}, but we already checked")
                        
                        # Try with a unique filename instead
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        name, ext = os.path.splitext(filename)
                        new_filename = f"{name}_{timestamp}{ext}"
                        new_path = f"{phone_number}/{new_filename}"
                        
                        logger.info(f"Trying with alternative path: {new_path}")
                        
                        try:
                            result = self.service_client.storage.from_("whatsapp-files").upload(
                                new_path,
                                file_content,
                                {"content-type": content_type}
                            )
                            
                            # Get the URL
                            url = self.service_client.storage.from_("whatsapp-files").get_public_url(new_path)
                            
                            # Update database
                            self.service_client.table("files").update({
                                "uploaded": True,
                                "storage_path": new_path,
                                "storage_url": url,
                                "updated_at": datetime.utcnow().isoformat()
                            }).eq("id", str(file_id)).execute()
                            
                            return {"success": True, "storage_path": new_path, "url": url}
                        except Exception as alt_e:
                            logger.error(f"Alternative upload failed: {str(alt_e)}")
                            return {"success": False, "error": f"Alternative upload failed: {str(alt_e)}"}
                
                logger.error(f"Error uploading file: {str(e)}")
                
                # Update upload attempts
                self.service_client.table("files").update({
                    "upload_attempts": file_data.get("upload_attempts", 0) + 1,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(file_id)).execute()
                
                return {"success": False, "error": str(e)}
                
        except Exception as e:
            logger.error(f"Unexpected error in upload_file: {str(e)}")
            return {"success": False, "error": str(e)}        

             
    def get_files(self, phone_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get files from Supabase Storage, optionally filtered by phone number."""
        # Use service client for consistent access patterns
        query = self.service_client.table("files").select("*").eq("user_id", str(self.user_id))
        
        if phone_number:
            query = query.eq("phone_number", phone_number)
        
        result = query.execute()
        return result.data if result.data else []
    
    def get_missing_files(self) -> List[Dict[str, Any]]:
        """Get files that have not been uploaded successfully."""
        # Use service client for consistent access patterns
        result = self.service_client.table("files") \
            .select("*") \
            .eq("user_id", str(self.user_id)) \
            .eq("uploaded", False) \
            .execute()
        
        return result.data if result.data else []
        
    def get_file_url(self, file_id: UUID) -> Optional[str]:
        """Get the public URL for a file."""
        try:
            # Get file info
            file_query = self.service_client.table("files").select("*").eq("id", str(file_id)).execute()
            
            if not file_query.data:
                return None
                
            file_data = file_query.data[0]
            
            # If we already have a storage URL, return it
            if "storage_url" in file_data and file_data["storage_url"]:
                return file_data["storage_url"]
                
            # If we have a storage path but no URL, generate it
            if "storage_path" in file_data and file_data["storage_path"]:
                try:
                    url = self.service_client.storage.from_("whatsapp-files").get_public_url(file_data["storage_path"])
                    
                    # Update the record with the URL
                    self.service_client.table("files").update({
                        "storage_url": url,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", str(file_id)).execute()
                    
                    return url
                except Exception as e:
                    logger.error(f"Error getting URL for file {file_id}: {str(e)}")
                    return None
            
            return None
        except Exception as e:
            logger.error(f"Error in get_file_url: {str(e)}")
            return None