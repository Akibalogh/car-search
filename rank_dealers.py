#!/usr/bin/env python3
"""
Dealer Ranking Script
Ranks dealerships using pricing fairness, Google reviews, distance, and inventory.
Outputs ranked table and top 5 dealers to visit.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
import math
from typing import Dict, Tuple, Optional
from playwright.sync_api import sync_playwright
import time
from urllib.parse import quote_plus
import json

# Configuration
INPUT_FILE = 'scraped_car_data.xlsx'
CACHE_FILE = 'dealer_info_cache.json'  # Cache for dealer info to avoid re-fetching
ORIGIN = "White Plains, NY 10601"
EXCLUDE_ADDRESS = "229 N Franklin St, Hempstead, NY 11550"
MAYBE_FAR_ADDRESS = "236 W Fordham Rd, Bronx, NY 10468"
DRIVING_TIME_CUTOFF = 30  # minutes

# Scoring weights
WEIGHT_REVIEWS = 0.35
WEIGHT_FAIRNESS = 0.35
WEIGHT_PROXIMITY = 0.25
WEIGHT_INVENTORY = 0.05


def normalize_column_name(df: pd.DataFrame, possible_names: list) -> Optional[str]:
    """Fuzzy match column names."""
    for col in df.columns:
        col_lower = col.lower().replace('_', '').replace(' ', '')
        for name in possible_names:
            name_lower = name.lower().replace('_', '').replace(' ', '')
            if name_lower in col_lower or col_lower in name_lower:
                return col
    return None


def load_and_normalize_data(filepath: str) -> pd.DataFrame:
    """Step 1: Load and normalize data."""
    print("="*80)
    print("STEP 1: Loading and Normalizing Data")
    print("="*80)
    
    df = pd.read_excel(filepath)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Normalize column names
    dealer_col = normalize_column_name(df, ['dealer_name', 'dealer', 'dealership'])
    year_col = normalize_column_name(df, ['year'])
    make_col = normalize_column_name(df, ['make'])
    model_col = normalize_column_name(df, ['model'])
    trim_col = normalize_column_name(df, ['trim', 'variant'])
    price_col = normalize_column_name(df, ['full_price', 'price', 'cash_price', 'list_price', 'sale_price'])
    address_col = normalize_column_name(df, ['dealer_address', 'address'])
    url_col = normalize_column_name(df, ['url', 'listing_url', 'source_url'])
    
    # Rename columns
    rename_map = {}
    if dealer_col: rename_map[dealer_col] = 'dealer_name'
    if year_col: rename_map[year_col] = 'year'
    if make_col: rename_map[make_col] = 'make'
    if model_col: rename_map[model_col] = 'model'
    if trim_col: rename_map[trim_col] = 'trim'
    if price_col: rename_map[price_col] = 'price'
    if address_col: rename_map[address_col] = 'dealer_address'
    if url_col: rename_map[url_col] = 'listing_url'
    
    df = df.rename(columns=rename_map)
    
    # Ensure required columns exist
    required = ['dealer_name', 'price', 'year', 'make', 'model']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Filter rows with required data
    initial_count = len(df)
    df = df.dropna(subset=['dealer_name', 'price', 'year', 'make', 'model'])
    print(f"Filtered to {len(df)} rows with complete data (removed {initial_count - len(df)} rows)")
    
    # Create spec_key
    df['trim'] = df.get('trim', '').fillna('')
    df['spec_key'] = df.apply(
        lambda row: f"{row['year']}|{row['make']}|{row['model']}|{row['trim']}" if row['trim'] 
        else f"{row['year']}|{row['make']}|{row['model']}", 
        axis=1
    )
    
    # Convert price to numeric
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])
    
    print(f"Final dataset: {len(df)} rows")
    print(f"Unique dealers: {df['dealer_name'].nunique()}")
    print(f"Unique specs: {df['spec_key'].nunique()}")
    
    return df


def compute_pricing_fairness(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2: Compute pricing fairness scores per dealer."""
    print("\n" + "="*80)
    print("STEP 2: Computing Pricing Fairness")
    print("="*80)
    
    # Compute median price per spec
    spec_medians = df.groupby('spec_key')['price'].median().to_dict()
    df['spec_median_price'] = df['spec_key'].map(spec_medians)
    
    # Compute relative percentage
    df['rel_pct'] = (df['price'] - df['spec_median_price']) / df['spec_median_price']
    
    # Aggregate per dealer
    dealer_stats = df.groupby('dealer_name').agg({
        'price': 'count',  # listings
        'spec_key': 'nunique',  # unique_specs
        'rel_pct': ['median', lambda x: (x < 0).sum() / len(x), lambda x: (x.abs() <= 0.01).sum() / len(x)]
    }).reset_index()
    
    dealer_stats.columns = ['dealer_name', 'listings', 'unique_specs', 'median_rel_pct', 
                           'pct_below_median', 'pct_within_1pct']
    
    # Compute fairness score
    def calc_fairness_score(row):
        # Clamp median_rel_pct to [-0.10, +0.10]
        clamped = max(-0.10, min(0.10, row['median_rel_pct']))
        
        # Map to 0-100: -10% => 100, 0% => 50, +10% => 0
        score = 50 - (clamped / 0.10) * 50
        
        # Apply small-sample penalty
        if row['listings'] < 3:
            score *= 0.8
        elif row['listings'] < 5:
            score *= 0.9
        
        return max(0, min(100, score))
    
    dealer_stats['fairness_score'] = dealer_stats.apply(calc_fairness_score, axis=1)
    
    print(f"Computed fairness for {len(dealer_stats)} dealers")
    print(f"Median fairness score: {dealer_stats['fairness_score'].median():.1f}")
    
    return dealer_stats


