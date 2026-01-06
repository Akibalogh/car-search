#!/usr/bin/env python3
"""Debug dealer name selector."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

SESSION_FILE = 'truecar_session.json'
TEST_URL = 'https://www.truecar.com/new-cars-for-sale/listing/4T1DAACK3TU662973/2026-toyota-camry/'

async def debug():
    """Debug dealer name selector."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel='chrome')
        context = await browser.new_context(storage_state=SESSION_FILE)
        page = await context.new_page()
        
        await page.goto(TEST_URL, wait_until="domcontentloaded", timeout=120000)
        await page.wait_for_timeout(4000)
        
        # Try different selectors
        print("Testing different selectors for dealer name:")
        
        selectors = [
            'div[data-test="vdpDealerHeader"]',
            'div[data-test="vdpDealerHeader"] span',
            'div[data-test="vdpDealerHeader"] div.heading-4 span',
            'div[data-test="vdpDealerHeader"] div[class*="heading-4"] span',
            'div[data-test="vdpDealerHeader"] div[class*="heading-md-2"] span',
        ]
        
        for selector in selectors:
            try:
                elems = await page.locator(selector).all()
                print(f"\n{selector}: {len(elems)} elements found")
                for i, elem in enumerate(elems[:3]):
                    text = await elem.inner_text()
                    print(f"  [{i}] {text.strip()[:80]}")
            except Exception as e:
                print(f"{selector}: Error - {e}")
        
        # Also try getting the HTML structure
        print("\n\nHTML structure of dealer header:")
        try:
            header = page.locator('div[data-test="vdpDealerHeader"]').first
            if await header.count() > 0:
                html = await header.inner_html()
                print(html[:500])
        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug())



