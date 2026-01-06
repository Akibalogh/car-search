#!/usr/bin/env python3
"""Simple test to verify Playwright browser can open."""

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    print("Testing browser launch...")
    async with async_playwright() as p:
        try:
            print("Launching Chromium...")
            browser = await p.chromium.launch(headless=False)
            print("Browser launched successfully!")
            context = await browser.new_context()
            page = await context.new_page()
            
            print("Navigating to Google...")
            await page.goto("https://www.google.com")
            print(f"Page title: {await page.title()}")
            print("Browser is open! You should see it.")
            
            input("\nPress ENTER to close the browser...")
            await browser.close()
            print("Browser closed.")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_browser())

