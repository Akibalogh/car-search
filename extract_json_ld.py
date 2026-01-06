#!/usr/bin/env python3
"""Extract JSON-LD structured data from TrueCar page."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import json

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F43SA088174/2025-honda-accord/"

async def extract_json_ld():
    """Extract and parse JSON-LD structured data."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, channel='chrome')
        except:
            browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(storage_state=SESSION_FILE)
        page = await context.new_page()
        
        try:
            await page.goto(TEST_URL, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_timeout(4000)
            
            print("="*80)
            print("JSON-LD STRUCTURED DATA EXTRACTION")
            print("="*80)
            
            # Extract JSON-LD scripts
            scripts = await page.locator('script[type="application/ld+json"]').all()
            print(f"\nFound {len(scripts)} JSON-LD scripts\n")
            
            all_data = []
            for i, script in enumerate(scripts):
                try:
                    content = await script.inner_text()
                    data = json.loads(content)
                    all_data.append(data)
                    
                    print(f"Script {i+1}:")
                    print(f"  Type: {data.get('@type', 'unknown')}")
                    if 'name' in data:
                        print(f"  Name: {data.get('name')}")
                    if 'offers' in data:
                        print(f"  Has offers: Yes")
                    print(f"  Keys: {list(data.keys())[:10]}")
                    print()
                except Exception as e:
                    print(f"Script {i+1}: Error parsing - {e}\n")
            
            # Look for dealer/seller info
            print("="*80)
            print("DEALER/SELLER INFORMATION IN JSON-LD:")
            print("="*80)
            for i, data in enumerate(all_data):
                print(f"\nScript {i+1}:")
                # Print full structure (pretty)
                print(json.dumps(data, indent=2)[:1000])  # First 1000 chars
                print("...")
            
            # Also check page HTML for data attributes
            print("\n" + "="*80)
            print("HTML DATA ATTRIBUTES:")
            print("="*80)
            
            # Look for elements with data-testid containing dealer/price/etc
            test_ids = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('[data-testid]');
                    const testIds = new Set();
                    elements.forEach(el => {
                        const id = el.getAttribute('data-testid');
                        if (id && (id.includes('dealer') || id.includes('price') || id.includes('address') || id.includes('vin'))) {
                            testIds.add(id);
                        }
                    });
                    return Array.from(testIds);
                }
            """)
            
            if test_ids:
                print(f"\nFound {len(test_ids)} relevant data-testid attributes:")
                for tid in sorted(test_ids)[:20]:
                    print(f"  - {tid}")
            else:
                print("\nNo relevant data-testid attributes found")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(extract_json_ld())



