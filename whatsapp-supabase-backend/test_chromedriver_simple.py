#!/usr/bin/env python3
import sys
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def test_chromedriver():
    print(f"Testing ChromeDriver on {platform.system()} ({platform.machine()})")
    
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Simple driver setup that works with all webdriver-manager versions
        driver_path = ChromeDriverManager().install()
        print(f"Using ChromeDriver at path: {driver_path}")
        service = Service(executable_path=driver_path)
        
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
