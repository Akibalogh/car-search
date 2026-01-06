#!/usr/bin/env python3
"""Test using system Chrome instead of bundled Chromium."""

import asyncio
from playwright.async_api import async_playwright

async def test_system_chrome():
    """Test if system Chrome works better than bundled Chromium."""
    print("Testing system Chrome...")
    
    try:
        async with async_playwright() as p:
            print("Launching system Chrome...")
            browser = await p.chromium.launch(
                headless=True,  # Headless for testing
                channel='chrome'  # Use system Chrome
            )
            print("✓ System Chrome launched!")
            
            context = await browser.new_context()
            print("✓ Context created!")
            
            page = await context.new_page()
            print("✓ Page created!")
            
            print("Navigating to Google...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            title = await page.title()
            print(f"✓ Page loaded! Title: {title}")
            
            await browser.close()
            print("✓ Test PASSED - System Chrome works!")
            return True
            
    except Exception as e:
        print(f"✗ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_headless_chromium():
    """Test headless bundled Chromium."""
    print("\nTesting headless bundled Chromium...")
    
    try:
        async with async_playwright() as p:
            print("Launching headless Chromium...")
            browser = await p.chromium.launch(headless=True)
            print("✓ Headless Chromium launched!")
            
            context = await browser.new_context()
            print("✓ Context created!")
            
            page = await context.new_page()
            print("✓ Page created!")
            
            print("Navigating to Google...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            title = await page.title()
            print(f"✓ Page loaded! Title: {title}")
            
            await browser.close()
            print("✓ Test PASSED - Headless Chromium works!")
            return True
            
    except Exception as e:
        print(f"✗ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run tests."""
    print("="*80)
    print("BROWSER STABILITY TESTS")
    print("="*80)
    
    result1 = await test_system_chrome()
    result2 = await test_headless_chromium()
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"System Chrome: {'✓ PASS' if result1 else '✗ FAIL'}")
    print(f"Headless Chromium: {'✓ PASS' if result2 else '✗ FAIL'}")
    
    if result1:
        print("\n✓ System Chrome works! Use channel='chrome' in scraper")
    elif result2:
        print("\n✓ Headless Chromium works! Use headless=True in scraper")
    else:
        print("\n✗ Both failed. Recommend using cloud service (Google Colab)")

if __name__ == '__main__':
    asyncio.run(main())

