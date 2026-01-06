#!/usr/bin/env python3
"""Test extraction of key fields: dealer name, make/model, price, URL."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from full_scraper import scrape_car_page

SESSION_FILE = 'truecar_session.json'
TEST_URLS = [
    "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F40SA088701/2025-honda-accord/",
    "https://www.truecar.com/new-cars-for-sale/listing/4T1DAACK3TU662973/2026-toyota-camry/",
]

async def test_key_fields():
    """Test extraction of key fields."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, channel='chrome')
        except:
            browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(storage_state=SESSION_FILE)
        
        for url in TEST_URLS:
            page = await context.new_page()
            try:
                print("\n" + "="*80)
                print(f"TESTING: {url}")
                print("="*80)
                
                result = await scrape_car_page(page, url)
                
                print("\nKEY FIELDS:")
                print("-" * 80)
                print(f"✓ URL: {result.get('url', 'MISSING')}")
                print(f"✓ Dealer Name: {result.get('dealer_name', 'MISSING')}")
                print(f"✓ Make: {result.get('make', 'MISSING')}")
                print(f"✓ Model: {result.get('model', 'MISSING')}")
                print(f"✓ Lease Price: ${result.get('lease_monthly', 'MISSING')}/mo" if result.get('lease_monthly') else "✗ Lease Price: MISSING")
                
                # Check if all key fields are present
                key_fields = {
                    'url': result.get('url'),
                    'dealer_name': result.get('dealer_name'),
                    'make': result.get('make'),
                    'model': result.get('model'),
                    'lease_monthly': result.get('lease_monthly'),
                }
                
                missing = [k for k, v in key_fields.items() if not v]
                if missing:
                    print(f"\n⚠ Missing key fields: {', '.join(missing)}")
                else:
                    print(f"\n✓ All key fields extracted successfully!")
                
                if result.get('error'):
                    print(f"\n✗ Error: {result.get('error')}")
                
            except Exception as e:
                print(f"\n✗ Error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await page.close()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_key_fields())



