#!/usr/bin/env python3
"""
Selenium scraper using Playwright session cookies.
Converts Playwright cookies to Selenium format.
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime
from pathlib import Path
import json

# Test URL
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/"

# Playwright session file
PLAYWRIGHT_SESSION = 'truecar_session.json'


def setup_driver(headless=True):
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
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise


def convert_playwright_cookies_to_selenium(playwright_session_file):
    """Convert Playwright cookies to Selenium format."""
    if not Path(playwright_session_file).exists():
        return None
    
    with open(playwright_session_file, 'r') as f:
        playwright_data = json.load(f)
    
    # Playwright session has cookies in a specific format
    cookies = playwright_data.get('cookies', [])
    selenium_cookies = []
    
    for cookie in cookies:
        # Convert Playwright cookie format to Selenium format
        selenium_cookie = {
            'name': cookie.get('name'),
            'value': cookie.get('value'),
            'domain': cookie.get('domain'),
            'path': cookie.get('path', '/'),
        }
        
        # Add optional fields if present
        if 'expires' in cookie:
            selenium_cookie['expires'] = cookie['expires']
        if 'httpOnly' in cookie:
            selenium_cookie['httpOnly'] = cookie['httpOnly']
        if 'secure' in cookie:
            selenium_cookie['secure'] = cookie['secure']
        if 'sameSite' in cookie:
            selenium_cookie['sameSite'] = cookie['sameSite']
        
        selenium_cookies.append(selenium_cookie)
    
    return selenium_cookies


def scrape_car_page(driver, url):
    """Scrape a single TrueCar car listing page."""
    try:
        print(f"  Navigating to: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
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
        
        # Extract dealer name
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
    """Test scraper on a single URL using saved cookies."""
    print("="*80)
    print("SELENIUM SCRAPER TEST (Using Playwright Session Cookies)")
    print("="*80)
    print(f"Testing on URL: {TEST_URL}\n")
    
    # Check if we have saved Playwright session
    if not Path(PLAYWRIGHT_SESSION).exists():
        print(f"ERROR: {PLAYWRIGHT_SESSION} not found!")
        print("Please run simple_login.py first to save your session.")
        return
    
    driver = None
    try:
        print("Setting up Selenium driver...")
        driver = setup_driver(headless=False)  # Visible for testing
        
        print("Loading TrueCar homepage...")
        driver.get("https://www.truecar.com")
        time.sleep(2)
        
        print("Loading cookies from Playwright session...")
        selenium_cookies = convert_playwright_cookies_to_selenium(PLAYWRIGHT_SESSION)
        if selenium_cookies:
            print(f"Found {len(selenium_cookies)} cookies to load...")
            for cookie in selenium_cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"  Warning: Could not add cookie {cookie.get('name')}: {e}")
            
            print("Cookies loaded. Reloading page...")
            driver.refresh()
            time.sleep(3)
        else:
            print("No cookies found in session file!")
        
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
            print("\nClosing browser...")
            input("Press ENTER to close browser...")  # Keep browser open for inspection
            driver.quit()
            print("Browser closed.")


if __name__ == '__main__':
    test_single_url()

