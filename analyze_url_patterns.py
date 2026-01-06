#!/usr/bin/env python3
"""Analyze URL patterns from input Excel files."""
import pandas as pd
import re
from collections import Counter
from pathlib import Path

def analyze_input_urls():
    """Analyze URLs from input Excel files to find patterns."""
    excel_files = ['Accord.xlsx', 'Altima.xlsx', 'Camry.xlsx', 'impreza.xlsx', 'Mazda3.xlsx']
    
    all_urls = []
    url_by_file = {}
    
    print("="*80)
    print("INPUT URL PATTERN ANALYSIS")
    print("="*80)
    
    for excel_file in excel_files:
        file_path = Path(excel_file)
        if not file_path.exists():
            print(f"\n⚠ {excel_file} not found, skipping...")
            continue
        
        try:
            df = pd.read_excel(excel_file)
            if 'Car URL' not in df.columns:
                print(f"\n⚠ 'Car URL' column not found in {excel_file}, skipping...")
                continue
            
            urls = df['Car URL'].dropna().unique().tolist()
            url_by_file[excel_file] = urls
            all_urls.extend(urls)
            print(f"\n✓ {excel_file}: {len(urls)} URLs")
            
        except Exception as e:
            print(f"\n✗ Error processing {excel_file}: {e}")
            continue
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {len(all_urls)} URLs from {len(url_by_file)} files")
    print(f"{'='*80}")
    
    print(f"\n1. URL STRUCTURE BREAKDOWN")
    
    # Category (used-cars vs new-cars)
    categories = Counter()
    makes = Counter()
    has_listing = Counter()
    year_patterns = Counter()
    
    for url in all_urls:
        url_str = str(url).lower()
        
        # Category
        if 'used-cars' in url_str:
            categories['used-cars'] += 1
        elif 'new-cars' in url_str:
            categories['new-cars'] += 1
        else:
            categories['unknown'] += 1
        
        # Make
        car_makes = ['honda', 'toyota', 'nissan', 'mazda', 'subaru']
        for make in car_makes:
            if make in url_str:
                makes[make] += 1
                break
        
        # Listing pattern
        if '/listing/' in url_str:
            has_listing['has_listing'] += 1
        else:
            has_listing['no_listing'] += 1
        
        # Year pattern
        year_match = re.search(r'/(\d{4})-', url_str)
        if year_match:
            year = year_match.group(1)
            year_patterns[year] += 1
    
    print(f"\n   Categories:")
    for cat, count in categories.most_common():
        print(f"      {cat}: {count} ({count/len(all_urls)*100:.1f}%)")
    
    print(f"\n   Makes:")
    for make, count in makes.most_common():
        print(f"      {make}: {count} ({count/len(all_urls)*100:.1f}%)")
    
    print(f"\n   Listing pattern:")
    for pattern, count in has_listing.most_common():
        print(f"      {pattern}: {count}")
    
    print(f"\n   Years (top 10):")
    for year, count in year_patterns.most_common(10):
        print(f"      {year}: {count}")
    
    print(f"\n2. SAMPLE URLS FROM EACH FILE")
    for excel_file, urls in url_by_file.items():
        print(f"\n   {excel_file} (first 5 URLs):")
        for i, url in enumerate(urls[:5], 1):
            print(f"      {i}. {url}")
    
    print(f"\n3. URL VARIATIONS")
    # Check for different URL formats
    url_formats = Counter()
    for url in all_urls[:100]:  # Sample first 100
        url_str = str(url)
        if '/for-sale/listing/' in url_str:
            url_formats['for-sale/listing'] += 1
        elif '/listing/' in url_str:
            url_formats['listing_only'] += 1
        else:
            url_formats['other'] += 1
    
    print(f"\n   URL format patterns (sample of 100):")
    for fmt, count in url_formats.most_common():
        print(f"      {fmt}: {count}")
    
    print(f"\n{'='*80}\n")
    
    return all_urls

if __name__ == '__main__':
    analyze_input_urls()



