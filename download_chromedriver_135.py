#!/usr/bin/env python3
"""
Script to download ChromeDriver version 135.0.7049.95 for Chrome 135
"""

import os
import sys
import platform
import zipfile
import shutil
from urllib.request import urlretrieve

# Define compatible ChromeDriver version for Chrome 135
CHROMEDRIVER_VERSION = "135.0.7049.95"

# Create directory for ChromeDriver
chrome_dir = "chromedriver_135"
os.makedirs(chrome_dir, exist_ok=True)

# Determine platform and download URL
system = platform.system()
if system == "Darwin":  # macOS
    if platform.machine() == "arm64":
        platform_name = "mac_arm64"
    else:
        platform_name = "mac64"
elif system == "Windows":
    platform_name = "win32"
elif system == "Linux":
    platform_name = "linux64"
else:
    print(f"Unsupported platform: {system}")
    sys.exit(1)

# Construct download URL using Chrome for Testing repository
download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{CHROMEDRIVER_VERSION}/chromedriver-{platform_name}.zip"

# Download ChromeDriver
print(f"Downloading ChromeDriver version {CHROMEDRIVER_VERSION} for {platform_name}...")
zip_path = os.path.join(chrome_dir, "chromedriver.zip")

try:
    urlretrieve(download_url, zip_path)
    print(f"Downloaded ChromeDriver to {zip_path}")
except Exception as e:
    # Try alternative URL format
    alt_download_url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{CHROMEDRIVER_VERSION}/{platform_name}/chromedriver-{platform_name}.zip"
    try:
        print(f"First URL failed, trying alternative URL...")
        urlretrieve(alt_download_url, zip_path)
        print(f"Downloaded ChromeDriver to {zip_path}")
    except Exception as e2:
        print(f"Error downloading ChromeDriver: {e2}")
        print(f"Please download ChromeDriver 135.0.7049.95 manually from:")
        print(f"https://chromedriver.chromium.org/downloads")
        sys.exit(1)

# Extract ChromeDriver
print(f"Extracting ChromeDriver...")
try:
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(chrome_dir)
    
    # The extracted structure might be in a subdirectory
    chromedriver_path = ""
    for root, dirs, files in os.walk(chrome_dir):
        for file in files:
            if file == "chromedriver" or file == "chromedriver.exe":
                chromedriver_path = os.path.join(root, file)
                break
    
    if not chromedriver_path:
        # Look for the executable in a nested directory
        nested_dir = os.path.join(chrome_dir, f"chromedriver-{platform_name}")
        if os.path.exists(nested_dir):
            for file in os.listdir(nested_dir):
                if file == "chromedriver" or file == "chromedriver.exe":
                    chromedriver_path = os.path.join(nested_dir, file)
                    break
    
    if not chromedriver_path:
        print("Could not find chromedriver executable in the extracted files.")
        sys.exit(1)
    
    # Make executable
    if system != "Windows":
        os.chmod(chromedriver_path, 0o755)
    
    # Create a copy at the project root for easy access
    project_driver = "chromedriver.exe" if system == "Windows" else "chromedriver"
    shutil.copy(chromedriver_path, project_driver)
    os.chmod(project_driver, 0o755)
    
    print(f"Extracted ChromeDriver to {chromedriver_path}")
    print(f"Copied to {os.path.abspath(project_driver)}")
    
    # Output instructions for setting WDM_CHROME_VERSION
    print("\nTo use with webdriver_manager, set this environment variable:")
    if system == "Windows":
        print("set WDM_CHROME_VERSION=135")
    else:
        print("export WDM_CHROME_VERSION=135")
    
    # Create a small script to modify the WhatsApp service
    whatsapp_service_path = "app/services/whatsapp_service.py"
    if os.path.exists(whatsapp_service_path):
        print("\nModifying WhatsApp service to use the downloaded ChromeDriver...")
        
        # Backup the file
        backup_path = f"{whatsapp_service_path}.backup"
        shutil.copy(whatsapp_service_path, backup_path)
        print(f"Created backup at {backup_path}")
        
        # Read the file
        with open(whatsapp_service_path, "r") as f:
            content = f.read()
        
        # Replace the ChromeDriver initialization
        if "ChromeDriverManager().install()" in content:
            driver_abs_path = os.path.abspath(project_driver)
            # Escape backslashes for Windows paths
            if system == "Windows":
                driver_abs_path = driver_abs_path.replace("\\", "\\\\")
            
            modified_content = content.replace(
                "service = Service(ChromeDriverManager().install())",
                f'service = Service(executable_path=r"{driver_abs_path}")'
            )
            
            # Write the modified content
            with open(whatsapp_service_path, "w") as f:
                f.write(modified_content)
            
            print(f"Successfully updated {whatsapp_service_path}")
        else:
            print(f"Could not find 'ChromeDriverManager().install()' in {whatsapp_service_path}")
    
    print("\nSetup complete!")
    print(f"ChromeDriver version {CHROMEDRIVER_VERSION} is ready to use.")
    
except Exception as e:
    print(f"Error extracting ChromeDriver: {e}")
    sys.exit(1)