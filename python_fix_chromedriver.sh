#!/bin/bash

# Script to fix Chrome Driver compatibility issues
echo "WhatsApp-Supabase ChromeDriver Fix Script"
echo "========================================"

# Determine OS type
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
    CHROME_PATH=$(which google-chrome)
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="win"
    # Use PowerShell to find Chrome path
    CHROME_PATH=$(powershell.exe -command "(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe').'(Default)'")
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected platform: $PLATFORM"
echo "Chrome path: $CHROME_PATH"

# Get Chrome version
if [[ "$PLATFORM" == "mac" ]]; then
    CHROME_VERSION=$("$CHROME_PATH" --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+")
    CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1)
elif [[ "$PLATFORM" == "linux" ]]; then
    CHROME_VERSION=$("$CHROME_PATH" --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+")
    CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1)
elif [[ "$PLATFORM" == "win" ]]; then
    CHROME_VERSION=$(powershell.exe -command "(Get-Item '$CHROME_PATH').VersionInfo.FileVersion")
    CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1)
fi

echo "Chrome version: $CHROME_VERSION"
echo "Chrome major version: $CHROME_MAJOR_VERSION"

# Determine ChromeDriver download URL
CHROMEDRIVER_BASE_URL="https://chromedriver.storage.googleapis.com"

# Get matching ChromeDriver version
echo "Finding matching ChromeDriver version..."
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR_VERSION")

echo "Matching ChromeDriver version: $CHROMEDRIVER_VERSION"

# Determine download URL based on platform
if [[ "$PLATFORM" == "mac" ]]; then
    # Check architecture
    if [[ $(uname -m) == "arm64" ]]; then
        CHROMEDRIVER_URL="$CHROMEDRIVER_BASE_URL/$CHROMEDRIVER_VERSION/chromedriver_mac_arm64.zip"
    else
        CHROMEDRIVER_URL="$CHROMEDRIVER_BASE_URL/$CHROMEDRIVER_VERSION/chromedriver_mac64.zip"
    fi
elif [[ "$PLATFORM" == "linux" ]]; then
    CHROMEDRIVER_URL="$CHROMEDRIVER_BASE_URL/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
elif [[ "$PLATFORM" == "win" ]]; then
    CHROMEDRIVER_URL="$CHROMEDRIVER_BASE_URL/$CHROMEDRIVER_VERSION/chromedriver_win32.zip"
fi

echo "Download URL: $CHROMEDRIVER_URL"

# Create downloads directory
mkdir -p downloads
cd downloads

# Download ChromeDriver
echo "Downloading ChromeDriver..."
curl -L -O "$CHROMEDRIVER_URL"

# Extract the zip file
echo "Extracting ChromeDriver..."
unzip -o "chromedriver_*.zip"

# Make it executable
chmod +x chromedriver

# Determine installation path
if [[ "$PLATFORM" == "mac" ]] || [[ "$PLATFORM" == "linux" ]]; then
    INSTALL_PATH="/usr/local/bin/chromedriver"
    echo "Installing ChromeDriver to $INSTALL_PATH"
    # Check if we have permission
    if [ -w "$(dirname "$INSTALL_PATH")" ]; then
        cp chromedriver "$INSTALL_PATH"
    else
        echo "Need admin privileges to install to $INSTALL_PATH"
        sudo cp chromedriver "$INSTALL_PATH"
    fi
elif [[ "$PLATFORM" == "win" ]]; then
    INSTALL_PATH="C:\\chromedriver.exe"
    echo "Installing ChromeDriver to $INSTALL_PATH"
    # No sudo on Windows, but might need admin privileges
    cp chromedriver.exe "$INSTALL_PATH"
fi

echo "Creating symbolic link for your project..."
cd ..
ln -sf downloads/chromedriver chromedriver

echo "Installation complete!"
echo "ChromeDriver version $CHROMEDRIVER_VERSION installed successfully."
echo ""
echo "You can now run your application with a compatible ChromeDriver."