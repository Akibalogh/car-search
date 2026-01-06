#!/usr/bin/env python3
"""
TrueCar scraper with manual login option.
User logs in manually once, then we save the session for reuse.
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import re
from datetime import datetime
from pathlib import Path
import json

# Session storage file
SESSION_FILE = 'truecar_session.json'

# Test URL
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/"


async def manual_login_and_save_session():
    """Open browser, let user log in manually, then save session."""
    print("="*80)
    print("MANUAL LOGIN SETUP")
    print("="*80)
    print("A browser window will open.")
    print("Please:")
    print("1. Log in to TrueCar manually in the browser")
    print("2. Once logged in, press ENTER in this terminal")
    print("3. The session will be saved for future use")
    print("="*80)
    
    browser = None
    try:
        async with async_playwright() as p:
            print("\nLaunching browser...")
            try:
                # Use system Chrome (more stable than bundled Chromium)
                browser = await p.chromium.launch(
                    headless=False,  # Visible browser
                    channel='chrome'  # Use system Chrome
                )
                print("Browser launched (using system Chrome)!")
            except Exception as e:
                print(f"Could not use system Chrome: {e}")
                print("Trying bundled Chromium...")
                browser = await p.chromium.launch(headless=False)
                print("Browser launched (using bundled Chromium)!")
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            print("Navigating to TrueCar...")
            await page.goto("https://www.truecar.com", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            print("\nBrowser opened and ready!")
            print("Please log in to TrueCar in the browser window...")
            print("(The browser will stay open until you press ENTER)\n")
            
            # Wait for user to press Enter
            input("Press ENTER after you have logged in to TrueCar...")
            
            # Save the session state
            print("\nSaving session...")
            storage_state = await context.storage_state()
            with open(SESSION_FILE, 'w') as f:
                json.dump(storage_state, f)
            
            print(f"✓ Session saved to {SESSION_FILE}")
            print("You can now run the scraper with this saved session!")
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            try:
                await browser.close()
                print("\nBrowser closed.")
            except:
                pass


async def scrape_with_saved_session(url):
    """Scrape a URL using saved session."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        print("Please run the script with --login flag first to save your session.")
        return None
    
    browser = None
    try:
        async with async_playwright() as p:
            # Load saved session
            print("Launching browser with saved session...")
            try:
                # Use headless=True for automated scraping (more stable)
                browser = await p.chromium.launch(headless=True, channel='chrome')
                print("✓ Browser launched (headless, system Chrome)")
            except Exception as e:
                print(f"Could not use system Chrome: {e}")
                try:
                    browser = await p.chromium.launch(headless=True)
                    print("✓ Browser launched (headless, bundled Chromium)")
                except Exception as e2:
                    print(f"Error: {e2}")
                    raise
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                storage_state=SESSION_FILE,  # Load saved session
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            try:
                print(f"Navigating to: {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)
                
                # Extract data
                page_text = await page.inner_text('body')
                content = await page.content()
                
                result = {
                    'url': url,
                    'scrape_timestamp': datetime.now().isoformat(),
                    'error': None,
                }
                
                # Check if dealer name is visible
                if 'White Plains Honda' in page_text or 'Honda' in page_text:
                    # Try to extract dealer name
                    dealer_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Honda)'
                    dealer_matches = re.findall(dealer_pattern, page_text)
                    if dealer_matches:
                        for match in dealer_matches:
                            if not any(x in match.lower() for x in ['accord', 'civic']):
                                if 8 <= len(match) <= 100:
                                    result['dealer_name'] = match.strip()
                                    break
                
                # Extract address
                address_pattern = r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
                address_match = re.search(address_pattern, page_text)
                if address_match:
                    result['dealer_address'] = address_match.group(1).strip()
                
                # Extract vehicle details
                # VIN
                vin_pattern = r'\b([A-HJ-NPR-Z0-9]{17})\b'
                vin_match = re.search(vin_pattern, page_text)
                result['vin'] = vin_match.group(1) if vin_match else None
                
                # Year, Make, Model, Trim
                title = await page.title()
                vehicle_match = re.search(r'(?:New\s+)?(\d{4})\s+(Honda|Toyota|Nissan|Mazda|Subaru)\s+(\w+)\s+(.+?)(?:\s*[-|]|For Sale|$)', title)
                if vehicle_match:
                    result['year'] = vehicle_match.group(1)
                    result['make'] = vehicle_match.group(2)
                    result['model'] = vehicle_match.group(3)
                    trim_text = vehicle_match.group(4).strip()
                    trim_text = re.sub(r'\s+For Sale.*$', '', trim_text, flags=re.I)
                    result['trim'] = trim_text
                
                # Stock Number
                stock_match = re.search(r'Stock\s+([A-Z0-9]+)(?:\s|Listed|$)', page_text, re.I)
                result['stock_number'] = stock_match.group(1) if stock_match else None
                
                # Lease Price
                lease_match = re.search(r'Lease[:\s]+\$([0-9,]+)/mo', page_text, re.I)
                result['lease_monthly'] = lease_match.group(1).replace(',', '') if lease_match else None
                
                # MSRP
                msrp_match = re.search(r'MSRP[:\s]+\$([0-9,]+)', page_text, re.I)
                result['msrp'] = msrp_match.group(1).replace(',', '') if msrp_match else None
                
                print("\n" + "="*80)
                print("SCRAPING RESULTS:")
                print("="*80)
                for key, value in result.items():
                    print(f"{key}: {value}")
                
                return result
                
            except Exception as e:
                print(f"ERROR: {e}")
                import traceback
                traceback.print_exc()
                return {'url': url, 'error': str(e), 'scrape_timestamp': datetime.now().isoformat()}
            finally:
                if page:
                    try:
                        await page.close()
                    except:
                        pass
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
    except Exception as e:
        print(f"ERROR in browser setup: {e}")
        import traceback
        traceback.print_exc()
        return {'url': url, 'error': str(e), 'scrape_timestamp': datetime.now().isoformat()}


async def main():
    """Main function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--login':
        # Manual login mode
        await manual_login_and_save_session()
    else:
        # Scraping mode with saved session
        # Use URL from command line if provided, otherwise use default TEST_URL
        url = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '--login' else TEST_URL
        result = await scrape_with_saved_session(url)
        if result:
            df_result = pd.DataFrame([result])
            output_file = 'test_scrape_result.xlsx'
            df_result.to_excel(output_file, index=False)
            print(f"\nResults saved to {output_file}")


if __name__ == '__main__':
    asyncio.run(main())

