#!/usr/bin/env python3
"""
Full TrueCar scraper - processes all Excel files with concurrent scraping.
Uses saved Playwright session for authentication.
"""

import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import re
from datetime import datetime
from pathlib import Path
import json
import time

# Global variable for URL to source mapping (used in scrape_urls_batch)
urls_to_source = {}

# Configuration
SESSION_FILE = 'truecar_session.json'
OUTPUT_FILE = 'scraped_car_data.xlsx'
CHECKPOINT_FILE = 'scraping_checkpoint.json'
CHECKPOINT_INTERVAL = 10  # Save progress every N URLs

# Rate limiting
DELAY_BETWEEN_REQUESTS = 2.0  # seconds (increased to reduce load)
CONCURRENT_BROWSERS = 2  # Number of concurrent browser instances (reduced to prevent memory issues)


async def scrape_car_page(page, url):
    """Scrape a single TrueCar car listing page."""
    try:
        # Use domcontentloaded instead of networkidle (faster, less strict)
        # Increased timeout and wait time for better reliability
        await page.goto(url, wait_until="domcontentloaded", timeout=120000)
        await page.wait_for_timeout(4000)  # Increased wait for dynamic content
        
        # Get page content with error handling
        try:
            page_text = await page.inner_text('body')
            content = await page.content()
        except Exception as e:
            # If we can't get page text, try again after a short wait
            await page.wait_for_timeout(2000)
            page_text = await page.inner_text('body')
            content = await page.content()
        
        result = {
            'url': url,
            'scrape_timestamp': datetime.now().isoformat(),
            'error': None,
        }
        
        # Extract vehicle details
        # VIN
        vin_pattern = r'\b([A-HJ-NPR-Z0-9]{17})\b'
        vin_match = re.search(vin_pattern, page_text)
        result['vin'] = vin_match.group(1) if vin_match else None
        
        # Year, Make, Model, Trim from title
        try:
            title = await page.title()
            vehicle_match = re.search(r'(?:New\s+)?(\d{4})\s+(Honda|Toyota|Nissan|Mazda|Subaru)\s+(\w+)\s+(.+?)(?:\s*[-|]|For Sale|$)', title)
            if vehicle_match and len(vehicle_match.groups()) >= 4:
                result['year'] = vehicle_match.group(1)
                result['make'] = vehicle_match.group(2)
                result['model'] = vehicle_match.group(3)
                trim_text = vehicle_match.group(4).strip()
                trim_text = re.sub(r'\s+For Sale.*$', '', trim_text, flags=re.I)
                result['trim'] = trim_text
            else:
                result['year'] = None
                result['make'] = None
                result['model'] = None
                result['trim'] = None
        except Exception as e:
            result['year'] = None
            result['make'] = None
            result['model'] = None
            result['trim'] = None
        
        # Stock Number
        stock_match = re.search(r'Stock\s+([A-Z0-9]+)(?:\s|Listed|$)', page_text, re.I)
        result['stock_number'] = stock_match.group(1) if stock_match else None
        
        # Extract dealer name - OPTIMIZED (PRIORITY: dealer name is most important field)
        dealer_name = None
        
        # Method 1: DOM selector - dealer name is in data-test="vdpDealerHeader" (PRIMARY METHOD)
        try:
            dealer_header = page.locator('div[data-test="vdpDealerHeader"]')
            if await dealer_header.count() > 0:
                # Dealer name is in the first span inside the header
                spans = dealer_header.locator('span')
                if await spans.count() > 0:
                    candidate = await spans.first.inner_text()
                    candidate = candidate.strip() if candidate else None
                    # Validate it looks like a dealer name (has reasonable length, contains text)
                    if candidate and 5 <= len(candidate) <= 80:
                        dealer_name = candidate
        except Exception as e:
            pass  # Fall back to text-based extraction
        
        # Method 2: Extract from HTML content - look for "[Brand] of [Location]" pattern
        if not dealer_name:
            try:
                content = await page.content()
                
                # Look for "dealershipName" or similar in JSON
                json_patterns = [
                    r'"dealershipName"\s*:\s*"([^"]+)"',
                    r'"dealerName"\s*:\s*"([^"]+)"',
                    r'"sellerName"\s*:\s*"([^"]+)"',
                    r'"name"\s*:\s*"([^"]+)"\s*[,\}].*?"address',
                ]
                for pattern in json_patterns:
                    matches = re.findall(pattern, content, re.I)
                    for match in matches:
                        name = match.strip()
                        if name and len(name) > 5 and name.lower() not in ['truecar', 'dealer', 'certified dealer']:
                            if re.search(r'\b(of|Honda|Toyota|Nissan|Mazda|Subaru)\b', name, re.I):
                                dealer_name = name
                                break
                    if dealer_name:
                        break
                
                # Look for "[Brand] of [Location]" pattern
                if not dealer_name:
                    brand_of_pattern = r'\b(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
                    matches = re.findall(brand_of_pattern, content)
                    if matches:
                        brand, location = matches[0]
                        dealer_name = f"{brand} of {location}"
            except:
                pass
        
        # Method 3: Extract from page text - look near location/address
        if not dealer_name:
            try:
                # Find location first (e.g., "New Rochelle, NY")
                location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}),\s*[A-Z]{2}\b'
                location_match = re.search(location_pattern, page_text)
                
                if location_match:
                    location = location_match.group(1)
                    location_pos = page_text.find(location)
                    if location_pos >= 0:
                        context = page_text[max(0, location_pos - 200):location_pos + 50]
                        
                        # Try "[Brand] of [Location]"
                        brand_of_pattern = r'\b(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\s+of\s+' + re.escape(location) + r'\b'
                        match = re.search(brand_of_pattern, context, re.I)
                        if match:
                            dealer_name = match.group(0).title()
                
                # Fallback: look near location (address extraction removed - not needed)
                if not dealer_name:
                    # Just try to find dealer name pattern in broader context
                    location_brand_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis)\b'
                    matches = re.findall(location_brand_pattern, page_text[:5000], re.I)  # Check first 5000 chars
                    if matches:
                        reject_words = ['heated', 'driver', 'seat', 'climate', 'control', 'zone', 
                                      'not', 'available', 'hybrid', 'visit', 'discover', 'notes']
                        for loc, brand in matches:
                            candidate = f"{loc} {brand}"
                            if not any(rw in candidate.lower() for rw in reject_words) and ' ' in loc:
                                dealer_name = candidate
                                break
            except:
                pass
        
        result['dealer_name'] = dealer_name
        # Dealer address not needed - removed
        
        # Extract pricing information - Lease Monthly Payment (primary requirement)
        # Method 1: DOM selector: data-test="pricingSectionRadioGroupPrice" data-test-item="lease"
        lease_price = None
        try:
            lease_elem = page.locator('span[data-test="pricingSectionRadioGroupPrice"][data-test-item="lease"]').first
            if await lease_elem.count() > 0:
                lease_text = await lease_elem.inner_text()
                # Extract price from text like "$525/mo" or "$525/mo\nEstimate"
                lease_match = re.search(r'\$([0-9,]+)/mo', lease_text)
                if lease_match:
                    lease_price = lease_match.group(1).replace(',', '')
        except Exception as e:
            pass
        
        # Method 2: Try all pricing radio group elements and find lease
        if not lease_price:
            try:
                all_pricing = page.locator('*[data-test="pricingSectionRadioGroupPrice"]')
                count = await all_pricing.count()
                for i in range(count):
                    try:
                        elem = all_pricing.nth(i)
                        test_item = await elem.get_attribute('data-test-item')
                        if test_item and 'lease' in test_item.lower():
                            text = await elem.inner_text()
                            match = re.search(r'\$([0-9,]+)/mo', text)
                            if match:
                                lease_price = match.group(1).replace(',', '')
                                break
                    except:
                        continue
            except:
                pass
        
        # Method 3: Look for lease in parent containers with pricing
        if not lease_price:
            try:
                # Look for containers that have "Lease" text and price nearby
                pricing_containers = page.locator('*[data-test*="pricing"], *[data-test*="pricingSection"]')
                count = await pricing_containers.count()
                for i in range(min(10, count)):  # Check first 10 containers
                    try:
                        container_text = await pricing_containers.nth(i).inner_text()
                        # Look for "Lease" followed by price
                        if 'lease' in container_text.lower():
                            match = re.search(r'lease[^$]*\$([0-9,]+)/mo', container_text, re.I)
                            if match:
                                lease_price = match.group(1).replace(',', '')
                                break
                    except:
                        continue
            except:
                pass
        
        # Method 4: Enhanced text-based extraction with broader context
        if not lease_price:
            lease_patterns = [
                r'Lease[:\s]+\$([0-9,]+)/mo',  # "Lease: $525/mo"
                r'\$([0-9,]+)/mo[^0-9]*lease',  # "$525/mo ... lease"
                r'lease[^$]*\$([0-9,]+)/mo',    # "lease ... $525/mo"
                r'\$([0-9,]+)/mo.*?Estimate',   # "$525/mo Estimate"
            ]
            for pattern in lease_patterns:
                lease_match = re.search(pattern, page_text, re.I)
                if lease_match:
                    lease_price = lease_match.group(1).replace(',', '')
                    break
        
        # Method 5: Look in HTML content for lease-related data attributes or JSON
        if not lease_price:
            try:
                content = await page.content()
                # Look for data attributes
                data_patterns = [
                    r'data-lease[^=]*=["\']([0-9,]+)',
                    r'data-monthly[^=]*=["\']([0-9,]+)',
                ]
                for pattern in data_patterns:
                    match = re.search(pattern, content, re.I)
                    if match:
                        lease_price = match.group(1).replace(',', '')
                        break
            except:
                pass
        
        # Method 6: Try clicking lease button/tab if found (interaction-based)
        if not lease_price:
            try:
                # Look for lease buttons/tabs
                lease_buttons = page.locator('button:has-text("Lease"), [role="button"]:has-text("Lease"), [role="tab"]:has-text("Lease"), a[role="tab"]:has-text("Lease")')
                count = await lease_buttons.count()
                if count > 0:
                    # Try clicking the first lease button/tab
                    await lease_buttons.first.click()
                    await page.wait_for_timeout(2000)  # Wait for content to load
                    
                    # Check if lease price appears after click
                    lease_elem = page.locator('span[data-test="pricingSectionRadioGroupPrice"][data-test-item="lease"]').first
                    if await lease_elem.count() > 0:
                        lease_text = await lease_elem.inner_text()
                        lease_match = re.search(r'\$([0-9,]+)/mo', lease_text)
                        if lease_match:
                            lease_price = lease_match.group(1).replace(',', '')
            except:
                pass  # If interaction fails, continue without it
        
        result['lease_monthly'] = lease_price
        
        # Full Price Extraction (prioritize list_price, then cash_price, then MSRP)
        # MSRP
        msrp_match = re.search(r'MSRP[:\s]+\$([0-9,]+)', page_text, re.I)
        result['msrp'] = msrp_match.group(1).replace(',', '') if msrp_match else None
        
        # List Price (best coverage - 99.5%)
        list_price_match = re.search(r'List\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
        result['list_price'] = list_price_match.group(1).replace(',', '') if list_price_match else None
        
        # Cash Price
        cash_match = re.search(r'Cash\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
        result['cash_price'] = cash_match.group(1).replace(',', '') if cash_match else None
        
        # Your Price (alternative full price field)
        your_price_match = re.search(r'Your\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
        result['your_price'] = your_price_match.group(1).replace(',', '') if your_price_match else None
        
        # Full Price - prioritize list_price (most common), then cash_price, then MSRP, then your_price
        full_price = None
        if result['list_price']:
            full_price = result['list_price']
        elif result['cash_price']:
            full_price = result['cash_price']
        elif result['msrp']:
            full_price = result['msrp']
        elif result.get('your_price'):
            full_price = result['your_price']
        result['full_price'] = full_price
        
        # Dealer Discount
        discount_match = re.search(r'Dealer\s+discount[:\s]+[-\$]?([0-9,]+)', page_text, re.I)
        result['dealer_discount'] = discount_match.group(1).replace(',', '') if discount_match else None
        
        # Finance Monthly
        finance_match = re.search(r'Finance[:\s]+\$([0-9,]+)/mo', page_text, re.I)
        result['finance_monthly'] = finance_match.group(1).replace(',', '') if finance_match else None
        
        # Additional vehicle details
        # Exterior Color
        ext_color_match = re.search(r'Exterior\s+color[:\s]+([^\n]+)', page_text, re.I)
        result['exterior_color'] = ext_color_match.group(1).strip() if ext_color_match else None
        
        # Interior Color
        int_color_match = re.search(r'Interior\s+color[:\s]+([^\n]+)', page_text, re.I)
        result['interior_color'] = int_color_match.group(1).strip() if int_color_match else None
        
        # MPG
        mpg_patterns = [
            r'MPG[:\s]+(\d+)\s*city\s*/\s*(\d+)\s*highway',
            r'(\d+)\s*city\s*/\s*(\d+)\s*highway',
        ]
        mpg = None
        for pattern in mpg_patterns:
            mpg_match = re.search(pattern, page_text, re.I)
            if mpg_match and len(mpg_match.groups()) >= 2:
                mpg = f"{mpg_match.group(1)} city / {mpg_match.group(2)} highway"
                break
        result['mpg'] = mpg
        
        return result
        
    except Exception as e:
        return {
            'url': url,
            'scrape_timestamp': datetime.now().isoformat(),
            'error': str(e),
        }


def deduplicate_results(results_df):
    """Deduplicate results based on VIN or other factors."""
    print(f"\nDeduplicating {len(results_df)} records...")
    
    # Remove records with errors first (but keep them for reference)
    error_records = results_df[results_df['error'].notna()].copy()
    valid_records = results_df[results_df['error'].isna()].copy()
    
    print(f"  Valid records: {len(valid_records)}")
    print(f"  Error records: {len(error_records)}")
    
    if len(valid_records) == 0:
        return results_df
    
    # Primary deduplication: VIN
    if 'vin' in valid_records.columns:
        # Remove duplicates by VIN, keep first occurrence
        before = len(valid_records)
        valid_records = valid_records.drop_duplicates(subset=['vin'], keep='first')
        vin_duplicates = before - len(valid_records)
        if vin_duplicates > 0:
            print(f"  Removed {vin_duplicates} duplicates by VIN")
    
    # Fallback deduplication: Make + Model + Trim + Year + Stock + Dealer
    if 'make' in valid_records.columns:
        dedup_cols = ['make', 'model', 'year']
        if 'trim' in valid_records.columns:
            dedup_cols.append('trim')
        if 'stock_number' in valid_records.columns:
            dedup_cols.append('stock_number')
        if 'dealer_name' in valid_records.columns:
            dedup_cols.append('dealer_name')
        
        before = len(valid_records)
        valid_records = valid_records.drop_duplicates(subset=dedup_cols, keep='first')
        other_duplicates = before - len(valid_records)
        if other_duplicates > 0:
            print(f"  Removed {other_duplicates} duplicates by other factors")
    
    # Combine valid and error records
    final_df = pd.concat([valid_records, error_records], ignore_index=True)
    print(f"  Final unique records: {len(valid_records)}")
    
    return final_df


async def scrape_urls_batch(context, urls, start_idx, total, batch_id):
    """Scrape a batch of URLs using a single context, creating new page for each URL."""
    results = []
    
    for i, url in enumerate(urls):
        global_idx = start_idx + i + 1
        print(f"  [{global_idx}/{total}] Browser {batch_id+1}: Scraping {url[:70]}...", flush=True)
        
        page = None
        try:
            # Create a new page for each URL to prevent memory accumulation
            page = await context.new_page()
            result = await scrape_car_page(page, url)
            result['source_file'] = urls_to_source.get(url, 'unknown')
            results.append(result)
            
            # Log success/error
            if result.get('error'):
                print(f"    ✗ Error: {result['error'][:60]}", flush=True)
            else:
                dealer = result.get('dealer_name', 'N/A')[:30]
                print(f"    ✓ Success - Dealer: {dealer}", flush=True)
                
        except Exception as e:
            error_msg = str(e)[:60]
            print(f"    ✗ Exception: {error_msg}", flush=True)
            results.append({
                'url': url,
                'scrape_timestamp': datetime.now().isoformat(),
                'error': str(e),
                'source_file': urls_to_source.get(url, 'unknown')
            })
        finally:
            # Always close the page to free memory
            if page:
                try:
                    await page.close()
                except:
                    pass
            
            # Periodic garbage collection
            if i > 0 and i % 10 == 0:
                import gc
                gc.collect()
        
        # Rate limiting
        if i < len(urls) - 1:
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    
    return results


async def scrape_all_urls(urls, url_to_source_map):
    """Scrape all URLs with concurrent browsers."""
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        print("Please run simple_login.py first to save your session.")
        return None
    
    all_results = []
    global urls_to_source
    urls_to_source = url_to_source_map
    
    async with async_playwright() as p:
        # Launch browsers and contexts
        browsers = []
        contexts = []
        
        print(f"Launching {CONCURRENT_BROWSERS} browser instances...")
        for i in range(CONCURRENT_BROWSERS):
            try:
                # Use system Chrome (more stable than bundled Chromium)
                # Add memory-saving options
                browser = await p.chromium.launch(
                    headless=True, 
                    channel='chrome',
                    args=['--disable-dev-shm-usage', '--disable-gpu', '--no-sandbox']
                )
            except Exception as e:
                print(f"Warning: Could not use system Chrome: {e}")
                print("Falling back to bundled Chromium...")
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-dev-shm-usage', '--disable-gpu', '--no-sandbox']
                )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                storage_state=SESSION_FILE,
                viewport={'width': 1920, 'height': 1080}
            )
            browsers.append(browser)
            contexts.append(context)
        
        print(f"✓ {len(browsers)} browsers ready\n")
        
        # Distribute URLs across browsers
        urls_per_browser = len(urls) // CONCURRENT_BROWSERS
        remainder = len(urls) % CONCURRENT_BROWSERS
        
        tasks = []
        start_idx = 0
        
        for i in range(CONCURRENT_BROWSERS):
            # Distribute remainder URLs to first browsers
            count = urls_per_browser + (1 if i < remainder else 0)
            browser_urls = urls[start_idx:start_idx + count]
            
            if browser_urls:
                task = scrape_urls_batch(contexts[i], browser_urls, start_idx, len(urls), i)
                tasks.append(task)
                start_idx += count
        
        # Run all tasks concurrently
        print(f"Scraping {len(urls)} URLs with {len(tasks)} concurrent browsers...\n")
        print("="*80, flush=True)
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for i, batch in enumerate(batch_results):
            if isinstance(batch, Exception):
                print(f"✗ ERROR in batch {i+1}: {batch}", flush=True)
                import traceback
                traceback.print_exc()
            else:
                all_results.extend(batch)
                print(f"✓ Batch {i+1} completed: {len(batch)} results", flush=True)
        
        print("="*80, flush=True)
        print(f"Total results collected: {len(all_results)}", flush=True)
        
        # Close browsers
        for browser in browsers:
            await browser.close()
    
    return all_results


def load_checkpoint():
    """Load checkpoint data if it exists."""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {'processed_urls': [], 'results': []}


def save_checkpoint(processed_urls, results):
    """Save checkpoint data."""
    checkpoint_data = {
        'processed_urls': processed_urls,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)


def process_excel_files():
    """Process all Excel files and scrape URLs."""
    excel_files = ['Accord.xlsx', 'Altima.xlsx', 'Camry.xlsx', 'impreza.xlsx', 'Mazda3.xlsx']
    all_urls = []
    url_to_source = {}
    
    print("Reading Excel files...")
    for excel_file in excel_files:
        file_path = Path(excel_file)
        if not file_path.exists():
            print(f"Warning: {excel_file} not found, skipping...")
            continue
        
        try:
            df = pd.read_excel(excel_file)
            
            if 'Car URL' not in df.columns:
                print(f"Warning: 'Car URL' column not found in {excel_file}, skipping...")
                continue
            
            urls = df['Car URL'].dropna().unique().tolist()
            print(f"  {excel_file}: {len(urls)} unique URLs")
            
            for url in urls:
                all_urls.append(url)
                url_to_source[url] = excel_file
            
        except Exception as e:
            print(f"Error processing {excel_file}: {e}")
            continue
    
    print(f"\nTotal unique URLs to scrape: {len(all_urls)}\n")
    return all_urls, url_to_source


async def main():
    """Main function to run the full scraper."""
    print("="*80)
    print("TRUECAR FULL SCRAPER")
    print("="*80)
    print(f"Concurrent browsers: {CONCURRENT_BROWSERS}")
    print(f"Rate limiting: {DELAY_BETWEEN_REQUESTS}s between requests")
    print(f"Checkpoint interval: Every {CHECKPOINT_INTERVAL} URLs")
    print("="*80 + "\n")
    
    # Check for session file
    if not Path(SESSION_FILE).exists():
        print(f"ERROR: Session file {SESSION_FILE} not found!")
        print("Please run: python3 simple_login.py")
        print("Then log in to TrueCar manually and save your session.")
        return
    
    # Process Excel files
    all_urls, url_to_source = process_excel_files()
    
    if not all_urls:
        print("No URLs to scrape!")
        return
    
    # Load checkpoint if exists
    checkpoint = load_checkpoint()
    processed_urls = set(checkpoint.get('processed_urls', []))
    
    # Filter out already processed URLs
    urls_to_scrape = [url for url in all_urls if url not in processed_urls]
    
    if processed_urls:
        print(f"Found checkpoint: {len(processed_urls)} URLs already processed")
        print(f"Remaining URLs to scrape: {len(urls_to_scrape)}\n")
    
    if not urls_to_scrape:
        print("All URLs already processed!")
        all_results = checkpoint.get('results', [])
    else:
        # Scrape URLs
        start_time = datetime.now()
        results = await scrape_all_urls(urls_to_scrape, url_to_source)
        
        if not results:
            print("ERROR: No results returned from scraping!")
            return
        
        # Combine with checkpoint results
        all_results = checkpoint.get('results', []) + results
        
        # Add source file to all results (if not already set)
        for result in all_results:
            if 'source_file' not in result:
                result['source_file'] = url_to_source.get(result['url'], 'unknown')
        
        elapsed = datetime.now() - start_time
        print(f"\n✓ Scraping completed in {elapsed}", flush=True)
        print(f"  Total results: {len(all_results)}", flush=True)
        
        # Count errors
        errors = sum(1 for r in all_results if r.get('error'))
        if errors > 0:
            print(f"  Errors: {errors}", flush=True)
    
    # Convert to DataFrame
    df_results = pd.DataFrame(all_results)
    
    # Deduplicate
    df_results = deduplicate_results(df_results)
    
    # Reorder columns (important fields first)
    column_order = [
        'make', 'model', 'trim', 'year',
        'dealer_name', 'lease_monthly', 'full_price',
        'vin', 'stock_number',
        'msrp', 'list_price', 'cash_price', 'your_price', 'dealer_discount', 'finance_monthly',
        'exterior_color', 'interior_color', 'mpg',
        'source_file', 'url', 'scrape_timestamp', 'error'
    ]
    
    # Only include columns that exist
    column_order = [col for col in column_order if col in df_results.columns]
    other_cols = [col for col in df_results.columns if col not in column_order]
    df_results = df_results[column_order + other_cols]
    
    # Save to Excel (with proper encoding and formatting)
    print(f"\nSaving results to {OUTPUT_FILE}...", flush=True)
    try:
        # Clean data to prevent formatting issues
        # Replace any problematic characters that might cause Excel issues
        for col in df_results.columns:
            if df_results[col].dtype == 'object':
                # Convert to string, handling NaN values
                df_results[col] = df_results[col].fillna('').astype(str)
                # Remove newlines, tabs, and excessive whitespace
                df_results[col] = df_results[col].str.replace(r'[\n\r\t]+', ' ', regex=True)
                df_results[col] = df_results[col].str.replace(r'\s+', ' ', regex=True)
                df_results[col] = df_results[col].str.strip()
                # Replace empty strings with None for cleaner Excel output
                df_results[col] = df_results[col].replace('', None)
        
        # Use openpyxl engine with explicit formatting
        from openpyxl import Workbook
        df_results.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
        print(f"✓ Results saved to {OUTPUT_FILE}", flush=True)
    except Exception as e:
        print(f"✗ Error saving Excel file: {e}", flush=True)
        # Fallback to CSV if Excel fails
        csv_file = OUTPUT_FILE.replace('.xlsx', '.csv')
        df_results.to_csv(csv_file, index=False)
        print(f"✓ Saved to CSV instead: {csv_file}", flush=True)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total records: {len(df_results)}")
    print(f"Records with dealer name: {df_results['dealer_name'].notna().sum()}")
    print(f"Records with lease price: {df_results['lease_monthly'].notna().sum()}")
    print(f"Records with make/model: {((df_results['make'].notna()) & (df_results['model'].notna())).sum()}")
    print(f"Records with errors: {df_results['error'].notna().sum()}")
    
    # Remove checkpoint file after successful completion
    if Path(CHECKPOINT_FILE).exists():
        Path(CHECKPOINT_FILE).unlink()
        print(f"\n✓ Checkpoint file removed (completed successfully)")


if __name__ == '__main__':
    asyncio.run(main())

