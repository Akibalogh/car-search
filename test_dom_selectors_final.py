#!/usr/bin/env python3
"""Test DOM selector extraction for dealer name and lease price."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

SESSION_FILE = 'truecar_session.json'
TEST_URLS = [
    'https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F40SA088701/2025-honda-accord/',
    'https://www.truecar.com/new-cars-for-sale/listing/4T1DAACK3TU662973/2026-toyota-camry/',
]

async def test_extraction():
    """Test dealer name and lease price extraction."""
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
                await page.goto(url, wait_until="domcontentloaded", timeout=120000)
                await page.wait_for_timeout(4000)
                
                print(f"\n{'='*80}")
                print(f"URL: {url}")
                print(f"{'='*80}")
                
                # Test dealer name extraction
                dealer_name = None
                try:
                    dealer_header = page.locator('div[data-test="vdpDealerHeader"]')
                    if await dealer_header.count() > 0:
                        dealer_name_elem = dealer_header.locator('div.heading-4 span, div.heading-md-2 span').first
                        if await dealer_name_elem.count() > 0:
                            dealer_name = await dealer_name_elem.inner_text()
                            dealer_name = dealer_name.strip() if dealer_name else None
                except Exception as e:
                    print(f"  Dealer name extraction error: {e}")
                
                print(f"Dealer name: {dealer_name}")
                
                # Test address extraction
                dealer_address = None
                try:
                    dealer_header = page.locator('div[data-test="vdpDealerHeader"]')
                    if await dealer_header.count() > 0:
                        address_elem = dealer_header.locator('div.hidden.md\\:block').first
                        if await address_elem.count() > 0:
                            dealer_address = await address_elem.inner_text()
                            dealer_address = dealer_address.strip() if dealer_address else None
                except Exception as e:
                    print(f"  Address extraction error: {e}")
                
                print(f"Dealer address: {dealer_address}")
                
                # Test lease price extraction
                lease_price = None
                try:
                    lease_elem = page.locator('span[data-test="pricingSectionRadioGroupPrice"][data-test-item="lease"]').first
                    if await lease_elem.count() > 0:
                        lease_text = await lease_elem.inner_text()
                        import re
                        lease_match = re.search(r'\$([0-9,]+)/mo', lease_text)
                        if lease_match:
                            lease_price = lease_match.group(1).replace(',', '')
                except Exception as e:
                    print(f"  Lease price extraction error: {e}")
                
                print(f"Lease monthly: ${lease_price}/mo" if lease_price else "Lease monthly: Not found")
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
            finally:
                await page.close()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_extraction())



