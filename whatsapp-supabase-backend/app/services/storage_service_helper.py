import os
import hashlib
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
import mimetypes
from app.utils.logger import get_logger

logger = get_logger()

class StorageServiceHelper:
    """
    Helper class for cloud storage services.
    Handles common functionality like file path generation, metadata extraction, etc.
    """
    def __init__(self, storage_service):
        """
        Initialize with a storage service adapter
        
        Args:
            storage_service: Storage service adapter that implements required methods
        """
        self.storage_service = storage_service
        
    def upload_file(self, file_path: str, user_id: str, phone_number: Optional[str] = None, 
                   metadata: Dict[str, Any] = None, max_retries: int = 2, force_upload: bool = False) -> str:
        """
        Upload a file to storage with appropriate path and metadata
        
        Args:
            file_path: Path to local file
            user_id: User ID for path organization
            phone_number: Phone number for file organization
            metadata: Additional file metadata
            max_retries: Maximum number of retry attempts
            force_upload: Force upload even if the file appears to exist
            
        Returns:
            Public URL of the uploaded file
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found for upload: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Default metadata
        if metadata is None:
            metadata = {}
            
        # Extract filename
        filename = os.path.basename(file_path)
        
        # Generate file hash if not provided
        if "file_hash" not in metadata:
            try:
                file_hash = self._calculate_file_hash(file_path)
                metadata["file_hash"] = file_hash
            except Exception as e:
                logger.error(f"Failed to calculate file hash for {file_path}: {str(e)}")
                raise
        else:
            file_hash = metadata["file_hash"]
        
        # Check file size for logging
        try:
            file_size = os.path.getsize(file_path)
            logger.debug(f"File size for {filename}: {file_size} bytes")
        except Exception as e:
            logger.warning(f"Unable to determine file size for {filename}: {e}")
        
        # Skip existing file check if force_upload is True
        if not force_upload:
            # Check if file with same hash already exists
            try:
                existing_files = self.storage_service.query_files({"metadata": {"file_hash": file_hash}})
                if existing_files:
                    logger.info(f"File with hash {file_hash} found in database")
                    
                    # Get the storage path
                    storage_path = existing_files[0].get("storage_path", "")
                    if storage_path:
                        # Verify file actually exists in storage
                        bucket = "whatsapp-files"  # Use your bucket name
                        exists_in_storage = self.storage_service._check_file_exists(bucket, storage_path)
                        
                        if exists_in_storage:
                            logger.info(f"Verified file with hash {file_hash} exists at {storage_path}")
                            return existing_files[0].get("storage_url", "")
                        else:
                            logger.warning(f"File with hash {file_hash} marked as existing but not found in storage at {storage_path}")
                            # Continue with upload
            except Exception as e:
                logger.error(f"Error checking for existing file: {str(e)}")
                # Continue with upload
            
        # Generate destination path based on phone number if available
        if phone_number:
            # Clean the phone number (remove + and spaces)
            clean_phone = phone_number.replace("+", "").replace(" ", "")
            destination_path = f"{clean_phone}/{filename}"
            logger.debug(f"Generated phone-based path: {destination_path}")
        else:
            # Fall back to user_id based path if phone number not provided
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            destination_path = f"{user_id}/{timestamp}_{filename}"
            logger.debug(f"Generated user-based path: {destination_path}")
        
        # Guess mime type if not provided
        if "mime_type" not in metadata:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                metadata["mime_type"] = mime_type
            else:
                metadata["mime_type"] = "application/octet-stream"
            logger.debug(f"Detected mime type: {metadata['mime_type']}")
        
        # Add phone number to metadata if available
        if phone_number:
            metadata["phone_number"] = phone_number
            
        # Add user_id to metadata
        metadata["user_id"] = user_id
                
        # Upload file with retries
        attempt = 0
        last_error = None
        bucket = "whatsapp-files"  # Use your bucket name
        
        while attempt <= max_retries:
            try:
                attempt += 1
                logger.info(f"Upload attempt {attempt} for {filename} to {destination_path}")
                
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                # Use force_upload for second attempt onwards
                if attempt > 1 or force_upload:
                    upload_result = self.storage_service.force_upload(
                        bucket=bucket,
                        destination_path=destination_path,
                        file_content=file_content,
                        content_type=metadata.get("mime_type")
                    )
                else:
                    upload_result = self.storage_service.upload(
                        bucket=bucket,
                        destination_path=destination_path,
                        file_content=file_content,
                        content_type=metadata.get("mime_type")
                    )
                
                # Check result status
                status = upload_result.get("status", "")
                
                if status in ["uploaded", "uploaded_with_new_name", "exists"]:
                    # Get the actual path that was used (may have changed if renamed)
                    actual_path = upload_result.get("path", destination_path)
                    
                    # Get public URL
                    url = self.storage_service.get_url(bucket, actual_path)
                    
                    # Update database record with storage path
                    self._update_file_record(file_hash, actual_path, url, metadata)
                    
                    logger.info(f"Successfully uploaded file {filename} to {actual_path} (status: {status})")
                    return url
                elif status == "upload_failed_verification":
                    logger.error(f"Upload verification failed for {destination_path}")
                    last_error = f"Verification failed: {upload_result.get('verification_error', 'unknown error')}"
                    # Continue to next retry
                else:
                    logger.error(f"Upload failed with status {status}")
                    last_error = upload_result.get("error", "unknown error")
                    # Continue to next retry
                
            except Exception as e:
                logger.error(f"Error during upload attempt {attempt} for {filename}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                last_error = str(e)
        
        # All attempts failed
        logger.error(f"All {max_retries + 1} upload attempts failed for {filename}")
        
        # Increment upload attempts in the database
        try:
            self._increment_upload_attempts(file_hash)
        except Exception as db_err:
            logger.error(f"Failed to update upload attempts: {str(db_err)}")
        
        # Try creating an "upload failed" record for monitoring
        try:
            failed_record = {
                "file_hash": file_hash,
                "local_path": file_path,
                "attempted_path": destination_path,
                "last_error": last_error,
                "upload_attempts": attempt,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "failed"
            }
            
            if phone_number:
                failed_record["phone_number"] = phone_number
                
            if user_id:
                failed_record["user_id"] = user_id
                
            # Use the database_client method for database operations
            self._insert_failed_upload_record(failed_record)
            logger.info(f"Recorded failed upload for {filename}")
        except Exception as e:
            logger.error(f"Error creating failure record: {str(e)}")
            
        raise Exception(f"Failed to upload file after {max_retries + 1} attempts: {last_error}")
    
    def _insert_failed_upload_record(self, record: Dict[str, Any]) -> None:
        """Insert a record into the failed_uploads table using the service client."""
        # Check if storage_service has a service_client attribute
        if hasattr(self.storage_service, 'service_client'):
            self.storage_service.service_client.table("failed_uploads").insert(record).execute()
        # For SupabaseStorageService which directly has supabase attribute
        elif hasattr(self.storage_service, 'supabase'):
            self.storage_service.supabase.table("failed_uploads").insert(record).execute()
        else:
            logger.error("No suitable client found for database operations")
            raise ValueError("No suitable client found for database operations")
    
    def verify_storage(self, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify files in the database actually exist in storage and report inconsistencies
        
        Args:
            phone_number: Optional phone number to filter files
            
        Returns:
            Dictionary with verification results
        """
        results = {
            "total_files": 0,
            "verified_files": 0,
            "missing_files": 0,
            "details": []
        }
        
        try:
            # Query files from database
            db_results = self._query_files_for_verification(phone_number)
            
            if not db_results:
                logger.info(f"No files found in database for verification")
                return results
                
            results["total_files"] = len(db_results)
            
            bucket = "whatsapp-files"  # Use your bucket name
            
            # Check each file
            for file_record in db_results:
                storage_path = file_record.get("storage_path", "")
                file_hash = file_record.get("file_hash", "")
                
                if not storage_path:
                    logger.warning(f"File record {file_record.get('id', 'unknown')} has no storage path")
                    continue
                    
                # Verify file exists in storage
                exists_in_storage = self.storage_service._check_file_exists(bucket, storage_path)
                
                if exists_in_storage:
                    results["verified_files"] += 1
                else:
                    results["missing_files"] += 1
                    logger.warning(f"File missing in storage: {storage_path}")
                    
                    results["details"].append({
                        "file_id": file_record.get("id", "unknown"),
                        "file_hash": file_hash,
                        "storage_path": storage_path,
                        "phone_number": file_record.get("phone_number", "unknown"),
                        "status": "missing"
                    })
                    
            return results
        except Exception as e:
            logger.error(f"Error during storage verification: {str(e)}")
            results["error"] = str(e)
            return results
    
    def _query_files_for_verification(self, phone_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query files for verification using the appropriate client."""
        # Check which client to use
        if hasattr(self.storage_service, 'service_client'):
            # For StorageService
            query = self.storage_service.service_client.table("files").select("*").eq("uploaded", True)
            
            if phone_number:
                clean_phone = phone_number.replace("+", "").replace(" ", "")
                query = query.eq("phone_number", clean_phone)
                
            result = query.execute()
            return result.data if result.data else []
            
        elif hasattr(self.storage_service, 'supabase'):
            # For SupabaseStorageService
            query = self.storage_service.supabase.table("files").select("*").eq("uploaded", True)
            
            if phone_number:
                clean_phone = phone_number.replace("+", "").replace(" ", "")
                query = query.eq("phone_number", clean_phone)
                
            result = query.execute()
            return result.data if result.data else []
            
        else:
            logger.error("No suitable client found for database operations")
            return []
    
    def _update_file_record(self, file_hash: str, storage_path: str, storage_url: str, metadata: Dict[str, Any]) -> None:
        """Update or create a file record in the database"""
        try:
            # Update existing record if it exists
            update_data = {
                "uploaded": True,
                "storage_path": storage_path,
                "storage_url": storage_url,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add phone number if available
            if "phone_number" in metadata:
                update_data["phone_number"] = metadata["phone_number"]
                
            # Add user_id if available
            if "user_id" in metadata:
                update_data["user_id"] = metadata["user_id"]
            
            # Choose the appropriate client
            client = self._get_database_client()
            
            # Update database
            result = client.table("files").update(update_data).eq("file_hash", file_hash).execute()
            
            # If no rows updated, create a new record
            if not result.data or len(result.data) == 0:
                logger.info(f"No existing record for file hash {file_hash}, creating new record")
                
                # Create minimal record data
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
                
                # Add phone number if available
                if "phone_number" in metadata:
                    file_data["phone_number"] = metadata["phone_number"]
                    
                # Add user_id if available
                if "user_id" in metadata:
                    file_data["user_id"] = metadata["user_id"]
                    
                # Insert new record
                client.table("files").insert(file_data).execute()
        except Exception as e:
            logger.error(f"Failed to update file record for {file_hash}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _get_database_client(self):
        """Get the appropriate database client based on the storage service type."""
        if hasattr(self.storage_service, 'service_client'):
            return self.storage_service.service_client
        elif hasattr(self.storage_service, 'supabase'):
            return self.storage_service.supabase
        else:
            logger.error("No suitable client found for database operations")
            raise ValueError("No suitable client found for database operations")
            
    def _increment_upload_attempts(self, file_hash: str) -> None:
        """Increment the upload attempts counter for a file"""
        try:
            client = self._get_database_client()
            
            # First, get current value
            result = client.table("files").select("upload_attempts").eq("file_hash", file_hash).execute()
            
            if result.data and len(result.data) > 0:
                current_attempts = result.data[0].get("upload_attempts", 0)
                
                # Update counter
                client.table("files").update({
                    "upload_attempts": current_attempts + 1,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("file_hash", file_hash).execute()
            else:
                logger.warning(f"No record found for file hash {file_hash} when incrementing upload attempts")
        except Exception as e:
            logger.error(f"Error incrementing upload attempts for {file_hash}: {str(e)}")
            
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def force_upload_all_missing(self) -> Dict[str, Any]:
        """Force upload all files that are marked as uploaded but missing from storage"""
        results = {
            "total_checked": 0,
            "missing_files": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "details": []
        }
        
        # First, find all files that need to be uploaded
        verify_results = self.verify_storage()
        
        results["total_checked"] = verify_results["total_files"]
        results["missing_files"] = verify_results["missing_files"]
        
        if verify_results["missing_files"] == 0:
            logger.info("No missing files to force upload")
            return results
            
        # Process each missing file
        for file_detail in verify_results["details"]:
            try:
                file_hash = file_detail["file_hash"]
                storage_path = file_detail["storage_path"]
                
                # Query file record to get local path
                client = self._get_database_client()
                file_query = client.table("files").select("*").eq("file_hash", file_hash).execute()
                
                if not file_query.data or len(file_query.data) == 0:
                    logger.error(f"No database record found for file hash {file_hash}")
                    results["failed_uploads"] += 1
                    file_detail["upload_result"] = "failed"
                    file_detail["error"] = "no_database_record"
                    results["details"].append(file_detail)
                    continue
                
                file_record = file_query.data[0]
                local_path = file_record.get("local_path", "")
                
                if not local_path or not os.path.exists(local_path):
                    logger.error(f"Local file not found at {local_path} for file hash {file_hash}")
                    results["failed_uploads"] += 1
                    file_detail["upload_result"] = "failed"
                    file_detail["error"] = "local_file_not_found"
                    results["details"].append(file_detail)
                    continue
                
                # Force upload the file
                try:
                    phone_number = file_record.get("phone_number")
                    user_id = file_record.get("user_id")
                    
                    metadata = {
                        "file_hash": file_hash,
                        "mime_type": file_record.get("mime_type", "application/octet-stream")
                    }
                    
                    if phone_number:
                        metadata["phone_number"] = phone_number
                    
                    if user_id:
                        metadata["user_id"] = user_id
                    
                    # Call upload_file with force_upload=True
                    url = self.upload_file(
                        file_path=local_path,
                        user_id=user_id or "unknown",
                        phone_number=phone_number,
                        metadata=metadata,
                        force_upload=True
                    )
                    
                    logger.info(f"Successfully force uploaded file with hash {file_hash} to {storage_path}")
                    results["successful_uploads"] += 1
                    file_detail["upload_result"] = "success"
                    file_detail["url"] = url
                    results["details"].append(file_detail)
                    
                except Exception as upload_error:
                    logger.error(f"Failed to force upload file with hash {file_hash}: {str(upload_error)}")
                    results["failed_uploads"] += 1
                    file_detail["upload_result"] = "failed"
                    file_detail["error"] = str(upload_error)
                    results["details"].append(file_detail)
                
            except Exception as e:
                logger.error(f"Error processing missing file: {str(e)}")
                results["failed_uploads"] += 1
        
        return results