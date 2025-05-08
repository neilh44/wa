import os
import sys
from supabase import create_client

# Supabase settings
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
BUCKET_NAME = "whatsapp-files"

def main():
    # Check command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python simple_upload.py <file_path> <user_id>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    user_id = sys.argv[2]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Extract phone number from WhatsApp path
    phone_number = None
    parts = file_path.split('/')
    for i, part in enumerate(parts):
        if part == "Media" and i+1 < len(parts) and "@s.whatsapp.net" in parts[i+1]:
            phone_with_suffix = parts[i+1]
            phone_number = phone_with_suffix.split('@')[0]
            break
    
    # Create Supabase client
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Error: Missing Supabase environment variables SUPABASE_URL or SUPABASE_SERVICE_KEY")
        sys.exit(1)
    
    try:
        print("Connecting to Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        sys.exit(1)
    
    # Prepare storage path
    filename = os.path.basename(file_path)
    if phone_number:
        destination_path = f"{phone_number}/{filename}"
        print(f"Using phone number from path: {phone_number}")
    else:
        destination_path = f"{user_id}/{filename}"
        print("No phone number found in path, using user ID for organization")
    
    # Upload file
    try:
        print(f"Uploading file: {filename}")
        print(f"Destination: {destination_path}")
        
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Upload to Supabase
        result = supabase.storage.from_(BUCKET_NAME).upload(
            destination_path,
            file_content
        )
        
        # Get public URL
        url = supabase.storage.from_(BUCKET_NAME).get_public_url(destination_path)
        
        print("Upload successful!")
        print(f"Public URL: {url}")
        
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        if hasattr(e, 'json') and callable(e.json):
            try:
                error_details = e.json()
                print(f"Error details: {error_details}")
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()