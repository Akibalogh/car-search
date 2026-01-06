#!/usr/bin/env python3
"""Test different login approaches for TrueCar."""

import asyncio
from playwright.async_api import async_playwright

async def test_login_approaches():
    """Test different ways to access TrueCar login."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # Approach 1: Navigate to car listing page directly
            print("Approach 1: Navigate to car listing page...")
            test_url = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/"
            await page.goto(test_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Look for login/sign in links
            print("Looking for login/sign in links...")
            login_links = await page.locator('a:has-text("Sign In"), a:has-text("Sign in"), a:has-text("Log In"), button:has-text("Sign In")').all()
            print(f"Found {len(login_links)} login links")
            
            for i, link in enumerate(login_links[:5]):
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    visible = await link.is_visible()
                    print(f"  Link {i}: text='{text}', href='{href}', visible={visible}")
                except:
                    pass
            
            # Check if dealer name is visible
            page_text = await page.inner_text('body')
            if 'White Plains Honda' in page_text:
                print("Dealer name 'White Plains Honda' found in page text!")
            else:
                print("Dealer name not found - might need login")
            
            # Save HTML for inspection
            html = await page.content()
            with open('test_page.html', 'w', encoding='utf-8') as f:
                f.write(html[:50000])  # First 50k chars
            print("Saved page HTML to test_page.html")
            
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_login_approaches())