def get_google_reviews_and_address(dealer_name: str, browser_context) -> Dict:
    """Step 3: Get Google reviews and address for a dealer."""
    result = {
        'address': None,
        'rating': None,
        'review_count': None
    }
    
    try:
        # Try Google Maps search first (more reliable for addresses)
        queries = [
            f"{dealer_name} dealership",
            f"{dealer_name} auto dealer",
            f"{dealer_name} car dealer"
        ]
        
        for query in queries:
            try:
                # Try Google Maps directly
                maps_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
                
                page = browser_context.new_page()
                page.goto(maps_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(4)  # Wait for maps to load
                
                # Try to get address from URL or page content
                current_url = page.url
                content = page.content()
                page_text = page.inner_text('body')
                
                # Extract from URL if it contains coordinates/place
                if '/place/' in current_url or '/@' in current_url:
                    # URL might have address info
                    pass
                
                # Look for address in page text - Maps shows it prominently
                # Try to find address patterns in visible text
                address_patterns = [
                    r'(\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Ave|Rd|Blvd|Dr|Ln|Way|Pkwy|Hwy|Street|Avenue|Road|Boulevard|Drive|Lane)[^,\n]*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\s+\d{5})',
                    r'(\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Ave|Rd|Blvd|Dr|Ln|Way|Pkwy|Hwy)[^,\n]*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\s+\d{5})',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\s+\d{5})',
                ]
                
                # Search in page text (more reliable than HTML)
                for pattern in address_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        addr = match.strip() if isinstance(match, str) else match[0].strip() if match else None
                        if addr and len(addr) > 10 and ('NY' in addr or 'NJ' in addr or 'CT' in addr):
                            result['address'] = addr
                            break
                    if result['address']:
                        break
                
                # Extract rating from Maps page - try multiple approaches
                # Google Maps shows rating in various formats
                rating_patterns = [
                    r'(\d+\.\d+)\s*(?:stars?|★|⭐|out of 5|\/5)',
                    r'Rating[:\s]*(\d+\.\d+)',
                    r'(\d+\.\d+)\s*\/\s*5',
                    r'(\d+\.\d+)\s*out of 5',
                    r'aria-label="[^"]*(\d+\.\d+)[^"]*stars?',
                    r'data-value="(\d+\.\d+)"',  # Sometimes in data attributes
                ]
                
                # Also check HTML content for structured data
                for pattern in rating_patterns:
                    # Try in page text
                    match = re.search(pattern, page_text, re.I)
                    if match:
                        try:
                            rating = float(match.group(1))
                            if 1.0 <= rating <= 5.0:
                                result['rating'] = rating
                                break
                        except:
                            continue
                    
                    # Try in HTML content
                    match = re.search(pattern, content, re.I)
                    if match:
                        try:
                            rating = float(match.group(1))
                            if 1.0 <= rating <= 5.0:
                                result['rating'] = rating
                                break
                        except:
                            continue
                
                # Extract review count - Google Maps shows it near the rating
                review_patterns = [
                    r'([\d,]+)\s+reviews?',
                    r'\(([\d,]+)\s*reviews?\)',
                    r'([\d,]+)\s+Google reviews?',
                    r'([\d,]+)\s+ratings?',
                    r'reviewCount["\']?\s*:\s*["\']?(\d+)',  # JSON-LD format
                    r'"reviewCount"\s*:\s*(\d+)',
                ]
                
                for pattern in review_patterns:
                    # Try in page text first
                    match = re.search(pattern, page_text, re.I)
                    if match:
                        try:
                            count_str = match.group(1).replace(',', '')
                            count = int(count_str)
                            if count > 0:  # Valid review count
                                result['review_count'] = count
                                break
                        except:
                            continue
                    
                    # Try in HTML content
                    match = re.search(pattern, content, re.I)
                    if match:
                        try:
                            count_str = match.group(1).replace(',', '')
                            count = int(count_str)
                            if count > 0:
                                result['review_count'] = count
                                break
                        except:
                            continue
                
                page.close()
                
                # If we got address, we're good (rating/reviews are bonus)
                if result['address']:
                    break
                    
            except Exception as e:
                try:
                    page.close()
                except:
                    pass
                continue
        
        # If still no address or reviews, try regular Google search as fallback
        if not result['address'] or not result['rating']:
            try:
                search_url = f"https://www.google.com/search?q={quote_plus(dealer_name + ' dealership reviews')}"
                page = browser_context.new_page()
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(4)  # Wait for knowledge panel to load
                
                page_text = page.inner_text('body')
                content = page.content()
                
                # Try to extract from knowledge panel (right sidebar)
                # Google shows rating and reviews prominently in knowledge panel
                
                # Extract rating if not already found
                if not result['rating']:
                    rating_patterns = [
                        r'(\d+\.\d+)\s*(?:stars?|★|⭐)',
                        r'(\d+\.\d+)\s*out of 5',
                        r'Rating[:\s]*(\d+\.\d+)',
                        r'aria-label="[^"]*(\d+\.\d+)[^"]*stars?',
                    ]
                    for pattern in rating_patterns:
                        match = re.search(pattern, page_text, re.I)
                        if match:
                            try:
                                rating = float(match.group(1))
                                if 1.0 <= rating <= 5.0:
                                    result['rating'] = rating
                                    break
                            except:
                                continue
                
                # Extract review count if not already found
                if not result['review_count']:
                    review_patterns = [
                        r'([\d,]+)\s+reviews?',
                        r'\(([\d,]+)\s*reviews?\)',
                        r'([\d,]+)\s+Google reviews?',
                    ]
                    for pattern in review_patterns:
                        match = re.search(pattern, page_text, re.I)
                        if match:
                            try:
                                count_str = match.group(1).replace(',', '')
                                count = int(count_str)
                                if count > 0:
                                    result['review_count'] = count
                                    break
                            except:
                                continue
                
                # Try simpler address patterns if still missing
                if not result['address']:
                    simple_patterns = [
                        r'(\d+[^,\n]{10,50},\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\s+\d{5})',
                        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\s+\d{5})',
                    ]
                    for pattern in simple_patterns:
                        matches = re.findall(pattern, page_text)
                        for match in matches:
                            addr = match.strip()
                            if addr and len(addr) > 10 and ('NY' in addr or 'NJ' in addr or 'CT' in addr):
                                result['address'] = addr
                                break
                        if result['address']:
                            break
                
                page.close()
            except Exception as e:
                try:
                    page.close()
                except:
                    pass
        
        return result
        
    except Exception as e:
        print(f"  Error getting reviews for {dealer_name}: {e}")
        return result


