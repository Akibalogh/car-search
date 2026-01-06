#!/usr/bin/env python3
"""Test dealer name extraction using multiple methods."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import json
import re

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F43SA088174/2025-honda-accord/"

async def test_dealer_extraction():
    """Test multiple methods to extract dealer name."""
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
            print("DEALER NAME EXTRACTION TEST")
            print("="*80)
            print(f"URL: {TEST_URL}\n")
            
            dealer_name = None
            methods_tried = []
            
            # Method 1: JSON-LD structured data
            print("Method 1: JSON-LD Structured Data")
            try:
                scripts = await page.locator('script[type="application/ld+json"]').all()
                for script in scripts:
                    try:
                        data = json.loads(await script.inner_text())
                        # Look for seller/dealer info in JSON-LD
                        if 'seller' in data:
                            seller = data['seller']
                            if isinstance(seller, dict) and 'name' in seller:
                                dealer_name = seller['name']
                                methods_tried.append(f"JSON-LD seller.name: {dealer_name}")
                                print(f"  ✓ Found: {dealer_name}")
                                break
                        if 'offers' in data and isinstance(data['offers'], dict):
                            if 'seller' in data['offers']:
                                seller = data['offers']['seller']
                                if isinstance(seller, dict) and 'name' in seller:
                                    dealer_name = seller['name']
                                    methods_tried.append(f"JSON-LD offers.seller.name: {dealer_name}")
                                    print(f"  ✓ Found: {dealer_name}")
                                    break
                    except:
                        pass
            except Exception as e:
                print(f"  ✗ Error: {e}")
            
            # Method 2: DOM selectors - look for dealer name in HTML structure
            if not dealer_name:
                print("\nMethod 2: DOM Selectors")
                dealer_selectors = [
                    'h1',
                    'h2',
                    '[data-testid*="dealer"]',
                    '[class*="dealer-name" i]',
                    '[class*="seller-name" i]',
                    '[itemprop="name"]',
                ]
                
                for selector in dealer_selectors:
                    try:
                        elements = await page.locator(selector).all()
                        for elem in elements[:5]:  # Check first 5 matches
                            try:
                                text = await elem.inner_text()
                                text = text.strip()
                                # Check if it looks like a dealer name (location + brand)
                                if text and 8 <= len(text) <= 80:
                                    # Pattern: Location Name + Brand
                                    dealer_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\b', text)
                                    if dealer_match:
                                        name_part, brand = dealer_match.groups()
                                        candidate = f"{name_part} {brand}"
                                        # Reject feature words
                                        reject_words = ['heated', 'driver', 'seat', 'climate', 'control', 'zone', 'not', 'available', 'hybrid']
                                        if not any(rw in candidate.lower() for rw in reject_words):
                                            dealer_name = candidate
                                            methods_tried.append(f"DOM selector {selector}: {dealer_name}")
                                            print(f"  ✓ Found with {selector}: {dealer_name}")
                                            break
                            except:
                                pass
                        if dealer_name:
                            break
                    except:
                        pass
            
            # Method 3: Look near address element
            if not dealer_name:
                print("\nMethod 3: Extract near Address")
                try:
                    # Find address first
                    page_text = await page.inner_text('body')
                    address_pattern = r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
                    address_match = re.search(address_pattern, page_text)
                    
                    if address_match:
                        address = address_match.group(1)
                        address_pos = page_text.find(address)
                        if address_pos >= 0:
                            # Look 300 chars before address
                            context = page_text[max(0, address_pos - 300):address_pos]
                            dealer_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\b'
                            matches = re.findall(dealer_pattern, context)
                            if matches:
                                for match in reversed(matches):
                                    name_part, brand = match
                                    candidate = f"{name_part} {brand}"
                                    reject_words = ['heated', 'driver', 'seat', 'climate', 'control', 'zone', 'not', 'available', 'hybrid']
                                    if not any(rw in candidate.lower() for rw in reject_words) and ' ' in name_part:
                                        dealer_name = candidate
                                        methods_tried.append(f"Near address: {dealer_name}")
                                        print(f"  ✓ Found: {dealer_name}")
                                        break
                except Exception as e:
                    print(f"  ✗ Error: {e}")
            
            # Method 4: Try to find dealer section in HTML
            if not dealer_name:
                print("\nMethod 4: HTML Structure Analysis")
                try:
                    html = await page.content()
                    # Look for dealer info in HTML comments or specific sections
                    # Try to find structured data in script tags
                    script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
                    for script_content in script_matches:
                        # Look for dealer name in JSON-like structures
                        dealer_json_match = re.search(r'["\'](?:dealer|seller)Name["\']\s*:\s*["\']([^"\']+)["\']', script_content, re.I)
                        if dealer_json_match:
                            candidate = dealer_json_match.group(1).strip()
                            if 8 <= len(candidate) <= 80:
                                dealer_name = candidate
                                methods_tried.append(f"HTML script JSON: {dealer_name}")
                                print(f"  ✓ Found: {dealer_name}")
                                break
                except Exception as e:
                    print(f"  ✗ Error: {e}")
            
            print("\n" + "="*80)
            print("RESULT")
            print("="*80)
            if dealer_name:
                print(f"✓ Dealer Name: {dealer_name}")
                print(f"\nMethod that worked: {methods_tried[-1] if methods_tried else 'Unknown'}")
            else:
                print("✗ Could not extract dealer name")
                print("\nAll methods tried:")
                for method in methods_tried:
                    print(f"  - {method}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_dealer_extraction())



