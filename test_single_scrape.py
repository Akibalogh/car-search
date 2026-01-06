#!/usr/bin/env python3
"""Test scraping a single URL to see if it works."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import pandas as pd

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F43SA088174/2025-honda-accord/"

async def test_scrape():
    """Test scraping a single URL."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    print("Testing single URL scrape...")
    print(f"URL: {TEST_URL}")
    
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            try:
                browser = await p.chromium.launch(headless=True, channel='chrome')
                print("✓ Browser launched (system Chrome)")
            except Exception as e:
                print(f"Error launching browser: {e}")
                return
            
            print("Creating context with session...")
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                storage_state=SESSION_FILE,
                viewport={'width': 1920, 'height': 1080}
            )
            
            print("Creating page...")
            page = await context.new_page()
            
            print(f"Navigating to: {TEST_URL[:60]}...")
            try:
                await page.goto(TEST_URL, wait_until="domcontentloaded", timeout=90000)
                print("✓ Page loaded!")
                
                await page.wait_for_timeout(3000)
                
                page_text = await page.inner_text('body')
                print(f"✓ Page content retrieved ({len(page_text)} characters)")
                
                # Check if dealer name is visible
                if 'Honda' in page_text or 'dealer' in page_text.lower():
                    print("✓ Page appears to have dealer info")
                else:
                    print("⚠ Page may not have dealer info")
                
                await browser.close()
                print("✓ Test completed successfully!")
                
            except Exception as e:
                print(f"✗ Error during navigation/scraping: {e}")
                import traceback
                traceback.print_exc()
                await browser.close()
                
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_scrape())

