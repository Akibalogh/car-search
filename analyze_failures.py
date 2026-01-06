#!/usr/bin/env python3
"""Analyze failed URLs to find patterns."""
import pandas as pd
import re
from collections import Counter
from pathlib import Path

def analyze_failures():
    """Analyze failed URLs and find patterns."""
    excel_file = 'scraped_car_data.xlsx'
    
    if not Path(excel_file).exists():
        print(f"ERROR: {excel_file} not found!")
        return
    
    df = pd.read_excel(excel_file)
    errors = df[df['error'].notna()].copy()
    success = df[df['error'].isna()].copy()
    
    print("="*80)
    print("FAILED URL PATTERN ANALYSIS")
    print("="*80)
    
    print(f"\n1. OVERALL STATISTICS")
    print(f"   Total records: {len(df)}")
    print(f"   Failed: {len(errors)} ({len(errors)/len(df)*100:.1f}%)")
    print(f"   Success: {len(success)} ({len(success)/len(df)*100:.1f}%)")
    
    print(f"\n2. ERROR TYPES")
    error_counts = errors['error'].value_counts()
    for err, count in error_counts.head(10).items():
        print(f"   {err[:60]}: {count}")
    
    print(f"\n3. FAILED URL EXAMPLES (first 20)")
    for i, (_, row) in enumerate(errors.head(20).iterrows(), 1):
        print(f"   {i:2d}. {row['url']}")
        print(f"       Error: {str(row['error'])[:60]}")
    
    print(f"\n4. URL PATTERN ANALYSIS")
    
    def extract_patterns(url):
        """Extract patterns from URL."""
        patterns = {}
        
        # Category
        if 'used-cars' in url:
            patterns['category'] = 'used-cars'
        elif 'new-cars' in url:
            patterns['category'] = 'new-cars'
        else:
            patterns['category'] = 'unknown'
        
        # Make
        makes = ['honda', 'toyota', 'nissan', 'mazda', 'subaru', 'ford', 'chevrolet', 
                 'hyundai', 'kia', 'bmw', 'mercedes', 'audi', 'lexus', 'acura']
        for make in makes:
            if make in url.lower():
                patterns['make'] = make
                break
        else:
            patterns['make'] = 'unknown'
        
        # VIN pattern
        vin_match = re.search(r'/listing/([A-Z0-9]{17})/', url)
        if vin_match:
            patterns['has_vin'] = True
            vin = vin_match.group(1)
            # Check VIN characteristics
            patterns['vin_starts_with'] = vin[0] if len(vin) > 0 else 'unknown'
        else:
            patterns['has_vin'] = False
            patterns['vin_starts_with'] = 'none'
        
        # Year in URL
        year_match = re.search(r'/(\d{4})-', url)
        patterns['year'] = year_match.group(1) if year_match else 'unknown'
        
        return patterns
    
    error_patterns = [extract_patterns(url) for url in errors['url'].head(100)]
    success_patterns = [extract_patterns(url) for url in success['url'].head(100)]
    
    print(f"\n   Failed URLs - Category breakdown:")
    err_cats = Counter(p['category'] for p in error_patterns)
    for cat, count in err_cats.most_common():
        print(f"      {cat}: {count}")
    
    print(f"\n   Failed URLs - Make breakdown:")
    err_makes = Counter(p['make'] for p in error_patterns)
    for make, count in err_makes.most_common(10):
        print(f"      {make}: {count}")
    
    print(f"\n   Success URLs - Category breakdown:")
    succ_cats = Counter(p['category'] for p in success_patterns)
    for cat, count in succ_cats.most_common():
        print(f"      {cat}: {count}")
    
    print(f"\n   Success URLs - Make breakdown:")
    succ_makes = Counter(p['make'] for p in success_patterns)
    for make, count in succ_makes.most_common(10):
        print(f"      {make}: {count}")
    
    print(f"\n5. COMPARISON")
    print(f"\n   Failed vs Success ratios by category:")
    for cat in ['used-cars', 'new-cars']:
        err_count = err_cats.get(cat, 0)
        succ_count = succ_cats.get(cat, 0)
        total = err_count + succ_count
        if total > 0:
            err_rate = err_count / total * 100
            print(f"      {cat}: {err_count} failed, {succ_count} success ({err_rate:.1f}% failure rate)")
    
    print(f"\n6. SPECIFIC FAILED URL SAMPLES BY ERROR TYPE")
    common_error = error_counts.index[0]
    print(f"\n   Error: {common_error}")
    sample_urls = errors[errors['error'] == common_error]['url'].head(10).tolist()
    for i, url in enumerate(sample_urls, 1):
        print(f"      {i}. {url}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    analyze_failures()



