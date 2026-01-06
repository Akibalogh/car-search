#!/usr/bin/env python3
"""Test scraper with a small batch of URLs."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0, '.')
from full_scraper import scrape_car_page, SESSION_FILE
import re
from datetime import datetime

async def test_small_batch():
    """Test with 3 URLs."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    # Get 3 URLs from Accord.xlsx
    df = pd.read_excel('Accord.xlsx')
    urls = df['Car URL'].dropna().unique().tolist()[:3]
    
    print("="*80)
    print("TESTING SMALL BATCH (3 URLs)")
    print("="*80)
    print(f"URLs to test: {len(urls)}\n")
    
    async with async_playwright() as p:
        print("Launching browser...")
        try:
            browser = await p.chromium.launch(headless=True, channel='chrome')
            print("✓ Browser launched")
        except Exception as e:
            print(f"✗ Error launching browser: {e}")
            return
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            storage_state=SESSION_FILE,
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Testing: {url[:70]}...", flush=True)
            try:
                result = await scrape_car_page(page, url)
                results.append(result)
                
                if result.get('error'):
                    print(f"  ✗ Error: {result['error'][:60]}", flush=True)
                else:
                    dealer = result.get('dealer_name', 'N/A')[:40]
                    make = result.get('make', 'N/A')
                    model = result.get('model', 'N/A')
                    print(f"  ✓ Success - {make} {model} - Dealer: {dealer}", flush=True)
                    
            except Exception as e:
                print(f"  ✗ Exception: {str(e)[:60]}", flush=True)
                results.append({
                    'url': url,
                    'scrape_timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })
            
            # Small delay
            if i < len(urls):
                await asyncio.sleep(2)
        
        await browser.close()
        
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        success = sum(1 for r in results if not r.get('error'))
        errors = len(results) - success
        print(f"Total: {len(results)}")
        print(f"Success: {success}")
        print(f"Errors: {errors}")
        print("="*80)
        
        if success > 0:
            print("\n✓ Scraper is working! Ready to run full batch.")
        else:
            print("\n✗ All tests failed - need to investigate further")

if __name__ == '__main__':
    asyncio.run(test_small_batch())



