#!/usr/bin/env python3
"""Test the optimized dealer name extraction in full_scraper."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from full_scraper import scrape_car_page

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F40SA088701/2025-honda-accord/"

async def test():
    """Test optimized dealer name extraction."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, channel='chrome')
        except:
            browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(storage_state=SESSION_FILE)
        page = await context.new_page()
        
        try:
            print("Testing optimized dealer name extraction...")
            print(f"URL: {TEST_URL}")
            print(f"Expected: Honda of New Rochelle\n")
            
            result = await scrape_car_page(page, TEST_URL)
            
            print("="*80)
            print("RESULTS")
            print("="*80)
            print(f"Dealer name: {result.get('dealer_name')}")
            print(f"Dealer address: {result.get('dealer_address')}")
            print(f"Error: {result.get('error')}")
            
            if result.get('dealer_name') == "Honda of New Rochelle":
                print("\n✓ SUCCESS! Matches expected result!")
            elif result.get('dealer_name'):
                print(f"\n⚠ Extracted '{result.get('dealer_name')}' but expected 'Honda of New Rochelle'")
            else:
                print("\n✗ Could not extract dealer name")
            print("="*80)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test())



