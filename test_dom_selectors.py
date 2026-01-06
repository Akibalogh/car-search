#!/usr/bin/env python3
"""Test DOM selectors on a TrueCar page to find standard structure."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import json

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F43SA088174/2025-honda-accord/"

async def test_selectors():
    """Test various DOM selectors to find standard structure."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        return
    
    print("Testing DOM selectors on TrueCar page...")
    print(f"URL: {TEST_URL}\n")
    
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
            print("DOM SELECTOR TESTING")
            print("="*80)
            
            # Try common selector patterns
            selectors_to_test = {
                'dealer_name': [
                    'h1',
                    'h2',
                    '[data-testid*="dealer"]',
                    '[class*="dealer" i]',
                    '[data-qa*="dealer"]',
                    'header h1',
                    'header h2',
                    '.dealer-name',
                    '[itemprop="name"]',
                ],
                'address': [
                    'address',
                    '[itemprop="address"]',
                    '[data-testid*="address"]',
                    '[class*="address" i]',
                    '.address',
                ],
                'price': [
                    '[data-testid*="price"]',
                    '[class*="price" i]',
                    '[data-qa*="price"]',
                    '.price',
                    '[data-testid*="lease"]',
                ],
                'vin': [
                    '[data-testid*="vin"]',
                    '[class*="vin" i]',
                    'code',
                    'pre',
                ],
            }
            
            results = {}
            
            for field, selectors in selectors_to_test.items():
                print(f"\n{field.upper()}:")
                results[field] = []
                
                for selector in selectors:
                    try:
                        elements = await page.locator(selector).all()
                        if elements:
                            for elem in elements[:3]:  # Test first 3
                                try:
                                    text = await elem.inner_text()
                                    if text and len(text.strip()) < 200:
                                        results[field].append({
                                            'selector': selector,
                                            'text': text.strip()[:100]
                                        })
                                        print(f"  ✓ {selector}: {text.strip()[:80]}")
                                        break  # Use first match
                                except:
                                    pass
                    except Exception as e:
                        pass
            
            # Also try to find structured data (JSON-LD, microdata)
            print("\nSTRUCTURED DATA:")
            try:
                # Look for JSON-LD
                json_ld = await page.locator('script[type="application/ld+json"]').all()
                if json_ld:
                    print(f"  Found {len(json_ld)} JSON-LD scripts")
                    for script in json_ld[:2]:
                        try:
                            content = await script.inner_text()
                            print(f"    Length: {len(content)} chars")
                        except:
                            pass
            except:
                pass
            
            # Get HTML sample around dealer info
            print("\nHTML STRUCTURE SAMPLE:")
            try:
                # Try to find dealer section by looking for address pattern
                html = await page.content()
                # Look for address pattern in HTML
                import re
                addr_match = re.search(r'(\d+\s+[A-Za-z\s]+(?:Avenue|Ave|Street|St|Road|Rd)[^<]{0,200})', html, re.I)
                if addr_match:
                    context_html = html[max(0, addr_match.start()-500):addr_match.end()+500]
                    # Extract surrounding HTML tags
                    tags = re.findall(r'<[^>]+>', context_html)
                    print(f"  HTML tags around address (sample): {tags[:10]}")
            except Exception as e:
                print(f"  Error: {e}")
            
            print("\n" + "="*80)
            print("RECOMMENDED SELECTORS:")
            print("="*80)
            for field, matches in results.items():
                if matches:
                    print(f"\n{field}: {matches[0]['selector']}")
                    print(f"  Sample: {matches[0]['text'][:60]}")
                else:
                    print(f"\n{field}: No reliable selector found (fallback to regex)")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_selectors())



