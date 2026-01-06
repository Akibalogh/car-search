#!/usr/bin/env python3
"""Verify scraper results quality."""
import pandas as pd
from pathlib import Path

def verify_results():
    """Verify the scraper results."""
    output_file = 'scraped_car_data.xlsx'
    
    if not Path(output_file).exists():
        print(f"ERROR: {output_file} not found!")
        return
    
    print("="*80)
    print("SCRAPER RESULTS VERIFICATION")
    print("="*80)
    
    df = pd.read_excel(output_file)
    
    print(f"\n1. BASIC STATS")
    print(f"   Total records: {len(df)}")
    print(f"   Total columns: {len(df.columns)}")
    
    print(f"\n2. DATA QUALITY")
    
    # Check required fields
    required_fields = ['make', 'model', 'dealer_name', 'lease_monthly']
    for field in required_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            pct = (non_null / len(df) * 100) if len(df) > 0 else 0
            print(f"   {field:20} {non_null:4}/{len(df)} ({pct:5.1f}%)")
    
    print(f"\n3. DEALER NAME QUALITY")
    if 'dealer_name' in df.columns:
        dealers = df['dealer_name'].dropna().unique()
        print(f"   Unique dealers: {len(dealers)}")
        print(f"   Sample dealer names (first 10):")
        for i, dealer in enumerate(dealers[:10], 1):
            print(f"     {i:2}. {dealer}")
        
        # Check for common false positives
        false_positives = ['new', 'used', 'electric', 'research', 'sell', 'account', 
                          'remote', 'engine', 'start', 'liftgate']
        bad_dealers = [d for d in dealers if any(fp in str(d).lower() for fp in false_positives)]
        if bad_dealers:
            print(f"\n   ⚠ WARNING: Found {len(bad_dealers)} dealers that might be false positives:")
            for dealer in bad_dealers[:5]:
                print(f"     - {dealer}")
        else:
            print(f"   ✓ No obvious false positives detected")
    
    print(f"\n4. ERRORS")
    if 'error' in df.columns:
        errors = df['error'].notna().sum()
        print(f"   Records with errors: {errors}/{len(df)} ({(errors/len(df)*100):.1f}%)")
        if errors > 0:
            error_samples = df[df['error'].notna()]['error'].head(5).tolist()
            print(f"   Sample errors:")
            for i, err in enumerate(error_samples, 1):
                print(f"     {i}. {str(err)[:60]}")
    else:
        print(f"   No error column found")
    
    print(f"\n5. DEDUPLICATION")
    if 'vin' in df.columns:
        unique_vins = df['vin'].dropna().nunique()
        total_vins = df['vin'].notna().sum()
        print(f"   Unique VINs: {unique_vins}/{total_vins}")
    
    # Check for duplicates
    duplicate_cols = ['make', 'model', 'trim', 'year', 'dealer_name']
    available_cols = [col for col in duplicate_cols if col in df.columns]
    if len(available_cols) >= 3:
        duplicates = df.duplicated(subset=available_cols, keep=False).sum()
        print(f"   Potential duplicates (by {', '.join(available_cols[:3])}): {duplicates}")
    
    print(f"\n6. DATA DISTRIBUTION")
    if 'source_file' in df.columns:
        print(f"   Records by source file:")
        source_counts = df['source_file'].value_counts()
        for source, count in source_counts.items():
            print(f"     {source:20} {count:4}")
    
    if 'make' in df.columns:
        print(f"\n   Records by make:")
        make_counts = df['make'].value_counts()
        for make, count in make_counts.items():
            print(f"     {make:20} {count:4}")
    
    print(f"\n7. SAMPLE RECORDS")
    print(f"   First 3 complete records:")
    display_cols = ['make', 'model', 'trim', 'year', 'dealer_name', 'lease_monthly']
    available_display = [col for col in display_cols if col in df.columns]
    print(df[available_display].head(3).to_string())
    
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)

if __name__ == '__main__':
    verify_results()
