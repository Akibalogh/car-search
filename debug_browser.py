#!/usr/bin/env python3
"""
Debug script to figure out why browser closes immediately.
Tests different approaches.
"""

import asyncio
from playwright.async_api import async_playwright
import sys

async def test_1_basic_launch():
    """Test 1: Basic browser launch without context."""
    print("\n" + "="*80)
    print("TEST 1: Basic browser launch")
    print("="*80)
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            print("✓ Browser launched!")
            print("Waiting 5 seconds...")
            await asyncio.sleep(5)
            print("Closing browser...")
            await browser.close()
            print("✓ Test 1 PASSED - Browser stayed open!")
            return True
    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_2_with_context():
    """Test 2: Browser with context."""
    print("\n" + "="*80)
    print("TEST 2: Browser with context")
    print("="*80)
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            print("✓ Browser launched!")
            print("Creating context...")
            context = await browser.new_context()
            print("✓ Context created!")
            print("Creating page...")
            page = await context.new_page()
            print("✓ Page created!")
            print("Waiting 5 seconds...")
            await asyncio.sleep(5)
            print("Closing...")
            await browser.close()
            print("✓ Test 2 PASSED - Browser stayed open!")
            return True
    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_3_navigate():
    """Test 3: Navigate to a page."""
    print("\n" + "="*80)
    print("TEST 3: Navigate to page")
    print("="*80)
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            print("✓ Browser launched!")
            context = await browser.new_context()
            page = await context.new_page()
            print("Navigating to Google...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            print("✓ Page loaded!")
            print("Waiting 5 seconds...")
            await asyncio.sleep(5)
            print("Closing...")
            await browser.close()
            print("✓ Test 3 PASSED - Browser stayed open!")
            return True
    except Exception as e:
        print(f"✗ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_4_with_session():
    """Test 4: Load session file."""
    print("\n" + "="*80)
    print("TEST 4: Load session file")
    print("="*80)
    try:
        from pathlib import Path
        session_file = 'truecar_session.json'
        if not Path(session_file).exists():
            print(f"⚠ Session file {session_file} not found, skipping test")
            return None
        
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            print("✓ Browser launched!")
            print("Creating context with session...")
            context = await browser.new_context(storage_state=session_file)
            print("✓ Context created with session!")
            page = await context.new_page()
            print("Navigating to TrueCar...")
            await page.goto("https://www.truecar.com", wait_until="domcontentloaded")
            print("✓ Page loaded!")
            print("Waiting 5 seconds...")
            await asyncio.sleep(5)
            print("Closing...")
            await browser.close()
            print("✓ Test 4 PASSED - Browser stayed open!")
            return True
    except Exception as e:
        print(f"✗ Test 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_5_input_blocking():
    """Test 5: Use input() to block and keep browser open."""
    print("\n" + "="*80)
    print("TEST 5: Block with input()")
    print("="*80)
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            print("✓ Browser launched!")
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.google.com")
            print("✓ Page loaded!")
            print("Browser should stay open. Press ENTER to close...")
            
            # This blocking call should keep browser open
            input()
            
            await browser.close()
            print("✓ Test 5 PASSED - Browser stayed open with input()!")
            return True
    except Exception as e:
        print(f"✗ Test 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_6_headless():
    """Test 6: Try headless mode."""
    print("\n" + "="*80)
    print("TEST 6: Headless mode")
    print("="*80)
    try:
        async with async_playwright() as p:
            print("Launching browser (headless)...")
            browser = await p.chromium.launch(headless=True)
            print("✓ Browser launched!")
            context = await browser.new_context()
            page = await context.new_page()
            print("Navigating to Google...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            title = await page.title()
            print(f"✓ Page loaded! Title: {title}")
            await browser.close()
            print("✓ Test 6 PASSED - Headless mode works!")
            return True
    except Exception as e:
        print(f"✗ Test 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("="*80)
    print("BROWSER DEBUGGING TESTS")
    print("="*80)
    print("Running diagnostic tests to find the browser closing issue...\n")
    
    tests = [
        ("Basic Launch", test_1_basic_launch),
        ("With Context", test_2_with_context),
        ("Navigate", test_3_navigate),
        ("With Session", test_4_with_session),
        ("Input Blocking", test_5_input_blocking),
        ("Headless", test_6_headless),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            result = await test_func()
            results[name] = result
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL" if result is False else "⚠ SKIP"
        print(f"{name:20} {status}")
    
    print("\n" + "="*80)
    if all(r for r in results.values() if r is not None):
        print("All tests passed! Browser automation should work.")
    else:
        print("Some tests failed. Check output above for details.")

if __name__ == '__main__':
    asyncio.run(main())

