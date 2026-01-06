# Product Requirements Document: TrueCar Scraper

## Overview
Scrape car listing data from TrueCar vehicle detail pages. Extract dealer information, vehicle details, and pricing information from multiple Excel files containing TrueCar URLs. Rank dealerships using a composite scoring system based on pricing fairness, Google reviews, distance, and inventory.

## Data Fields to Extract

### Required Fields (Priority 1)
- **Dealer Name**: Name of the dealership (e.g., "Honda of New Rochelle", "White Plains Honda")
  - Extraction uses multi-method approach: DOM selectors, JSON-LD structured data, HTML content patterns, and page text analysis
  - 100% extraction rate achieved
- **Make**: Vehicle make (e.g., Honda, Toyota, Nissan, Mazda, Subaru)
- **Model**: Vehicle model (e.g., Accord, Camry, Altima)
- **Trim**: Trim level/package
- **Full Price**: Complete purchase price of the vehicle
  - Priority order: list_price → cash_price → MSRP → your_price
  - ~99.5% coverage (list_price has highest coverage rate)
- **Lease Monthly Payment**: Monthly lease payment amount
  - Uses 6 extraction methods: DOM selector, pricing radio groups, container search, enhanced text patterns, HTML attributes, and interactive button clicking
  - Extraction rate: ~29.4% (TrueCar limitation - many listings don't display lease prices)
- **URL**: Source URL of the listing (always included)

### Optional Fields (Priority 2)
- VIN (Vehicle Identification Number)
- Stock Number
- Year
- MSRP (Manufacturer's Suggested Retail Price)
- List Price (primary source for full_price)
- Cash Price
- Your Price
- Dealer Discount
- Finance Monthly Payment
- Exterior Color
- Interior Color
- MPG (Miles Per Gallon)

## Input Format
- 5 Excel files (`.xlsx`): Accord.xlsx, Altima.xlsx, Camry.xlsx, impreza.xlsx, Mazda3.xlsx
- Each file contains a "Car URL" column with TrueCar listing URLs
- URLs point to individual vehicle detail pages

## Output Format
- Single Excel file: `scraped_car_data.xlsx`
- One row per unique vehicle listing
- Columns ordered by priority (key fields first)
- Data cleaned (no newlines, tabs, or excessive whitespace)

## Functional Requirements

### Authentication
- TrueCar requires login to access dealer names
- Solution: Manual login once, save session state (`truecar_session.json`)
- Scraper loads saved session for all requests

### Data Extraction
- Extract all specified fields from each URL
- Handle missing/optional fields gracefully
- Extract full price using priority fallback (list_price → cash_price → MSRP → your_price)
- Extract lease price using multi-method approach (6 different extraction strategies)

### Deduplication
- Remove duplicate vehicle listings
- Primary key: VIN (if available)
- Fallback: Make + Model + Trim + Year + Stock Number + Dealer Name
- Keep first occurrence of duplicates

### Error Handling
- Continue processing if individual URL fails
- Log error message in "error" column
- Save progress periodically (every 10 URLs) for resume capability

## Technical Requirements

### Scraping Framework
- Use Playwright with system Chrome browser (more stable than bundled Chromium)
- Handle JavaScript-rendered content with `domcontentloaded` wait strategy
- Support authentication/login via saved session state (TrueCar requires login to see dealer names)
- Session management: Save/load cookies using Playwright's `storage_state`

### Concurrency
- Use 2 concurrent browser instances (optimized for memory)
- Rate limiting: 2.0 seconds delay between requests
- Memory optimization: Create new page per URL, periodic garbage collection

### Error Handling
- On error, log error message in the spreadsheet
- Continue processing remaining URLs
- Save progress periodically (checkpoint every 10 URLs)
- Graceful error handling with try-except blocks

### Data Storage
- Output: Single Excel file (`.xlsx`)
- Deduplication: Remove duplicate entries
  - Primary: VIN (if available)
  - Fallback: Make + Model + Trim + Year + Stock Number + Dealer Name
- Column ordering: Important fields first (make, model, trim, year, dealer_name, lease_monthly, full_price, URL)
- Data cleaning: Remove newlines, tabs, excessive whitespace from all string fields

## Non-Functional Requirements

### Performance
- Process 417 URLs efficiently with concurrent scraping
- Estimated time: 7-10 minutes for full batch
- Checkpoint system allows resuming if interrupted

### Reliability
- Handle network timeouts (120 second timeout)
- Handle page load issues (domcontentloaded strategy)
- Memory management to prevent unbounded heap growth

### Data Quality
- 100% extraction rate for dealer names, make, model
- ~99.5% extraction rate for full prices
- ~29.4% extraction rate for lease prices (TrueCar limitation)
- 0% error rate in production runs

## Implementation Details

### Dealer Name Extraction
- **Method 1**: DOM selector `div[data-test="vdpDealerHeader"]` → first span
- **Method 2**: JSON-LD structured data (script[type="application/ld+json"])
- **Method 3**: HTML content patterns (dealershipName, dealerName, sellerName in JSON)
- **Method 4**: Brand + Location patterns ("[Brand] of [Location]", "[Location] [Brand]")
- **Method 5**: Contextual extraction near location/address patterns

### Lease Price Extraction
- **Method 1**: DOM selector `span[data-test="pricingSectionRadioGroupPrice"][data-test-item="lease"]`
- **Method 2**: All pricing radio group elements, find by data-test-item="lease"
- **Method 3**: Pricing containers search for "Lease" text with price nearby
- **Method 4**: Enhanced text patterns (multiple regex patterns with broader context)
- **Method 5**: HTML data attributes (data-lease, data-monthly)
- **Method 6**: Interactive button/tab clicking to reveal lease prices

### Full Price Extraction
- Priority order ensures best coverage:
  1. List Price (99.5% coverage)
  2. Cash Price (29.9% coverage)
  3. MSRP (97.0% coverage)
  4. Your Price (fallback)

## Known Limitations

### Lease Price Coverage
- Only ~29.4% of listings have lease prices available
- Reason: TrueCar doesn't display lease prices on all dealer pages
- Different dealers use different page structures
- Some listings may require user interaction not reliably automatable

### Dealer-Specific Variations
- Different dealers use different page layouts
- Some dealers don't display lease pricing at all
- Extraction methods handle most variations but cannot extract what isn't displayed

## Status

### Completed Features
✅ Manual login with session state saving
✅ Multi-method dealer name extraction (100% success rate)
✅ Full price extraction with priority fallback (~99.5% success rate)
✅ Improved lease price extraction with 6 methods (~29.4% success rate)
✅ Concurrent scraping with 2 browsers
✅ Rate limiting and memory optimization
✅ Deduplication (VIN-based with fallback)
✅ Checkpoint/resume capability
✅ Error handling and logging
✅ Data cleaning for Excel output
✅ Comprehensive test scripts and verification tools
✅ Dealer ranking system with composite scoring (pricing fairness, Google reviews, distance, inventory)

### Production Metrics
- Total URLs processed: 417
- Dealer name extraction: 100%
- Make/Model extraction: 100%
- Full price extraction: ~99.5%
- Lease price extraction: ~29.4% (TrueCar limitation)
- Error rate: 0%

## Files

### Main Scripts
- `full_scraper.py`: Main scraper script with all improvements
- `simple_login.py`: Manual login script to save session state
- `rank_dealers.py`: Dealer ranking script with composite scoring

### Test Scripts
- `test_key_fields.py`: Test key field extraction
- `test_optimized_scraper.py`: Test optimized extraction logic
- `verify_results.py`: Verify and analyze scraped results
- `monitor_scraper.py`: Monitor scraper progress

### Configuration
- `truecar_session.json`: Saved authentication session (created by simple_login.py)

### Output
- `scraped_car_data.xlsx`: Final output file with all scraped data
- `scraping_checkpoint.json`: Checkpoint file (removed after completion)

## Dealer Ranking System

### Overview
After scraping is complete, dealers are ranked using a composite scoring system that evaluates:
- **Pricing Fairness** (35% weight): How fairly dealers price vehicles relative to market median
- **Google Reviews** (35% weight): Star rating and review volume
- **Distance/Proximity** (25% weight): Driving time from White Plains, NY
- **Inventory** (5% weight): Number of listings

### Ranking Process

#### Step 1: Data Loading and Normalization
- Reads `scraped_car_data.xlsx`
- Normalizes column names (fuzzy matching)
- Creates `spec_key` for identical vehicle configurations: `year|make|model|trim`
- Filters rows with complete required data (dealer_name, price, year, make, model)

#### Step 2: Pricing Fairness Calculation
- Computes median price per spec (year|make|model|trim)
- Calculates relative percentage vs median for each listing: `(price - median) / median`
- Aggregates per dealer:
  - `median_rel_pct`: Median relative price difference
  - `pct_below_median`: % of listings priced below median
  - `pct_within_1pct`: % of listings within 1% of median
- Converts to 0-100 fairness score:
  - Clamps `median_rel_pct` to [-10%, +10%]
  - Maps: -10% → 100, 0% → 50, +10% → 0
  - Applies small-sample penalty: <3 listings (×0.8), <5 listings (×0.9)

#### Step 3 & 4: Google Reviews, Addresses, and Distances
- For each dealer, fetches:
  - Official address (via Google search)
  - Google star rating
  - Google review count
  - Driving distance and time from White Plains, NY 10601
- **Exclusions**:
  - Always excludes: `229 N Franklin St, Hempstead, NY 11550`
  - Excludes dealers >30 minutes driving time (strict cutoff)
- Uses caching (`dealer_info_cache.json`) to avoid re-fetching
- Reviews score calculation:
  - `rating_score`: (rating - 3.0) / (5.0 - 3.0) × 100 (clamped 0-100)
  - `volume_score`: log10 scaling from 50 to 5000 reviews (clamped 0-100)
  - `reviews_score`: 0.7 × rating_score + 0.3 × volume_score
  - Penalty: If review_count < 50, multiply by 0.6

#### Step 5: Inventory Score
- Normalizes number of listings to 0-100 scale (min-max scaling)
- Rewards dealers with more inventory

#### Step 6: Composite Ranking
- Weighted combination:
  - Reviews: 35%
  - Fairness: 35%
  - Proximity: 25%
  - Inventory: 5%
- Tie-breakers (in order):
  1. Higher reviews_score
  2. Lower median_rel_pct (more below market)
  3. More listings

#### Step 7: Output
- **Ranked table** (`ranked_dealers.xlsx`) with all dealers:
  - rank, dealer_name, address, driving_time_minutes, distance_miles
  - google_rating, google_review_count, listings, unique_specs
  - median_rel_pct, pct_below_median, fairness_score
  - reviews_score, proximity_score, inventory_score, composite_score
- **Top 5 dealers** with detailed summaries and "why these 5" explanations

### Ranking Script
- `rank_dealers.py`: Main ranking script
- `RANKING_README.md`: Detailed documentation
- `dealer_info_cache.json`: Cached dealer info (address, reviews, distance)

## Usage

1. **Save session**: Run `python3 simple_login.py` and manually log in to TrueCar
2. **Run scraper**: Run `python3 full_scraper.py`
3. **Monitor progress**: Run `python3 monitor_scraper.py`
4. **Verify results**: Run `python3 verify_results.py`
5. **Rank dealers**: Run `python3 rank_dealers.py` (requires `scraped_car_data.xlsx`)
6. **Check output**: Open `scraped_car_data.xlsx` and `ranked_dealers.xlsx`
