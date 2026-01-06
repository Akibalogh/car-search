#!/usr/bin/env python3
"""Monitor scraper progress."""

from pathlib import Path
import json
import time
import subprocess

CHECKPOINT_FILE = 'scraping_checkpoint.json'
OUTPUT_FILE = 'scraped_car_data.xlsx'
TOTAL_URLS = 417

def check_process():
    """Check if scraper process is running."""
    try:
        result = subprocess.run(['pgrep', '-f', 'full_scraper.py'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip().split('\n')) > 0
    except:
        return False

def check_progress():
    """Check scraper progress."""
    print("="*60)
    print("SCRAPER MONITOR")
    print("="*60)
    
    # Check if process is running
    is_running = check_process()
    print(f"Process running: {'✓ YES' if is_running else '✗ NO'}")
    
    # Check checkpoint file
    checkpoint = Path(CHECKPOINT_FILE)
    if checkpoint.exists():
        try:
            with open(checkpoint, 'r') as f:
                data = json.load(f)
            
            processed = len(data.get('processed_urls', []))
            results = len(data.get('results', []))
            timestamp = data.get('timestamp', 'unknown')
            
            print(f"\nCheckpoint file exists: ✓")
            print(f"URLs processed: {processed}/{TOTAL_URLS} ({(processed/TOTAL_URLS*100):.1f}%)")
            print(f"Results collected: {results}")
            print(f"Last update: {timestamp}")
            
            # Count errors
            errors = sum(1 for r in data.get('results', []) if r.get('error'))
            if errors > 0:
                print(f"Errors: {errors}")
        except Exception as e:
            print(f"Error reading checkpoint: {e}")
    else:
        print(f"\nCheckpoint file: Not created yet (checkpoint saved every 10 URLs)")
    
    # Check output file
    output = Path(OUTPUT_FILE)
    if output.exists():
        size = output.stat().st_size
        print(f"\nOutput file exists: ✓ ({size:,} bytes)")
    else:
        print(f"\nOutput file: Not created yet (will be created when complete)")
    
    print("="*60)

if __name__ == '__main__':
    check_progress()

