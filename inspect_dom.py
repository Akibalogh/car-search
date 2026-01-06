#!/usr/bin/env python3
"""Inspect DOM structure of a TrueCar page to find standard selectors."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import json

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F43SA088174/2025-honda-accord/"

async def inspect_dom():
    """Inspect DOM structure and find standard selectors."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    print("Inspecting DOM structure of TrueCar page...")
    print(f"URL: {TEST_URL}\n")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=False, channel='chrome')
        except:
            browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            storage_state=SESSION_FILE,
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            await page.goto(TEST_URL, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_timeout(4000)
            
            print("="*80)
            print("DOM STRUCTURE ANALYSIS")
            print("="*80)
            
            # Try to find dealer name elements
            print("\n1. DEALER NAME SELECTORS")
            dealer_selectors = [
                '[data-testid*="dealer"]',
                '[class*="dealer"]',
                '[class*="Dealer"]',
                'h1', 'h2', 'h3',
                '[data-qa*="dealer"]',
                '[id*="dealer"]',
            ]
            
            for selector in dealer_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        print(f"\n   Selector: {selector} ({len(elements)} elements found)")
                        for i, elem in enumerate(elements[:3]):  # First 3
                            try:
                                text = await elem.inner_text()
                                if text and len(text.strip()) < 100:
                                    print(f"      [{i+1}] {text.strip()[:80]}")
                            except:
                                pass
                except:
                    pass
            
            # Try to find address elements
            print("\n2. DEALER ADDRESS SELECTORS")
            address_selectors = [
                '[data-testid*="address"]',
                '[class*="address"]',
                '[class*="Address"]',
                '[data-qa*="address"]',
                'address',
                '[itemprop="address"]',
            ]
            
            for selector in address_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        print(f"\n   Selector: {selector} ({len(elements)} elements found)")
                        for i, elem in enumerate(elements[:3]):
                            try:
                                text = await elem.inner_text()
                                if text and len(text.strip()) < 150:
                                    print(f"      [{i+1}] {text.strip()[:100]}")
                            except:
                                pass
                except:
                    pass
            
            # Try to find pricing elements
            print("\n3. PRICING SELECTORS")
            price_selectors = [
                '[data-testid*="price"]',
                '[class*="price"]',
                '[class*="Price"]',
                '[data-qa*="price"]',
                '[data-testid*="lease"]',
                '[class*="lease"]',
            ]
            
            for selector in price_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        print(f"\n   Selector: {selector} ({len(elements)} elements found)")
                        for i, elem in enumerate(elements[:5]):
                            try:
                                text = await elem.inner_text()
                                if text and '$' in text and len(text.strip()) < 100:
                                    print(f"      [{i+1}] {text.strip()[:80]}")
                            except:
                                pass
                except:
                    pass
            
            # Try to find vehicle info elements
            print("\n4. VEHICLE INFO SELECTORS")
            vehicle_selectors = [
                '[data-testid*="vin"]',
                '[class*="vin"]',
                'h1',
                '[data-testid*="vehicle"]',
                '[class*="vehicle"]',
            ]
            
            for selector in vehicle_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        print(f"\n   Selector: {selector} ({len(elements)} elements found)")
                        for i, elem in enumerate(elements[:3]):
                            try:
                                text = await elem.inner_text()
                                if text and len(text.strip()) < 150:
                                    print(f"      [{i+1}] {text.strip()[:100]}")
                            except:
                                pass
                except:
                    pass
            
            # Get page HTML structure (sample)
            print("\n5. PAGE STRUCTURE (sample)")
            print("   Getting page title and main headings...")
            title = await page.title()
            print(f"   Title: {title}")
            
            headings = await page.locator('h1, h2, h3').all()
            print(f"   Headings found: {len(headings)}")
            for i, h in enumerate(headings[:5]):
                try:
                    text = await h.inner_text()
                    print(f"      H{i+1}: {text.strip()[:80]}")
                except:
                    pass
            
            # Look for common data attributes
            print("\n6. DATA ATTRIBUTES")
            data_attrs = ['data-testid', 'data-qa', 'data-cy', 'data-test']
            for attr in data_attrs:
                try:
                    elements = await page.locator(f'[{attr}]').all()
                    if elements:
                        attrs_found = set()
                        for elem in elements[:20]:  # Sample
                            try:
                                val = await elem.get_attribute(attr)
                                if val:
                                    attrs_found.add(val)
                            except:
                                pass
                        if attrs_found:
                            print(f"\n   {attr} values (sample):")
                            for val in list(attrs_found)[:10]:
                                print(f"      {val}")
                except:
                    pass
            
            print("\n" + "="*80)
            print("Inspection complete. Check output above for potential selectors.")
            print("="*80)
            
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_dom())



