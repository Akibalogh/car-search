#!/usr/bin/env python3
"""Debug the scraper to find the error."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import re
import sys
sys.path.insert(0, '.')
from full_scraper import SESSION_FILE

async def debug_scrape():
    """Test scraping with debugging."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    # Get a URL that likely has errors
    import pandas as pd
    df = pd.read_excel('scraped_car_data.xlsx')
    error_rows = df[df['error'].notna()]
    if len(error_rows) > 0:
        test_url = error_rows.iloc[0]['url']
        print(f"Testing URL with error: {test_url[:80]}...")
    else:
        print("No errors found to debug")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel='chrome')
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            storage_state=SESSION_FILE,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("Navigating to page...")
            await page.goto(test_url, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_timeout(3000)
            
            page_text = await page.inner_text('body')
            print(f"Page text length: {len(page_text)}")
            
            # Test dealer name extraction
            print("\nTesting dealer name extraction...")
            dealer_name = None
            
            false_positives = [
                'accord', 'camry', 'altima', 'mazda3', 'impreza', 'civic', 'new', 'used', 
                'electric', 'research', 'sell', 'your', 'car', 'account', 'remote', 'engine', 
                'start', 'liftgate', 'leather', 'seats', 'navigation', 'backup', 'camera',
                'blind', 'spot', 'monitoring', 'premium', 'audio', 'system', 'parking', 'assist'
            ]
            
            dealer_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\b'
            
            print(f"Running regex pattern...")
            dealer_matches = re.findall(dealer_pattern, page_text)
            print(f"Found {len(dealer_matches)} matches")
            
            if dealer_matches:
                print(f"First few matches: {dealer_matches[:5]}")
                for i, match in enumerate(dealer_matches[:10]):
                    print(f"  Match {i+1}: {match} (type: {type(match)})")
                    try:
                        if isinstance(match, tuple):
                            name_part, brand = match
                            print(f"    Unpacked: name_part='{name_part}', brand='{brand}'")
                            candidate = f"{name_part} {brand}".strip()
                            lower_candidate = candidate.lower()
                            
                            if any(fp in lower_candidate for fp in false_positives):
                                print(f"    Skipped (false positive)")
                                continue
                            
                            if ' ' not in name_part:
                                print(f"    Skipped (no space in name_part)")
                                continue
                            
                            if 8 <= len(candidate) <= 60:
                                dealer_name = candidate
                                print(f"    ✓ Selected: {dealer_name}")
                                break
                        else:
                            print(f"    Not a tuple, skipping")
                    except Exception as e:
                        print(f"    ERROR processing match: {e}")
                        import traceback
                        traceback.print_exc()
            
            print(f"\nFinal dealer_name: {dealer_name}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_scrape())