def compute_reviews_score(rating: Optional[float], review_count: Optional[int]) -> float:
    """Convert Google reviews to 0-100 score."""
    if rating is None or review_count is None:
        return 0.0
    
    # Rating score: 3.0 stars -> 0, 5.0 -> 100
    rating_score = ((rating - 3.0) / (5.0 - 3.0)) * 100
    rating_score = max(0, min(100, rating_score))
    
    # Volume score: log scaling
    if review_count < 50:
        volume_score = 0
    else:
        volume_score = (math.log10(review_count) - math.log10(50)) / (math.log10(5000) - math.log10(50)) * 100
        volume_score = max(0, min(100, volume_score))
    
    reviews_score = 0.7 * rating_score + 0.3 * volume_score
    
    # Apply penalty for low review count
    if review_count < 50:
        reviews_score *= 0.6
    
    return reviews_score


def get_distance_and_time(origin: str, destination: str, browser_context) -> Tuple[Optional[float], Optional[float]]:
    """Step 4: Get driving distance (miles) and time (minutes) from origin to destination."""
    try:
        # Use Google Maps directions (more reliable)
        directions_url = f"https://www.google.com/maps/dir/{quote_plus(origin)}/{quote_plus(destination)}"
        
        page = browser_context.new_page()
        page.goto(directions_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)  # Wait for directions to load
        
        page_text = page.inner_text('body')
        content = page.content()
        current_url = page.url
        
        distance_miles = None
        time_minutes = None
        
        # Google Maps shows distance and time prominently in the directions panel
        # Look for patterns like "15.2 mi" and "25 min"
        
        # Try to find distance and time together
        combined_patterns = [
            r'(\d+\.?\d*)\s*(?:miles?|mi\.?)[^\d]*(\d+)\s*(?:min(?:utes?)?|mins?)',
            r'(\d+)\s*(?:min(?:utes?)?|mins?)[^\d]*(\d+\.?\d*)\s*(?:miles?|mi\.?)',
        ]
        for pattern in combined_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                try:
                    val1 = match.group(1)
                    val2 = match.group(2)
                    # Determine which is distance and which is time
                    if 'mi' in match.group(0).lower() or 'mile' in match.group(0).lower():
                        # First might be distance, second time
                        if float(val1) < 200:  # Reasonable distance
                            distance_miles = float(val1)
                        if int(val2) < 300:  # Reasonable time
                            time_minutes = int(val2)
                    else:
                        # First might be time, second distance
                        if int(val1) < 300:
                            time_minutes = int(val1)
                        if float(val2) < 200:
                            distance_miles = float(val2)
                    if distance_miles and time_minutes:
                        break
                except:
                    continue
        
        # If not found together, search separately
        if not distance_miles:
            distance_patterns = [
                r'(\d+\.?\d*)\s*(?:miles?|mi\.?)',
                r'(\d+\.?\d*)\s*mi\b',
            ]
            for pattern in distance_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches:
                    try:
                        dist = float(match)
                        if 0.1 <= dist <= 200:  # Reasonable range
                            distance_miles = dist
                            break
                    except:
                        continue
                if distance_miles:
                    break
        
        if not time_minutes:
            time_patterns = [
                r'(\d+)\s*(?:min(?:utes?)?|mins?)',
                r'(\d+)\s*min\b',
            ]
            for pattern in time_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches:
                    try:
                        t = int(match)
                        if 1 <= t <= 300:  # Reasonable range
                            time_minutes = t
                            break
                    except:
                        continue
                if time_minutes:
                    break
        
        page.close()
        return distance_miles, time_minutes
        
    except Exception as e:
        print(f"  Error getting distance for {destination}: {e}")
        try:
            page.close()
        except:
            pass
        return None, None


