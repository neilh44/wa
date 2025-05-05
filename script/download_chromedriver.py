#!/usr/bin/env python3
"""
Chrome Driver Downloader - Simple script to download a ChromeDriver matching your Chrome version
"""

import os
import sys
import platform
import subprocess
import zipfile
import shutil
from urllib.request import urlretrieve
import re
import requests

def get_chrome_version():
    """Get the installed Chrome version."""
    system = platform.system()
    chrome_version = None
    
    try:
        if system == "Darwin":  # macOS
            process = subprocess.Popen(
                ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            output, _ = process.communicate()
            match = re.search(r'Google Chrome ([0-9.]+)', output.decode('utf-8'))
            if match:
                chrome_version = match.group(1)
        elif system == "Windows":
            try:
                # First method using registry
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                chrome_version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
            except:
                # Second method using PowerShell
                process = subprocess.Popen(
                    ['powershell', '-command', '(Get-Item "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe").VersionInfo.FileVersion'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                output, _ = process.communicate()
                chrome_version = output.decode('utf-8').strip()
        elif system == "Linux":
            process = subprocess.Popen(
                ['google-chrome', '--version'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            output, _ = process.communicate()
            match = re.search(r'Google Chrome ([0-9.]+)', output.decode('utf-8'))
            if match:
                chrome_version = match.group(1)
    except Exception as e:
        print(f"Error getting Chrome version: {e}")
        chrome_version = None
    
    return chrome_version

def download_chromedriver(chrome_version):
    """Download the ChromeDriver matching the Chrome version."""
    if not chrome_version:
        print("Could not determine Chrome version. Please install Chrome.")
        return None
    
    # Get the major version
    major_version = chrome_version.split('.')[0]
    print(f"Chrome major version: {major_version}")
    
    # Get the matching ChromeDriver version
    try:
        response = requests.get(f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}")
        if response.status_code != 200:
            print(f"Could not find ChromeDriver for Chrome version {major_version}")
            return None
        
        chromedriver_version = response.text.strip()
        print(f"Matching ChromeDriver version: {chromedriver_version}")
    except Exception as e:
        print(f"Error finding matching ChromeDriver version: {e}")
        return None
    
    # Determine platform and download URL
    system = platform.system()
    machine = platform.machine().lower()
    
    if system == "Darwin":  # macOS
        if machine == "arm64" or machine == "aarch64":
            platform_name = "mac_arm64"
        else:
            platform_name = "mac64"
    elif system == "Windows":
        platform_name = "win32"
    elif system == "Linux":
        platform_name = "linux64"
    else:
        print(f"Unsupported platform: {system}")
        return None
    
    download_url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_{platform_name}.zip"
    print(f"Download URL: {download_url}")
    
    # Create downloads directory
    os.makedirs("downloads", exist_ok=True)
    zip_path = os.path.join("downloads", "chromedriver.zip")
    
    try:
        print(f"Downloading ChromeDriver...")
        urlretrieve(download_url, zip_path)
        
        # Extract the zip file
        print(f"Extracting ChromeDriver...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("downloads")
        
        # Determine chromedriver executable path
        if system == "Windows":
            chromedriver_path = os.path.join("downloads", "chromedriver.exe")
        else:
            chromedriver_path = os.path.join("downloads", "chromedriver")
            # Make it executable
            os.chmod(chromedriver_path, 0o755)
            
        # Create a link in the project root
        project_driver = "chromedriver.exe" if system == "Windows" else "chromedriver"
        if os.path.exists(project_driver):
            os.remove(project_driver)
        
        shutil.copy(chromedriver_path, project_driver)
        print(f"Copied ChromeDriver to current directory: {os.getcwd()}")
        
        return chromedriver_path
    except Exception as e:
        print(f"Error downloading or extracting ChromeDriver: {e}")
        return None

def main():
    print("Chrome Driver Downloader")
    print("=" * 30)
    
    # Get Chrome version
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("Failed to detect Chrome version. Using '135' from error logs.")
        chrome_version = "135.0.0.0"
    
    print(f"Chrome version: {chrome_version}")
    
    # Download matching ChromeDriver
    chromedriver_path = download_chromedriver(chrome_version)
    if chromedriver_path:
        print(f"\nSuccess! ChromeDriver downloaded to: {chromedriver_path}")
        print(f"A copy has also been placed in the current directory.")
        
        # Tell the user how to use this with webdriver-manager
        print("\nTo force webdriver-manager to use this version:")
        print("Set the WDM_CHROME_VERSION environment variable:")
        major_version = chrome_version.split('.')[0]
        if platform.system() == "Windows":
            print(f"  set WDM_CHROME_VERSION={major_version}")
        else:
            print(f"  export WDM_CHROME_VERSION={major_version}")
        
        # Also create a small script to set the env var
        if platform.system() == "Windows":
            with open("set_chrome_version.bat", "w") as f:
                f.write(f"@echo off\nset WDM_CHROME_VERSION={major_version}\necho Chrome version set to %WDM_CHROME_VERSION%\n")
            print("Created set_chrome_version.bat - run this before starting your application")
        else:
            with open("set_chrome_version.sh", "w") as f:
                f.write(f"#!/bin/bash\nexport WDM_CHROME_VERSION={major_version}\necho Chrome version set to $WDM_CHROME_VERSION\n")
            os.chmod("set_chrome_version.sh", 0o755)
            print("Created set_chrome_version.sh - run this with: source set_chrome_version.sh")
    else:
        print("Failed to download ChromeDriver.")

if __name__ == "__main__":
    main()