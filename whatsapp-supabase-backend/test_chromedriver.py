#!/usr/bin/env python3
import sys
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

def test_chromedriver():
    print(f"Testing ChromeDriver on {platform.system()} ({platform.machine()})")
    
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Detect platform and set appropriate driver
        system_platform = platform.system()
        
        # Special handling for Mac (macOS)
        if system_platform == "Darwin":
            # For Apple Silicon (M1/M2)
            if platform.machine() == "arm64":
                print("Detected Apple Silicon (M1/M2)")
                driver_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            # For Intel Mac
            else:
                print("Detected Intel Mac")
                driver_path = ChromeDriverManager().install()
            
            print(f"Using ChromeDriver at path: {driver_path}")
            service = Service(executable_path=driver_path)
        else:
            # For other platforms (Linux, Windows)
            service = Service(ChromeDriverManager().install())
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Open a test page
        driver.get("https://www.google.com")
        
        # Check if driver works
        title = driver.title
        print(f"Successfully opened: {title}")
        
        # Close the driver
        driver.quit()
        
        print("ChromeDriver test successful!")
        return True
    except Exception as e:
        print(f"ChromeDriver test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_chromedriver()
    sys.exit(0 if success else 1)
