#!/usr/bin/env python3
"""Test scraper to find dealer info in HTML."""

import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/?buildId=P9WFQM823WN&paymentPreference=lease&position=1&returnTo=%2Fdashboard%2FP9WFQM823WN%2Fbest-matches%2F%3FdealType%3Dlease'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')
page_text = soup.get_text()

# Look for dealer name pattern
print("Looking for dealer name patterns...")
dealer_patterns = [
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Honda)',
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Toyota)',
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Nissan)',
]

for pattern in dealer_patterns:
    matches = re.findall(pattern, page_text)
    if matches:
        print(f"Pattern {pattern}: {matches[:5]}")

# Look for address
print("\nLooking for addresses...")
address_pattern = r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
address_matches = re.findall(address_pattern, page_text)
if address_matches:
    print(f"Found addresses: {address_matches[:3]}")

# Search for "White Plains" specifically (from user's example)
print("\nSearching for 'White Plains'...")
if 'White Plains' in page_text:
    idx = page_text.find('White Plains')
    context = page_text[max(0, idx-100):idx+200]
    print(f"Context: {context}")

# Search in HTML source directly
print("\n\nSearching HTML source...")
html_text = response.text
if 'White Plains Honda' in html_text:
    print("Found 'White Plains Honda' in HTML source!")
    idx = html_text.find('White Plains Honda')
    context = html_text[max(0, idx-200):idx+300]
    print(f"HTML context: {context[:500]}")

