#!/usr/bin/env python3
"""Check scraper progress and show failure patterns."""
import json
import pandas as pd
from pathlib import Path
from collections import Counter
import re

def check_progress():
    """Check scraper progress from checkpoint or output file."""
    checkpoint_file = 'scraping_checkpoint.json'
    output_file = 'scraped_car_data.xlsx'
    
    # Check if output file exists
    if Path(output_file).exists():
        print("="*80)
        print("ANALYZING COMPLETED SCRAPE - FAILURE PATTERNS")
        print("="*80)
        
        df = pd.read_excel(output_file)
        errors = df[df['error'].notna()].copy()
        success = df[df['error'].isna()].copy()
        
        print(f"\nTotal records: {len(df)}")
        print(f"Success: {len(success)} ({len(success)/len(df)*100:.1f}%)")
        print(f"Failed: {len(errors)} ({len(errors)/len(df)*100:.1f}%)")
        
        print(f"\n{'='*80}")
        print("ERROR BREAKDOWN")
        print(f"{'='*80}")
        error_counts = errors['error'].value_counts()
        for err, count in error_counts.head(10).items():
            print(f"\n{err[:70]}: {count} occurrences")
        
        print(f"\n{'='*80}")
        print("FAILED URL EXAMPLES (first 20)")
        print(f"{'='*80}")
        for i, (_, row) in enumerate(errors.head(20).iterrows(), 1):
            print(f"\n{i:2d}. {row['url']}")
            print(f"     Error: {str(row['error'])[:70]}")
            if 'source_file' in row and pd.notna(row['source_file']):
                print(f"     Source: {row['source_file']}")
        
        print(f"\n{'='*80}")
        print("PATTERN ANALYSIS")
        print(f"{'='*80}")
        
        # Analyze patterns in failed URLs
        def analyze_url(url):
            patterns = {}
            url_str = str(url).lower()
            
            # Make
            makes = ['honda', 'toyota', 'nissan', 'mazda', 'subaru']
            for make in makes:
                if make in url_str:
                    patterns['make'] = make
                    break
            
            # Year
            year_match = re.search(r'/(\d{4})-', url_str)
            patterns['year'] = year_match.group(1) if year_match else 'unknown'
            
            # Has query params
            patterns['has_query'] = '?' in url and 'buildId' in url
            
            return patterns
        
        err_patterns = [analyze_url(u) for u in errors['url'].head(100)]
        succ_patterns = [analyze_url(u) for u in success['url'].head(100)]
        
        print(f"\nFailed URLs - Make breakdown (sample of 100):")
        err_makes = Counter(p.get('make', 'unknown') for p in err_patterns)
        for make, count in err_makes.most_common():
            print(f"   {make}: {count}")
        
        print(f"\nFailed URLs - Year breakdown (sample of 100):")
        err_years = Counter(p.get('year', 'unknown') for p in err_patterns)
        for year, count in err_years.most_common():
            print(f"   {year}: {count}")
        
        print(f"\nSuccess URLs - Make breakdown (sample of 100):")
        succ_makes = Counter(p.get('make', 'unknown') for p in succ_patterns)
        for make, count in succ_makes.most_common():
            print(f"   {make}: {count}")
        
        print(f"\nSuccess URLs - Year breakdown (sample of 100):")
        succ_years = Counter(p.get('year', 'unknown') for p in succ_patterns)
        for year, count in succ_years.most_common():
            print(f"   {year}: {count}")
        
        # Compare failure rates by make
        print(f"\n{'='*80}")
        print("FAILURE RATE BY MAKE (sample)")
        print(f"{'='*80}")
        all_makes = set(err_makes.keys()) | set(succ_makes.keys())
        for make in sorted(all_makes):
            err_count = err_makes.get(make, 0)
            succ_count = succ_makes.get(make, 0)
            total = err_count + succ_count
            if total > 0:
                rate = err_count / total * 100
                print(f"   {make}: {err_count}/{total} failed ({rate:.1f}%)")
        
    elif Path(checkpoint_file).exists():
        print("="*80)
        print("CHECKING PROGRESS FROM CHECKPOINT")
        print("="*80)
        
        with open(checkpoint_file, 'r') as f:
            cp = json.load(f)
        
        results = cp.get('results', [])
        errors = [r for r in results if r.get('error')]
        success = [r for r in results if not r.get('error')]
        
        print(f"\nProcessed: {len(results)} URLs")
        print(f"Success: {len(success)}")
        print(f"Failed: {len(errors)}")
        
        if errors:
            print(f"\nError types:")
            err_types = Counter(str(e.get('error', ''))[:50] for e in errors)
            for err, count in err_types.most_common(5):
                print(f"   {err}: {count}")
            
            print(f"\nSample failed URLs (first 10):")
            for i, err in enumerate(errors[:10], 1):
                print(f"   {i}. {err.get('url', 'N/A')}")
                print(f"      Error: {str(err.get('error', ''))[:60]}")
    else:
        print("No checkpoint or output file found. Scraper may not have started yet.")

if __name__ == '__main__':
    check_progress()



