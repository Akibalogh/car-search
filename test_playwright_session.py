#!/usr/bin/env python3
"""
Simple test of Playwright with saved session.
Just try to navigate to a page and see if the browser stays open.
"""

import asyncio
from playwright.async_api import async_playwright
import json

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/"

async def test_session():
    """Test using saved session."""
    print(f"Loading session from {SESSION_FILE}...")
    
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)  # Visible browser
        
        print("Loading session...")
        context = await browser.new_context(
            storage_state=SESSION_FILE,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        print("Creating page...")
        page = await context.new_page()
        
        print(f"Navigating to: {TEST_URL}")
        try:
            await page.goto(TEST_URL, wait_until="networkidle", timeout=60000)
            print("✓ Page loaded!")
            
            # Wait a bit
            await page.wait_for_timeout(5000)
            
            # Get page text
            page_text = await page.inner_text('body')
            
            # Check if dealer name is visible (means we're logged in)
            if 'White Plains Honda' in page_text or len(page_text) > 1000:
                print("✓ Page content loaded! Dealer info should be visible.")
                print(f"Page text length: {len(page_text)}")
                
                # Check for dealer name
                if 'White Plains Honda' in page_text:
                    print("✓ Dealer name found in page!")
                else:
                    print("⚠ Dealer name not found - may not be logged in")
            else:
                print("⚠ Page content seems incomplete")
            
            print("\nBrowser should stay open. Press ENTER to close...")
            input()
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
            print("Browser closed.")

if __name__ == '__main__':
    asyncio.run(test_session())

