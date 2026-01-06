#!/usr/bin/env python3
"""Test scraper on a single URL."""

import sys
sys.path.insert(0, '.')

from scraper import scrape_car_page
import json

url = 'https://www.truecar.com/new-cars-for-sale/listing/1HGCY1F46SA088492/2025-honda-accord/?buildId=P9WFQM823WN&paymentPreference=lease&position=1&returnTo=%2Fdashboard%2FP9WFQM823WN%2Fbest-matches%2F%3FdealType%3Dlease'

print(f"Testing scraper on: {url}")
result = scrape_car_page(url)

print("\n" + "="*80)
print("RESULT:")
print("="*80)
for key, value in result.items():
    print(f"{key}: {value}")

