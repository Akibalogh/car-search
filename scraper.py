#!/usr/bin/env python3
"""
TrueCar scraper to extract dealer and vehicle information from car listing pages.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse
import sys
from pathlib import Path

# Rate limiting - be respectful to the server
DELAY_BETWEEN_REQUESTS = 1  # seconds

def extract_text_by_label(soup, label_text):
    """Extract text value following a label in the HTML."""
    # Try to find the label and get the next text node or sibling
    labels = soup.find_all(text=re.compile(re.escape(label_text), re.I))
    for label in labels:
        parent = label.parent
        if parent:
            # Try next sibling
            next_elem = parent.find_next_sibling()
            if next_elem:
                text = next_elem.get_text(strip=True)
                if text:
                    return text
            # Try within the same parent
            text = parent.get_text(strip=True)
            # Remove the label text to get the value
            value = text.replace(label_text, '').strip(':').strip()
            if value and value != label_text:
                return value
    return None

def extract_dealer_info(soup):
    """Extract dealer name and address from the page."""
    dealer_name = None
    dealer_address = None
    
    page_text = soup.get_text()
    
    # Strategy 1: Look for dealer name pattern in entire text (e.g., "White Plains Honda")
    # Pattern: Location + Brand name (e.g., "White Plains Honda")
    dealer_name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Honda|Toyota|Nissan|Mazda|Subaru|Ford|Chevrolet|Hyundai|Kia|BMW|Mercedes|Audi|Lexus|Acura|Infiniti|Volvo|Jeep|Ram|Dodge|Chrysler|Buick|Cadillac|GMC|Lincoln|Genesis))'
    
    # Try to find dealer name in text - look for patterns
    dealer_name_matches = re.findall(dealer_name_pattern, page_text)
    if dealer_name_matches:
        # Filter out generic or invalid matches
        for match in dealer_name_matches:
            # Skip if it contains vehicle model names
            if any(x in match.lower() for x in ['accord', 'camry', 'altima', 'mazda3', 'impreza', 'civic', 'cr-v']):
                continue
            # Skip if it's too short or too long
            if len(match) < 8 or len(match) > 100:
                continue
            # Skip common prefixes
            if match.startswith(('Your Local ', 'Local ', 'New ', 'Used ', 'CPO ')):
                match = match.replace('Your Local ', '').replace('Local ', '').replace('New ', '').replace('Used ', '').replace('CPO ', '')
            dealer_name = match.strip()
            break
    
    # Strategy 2: Try to find address pattern first, then look for dealer name before it
    address_patterns = [
        r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)',
        r'(\d+\s+[A-Za-z0-9\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy),\s*[A-Za-z\s]+,\s*[A-Z]{2})',
    ]
    
    # Find address
    for pattern in address_patterns:
        match = re.search(pattern, page_text)
        if match:
            dealer_address = match.group(1).strip()
            break
    
    # Strategy 3: If dealer name not found yet, look for it near the address
    if not dealer_name and dealer_address:
        addr_idx = page_text.find(dealer_address)
        if addr_idx > 0:
            # Look in text before address
            preceding_text = page_text[max(0, addr_idx-500):addr_idx]
            name_match = re.search(dealer_name_pattern, preceding_text)
            if name_match:
                potential_name = name_match.group(1).strip()
                # Skip if it contains vehicle model names
                if not any(x in potential_name.lower() for x in ['accord', 'camry', 'altima', 'mazda3', 'impreza']):
                    if 8 <= len(potential_name) <= 100:
                        # Remove common prefixes
                        for prefix in ['Your Local ', 'Local ', 'New ', 'Used ', 'CPO ']:
                            if potential_name.startswith(prefix):
                                potential_name = potential_name[len(prefix):]
                        dealer_name = potential_name.strip()
    
    # Clean up dealer name if found
    if dealer_name:
        dealer_name = dealer_name.strip()
        # Remove common prefixes/suffixes
        dealer_name = re.sub(r'^(New|Used|CPO|Your Local|Local)\s+', '', dealer_name, flags=re.I)
        dealer_name = dealer_name.strip()
    
    return dealer_name, dealer_address

def extract_vehicle_details(soup):
    """Extract vehicle details from the page."""
    details = {
        'year': None,
        'make': None,
        'model': None,
        'trim': None,
        'exterior_color': None,
        'interior_color': None,
        'mpg': None,
        'transmission': None,
        'drivetrain': None,
        'engine': None,
        'fuel_type': None,
        'vin': None,
        'stock_number': None,
        'location': None,
        'msrp': None,
        'list_price': None,
        'dealer_discount': None,
        'your_price': None,
        'cash_price': None,
        'lease_monthly': None,
        'finance_monthly': None,
    }
    
    page_text = soup.get_text()
    
    # Extract VIN
    vin_pattern = r'\b([A-HJ-NPR-Z0-9]{17})\b'
    vin_match = re.search(vin_pattern, page_text)
    if vin_match:
        details['vin'] = vin_match.group(1)
    
    # Extract Stock Number
    stock_patterns = [
        r'Stock\s+([A-Z0-9]+)(?:\s|Listed|$)',
        r'Stock\s+Number[:\s]+([A-Z0-9]+)',
        r'Stock\s+([A-Z0-9]+)Listed',
    ]
    for pattern in stock_patterns:
        match = re.search(pattern, page_text, re.I)
        if match:
            stock = match.group(1).strip()
            # Remove trailing digits that might be part of "Listed" or other text
            stock = re.sub(r'\d+$', '', stock) if stock and stock[-1].isdigit() else stock
            details['stock_number'] = stock
            break
    
    # Extract year, make, model, trim from title or headings
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text()
        # Pattern: "New 2025 Honda Accord SE" or "2025 Honda Accord SE"
        vehicle_match = re.search(r'(?:New\s+)?(\d{4})\s+(Honda|Toyota|Nissan|Mazda|Subaru)\s+(\w+)\s+(.+?)(?:\s*[-|]|For Sale|$)', title_text)
        if vehicle_match:
            details['year'] = vehicle_match.group(1)
            details['make'] = vehicle_match.group(2)
            details['model'] = vehicle_match.group(3)
            trim_text = vehicle_match.group(4).strip()
            # Clean up trim - remove "For Sale" and other common suffixes
            trim_text = re.sub(r'\s+For Sale.*$', '', trim_text, flags=re.I)
            details['trim'] = trim_text.strip()
    
    # Extract colors
    exterior_match = re.search(r'Exterior\s+color[:\s]+([^\n]+)', page_text, re.I)
    if exterior_match:
        details['exterior_color'] = exterior_match.group(1).strip()
    
    interior_match = re.search(r'Interior\s+color[:\s]+([^\n]+)', page_text, re.I)
    if interior_match:
        details['interior_color'] = interior_match.group(1).strip()
    
    # Extract MPG - try multiple patterns
    mpg_patterns = [
        r'MPG[:\s]+(\d+)\s*city\s*/\s*(\d+)\s*highway',
        r'(\d+)\s*city\s*/\s*(\d+)\s*highway',
    ]
    for pattern in mpg_patterns:
        mpg_match = re.search(pattern, page_text, re.I)
        if mpg_match:
            details['mpg'] = f"{mpg_match.group(1)} city / {mpg_match.group(2)} highway"
            break
    
    # Extract Transmission
    trans_match = re.search(r'Transmission[:\s]+([^\n]+)', page_text, re.I)
    if trans_match:
        details['transmission'] = trans_match.group(1).strip()
    
    # Extract Drivetrain
    drive_match = re.search(r'Drivetrain[:\s]+([^\n]+)', page_text, re.I)
    if drive_match:
        details['drivetrain'] = drive_match.group(1).strip()
    
    # Extract Engine
    engine_match = re.search(r'Engine[:\s]+([^\n]+)', page_text, re.I)
    if engine_match:
        details['engine'] = engine_match.group(1).strip()
    
    # Extract Fuel Type
    fuel_match = re.search(r'Fuel\s+type[:\s]+([^\n]+)', page_text, re.I)
    if fuel_match:
        details['fuel_type'] = fuel_match.group(1).strip()
    
    # Extract Location
    location_match = re.search(r'Location[:\s]+([^\n\(]+)', page_text, re.I)
    if location_match:
        details['location'] = location_match.group(1).strip()
    
    # Extract Pricing
    # MSRP
    msrp_match = re.search(r'MSRP[:\s]+\$([0-9,]+)', page_text, re.I)
    if msrp_match:
        details['msrp'] = msrp_match.group(1).replace(',', '')
    
    # List Price
    list_price_match = re.search(r'List\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
    if list_price_match:
        details['list_price'] = list_price_match.group(1).replace(',', '')
    
    # Dealer Discount
    discount_match = re.search(r'Dealer\s+discount[:\s]+[-\$]?([0-9,]+)', page_text, re.I)
    if discount_match:
        details['dealer_discount'] = discount_match.group(1).replace(',', '')
    
    # Your Price
    your_price_match = re.search(r'Your\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
    if your_price_match:
        details['your_price'] = your_price_match.group(1).replace(',', '')
    
    # Cash Price
    cash_match = re.search(r'Cash\s+price[:\s]+\$([0-9,]+)', page_text, re.I)
    if cash_match:
        details['cash_price'] = cash_match.group(1).replace(',', '')
    
    # Lease Monthly
    lease_match = re.search(r'Lease[:\s]+\$([0-9,]+)/mo', page_text, re.I)
    if lease_match:
        details['lease_monthly'] = lease_match.group(1).replace(',', '')
    
    # Finance Monthly
    finance_match = re.search(r'Finance[:\s]+\$([0-9,]+)/mo', page_text, re.I)
    if finance_match:
        details['finance_monthly'] = finance_match.group(1).replace(',', '')
    
    return details

def extract_dealer_from_json(html_text):
    """Extract dealer info from JSON data embedded in HTML."""
    dealer_name = None
    dealer_address = None
    
    # Look for address1 in JSON
    address_match = re.search(r'\"address1\"\s*:\s*\"([^\"]+)\"', html_text)
    if address_match:
        address1 = address_match.group(1).strip()
        # Look for city and state
        city_match = re.search(r'\"city\"\s*:\s*\"([^\"]+)\"', html_text)
        state_match = re.search(r'\"state\"\s*:\s*\"([^\"]+)\"', html_text)
        zip_match = re.search(r'\"zip\"\s*:\s*\"?([^\",}]+)\"?', html_text)
        
        address_parts = [address1]
        if city_match:
            address_parts.append(city_match.group(1).strip())
        if state_match:
            address_parts.append(state_match.group(1).strip())
        if zip_match:
            address_parts.append(zip_match.group(1).strip())
        
        dealer_address = ', '.join(address_parts)
    
    # Look for dealer name in JSON - try multiple patterns
    name_patterns = [
        r'\"dealershipName\"\s*:\s*\"([^\"]+)\"',
        r'\"name\"\s*:\s*\"([^\"]+)\"\s*[,\}].*?\"address1\"',
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, html_text)
        if name_match:
            potential_name = name_match.group(1).strip()
            # Skip generic names
            if potential_name.lower() not in ['truecar', 'dealer']:
                dealer_name = potential_name
                break
    
    return dealer_name, dealer_address

def scrape_car_page(url):
    """Scrape a single TrueCar page and extract dealer and vehicle information."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        html_text = response.text
        
        # Extract dealer info - try JSON first, then text-based
        dealer_name_json, dealer_address_json = extract_dealer_from_json(html_text)
        dealer_name_text, dealer_address_text = extract_dealer_info(soup)
        
        # Prefer JSON data if available, otherwise use text-based
        dealer_name = dealer_name_json or dealer_name_text
        dealer_address = dealer_address_json or dealer_address_text
        
        # Extract vehicle details
        vehicle_details = extract_vehicle_details(soup)
        
        result = {
            'url': url,
            'dealer_name': dealer_name,
            'dealer_address': dealer_address,
            **vehicle_details
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {
            'url': url,
            'error': str(e)
        }
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return {
            'url': url,
            'error': str(e)
        }

def process_excel_files():
    """Process all Excel files and scrape URLs."""
    excel_files = ['Accord.xlsx', 'Altima.xlsx', 'Camry.xlsx', 'impreza.xlsx', 'Mazda3.xlsx']
    all_results = []
    
    for excel_file in excel_files:
        file_path = Path(excel_file)
        if not file_path.exists():
            print(f"Warning: {excel_file} not found, skipping...")
            continue
        
        print(f"\nProcessing {excel_file}...")
        try:
            df = pd.read_excel(excel_file)
            
            if 'Car URL' not in df.columns:
                print(f"Warning: 'Car URL' column not found in {excel_file}, skipping...")
                continue
            
            urls = df['Car URL'].dropna().unique().tolist()
            print(f"Found {len(urls)} unique URLs in {excel_file}")
            
            for idx, url in enumerate(urls, 1):
                print(f"  Scraping {idx}/{len(urls)}: {url[:80]}...")
                result = scrape_car_page(url)
                result['source_file'] = excel_file
                all_results.append(result)
                
                # Rate limiting
                if idx < len(urls):
                    time.sleep(DELAY_BETWEEN_REQUESTS)
        
        except Exception as e:
            print(f"Error processing {excel_file}: {e}")
            continue
    
    return all_results

def main():
    """Main function to run the scraper."""
    print("Starting TrueCar scraper...")
    
    results = process_excel_files()
    
    if not results:
        print("No results to save.")
        return
    
    # Convert to DataFrame
    df_results = pd.DataFrame(results)
    
    # Save to Excel
    output_file = 'scraped_car_data.xlsx'
    df_results.to_excel(output_file, index=False)
    print(f"\nScraped data saved to {output_file}")
    print(f"Total records: {len(df_results)}")
    
    # Print summary
    print("\nSummary:")
    print(f"  Records with dealer name: {df_results['dealer_name'].notna().sum()}")
    print(f"  Records with dealer address: {df_results['dealer_address'].notna().sum()}")
    print(f"  Records with errors: {df_results.get('error', pd.Series()).notna().sum()}")

if __name__ == '__main__':
    main()

