import os
import hashlib
import platform
import mimetypes
from datetime import datetime
from typing import List, Dict, Any

from app.utils.logger import get_logger
from app.services.phone_extraction import PhoneExtractor

logger = get_logger()

class FileManager:
    """Manages WhatsApp file operations including scanning, hashing, and organizing."""
    
    def __init__(self, user_id, data_dir):
        self.user_id = user_id
        self.data_dir = data_dir
        self.phone_extractor = PhoneExtractor()
        
        # Create necessary directories
        self.downloads_dir = os.path.join(data_dir, "downloads")
        self.organized_dir = os.path.join(data_dir, "organized_by_phone")
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.organized_dir, exist_ok=True)
    
    def get_whatsapp_media_paths(self) -> List[str]:
        """Return platform-specific WhatsApp media paths."""
        paths = []
        
        # Add the primary specified path
        primary_path = "/Users/nileshhanotia/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/Message/Media"
        paths.append(primary_path)
        
        # Mac OS paths (more generalized versions)
        if platform.system() == "Darwin":  # Mac OS
            # Add potential Mac paths
            username = os.environ.get("USER", "")
            if username:
                paths.append(f"/Users/{username}/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/Message/Media")
        
        # Windows paths
        elif platform.system() == "Windows":
            # Add Windows-specific paths if needed
            username = os.environ.get("USERNAME", "")
            if username:
                paths.append(f"C:\\Users\\{username}\\AppData\\Local\\WhatsApp\\Media")
        
        # Linux paths
        elif platform.system() == "Linux":
            # Add Linux-specific paths if needed
            home = os.environ.get("HOME", "")
            if home:
                paths.append(f"{home}/.config/WhatsApp/Media")
        
        return paths
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file for deduplication."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def organize_file_by_phone(self, original_path: str, filename: str, phone_number: str, media_type: str) -> str:
        """
        Organize a file into a phone number-based directory structure.
        
        Args:
            original_path: Original file path
            filename: The name of the file
            phone_number: The phone number to organize by
            media_type: The type of media (image, video, audio, document)
            
        Returns:
            The new organized file path, or None if organization failed
        """
        if not phone_number or phone_number == "unknown":
            logger.warning(f"Cannot organize file without phone number: {original_path}")
            return None
            
        try:
            # Create base directory for organized files
            organized_base = os.path.join(self.data_dir, "organized")
            os.makedirs(organized_base, exist_ok=True)
            
            # Create directory for this phone number
            phone_dir = os.path.join(organized_base, phone_number)
            os.makedirs(phone_dir, exist_ok=True)
            
            # Create directory for this media type within the phone directory
            media_dir = os.path.join(phone_dir, media_type)
            os.makedirs(media_dir, exist_ok=True)
            
            # Determine the destination path
            dest_path = os.path.join(media_dir, filename)
            
            # Check if the file already exists at the destination
            if os.path.exists(dest_path):
                logger.info(f"File already exists at destination: {dest_path}")
                return dest_path
                
            # Copy the file (don't move, to keep the original)
            import shutil
            shutil.copy2(original_path, dest_path)
            logger.info(f"Organized file to: {dest_path}")
            
            return dest_path
        except Exception as e:
            logger.error(f"Error organizing file {original_path}: {str(e)}")
            return None
            
    def scan_whatsapp_files(self, active_chats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan directories for WhatsApp files.
        
        Args:
            active_chats: Dictionary of active chats with timestamps
            
        Returns:
            Dictionary with scan results including files and statistics
        """
        # Placeholder for downloaded files
        downloaded_files = []
        stats = {
            "images": 0,
            "documents": 0,
            "audio": 0,
            "video": 0,
            "other": 0,
            "total_size": 0,
            "error_count": 0,
            "duplicate_count": 0,
            "phone_numbers": {}  # Track files per phone number
        }
        
        # File type mappings
        file_type_mappings = {
            # Images
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic'],
            # Documents
            'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', 
                        '.csv', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers', '.key'],
            # Audio
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.opus', '.amr'],
            # Video
            'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            # Archives
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        }
        
        # Flatten for extension checking
        all_extensions = [ext for exts in file_type_mappings.values() for ext in exts]
        
        # WhatsApp specific file patterns
        whatsapp_patterns = [
            'WhatsApp Image', 'WhatsApp Video', 'WhatsApp Audio', 'WhatsApp Document',
            'WA', 'IMG-', 'VID-', 'AUD-', 'DOC-', 'PTT-'
        ]
        
        # Get media paths to scan
        possible_paths = self.get_whatsapp_media_paths()
        
        # Log all potential paths
        for path in possible_paths:
            exists = os.path.exists(path)
            readable = exists and os.access(path, os.R_OK)
            logger.info(f"Will scan directory: {path} (exists: {exists}, readable: {readable})")
        
        # Scan all potential directories
        paths_scanned = 0
        
        for base_path in possible_paths:
            # Skip paths that don't exist
            if not os.path.exists(base_path):
                logger.debug(f"Path does not exist: {base_path}")
                continue
            
            # Skip paths we don't have permission to read
            if not os.access(base_path, os.R_OK):
                logger.warning(f"No read permission for path: {base_path}")
                continue
                
            logger.info(f"Scanning directory: {base_path}")
            paths_scanned += 1
            
            # Take a snapshot of the directory structure for debugging
            dir_structure = []
            try:
                # Only list top-level directories to avoid excessive logging
                dir_structure = os.listdir(base_path)
                logger.debug(f"Directory structure: {', '.join(dir_structure[:10])}" + 
                            (f" and {len(dir_structure) - 10} more..." if len(dir_structure) > 10 else ""))
            except Exception as e:
                logger.error(f"Error listing directory structure: {str(e)}")
            
            # Walk through all directories and files
            try:
                file_count = 0
                for root, dirs, files in os.walk(base_path):
                    # Log progress periodically
                    if file_count > 0 and file_count % 100 == 0:
                        logger.info(f"Processed {file_count} files so far in {base_path}")
                    
                    for file in files:
                        file_count += 1
                        file_path = os.path.join(root, file)
                        
                        # Skip system files and non-media files
                        file_lower = file.lower()
                        
                        # Skip hidden files
                        if file.startswith('.'):
                            continue
                        
                        # Check if it's likely a WhatsApp file either by extension or pattern
                        is_valid_extension = any(file_lower.endswith(ext) for ext in all_extensions)
                        is_whatsapp_pattern = any(pattern.lower() in file_lower for pattern in whatsapp_patterns)
                        
                        if not (is_valid_extension or is_whatsapp_pattern):
                            continue
                        
                        logger.debug(f"Found potential WhatsApp file: {file}")
                        
                        try:
                            # Get file size and creation time
                            file_size = os.path.getsize(file_path)
                            
                            # Use creation time or modification time, whichever is more recent
                            file_ctime = os.path.getctime(file_path)
                            file_mtime = os.path.getmtime(file_path)
                            file_time = max(file_ctime, file_mtime)
                            file_date = datetime.fromtimestamp(file_time)
                            
                            # Try to determine mime type
                            mime_type, _ = mimetypes.guess_type(file_path)
                            if not mime_type:
                                # Use a default based on extension
                                mime_type = "application/octet-stream"
                            
                            # Determine media type
                            media_type = 'other'
                            for type_name, extensions in file_type_mappings.items():
                                if any(file_lower.endswith(ext) for ext in extensions):
                                    media_type = type_name
                                    break
                            
                            # Try to determine phone number from filename or match with active chats
                            phone_number = self.phone_extractor.extract_phone_number(file_path, file_date, active_chats)

                            
                            # Calculate file hash for deduplication
                            file_hash = self.calculate_file_hash(file_path)
                            
                            # Stats tracking
                            stats[media_type if media_type in stats else 'other'] += 1
                            stats['total_size'] += file_size
                            
                            # Check for duplicates
                            is_duplicate = False
                            for existing_file in downloaded_files:
                                if (existing_file["filename"] == file and 
                                    existing_file["size"] == file_size):
                                    is_duplicate = True
                                    stats['duplicate_count'] += 1
                                    break
                                    
                            if is_duplicate:
                                continue
                            
                            # Try to organize file by phone number
                            organized_path = self.organize_file_by_phone(file_path, file, phone_number, media_type)
                                
                            file_info = {
                                "filename": file,
                                "local_path": file_path,
                                "organized_path": organized_path,
                                "phone_number": phone_number,
                                "size": file_size,
                                "mime_type": mime_type,
                                "media_type": media_type,
                                "created_at": file_date.isoformat(),
                                "source_dir": base_path,
                                "file_hash": file_hash
                            }
                            
                            # Track files by phone number for stats
                            if phone_number not in stats["phone_numbers"]:
                                stats["phone_numbers"][phone_number] = {
                                    "count": 0,
                                    "size": 0,
                                    "types": {"image": 0, "video": 0, "audio": 0, "document": 0, "other": 0}
                                }
                            
                            stats["phone_numbers"][phone_number]["count"] += 1
                            stats["phone_numbers"][phone_number]["size"] += file_size
                            stats["phone_numbers"][phone_number]["types"][media_type if media_type in stats["phone_numbers"][phone_number]["types"] else "other"] += 1
                            
                            downloaded_files.append(file_info)
                            
                        except PermissionError:
                            logger.warning(f"Permission denied accessing file: {file_path}")
                            stats['error_count'] += 1
                        except Exception as e:
                            logger.error(f"Error processing file {file_path}: {str(e)}")
                            stats['error_count'] += 1
                            
            except PermissionError:
                logger.error(f"Permission denied when accessing directory: {base_path}")
            except Exception as e:
                logger.error(f"Error scanning directory {base_path}: {str(e)}")
        
        if paths_scanned == 0:
            logger.warning("No WhatsApp media directories were accessible for scanning")
            
        # Log statistics
        logger.info(f"Download scan complete. Found {len(downloaded_files)} new files:")
        logger.info(f"Images: {stats['images']}, Documents: {stats['documents']}, " 
                    f"Audio: {stats['audio']}, Video: {stats['video']}, Other: {stats['other']}")
        logger.info(f"Total size: {stats['total_size'] / (1024 * 1024):.2f} MB")
        
        # Log phone number statistics
        if stats['phone_numbers']:
            logger.info(f"Files organized by {len(stats['phone_numbers'])} phone numbers:")
            for phone, phone_stats in stats['phone_numbers'].items():
                logger.info(f"  - {phone}: {phone_stats['count']} files, " 
                        f"{phone_stats['size'] / (1024 * 1024):.2f} MB "
                        f"({phone_stats['types']})")
        
        return {
            "files": downloaded_files,
            "stats": stats,
            "paths_scanned": paths_scanned
        }
        
    def copy_file_to_downloads(self, file_path: str, filename: str) -> str:
        """
        Copy a file to the downloads directory.
        
        Args:
            file_path: Original file path
            filename: Original filename
            
        Returns:
            Path to the copied file
        """
        import shutil
        
        # Create destination path
        dest_path = os.path.join(self.downloads_dir, filename)
        
        # Check if file already exists
        if os.path.exists(dest_path):
            # Add timestamp to make unique
            base, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_path = os.path.join(self.downloads_dir, f"{base}_{timestamp}{ext}")
        
        # Copy the file
        try:
            shutil.copy2(file_path, dest_path)
            logger.debug(f"Copied file to downloads directory: {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"Error copying file to downloads directory: {str(e)}")
            return file_path
    
    def get_file_type_from_extension(self, filename: str) -> str:
        """
        Determine media type from file extension.
        
        Args:
            filename: Filename to analyze
            
        Returns:
            Media type category
        """
        # File type mappings
        file_type_mappings = {
            # Images
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic'],
            # Documents
            'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', 
                        '.csv', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers', '.key'],
            # Audio
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.opus', '.amr'],
            # Video
            'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            # Archives
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        }
        
        file_lower = filename.lower()
        for type_name, extensions in file_type_mappings.items():
            if any(file_lower.endswith(ext) for ext in extensions):
                return type_name
        
        return 'other'
    
    def is_whatsapp_file(self, filename: str) -> bool:
        """
        Check if file is likely a WhatsApp media file based on naming patterns.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if likely a WhatsApp file, False otherwise
        """
        # WhatsApp specific file patterns
        whatsapp_patterns = [
            'WhatsApp Image', 'WhatsApp Video', 'WhatsApp Audio', 'WhatsApp Document',
            'WA', 'IMG-', 'VID-', 'AUD-', 'DOC-', 'PTT-'
        ]
        
        file_lower = filename.lower()
        
        # Check for WhatsApp patterns
        is_whatsapp_pattern = any(pattern.lower() in file_lower for pattern in whatsapp_patterns)
        
        # Check for valid media extensions
        valid_extensions = [
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
            '.csv', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers', '.key',
            # Audio
            '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.opus', '.amr',
            # Video
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        ]
        
        is_valid_extension = any(file_lower.endswith(ext) for ext in valid_extensions)
        
        # Return true if it matches patterns or has valid extension
        return is_whatsapp_pattern or is_valid_extension
    
    def create_file_info(self, file_path: str, phone_number: str, active_chats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a file info dictionary for a WhatsApp file.
        
        Args:
            file_path: Path to the file
            phone_number: Phone number associated with the file (or None to extract)
            active_chats: Dictionary of active chats with timestamps
            
        Returns:
            File info dictionary
        """
        try:
            filename = os.path.basename(file_path)
            
            # Get file size and creation time
            file_size = os.path.getsize(file_path)
            
            # Use creation time or modification time, whichever is more recent
            file_ctime = os.path.getctime(file_path)
            file_mtime = os.path.getmtime(file_path)
            file_time = max(file_ctime, file_mtime)
            file_date = datetime.fromtimestamp(file_time)
            
            # Try to determine mime type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Use a default based on extension
                mime_type = "application/octet-stream"
            
            # Determine media type
            media_type = self.get_file_type_from_extension(filename)
            
            # Extract phone number if not provided
            if not phone_number:
                phone_number = self.phone_extractor.extract_phone_number(file_path, file_date, active_chats)
            
            # Calculate file hash for deduplication
            file_hash = self.calculate_file_hash(file_path)
            
            return {
                "filename": filename,
                "local_path": file_path,
                "phone_number": phone_number,
                "size": file_size,
                "mime_type": mime_type,
                "media_type": media_type,
                "created_at": file_date.isoformat(),
                "file_hash": file_hash
            }
            
        except Exception as e:
            logger.error(f"Error creating file info for {file_path}: {str(e)}")
            return None
            
    def process_bulk_upload(self, file_paths: List[str], phone_number: str = None) -> Dict[str, Any]:
        """
        Process a bulk upload of files.
        
        Args:
            file_paths: List of file paths to process
            phone_number: Optional phone number to associate with files
            
        Returns:
            Dictionary with process results
        """
        processed_files = []
        stats = {
            "total": len(file_paths),
            "processed": 0,
            "errors": 0,
            "by_type": {
                "image": 0,
                "document": 0,
                "audio": 0,
                "video": 0,
                "other": 0
            }
        }
        
        for file_path in file_paths:
            try:
                # Create file info
                file_info = self.create_file_info(file_path, phone_number, {})
                
                if file_info:
                    # Organize file by phone number
                    organized_path = self.organize_file_by_phone(
                        file_path, 
                        file_info["filename"], 
                        file_info["phone_number"], 
                        file_info["media_type"]
                    )
                    
                    # Update with organized path
                    file_info["organized_path"] = organized_path
                    
                    # Add to processed files
                    processed_files.append(file_info)
                    
                    # Update stats
                    stats["processed"] += 1
                    media_type = file_info["media_type"]
                    if media_type in stats["by_type"]:
                        stats["by_type"][media_type] += 1
                    else:
                        stats["by_type"]["other"] += 1
                else:
                    stats["errors"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                stats["errors"] += 1
        
        return {
            "files": processed_files,
            "stats": stats
        }