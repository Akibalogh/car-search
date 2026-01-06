# Dealer Ranking System

## Overview

This script ranks dealerships from the scraped car data using a composite scoring system that considers:
- **Pricing Fairness** (35% weight): How fairly dealers price vehicles relative to market median
- **Google Reviews** (35% weight): Star rating and review volume
- **Distance/Proximity** (25% weight): Driving time from White Plains, NY
- **Inventory** (5% weight): Number of listings

## Requirements

- Python 3.9+
- Required packages:
  ```bash
  pip install pandas openpyxl playwright numpy
  playwright install chromium
  ```

## Input File

- **File**: `scraped_car_data.xlsx`
- **Required columns**: `dealer_name`, `price` (or `full_price`), `year`, `make`, `model`, `trim` (optional)

## Usage

```bash
python3 rank_dealers.py
```

## Process

### Step 1: Load and Normalize Data
- Reads Excel file
- Normalizes column names (fuzzy matching)
- Creates `spec_key` for identical vehicle configurations
- Filters rows with complete required data

### Step 2: Pricing Fairness
- Computes median price per spec (year|make|model|trim)
- Calculates relative percentage vs median for each listing
- Aggregates per dealer:
  - `median_rel_pct`: Median relative price difference
  - `pct_below_median`: % of listings priced below median
  - `pct_within_1pct`: % of listings within 1% of median
- Converts to 0-100 fairness score (lower prices = higher score)
- Applies small-sample penalty for dealers with <5 listings

### Step 3 & 4: Google Reviews, Addresses, and Distances
- For each dealer, fetches:
  - Official address
  - Google star rating
  - Google review count
  - Driving distance and time from White Plains, NY
- **Exclusions**:
  - Always excludes: `229 N Franklin St, Hempstead, NY 11550`
  - Excludes dealers >30 minutes driving time
- Uses caching (`dealer_info_cache.json`) to avoid re-fetching

### Step 5: Inventory Score
- Normalizes number of listings to 0-100 scale
- Rewards dealers with more inventory

### Step 6: Composite Ranking
- Weighted combination:
  - Reviews: 35%
  - Fairness: 35%
  - Proximity: 25%
  - Inventory: 5%
- Tie-breakers: reviews_score, median_rel_pct, listings

### Step 7: Output
- **Ranked table** (`ranked_dealers.xlsx`) with all dealers
- **Top 5 dealers** with detailed summaries
- Includes "why these 5" explanations

## Output Files

- `ranked_dealers.xlsx`: Full ranked table with all scores
- `dealer_info_cache.json`: Cached dealer info (address, reviews, distance)

## Output Columns

- `rank`: Ranking position
- `dealer_name`: Dealer name
- `address`: Dealer address
- `driving_time_minutes`: Driving time from White Plains, NY
- `distance_miles`: Distance in miles
- `google_rating`: Google star rating
- `google_review_count`: Number of Google reviews
- `listings`: Number of listings
- `unique_specs`: Number of unique vehicle specs
- `median_rel_pct`: Median price difference vs market (%)
- `pct_below_median`: % of listings below median
- `fairness_score`: Pricing fairness score (0-100)
- `reviews_score`: Google reviews score (0-100)
- `proximity_score`: Distance score (0-100)
- `inventory_score`: Inventory score (0-100)
- `composite_score`: Final composite score (0-100)

## Notes

- The script uses Playwright to scrape Google search results for dealer info
- Rate limiting: 1 second delay between requests
- Caching prevents re-fetching dealer info on subsequent runs
- Distance cutoff: Strict 30-minute driving time limit
- Missing data: Dealers without Google reviews get reviews_score = 0

## Troubleshooting

- **File not found**: Ensure `scraped_car_data.xlsx` exists in the same directory
- **Missing columns**: Script will attempt fuzzy matching for column names
- **Google search fails**: May need to adjust wait times or search patterns
- **Distance calculation fails**: May need to verify address format or use alternative method