def compute_proximity_score(driving_time_minutes: Optional[float]) -> float:
    """Convert driving time to 0-100 proximity score."""
    import pandas as pd
    import numpy as np
    
    # Handle both None and NaN (pandas uses NaN for missing values)
    if driving_time_minutes is None or pd.isna(driving_time_minutes):
        # If no distance data, give a neutral score (50) instead of 0
        # This allows ranking to proceed based on other factors
        return 50.0
    
    if driving_time_minutes > DRIVING_TIME_CUTOFF:
        return 0.0
    
    score = 100 - (driving_time_minutes / DRIVING_TIME_CUTOFF) * 100
    return max(0, min(100, score))


def compute_inventory_score(listings: int, all_listings: pd.Series) -> float:
    """Step 5: Compute inventory score (0-100)."""
    if len(all_listings) == 0:
        return 50.0
    
    min_listings = all_listings.min()
    max_listings = all_listings.max()
    
    if min_listings == max_listings:
        return 50.0
    
    score = ((listings - min_listings) / (max_listings - min_listings)) * 100
    return max(0, min(100, score))


def main():
    """Main ranking workflow."""
    print("\n" + "="*80)
    print("DEALER RANKING SYSTEM")
    print("="*80)
    
    # Step 1: Load and normalize
    if not Path(INPUT_FILE).exists():
        print(f"ERROR: Input file '{INPUT_FILE}' not found!")
        return
    
    df = load_and_normalize_data(INPUT_FILE)
    
    # Step 2: Pricing fairness
    dealer_stats = compute_pricing_fairness(df)
    
    # Step 3 & 4: Get Google reviews, addresses, and distances
    print("\n" + "="*80)
    print("STEP 3 & 4: Getting Google Reviews, Addresses, and Distances")
    print("="*80)
    
    unique_dealers = dealer_stats['dealer_name'].unique()
    print(f"Fetching data for {len(unique_dealers)} dealers...")
    
    # Load cache if exists
    dealer_info = {}
    if Path(CACHE_FILE).exists():
        try:
            with open(CACHE_FILE, 'r') as f:
                dealer_info = json.load(f)
            print(f"Loaded {len(dealer_info)} dealers from cache")
        except:
            pass
    
    # Find dealers that need fetching
    dealers_to_fetch = [d for d in unique_dealers if d not in dealer_info or dealer_info.get(d) is None]
    print(f"Need to fetch {len(dealers_to_fetch)} dealers ({len(unique_dealers) - len(dealers_to_fetch)} cached)")
    
    if dealers_to_fetch:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, channel='chrome')
            context = browser.new_context()
            
            for i, dealer_name in enumerate(dealers_to_fetch, 1):
                print(f"[{i}/{len(dealers_to_fetch)}] Processing: {dealer_name}")
                
                # Get reviews and address
                reviews_data = get_google_reviews_and_address(dealer_name, context)
                address = reviews_data['address']
                rating = reviews_data['rating']
                review_count = reviews_data['review_count']
                
                # Apply exclusion rules
                if address and EXCLUDE_ADDRESS.lower() in address.lower():
                    print(f"  ⚠ EXCLUDED: Matches exclude address")
                    dealer_info[dealer_name] = None  # Mark for exclusion
                    # Save cache
                    with open(CACHE_FILE, 'w') as f:
                        json.dump(dealer_info, f, indent=2)
                    continue
                
                # Get distance if we have an address
                distance_miles = None
                driving_time_minutes = None
                
                if address:
                    distance_miles, driving_time_minutes = get_distance_and_time(ORIGIN, address, context)
                    
                    # Apply 30-minute cutoff
                    if driving_time_minutes and driving_time_minutes > DRIVING_TIME_CUTOFF:
                        # Special case for "maybe far" address
                        if MAYBE_FAR_ADDRESS.lower() in address.lower():
                            print(f"  ⚠ EXCLUDED: Over 30 min cutoff ({driving_time_minutes} min)")
                        else:
                            print(f"  ⚠ EXCLUDED: Over 30 min cutoff ({driving_time_minutes} min)")
                        dealer_info[dealer_name] = None
                        # Save cache
                        with open(CACHE_FILE, 'w') as f:
                            json.dump(dealer_info, f, indent=2)
                        continue
                
                # Store dealer info
                dealer_info[dealer_name] = {
                    'address': address,
                    'rating': rating,
                    'review_count': review_count,
                    'distance_miles': distance_miles,
                    'driving_time_minutes': driving_time_minutes
                }
                
                # Save cache periodically
                if i % 5 == 0:
                    with open(CACHE_FILE, 'w') as f:
                        json.dump(dealer_info, f, indent=2)
                
                # Rate limiting
                time.sleep(1)
            
            browser.close()
        
        # Final cache save
        with open(CACHE_FILE, 'w') as f:
            json.dump(dealer_info, f, indent=2)
        print(f"✓ Saved dealer info cache to {CACHE_FILE}")
    
    # Merge dealer info into stats
    dealer_stats['address'] = dealer_stats['dealer_name'].map(lambda x: dealer_info.get(x, {}).get('address') if dealer_info.get(x) else None)
    dealer_stats['google_rating'] = dealer_stats['dealer_name'].map(lambda x: dealer_info.get(x, {}).get('rating') if dealer_info.get(x) else None)
    dealer_stats['google_review_count'] = dealer_stats['dealer_name'].map(lambda x: dealer_info.get(x, {}).get('review_count') if dealer_info.get(x) else None)
    dealer_stats['distance_miles'] = dealer_stats['dealer_name'].map(lambda x: dealer_info.get(x, {}).get('distance_miles') if dealer_info.get(x) else None)
    dealer_stats['driving_time_minutes'] = dealer_stats['dealer_name'].map(lambda x: dealer_info.get(x, {}).get('driving_time_minutes') if dealer_info.get(x) else None)
    
    # Filter out excluded dealers (only those explicitly marked as None in cache)
    # Allow dealers with missing addresses but mark them
    excluded_dealers = [k for k, v in dealer_info.items() if v is None]
    dealer_stats = dealer_stats[~dealer_stats['dealer_name'].isin(excluded_dealers)].copy()
    
    # For dealers without addresses, we'll still rank them but with distance penalty
    print(f"Dealers with addresses: {dealer_stats['address'].notna().sum()}")
    print(f"Dealers without addresses: {dealer_stats['address'].isna().sum()}")
    
    # Step 5 & 6: Compute scores and composite ranking
    print("\n" + "="*80)
    print("STEP 5 & 6: Computing Scores and Composite Ranking")
    print("="*80)
    
    dealer_stats['reviews_score'] = dealer_stats.apply(
        lambda row: compute_reviews_score(row['google_rating'], row['google_review_count']), 
        axis=1
    )
    dealer_stats['proximity_score'] = dealer_stats['driving_time_minutes'].apply(compute_proximity_score)
    dealer_stats['inventory_score'] = dealer_stats['listings'].apply(
        lambda x: compute_inventory_score(x, dealer_stats['listings'])
    )
    
    # Apply 30-minute cutoff: filter out dealers with known distance > 30 min
    # (Keep those with unknown distance for now)
    before_cutoff = len(dealer_stats)
    dealer_stats = dealer_stats[
        (dealer_stats['driving_time_minutes'].isna()) | 
        (dealer_stats['driving_time_minutes'] <= DRIVING_TIME_CUTOFF)
    ].copy()
    after_cutoff = len(dealer_stats)
    if before_cutoff > after_cutoff:
        print(f"Filtered out {before_cutoff - after_cutoff} dealers over 30-minute cutoff")
    
    # Composite score
    dealer_stats['composite_score'] = (
        WEIGHT_REVIEWS * dealer_stats['reviews_score'] +
        WEIGHT_FAIRNESS * dealer_stats['fairness_score'] +
        WEIGHT_PROXIMITY * dealer_stats['proximity_score'] +
        WEIGHT_INVENTORY * dealer_stats['inventory_score']
    )
    
    # Sort by composite score (with tie-breakers)
    dealer_stats = dealer_stats.sort_values(
        by=['composite_score', 'reviews_score', 'median_rel_pct', 'listings'],
        ascending=[False, False, True, False]
    ).reset_index(drop=True)
    
    dealer_stats['rank'] = range(1, len(dealer_stats) + 1)
    
    # Step 7: Output results
    print("\n" + "="*80)
    print("STEP 7: OUTPUT - RANKED DEALER TABLE")
    print("="*80)
    
    output_cols = [
        'rank', 'dealer_name', 'address', 'driving_time_minutes', 'distance_miles',
        'google_rating', 'google_review_count', 'listings', 'unique_specs',
        'median_rel_pct', 'pct_below_median', 'fairness_score',
        'reviews_score', 'proximity_score', 'inventory_score', 'composite_score'
    ]
    
    output_df = dealer_stats[output_cols].copy()
    
    # Format percentages
    output_df['median_rel_pct'] = (output_df['median_rel_pct'] * 100).round(2)
    output_df['pct_below_median'] = (output_df['pct_below_median'] * 100).round(1)
    
    # Round scores
    score_cols = ['fairness_score', 'reviews_score', 'proximity_score', 'inventory_score', 'composite_score']
    for col in score_cols:
        output_df[col] = output_df[col].round(1)
    
    print("\n" + output_df.to_string(index=False))
    
    # Save to Excel
    output_file = 'ranked_dealers.xlsx'
    output_df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n✓ Saved ranked table to: {output_file}")
    
    # Top 5 dealers
    print("\n" + "="*80)
    print("TOP 5 DEALERS TO VISIT")
    print("="*80)
    
    top5 = output_df.head(5)
    for idx, row in top5.iterrows():
        print(f"\n{row['rank']}. {row['dealer_name']}")
        print(f"   Address: {row['address']}")
        print(f"   Distance: {row['distance_miles']:.1f} miles ({row['driving_time_minutes']:.0f} min)")
        print(f"   Google: {row['google_rating']:.1f} stars ({row['google_review_count']:.0f} reviews)")
        print(f"   Pricing: {row['median_rel_pct']:.1f}% vs median ({row['pct_below_median']:.1f}% below median)")
        print(f"   Inventory: {row['listings']:.0f} listings")
        print(f"   Composite Score: {row['composite_score']:.1f}/100")
        
        # Why this dealer
        reasons = []
        if row['google_rating'] >= 4.0 and row['google_review_count'] >= 100:
            reasons.append(f"Strong reviews ({row['google_rating']:.1f}★, {row['google_review_count']:.0f} reviews)")
        if row['median_rel_pct'] < 0:
            reasons.append(f"Fair pricing ({row['median_rel_pct']:.1f}% below median)")
        if row['driving_time_minutes'] <= 20:
            reasons.append(f"Close ({row['driving_time_minutes']:.0f} min away)")
        elif row['driving_time_minutes'] <= 30:
            reasons.append(f"Within range ({row['driving_time_minutes']:.0f} min away)")
        
        if reasons:
            print(f"   Why: {'; '.join(reasons)}")
    
    print("\n" + "="*80)
    print("RANKING COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()

