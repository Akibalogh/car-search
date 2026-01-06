#!/usr/bin/env python3
"""
TrueCar scraper using Selenium with authentication.
Tests on a single URL first.
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime
from pathlib import Path
import json

# TrueCar credentials
TRUECAR_EMAIL = "akibalogh@gmail.com"
TRUECAR_PASSWORD = "wtw-MWA@avf3khk.zpk"

# Test URL
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/"

# Session storage file
SESSION_FILE = 'selenium_session.json'


def setup_driver(headless=False):
    """Set up Selenium Chrome driver."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        # Use webdriver-manager to auto-install correct ChromeDriver version
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise


def login_to_truecar(driver):
    """Login to TrueCar and save cookies."""
    try:
        print("Navigating to TrueCar login page...")
        driver.get("https://www.truecar.com/login")
        time.sleep(3)  # Wait for page to load
        
        print("Looking for login form...")
        # Try to find email field
        email_input = None
        email_selectors = [
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name*='email' i]"),
        ]
        
        for by, selector in email_selectors:
            try:
                email_input = driver.find_element(by, selector)
                if email_input.is_displayed():
                    break
            except:
                continue
        
        if not email_input:
            print("ERROR: Could not find email input field")
            return False
        
        print("Entering email...")
        email_input.clear()
        email_input.send_keys(TRUECAR_EMAIL)
        time.sleep(1)
        
        # Find password field
        password_input = None
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        
        for by, selector in password_selectors:
            try:
                password_input = driver.find_element(by, selector)
                if password_input.is_displayed():
                    break
            except:
                continue
        
        if not password_input:
            print("ERROR: Could not find password input field")
            return False
        
        print("Entering password...")
        password_input.clear()
        password_input.send_keys(TRUECAR_PASSWORD)
        time.sleep(1)
        
        # Find and click login button
        login_button = None
        login_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Log in')]"),
            (By.CSS_SELECTOR, "button:has-text('Sign in')"),
        ]
        
        for by, selector in login_selectors:
            try:
                login_button = driver.find_element(by, selector)
                if login_button.is_displayed():
                    break
            except:
                continue
        
        if not login_button:
            print("ERROR: Could not find login button")
            return False
        
        print("Clicking login button...")
        login_button.click()
        time.sleep(5)  # Wait for login to complete
        
        # Check if login was successful
        current_url = driver.current_url
        if "login" not in current_url.lower():
            print(f"✓ Login appears successful! Redirected to: {current_url}")
            # Save cookies
            cookies = driver.get_cookies()
            with open(SESSION_FILE, 'w') as f:
                json.dump(cookies, f)
            print(f"✓ Cookies saved to {SESSION_FILE}")
            return True
        else:
            print("WARNING: Still on login page - login may have failed")
            return False
            
    except Exception as e:
        print(f"ERROR during login: {e}")
        import traceback
        traceback.print_exc()
        return False


