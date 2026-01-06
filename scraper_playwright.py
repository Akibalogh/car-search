#!/usr/bin/env python3
"""
TrueCar scraper using Playwright with authentication.
Tests on a single URL first.
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import re
from datetime import datetime
from pathlib import Path

# TrueCar credentials
TRUECAR_EMAIL = "akibalogh@gmail.com"
TRUECAR_PASSWORD = "wtw-MWA@avf3khk.zpk"

# Rate limiting
DELAY_BETWEEN_REQUESTS = 1.5  # seconds
CONCURRENT_BROWSERS = 3


async def login_to_truecar(page):
    """Login to TrueCar and return True if successful."""
    try:
        print("Attempting to navigate to login page...")
        # Try navigating to login page
        await page.goto("https://www.truecar.com/login", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(5000)  # Wait for page to fully load
        
        current_url = page.url
        print(f"Current URL after navigation: {current_url}")
        
        # Check if we got redirected
        if "login" not in current_url.lower():
            print(f"Got redirected to: {current_url}")
            # Maybe we're already logged in or redirected
            # Try going to a protected page to trigger login
            await page.goto("https://www.truecar.com/dashboard", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            current_url = page.url
            print(f"After dashboard navigation: {current_url}")
        
        # Try different possible selectors for email
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[id*="email" i]',
            'input[placeholder*="email" i]',
            'input[type="text"][name*="email" i]',
            'input[autocomplete="email"]',
        ]
        
        print("Looking for email input field...")
        email_filled = False
        for selector in email_selectors:
            try:
                email_input = page.locator(selector).first
                count = await email_input.count()
                if count > 0:
                    # Check if element is visible
                    if await email_input.is_visible():
                        await email_input.fill(TRUECAR_EMAIL)
                        print(f"  Found email field with selector: {selector}")
                        email_filled = True
                        break
            except Exception as e:
                continue
        
        if not email_filled:
            # Try to find any input field and see what's available
            print("DEBUG: Could not find email field, checking page content...")
            current_url = page.url
            print(f"DEBUG: Current URL: {current_url}")
            page_title = await page.title()
            print(f"DEBUG: Page title: {page_title}")
            all_inputs = await page.locator('input').all()
            print(f"DEBUG: Found {len(all_inputs)} input fields on page")
            for i, inp in enumerate(all_inputs[:10]):  # Check first 10
                try:
                    input_type = await inp.get_attribute('type')
                    input_name = await inp.get_attribute('name')
                    input_id = await inp.get_attribute('id')
                    placeholder = await inp.get_attribute('placeholder')
                    visible = await inp.is_visible()
                    print(f"  Input {i}: type={input_type}, name={input_name}, id={input_id}, placeholder={placeholder}, visible={visible}")
                except:
                    pass
            # Check for iframes (login forms might be in iframes)
            iframes = await page.locator('iframe').all()
            print(f"DEBUG: Found {len(iframes)} iframes on page")
            if len(iframes) > 0:
                print("  Login form might be in an iframe, trying...")
                for i, iframe in enumerate(iframes[:3]):
                    try:
                        frame = await iframe.content_frame()
                        if frame:
                            email_in_frame = frame.locator('input[type="email"], input[name*="email" i]').first
                            count = await email_in_frame.count()
                            if count > 0:
                                await email_in_frame.fill(TRUECAR_EMAIL)
                                print(f"  Found email field in iframe {i}")
                                email_filled = True
                                break
                    except:
                        continue
            if not email_filled:
                print("ERROR: Could not find email input field")
                return False
        
        # Fill password
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id*="password"]',
        ]
        
        password_filled = False
        for selector in password_selectors:
            try:
                password_input = page.locator(selector).first
                if await password_input.count() > 0:
                    await password_input.fill(TRUECAR_PASSWORD)
                    password_filled = True
                    break
            except:
                continue
        
        if not password_filled:
            print("ERROR: Could not find password input field")
            return False
        
        # Click login button
        print("Clicking login button...")
        login_selectors = [
            'button[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
        ]
        
        login_clicked = False
        for selector in login_selectors:
            try:
                login_btn = page.locator(selector).first
                if await login_btn.count() > 0:
                    await login_btn.click()
                    login_clicked = True
                    break
            except:
                continue
        
        if not login_clicked:
            print("ERROR: Could not find login button")
            return False
        
        # Wait for navigation after login
        print("Waiting for login to complete...")
        await page.wait_for_timeout(3000)  # Wait 3 seconds for login
        
        # Check if we're logged in by looking for user menu or dashboard
        current_url = page.url
        if "login" not in current_url.lower():
            print(f"Login appears successful! Redirected to: {current_url}")
            return True
        
        # Try to check for error messages
        error_elements = await page.locator('text=/error|invalid|incorrect/i').count()
        if error_elements > 0:
            print("ERROR: Login may have failed - error message detected")
            return False
        
        print("Login completed (URL check inconclusive)")
        return True
        
    except Exception as e:
        print(f"ERROR during login: {e}")
        return False


async def scrape_car_page(page, url):
    """Scrape a single TrueCar car listing page."""
    try:
        print(f"  Fetching: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)  # Wait for dynamic content
        
        # Get page content
        content = await page.content()
        page_text = await page.inner_text('body')
        
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
        
        # Year, Make, Model, Trim from title or page text
        title = await page.title()
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
        
        # Strategy 1: Look in page text for dealer name pattern
        dealer_name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis))'
        dealer_matches = re.findall(dealer_name_pattern, page_text)
        if dealer_matches:
            for match in dealer_matches:
                if not any(x in match.lower() for x in ['accord', 'camry', 'altima', 'mazda3', 'impreza', 'civic']):
                    if 8 <= len(match) <= 100:
                        dealer_name = match.strip()
                        break
        
        # Strategy 2: Try to find in HTML structure
        if not dealer_name:
            try:
                dealer_elements = await page.locator('[class*="dealer" i], [class*="seller" i]').all()
                for elem in dealer_elements[:10]:
                    text = await elem.inner_text()
                    if text and 8 <= len(text.strip()) <= 100:
                        if re.search(r'(Honda|Toyota|Nissan|Mazda|Subaru)', text, re.I):
                            if not any(x in text.lower() for x in ['accord', 'camry', 'altima', 'mazda3', 'impreza']):
                                dealer_name = text.strip()
                                break
            except:
                pass
        
        result['dealer_name'] = dealer_name
        
        # Extract dealer address
        dealer_address = None
        address_pattern = r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
        address_match = re.search(address_pattern, page_text)
        if address_match:
            dealer_address = address_match.group(1).strip()
        
        # Try JSON extraction for address
        if not dealer_address:
            address_json_match = re.search(r'"address1"\s*:\s*"([^"]+)"', content)
            if address_json_match:
                address1 = address_json_match.group(1)
                city_match = re.search(r'"city"\s*:\s*"([^"]+)"', content)
                state_match = re.search(r'"state"\s*:\s*"([^"]+)"', content)
                zip_match = re.search(r'"zip"\s*:\s*"?([^",}]+)"?', content)
                
                address_parts = [address1]
                if city_match:
                    address_parts.append(city_match.group(1))
                if state_match:
                    address_parts.append(state_match.group(1))
                if zip_match:
                    address_parts.append(zip_match.group(1))
                
                dealer_address = ', '.join(address_parts)
        
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
        return {
            'url': url,
            'scrape_timestamp': datetime.now().isoformat(),
            'error': str(e),
        }


async def test_single_url():
    """Test scraper on a single URL."""
    # Get one URL from Accord.xlsx
    df = pd.read_excel('Accord.xlsx')
    test_url = df['Car URL'].iloc[0]
    
    print(f"Testing scraper on single URL:")
    print(f"URL: {test_url}\n")
    
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)  # Headless for automation
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # Login first
            login_success = await login_to_truecar(page)
            if not login_success:
                print("\nERROR: Login failed. Please check credentials or handle CAPTCHA manually.")
                return
            
            # Wait a bit after login
            await page.wait_for_timeout(2000)
            
            # Scrape the test URL
            print(f"\nScraping test URL...")
            result = await scrape_car_page(page, test_url)
            
            # Display results
            print("\n" + "="*80)
            print("SCRAPING RESULTS:")
            print("="*80)
            for key, value in result.items():
                print(f"{key}: {value}")
            
            # Save to Excel for inspection
            df_result = pd.DataFrame([result])
            output_file = 'test_scrape_result.xlsx'
            df_result.to_excel(output_file, index=False)
            print(f"\nResults saved to {output_file}")
            
        finally:
            await browser.close()
            print("\nBrowser closed.")


if __name__ == '__main__':
    asyncio.run(test_single_url())

