#!/usr/bin/env python3
"""Very simple test - just open browser and wait."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Starting...")
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        print("Browser launched! Check if window opened.")
        print("Waiting 10 seconds...")
        await asyncio.sleep(10)
        print("Closing browser...")
        await browser.close()
        print("Done.")

if __name__ == '__main__':
    asyncio.run(main())

