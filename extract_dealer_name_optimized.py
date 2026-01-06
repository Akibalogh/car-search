#!/usr/bin/env python3
"""Optimized dealer name extraction - priority function."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import json
import re

SESSION_FILE = 'truecar_session.json'
TEST_URL = "https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F40SA088701/2025-honda-accord/"

async def extract_dealer_name_optimized(page):
    """
    Optimized dealer name extraction - tries multiple methods.
    Expected format: "Honda of New Rochelle" or "White Plains Honda" etc.
    """
    dealer_name = None
    
    # Method 1: JSON-LD structured data (most reliable)
    try:
        scripts = await page.locator('script[type="application/ld+json"]').all()
        for script in scripts:
            try:
                data = json.loads(await script.inner_text())
                # Look for seller/dealer name
                if 'seller' in data:
                    seller = data['seller']
                    if isinstance(seller, dict):
                        if 'name' in seller:
                            name = seller['name'].strip()
                            if name and len(name) > 5:
                                dealer_name = name
                                return dealer_name
                if 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, dict) and 'seller' in offers:
                        seller = offers['seller']
                        if isinstance(seller, dict) and 'name' in seller:
                            name = seller['name'].strip()
                            if name and len(name) > 5:
                                dealer_name = name
                                return dealer_name
            except:
                pass
    except:
        pass
    
    # Method 2: Extract from HTML content - look for dealer name patterns in JSON/scripts
    try:
        content = await page.content()
        
        # Pattern 1: Look for "dealershipName" or "dealerName" in JSON
        patterns = [
            r'"dealershipName"\s*:\s*"([^"]+)"',
            r'"dealerName"\s*:\s*"([^"]+)"',
            r'"sellerName"\s*:\s*"([^"]+)"',
            r'"name"\s*:\s*"([^"]+)"\s*[,\}].*?"address',
            r'"dealer"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.I)
            for match in matches:
                name = match.strip()
                # Reject generic names
                if name and len(name) > 5 and name.lower() not in ['truecar', 'dealer', 'certified dealer', 'seller']:
                    # Check if it looks like a dealer name (has location + brand pattern)
                    if re.search(r'\b(of|Honda|Toyota|Nissan|Mazda|Subaru)\b', name, re.I):
                        dealer_name = name
                        return dealer_name
        
        # Pattern 2: Look for "[Brand] of [Location]" pattern in HTML
        brand_of_location_pattern = r'\b(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
        matches = re.findall(brand_of_location_pattern, content)
        if matches:
            for brand, location in matches:
                dealer_name = f"{brand} of {location}"
                return dealer_name
        
        # Pattern 3: Look for "[Location] [Brand]" pattern
        location_brand_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\b'
        matches = re.findall(location_brand_pattern, content)
        if matches:
            # Filter out common false positives
            reject_words = ['heated', 'driver', 'seat', 'climate', 'control', 'zone', 
                          'not', 'available', 'hybrid', 'visit', 'discover', 'notes',
                          'seller', 'certified']
            for location, brand in matches:
                candidate = f"{location} {brand}"
                if not any(rw in candidate.lower() for rw in reject_words):
                    dealer_name = candidate
                    return dealer_name
                    
    except:
        pass
    
    # Method 3: Extract from page text near address/location
    try:
        page_text = await page.inner_text('body')
        
        # Find location first (e.g., "New Rochelle, NY")
        location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}),\s*[A-Z]{2}\b'
        location_match = re.search(location_pattern, page_text)
        
        if location_match:
            location = location_match.group(1)
            
            # Look for "[Brand] of [Location]" pattern near the location
            location_pos = page_text.find(location)
            if location_pos >= 0:
                # Look 200 chars before location for dealer name
                context = page_text[max(0, location_pos - 200):location_pos + 50]
                
                # Try "[Brand] of [Location]"
                brand_of_pattern = r'\b(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\s+of\s+' + re.escape(location) + r'\b'
                match = re.search(brand_of_pattern, context, re.I)
                if match:
                    dealer_name = match.group(0).title()
                    return dealer_name
                
                # Try "[Location] [Brand]" (before the location)
                location_brand_pattern = re.escape(location) + r'\s+(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\b'
                match = re.search(location_brand_pattern, context, re.I)
                if match:
                    dealer_name = f"{location} {match.group(1)}"
                    return dealer_name
    except:
        pass
    
    # Method 4: Look for address and extract dealer name near it
    try:
        page_text = await page.inner_text('body')
        address_pattern = r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
        address_match = re.search(address_pattern, page_text)
        
        if address_match:
            address = address_match.group(1)
            address_pos = page_text.find(address)
            if address_pos >= 0:
                # Look 400 chars before address
                context = page_text[max(0, address_pos - 400):address_pos]
                
                # Try "[Brand] of [Location]" pattern
                brand_of_pattern = r'\b(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
                matches = re.findall(brand_of_pattern, context, re.I)
                if matches:
                    brand, location = matches[-1]  # Use last match (closest to address)
                    dealer_name = f"{brand} of {location}"
                    return dealer_name
                
                # Try "[Location] [Brand]" pattern
                location_brand_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\b'
                matches = re.findall(location_brand_pattern, context, re.I)
                if matches:
                    reject_words = ['heated', 'driver', 'seat', 'climate', 'control', 'zone', 
                                  'not', 'available', 'hybrid', 'visit', 'discover', 'notes']
                    for location, brand in reversed(matches):
                        candidate = f"{location} {brand}"
                        if not any(rw in candidate.lower() for rw in reject_words) and ' ' in location:
                            dealer_name = candidate
                            return dealer_name
    except:
        pass
    
    return dealer_name

async def test():
    """Test the optimized extraction."""
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
            print("OPTIMIZED DEALER NAME EXTRACTION")
            print("="*80)
            print(f"URL: {TEST_URL}\n")
            print("Expected: Honda of New Rochelle\n")
            
            dealer_name = await extract_dealer_name_optimized(page)
            
            print("="*80)
            if dealer_name:
                print(f"✓ EXTRACTED: {dealer_name}")
                if dealer_name == "Honda of New Rochelle":
                    print("✓ MATCHES EXPECTED RESULT!")
                else:
                    print(f"⚠ Does not match expected 'Honda of New Rochelle'")
            else:
                print("✗ Could not extract dealer name")
            print("="*80)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test())



