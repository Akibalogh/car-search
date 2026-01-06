#!/usr/bin/env python3
"""Quick test of the scraper on a single URL."""

import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/?buildId=P9WFQM823WN&paymentPreference=lease&position=1&returnTo=%2Fdashboard%2FP9WFQM823WN%2Fbest-matches%2F%3FdealType%3Dlease'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Status code: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    page_text = soup.get_text()
    
    print(f"\nPage text length: {len(page_text)}")
    print(f"\nFirst 1000 chars:")
    print(page_text[:1000])
    
    # Try to find dealer name
    print("\n\nLooking for dealer name...")
    # Look for address pattern first
    address_pattern = r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
    match = re.search(address_pattern, page_text)
    if match:
        address = match.group(1)
        print(f"Found address: {address}")
        idx = match.start()
        preceding = page_text[max(0, idx-300):idx]
        print(f"\nText before address (last 300 chars):")
        print(preceding)
    
    # Check if page is JavaScript-rendered
    if 'truecar' not in page_text.lower()[:500]:
        print("\n\nWARNING: Page might be JavaScript-rendered. Content not found in initial HTML.")
        print("May need to use Selenium or Playwright instead of requests.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

