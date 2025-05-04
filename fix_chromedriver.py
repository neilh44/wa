import os
import sys
import requests
import zipfile
import platform
import shutil

# Specify the ChromeDriver version that works with Chrome 135
CHROMEDRIVER_VERSION = "135.0.5363.19"

# Create directory for ChromeDriver
chrome_dir = "chromedriver_135"
os.makedirs(chrome_dir, exist_ok=True)

# Determine platform and download URL
system = platform.system()
if system == "Darwin":  # macOS
    if platform.machine() == "arm64":
        driver_url = f"https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_mac_arm64.zip"
    else:
        driver_url = f"https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_mac64.zip"
elif system == "Windows":
    driver_url = f"https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_win32.zip"
elif system == "Linux":
    driver_url = f"https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
else:
    print(f"Unsupported platform: {system}")
    sys.exit(1)

# Download ChromeDriver
print(f"Downloading ChromeDriver version {CHROMEDRIVER_VERSION}...")
zip_path = os.path.join(chrome_dir, "chromedriver.zip")

try:
    response = requests.get(driver_url)
    response.raise_for_status()  # Raise exception for HTTP errors
    
    with open(zip_path, "wb") as f:
        f.write(response.content)
    
    print(f"Downloaded ChromeDriver to {zip_path}")
except Exception as e:
    print(f"Error downloading ChromeDriver: {e}")
    sys.exit(1)

# Extract ChromeDriver
print(f"Extracting ChromeDriver...")
try:
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(chrome_dir)
    
    # Make executable
    if system != "Windows":
        os.chmod(os.path.join(chrome_dir, "chromedriver"), 0o755)
    
    print(f"Extracted ChromeDriver to {chrome_dir}")
except Exception as e:
    print(f"Error extracting ChromeDriver: {e}")
    sys.exit(1)

# Get absolute path to ChromeDriver
if system == "Windows":
    driver_path = os.path.abspath(os.path.join(chrome_dir, "chromedriver.exe"))
else:
    driver_path = os.path.abspath(os.path.join(chrome_dir, "chromedriver"))

print(f"ChromeDriver path: {driver_path}")

# Modify WhatsApp service
service_file = "app/services/whatsapp_service.py"
if os.path.exists(service_file):
    print(f"Modifying {service_file}...")
    
    # Create backup
    backup_file = f"{service_file}.backup"
    shutil.copy(service_file, backup_file)
    print(f"Created backup at {backup_file}")
    
    try:
        # Read file content
        with open(service_file, "r") as f:
            content = f.read()
        
        # Replace ChromeDriverManager with direct path
        if "ChromeDriverManager().install()" in content:
            modified_content = content.replace(
                "service = Service(ChromeDriverManager().install())",
                f'service = Service(executable_path="{driver_path}")'
            )
            
            # Write modified content
            with open(service_file, "w") as f:
                f.write(modified_content)
            
            print(f"Successfully updated {service_file}")
        else:
            print(f"Could not find 'ChromeDriverManager().install()' in {service_file}")
            print("You may need to manually modify the file.")
    except Exception as e:
        print(f"Error modifying service file: {e}")
        print(f"You can still use the downloaded ChromeDriver at: {driver_path}")
else:
    print(f"Could not find {service_file} in the current directory")
    print(f"You can still use the downloaded ChromeDriver at: {driver_path}")

print("\nSetup complete!")
print(f"ChromeDriver version {CHROMEDRIVER_VERSION} is now available at: {driver_path}")
print("Make sure to update your code to use this specific ChromeDriver path.")