def scrape_car_page(driver, url):
    """Scrape a single TrueCar car listing page."""
    try:
        print(f"  Navigating to: {url}")
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Get page content
        page_text = driver.find_element(By.TAG_NAME, "body").text
        page_source = driver.page_source
        
        result = {
            'url': url,
            'scrape_timestamp': datetime.now().isoformat(),
            'error': None,
        }
        
        # Extract vehicle details
        # VIN
        vin_pattern = r'\b([A-HJ-NPR-Z0-9]{17})\b'
        vin_match = re.search(vin_pattern, page_text)
        result['vin'] = vin_match.group(1) if vin_match else None
        
        # Year, Make, Model, Trim from title
        title = driver.title
        vehicle_match = re.search(r'(?:New\s+)?(\d{4})\s+(Honda|Toyota|Nissan|Mazda|Subaru)\s+(\w+)\s+(.+?)(?:\s*[-|]|For Sale|$)', title)
        if vehicle_match:
            result['year'] = vehicle_match.group(1)
            result['make'] = vehicle_match.group(2)
            result['model'] = vehicle_match.group(3)
            trim_text = vehicle_match.group(4).strip()
            trim_text = re.sub(r'\s+For Sale.*$', '', trim_text, flags=re.I)
            result['trim'] = trim_text
        else:
            result['year'] = None
            result['make'] = None
            result['model'] = None
            result['trim'] = None
        
        # Stock Number
        stock_match = re.search(r'Stock\s+([A-Z0-9]+)(?:\s|Listed|$)', page_text, re.I)
        result['stock_number'] = stock_match.group(1) if stock_match else None
        
        # Extract dealer name - try multiple strategies
        dealer_name = None
        dealer_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis))'
        dealer_matches = re.findall(dealer_pattern, page_text)
        if dealer_matches:
            for match in dealer_matches:
                if not any(x in match.lower() for x in ['accord', 'camry', 'altima', 'mazda3', 'impreza', 'civic']):
                    if 8 <= len(match) <= 100:
                        dealer_name = match.strip()
                        break
        result['dealer_name'] = dealer_name
        
        # Extract dealer address
        dealer_address = None
        address_pattern = r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
        address_match = re.search(address_pattern, page_text)
        if address_match:
            dealer_address = address_match.group(1).strip()
        result['dealer_address'] = dealer_address
        
        # Extract pricing information
        # Lease Monthly Payment (primary requirement)
        lease_patterns = [
            r'Lease[:\s]+\$([0-9,]+)/mo',
            r'\$([0-9,]+)/mo.*?lease',
        ]
        lease_price = None
        for pattern in lease_patterns:
            lease_match = re.search(pattern, page_text, re.I)
            if lease_match:
                lease_price = lease_match.group(1).replace(',', '')
                break
        result['lease_monthly'] = lease_price
        
        # MSRP
        msrp_match = re.search(r'MSRP[:\s]+\$([0-9,]+)', page_text, re.I)
        result['msrp'] = msrp_match.group(1).replace(',', '') if msrp_match else None
        
        # List Price
        list_price_match = re.search(r'List\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
        result['list_price'] = list_price_match.group(1).replace(',', '') if list_price_match else None
        
        # Dealer Discount
        discount_match = re.search(r'Dealer\s+discount[:\s]+[-\$]?([0-9,]+)', page_text, re.I)
        result['dealer_discount'] = discount_match.group(1).replace(',', '') if discount_match else None
        
        # Cash Price
        cash_match = re.search(r'Cash\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
        result['cash_price'] = cash_match.group(1).replace(',', '') if cash_match else None
        
        # Finance Monthly
        finance_match = re.search(r'Finance[:\s]+\$([0-9,]+)/mo', page_text, re.I)
        result['finance_monthly'] = finance_match.group(1).replace(',', '') if finance_match else None
        
        # Additional vehicle details
        # Exterior Color
        ext_color_match = re.search(r'Exterior\s+color[:\s]+([^\n]+)', page_text, re.I)
        result['exterior_color'] = ext_color_match.group(1).strip() if ext_color_match else None
        
        # Interior Color
        int_color_match = re.search(r'Interior\s+color[:\s]+([^\n]+)', page_text, re.I)
        result['interior_color'] = int_color_match.group(1).strip() if int_color_match else None
        
        # MPG
        mpg_patterns = [
            r'MPG[:\s]+(\d+)\s*city\s*/\s*(\d+)\s*highway',
            r'(\d+)\s*city\s*/\s*(\d+)\s*highway',
        ]
        mpg = None
        for pattern in mpg_patterns:
            mpg_match = re.search(pattern, page_text, re.I)
            if mpg_match:
                mpg = f"{mpg_match.group(1)} city / {mpg_match.group(2)} highway"
                break
        result['mpg'] = mpg
        
        return result
        
    except Exception as e:
        print(f"  ERROR scraping {url}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'url': url,
            'scrape_timestamp': datetime.now().isoformat(),
            'error': str(e),
        }


def test_single_url():
    """Test scraper on a single URL."""
    print("="*80)
    print("SELENIUM SCRAPER TEST")
    print("="*80)
    print(f"Testing on URL: {TEST_URL}\n")
    
    driver = None
    try:
        # Check if we have saved cookies
        if Path(SESSION_FILE).exists():
            print(f"Found saved session: {SESSION_FILE}")
            print("Loading browser with saved cookies...\n")
            driver = setup_driver(headless=True)
            
            # Load cookies
            driver.get("https://www.truecar.com")
            with open(SESSION_FILE, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
        else:
            print("No saved session found. Will login...\n")
            driver = setup_driver(headless=False)  # Visible for login
            login_success = login_to_truecar(driver)
            if not login_success:
                print("\nERROR: Login failed. Please check credentials.")
                return
        
        # Scrape the test URL
        print(f"\nScraping test URL...")
        result = scrape_car_page(driver, TEST_URL)
        
        # Display results
        print("\n" + "="*80)
        print("SCRAPING RESULTS:")
        print("="*80)
        for key, value in result.items():
            print(f"{key}: {value}")
        
        # Save to Excel
        df_result = pd.DataFrame([result])
        output_file = 'test_scrape_result.xlsx'
        df_result.to_excel(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("\nBrowser closed.")


if __name__ == '__main__':
    test_single_url()

