import os
import traceback
from typing import Dict, List, Any, Optional, BinaryIO
from uuid import UUID
from datetime import datetime
import hashlib
import mimetypes
from app.utils.logger import get_logger
from app.config import settings
from supabase import create_client

logger = get_logger()

class SupabaseStorageService:
    """Implementation of storage service interface using Supabase Storage."""
    
    def __init__(self, supabase_client=None):
        """
        Initialize the Supabase storage service.
        
        Args:
            supabase_client: The Supabase client instance (optional)
                             If not provided, a service role client will be created
        """
        if supabase_client:
            logger.info("Using provided Supabase client")
            self.supabase = supabase_client
        else:
            # Create a new client with service role key
            logger.info("Creating new Supabase client with service role key")
            
            if not settings.supabase_url or not settings.supabase_service_key:
                logger.error("Missing Supabase configuration in settings")
                raise ValueError("Missing Supabase settings. Check supabase_url and supabase_service_key in settings.")
                
            self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    
    def upload(self, 
              bucket: str, 
              destination_path: str, 
              file_content: BinaryIO, 
              content_type: Optional[str] = None, 
              metadata: Optional[Dict[str, str]] = None,
              force_upload: bool = False) -> Dict[str, Any]:
        """
        Upload a file to Supabase storage.
        
        Args:
            bucket: Storage bucket name
            destination_path: Path within the bucket
            file_content: File content as bytes or file-like object
            content_type: Optional MIME type
            metadata: Optional metadata dictionary
            force_upload: Force upload even if the file appears to exist
            
        Returns:
            Dictionary with upload result
        """
        # Prepare file options
        file_options = {}
        if content_type:
            file_options["content-type"] = content_type

        # Log upload attempt with file size
        try:
            if hasattr(file_content, 'tell') and hasattr(file_content, 'seek'):
                current_pos = file_content.tell()
                file_content.seek(0, os.SEEK_END)
                file_size = file_content.tell()
                file_content.seek(current_pos)  # Reset position
                logger.info(f"Attempting to upload file to {bucket}/{destination_path} (size: {file_size} bytes)")
            else:
                logger.info(f"Attempting to upload file to {bucket}/{destination_path}")
        except Exception as e:
            logger.warning(f"Unable to determine file size for {destination_path}: {e}")
        
        # Skip existence check if force_upload is True
        if force_upload:
            logger.info(f"Force upload requested for {destination_path}, skipping existence check")
            file_exists = False
        else:
            # Check if file exists before uploading
            file_exists = self._check_file_exists(bucket, destination_path)
            
        # Upload to storage if file doesn't exist or force_upload is True
        if not file_exists:
            try:
                logger.info(f"Uploading file to {bucket}/{destination_path}")
                
                # Ensure file_content is at the beginning
                if hasattr(file_content, 'seek'):
                    file_content.seek(0)
                
                # Upload to storage
                result = self.supabase.storage.from_(bucket).upload(
                    destination_path, 
                    file_content,
                    file_options=file_options
                )
                
                # Verify upload was successful
                verification_result = self._verify_file_uploaded(bucket, destination_path)
                
                if verification_result["exists"]:
                    logger.info(f"Successfully verified upload of {destination_path}")
                    return {"path": destination_path, "status": "uploaded", "verified": True}
                else:
                    logger.error(f"Upload reported success but verification failed for {destination_path}")
                    logger.error(f"Verification details: {verification_result}")
                    
                    # Attempt to get more details about the bucket and storage
                    try:
                        bucket_info = self.supabase.storage.from_(bucket).list()
                        logger.info(f"Bucket {bucket} contains {len(bucket_info)} items")
                    except Exception as bucket_error:
                        logger.error(f"Failed to list bucket contents: {str(bucket_error)}")
                    
                    return {
                        "path": destination_path, 
                        "status": "upload_failed_verification", 
                        "verification_error": verification_result.get("error")
                    }
                
            except Exception as e:
                # Handle duplicate error specifically
                if hasattr(e, 'json') and isinstance(e.json(), dict):
                    error_data = e.json()
                    if error_data.get('error') == 'Duplicate':
                        logger.warning(f"Duplicate error reported by Supabase for {destination_path}")
                        
                        # Double check if the file actually exists
                        verification_result = self._verify_file_uploaded(bucket, destination_path)
                        
                        if verification_result["exists"]:
                            logger.info(f"Verified file exists at {destination_path} after duplicate error")
                            return {"path": destination_path, "status": "exists"}
                        else:
                            # Duplicate error but file doesn't exist - try uploading with a different path
                            logger.error(f"Duplicate error but file not found at {destination_path}! Trying with a different name")
                            
                            file_name, file_ext = os.path.splitext(destination_path)
                            new_path = f"{file_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
                            
                            # Ensure file_content is at the beginning
                            if hasattr(file_content, 'seek'):
                                file_content.seek(0)
                            
                            try:
                                # Try upload with new path
                                result = self.supabase.storage.from_(bucket).upload(
                                    new_path, 
                                    file_content,
                                    file_options=file_options
                                )
                                
                                # Verify this upload
                                if self._verify_file_uploaded(bucket, new_path)["exists"]:
                                    logger.info(f"Successfully uploaded with new path {new_path}")
                                    return {"path": new_path, "status": "uploaded_with_new_name"}
                                else:
                                    logger.error(f"Failed verification for alternative path {new_path}")
                                    return {"path": new_path, "status": "upload_failed_verification"}
                            except Exception as alt_e:
                                logger.error(f"Failed to upload with alternative path: {str(alt_e)}")
                                return {"path": destination_path, "status": "failed", "error": str(alt_e)}
                    else:
                        logger.error(f"Supabase error during upload: {error_data}")
                
                # Log full error details
                logger.error(f"Error uploading file to {destination_path}: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                if hasattr(e, 'json'):
                    try:
                        logger.error(f"Error JSON: {e.json()}")
                    except:
                        pass
                
                return {"path": destination_path, "status": "failed", "error": str(e)}
        else:
            logger.info(f"File already exists at {destination_path}, skipping upload")
            return {"path": destination_path, "status": "exists"}

    def _check_file_exists(self, bucket: str, path: str) -> bool:
        """
        Check if a file exists in Supabase storage.
        
        Args:
            bucket: Storage bucket name
            path: Path within the bucket
            
        Returns:
            Boolean indicating if file exists
        """
        try:
            # First try to get file public URL
            try:
                self.supabase.storage.from_(bucket).get_public_url(path)
            except Exception as url_error:
                logger.debug(f"Failed to get public URL for {path}: {str(url_error)}")
                return False
            
            # Then verify the file actually exists by listing its parent directory
            try:
                dirname = os.path.dirname(path) or '/'
                filename = os.path.basename(path)
                
                files = self.supabase.storage.from_(bucket).list(dirname)
                
                # Check if our file is in the list
                for file_item in files:
                    if file_item.get('name') == filename:
                        logger.info(f"Verified file exists: {path}")
                        return True
                
                logger.warning(f"File {filename} not found in {dirname} despite successful URL check")
                
                # Try to list files to see what's there
                try:
                    logger.debug(f"Files in directory {dirname}: {[f.get('name') for f in files]}")
                except Exception as list_debug_error:
                    logger.debug(f"Error listing directory content: {str(list_debug_error)}")
                
                return False
            except Exception as list_error:
                logger.warning(f"Error checking file existence by listing: {str(list_error)}")
                return False
        except Exception as e:
            logger.debug(f"Error checking if file exists at {path}: {str(e)}")
            return False
        
    def _verify_file_uploaded(self, bucket: str, path: str) -> Dict[str, Any]:
        """
        Verify a file was successfully uploaded to Supabase storage.
        
        Args:
            bucket: Storage bucket name
            path: Path within the bucket
            
        Returns:
            Dictionary with verification results
        """
        try:
            dirname = os.path.dirname(path) or '/'
            filename = os.path.basename(path)
            
            logger.debug(f"Verifying file exists at {bucket}/{path}")
            
            # Try to list files in the directory containing the file
            try:
                files = self.supabase.storage.from_(bucket).list(dirname)
                
                # Check if our file is in the list
                for file_item in files:
                    if file_item.get('name') == filename:
                        logger.debug(f"Verification successful: Found {filename} in {dirname}")
                        return {"exists": True}
                
                logger.error(f"Verification failed: File {filename} not found in {dirname}")
                return {"exists": False, "error": "file_not_found", "directory_contents": [f.get('name') for f in files]}
            except Exception as list_error:
                logger.error(f"Verification error when listing directory: {str(list_error)}")
                return {"exists": False, "error": "list_error", "error_details": str(list_error)}
        except Exception as e:
            logger.error(f"Error during verification of {path}: {str(e)}")
            return {"exists": False, "error": "verification_error", "error_details": str(e)}
    
    def force_upload(self, 
                    bucket: str, 
                    destination_path: str, 
                    file_content: BinaryIO, 
                    content_type: Optional[str] = None, 
                    metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Force upload a file to Supabase storage even if it appears to exist already.
        
        Args:
            bucket: Storage bucket name
            destination_path: Path within the bucket
            file_content: File content as bytes or file-like object
            content_type: Optional MIME type
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary with upload result
        """
        logger.info(f"Forcing upload of file to {bucket}/{destination_path}")
        
        # Try to remove the file first if it exists
        try:
            self.delete(bucket, destination_path)
        except Exception as e:
            logger.warning(f"Failed to delete existing file before force upload: {str(e)}")
        
        # Call upload with force_upload=True
        return self.upload(
            bucket=bucket,
            destination_path=destination_path,
            file_content=file_content,
            content_type=content_type,
            metadata=metadata,
            force_upload=True
        )

    def query_files(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query files based on metadata.
        
        Args:
            query_params: Dictionary with query parameters
            
        Returns:
            List of matching file metadata
        """
        try:
            # Check if we're querying by file hash
            if "metadata" in query_params and "file_hash" in query_params["metadata"]:
                file_hash = query_params["metadata"]["file_hash"]
                
                # Query the database table that tracks your files
                result = self.supabase.table("files").select("*").eq("file_hash", file_hash).execute()
                
                return result.data
            return []
        except Exception as e:
            logger.error(f"Error querying files: {str(e)}")
            return []
    
    def delete(self, bucket: str, path: str) -> Dict[str, Any]:
        """Delete a file from Supabase storage."""
        try:
            return self.supabase.storage.from_(bucket).remove([path])
        except Exception as e:
            logger.warning(f"Failed to delete file {path}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file in Supabase storage."""
        return self.supabase.storage.from_(bucket).get_public_url(path)
    
    def list_files(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in a Supabase storage bucket with optional prefix."""
        return self.supabase.storage.from_(bucket).list(prefix)
    
    def create_signed_url(self, bucket: str, path: str, expires_in: int = 60) -> Dict[str, Any]:
        """Create a signed URL for private file access."""
        return self.supabase.storage.from_(bucket).create_signed_url(path, expires_in)