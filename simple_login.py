#!/usr/bin/env python3
"""
Simplified login script - run this in your terminal directly.
"""

import asyncio
from playwright.async_api import async_playwright
import json
import sys

SESSION_FILE = 'truecar_session.json'

async def main():
    print("="*80)
    print("MANUAL LOGIN SETUP")
    print("="*80)
    print("A browser window will open.")
    print("Steps:")
    print("1. Log in to TrueCar in the browser window")
    print("2. Once logged in, come back here and press ENTER")
    print("3. Your session will be saved")
    print("="*80)
    print()
    
    browser = None
    context = None
    
    async with async_playwright() as p:
        try:
            print("Initializing Playwright...")
            print("Launching browser...")
            try:
                # Try Chrome first
                browser = await p.chromium.launch(
                    headless=False,
                    channel='chrome'
                )
                print("✓ Browser launched (using system Chrome)")
            except Exception as e:
                print(f"Note: Could not use system Chrome, trying bundled Chromium...")
                # Fallback to bundled Chromium
                browser = await p.chromium.launch(headless=False)
                print("✓ Browser launched (using bundled Chromium)")
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("✓ Context created")
            
            page = await context.new_page()
            print("✓ Page created")
            
            print("Navigating to TrueCar...")
            try:
                await page.goto("https://www.truecar.com", wait_until="domcontentloaded", timeout=30000)
                print("✓ Page loaded")
            except Exception as e:
                print(f"Warning during navigation: {e}")
            
            # Add a delay to ensure page is fully loaded
            await asyncio.sleep(3)
            
            print("\n" + "="*80)
            print("✓ Browser is open and ready!")
            print("Please log in to TrueCar in the browser window.")
            print("The browser will stay open until you press ENTER.")
            print("="*80 + "\n")
            
            # CRITICAL: Keep browser reference alive and don't exit async context
            # until user presses ENTER
            print("Waiting for you to log in and press ENTER...")
            print("(The browser will stay open - take your time!)")
            print("\nPress ENTER after you've logged in to TrueCar: ", end='', flush=True)
            
            # This blocking call keeps the script running and browser open
            try:
                user_input = input()
                print(f"\nGot input - saving session...")
            except (EOFError, KeyboardInterrupt):
                print("\n\nCancelled by user.")
                if browser:
                    await browser.close()
                return
            
            # Save session
            print("Saving session...")
            try:
                storage_state = await context.storage_state()
                with open(SESSION_FILE, 'w') as f:
                    json.dump(storage_state, f)
                print(f"✓ Session saved to {SESSION_FILE}\n")
            except Exception as e:
                print(f"Error saving session: {e}")
                import traceback
                traceback.print_exc()
            
            # Close browser
            if browser:
                print("Closing browser...")
                await browser.close()
                print("Done!")
                
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            if browser:
                try:
                    await browser.close()
                except:
                    pass

if __name__ == '__main__':
    asyncio.run(main())

