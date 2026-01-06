#!/usr/bin/env python3
"""Automatically run ranking when scraped_car_data.xlsx is ready."""

import time
from pathlib import Path
import subprocess

print("="*80)
print("AUTO-RANKING: Waiting for scraped_car_data.xlsx")
print("="*80)
print()

max_wait = 900  # 15 minutes
check_interval = 15  # Check every 15 seconds
elapsed = 0

while elapsed < max_wait:
    if Path('scraped_car_data.xlsx').exists():
        print("✓ File found! Running ranking script...")
        print()
        print("="*80)
        subprocess.run(['python3', 'rank_dealers.py'])
        break
    
    # Check if scraper is still running
    result = subprocess.run(['pgrep', '-f', 'full_scraper.py'], capture_output=True)
    scraper_running = result.returncode == 0
    
    if not scraper_running and elapsed > 60:
        print("⚠ Scraper not running and file not found after 1 minute")
        print("  You may need to run: python3 full_scraper.py")
        break
    
    time.sleep(check_interval)
    elapsed += check_interval
    if elapsed % 60 == 0:  # Print every minute
        print(f"[{elapsed//60}min] Waiting for scraper to complete...")

if not Path('scraped_car_data.xlsx').exists():
    print("\n⚠ Timeout - file not created")
    print("  Run manually: python3 full_scraper.py")
    print("  Then: python3 rank_dealers.py")

