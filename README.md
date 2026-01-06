# TrueCar Scraper & Dealer Ranking System

A comprehensive web scraping and ranking system for TrueCar vehicle listings with intelligent dealer evaluation based on pricing fairness, Google reviews, distance, and inventory.

## Features

### 🚗 Web Scraping
- **TrueCar Listings Scraper**: Extracts vehicle and dealer information from TrueCar detail pages
- **Multi-method Extraction**: 100% dealer name extraction using DOM selectors, JSON-LD, and pattern matching
- **Price Extraction**: Full price extraction with priority fallback (list_price → cash_price → MSRP)
- **Lease Price Extraction**: 6-method approach for maximum coverage
- **Session Management**: Persistent authentication using Playwright session state

### 📊 Dealer Ranking
- **Composite Scoring System**: Ranks dealers using weighted factors:
  - Pricing Fairness (35%): Compares dealer prices to market median
  - Google Reviews (35%): Star ratings and review volume
  - Distance/Proximity (25%): Driving time from White Plains, NY
  - Inventory (5%): Number of listings
- **Distance Filtering**: 30-minute driving time cutoff
- **Address & Review Lookup**: Automated Google Maps/Search integration

## Quick Start

### Prerequisites
- Python 3.9+
- Playwright
- Chrome browser (system installation)

### Installation
```bash
# Install dependencies
pip install pandas openpyxl playwright numpy

# Install Playwright browsers
playwright install chromium
```

### Usage

1. **Save TrueCar Session** (one-time setup):
   ```bash
   python3 simple_login.py
   # Manually log in to TrueCar in the browser window
   ```

2. **Run Scraper**:
   ```bash
   python3 full_scraper.py
   ```

3. **Rank Dealers**:
   ```bash
   python3 rank_dealers.py
   ```

4. **Check Results**:
   - `scraped_car_data.xlsx`: All scraped vehicle data
   - `ranked_dealers.xlsx`: Ranked dealer table with scores

## Project Structure

### Main Scripts
- `full_scraper.py`: Main scraper with all improvements
- `simple_login.py`: Manual login to save session state
- `rank_dealers.py`: Dealer ranking with composite scoring
- `monitor_scraper.py`: Monitor scraper progress
- `verify_results.py`: Verify and analyze scraped results

### Documentation
- `PRD.md`: Product Requirements Document
- `RANKING_README.md`: Detailed ranking system documentation
- `DATA_QUALITY_REPORT.md`: Data quality analysis
- `QUICK_START.md`: Quick start guide

## Data Extraction

### Extracted Fields
- **Required**: Dealer Name, Make, Model, Trim, Year, Full Price, Lease Monthly Payment, URL
- **Optional**: VIN, Stock Number, MSRP, List Price, Cash Price, Exterior/Interior Color, MPG

### Extraction Methods
- **Dealer Name**: 5-method approach (DOM selectors, JSON-LD, HTML patterns, brand+location, contextual)
- **Full Price**: Priority fallback system (99.5% coverage)
- **Lease Price**: 6-method approach (29.4% coverage - TrueCar limitation)

## Ranking System

### Scoring Formula
```
composite_score = 0.35 × reviews_score 
                + 0.35 × fairness_score 
                + 0.25 × proximity_score 
                + 0.05 × inventory_score
```

### Fairness Calculation
- Computes median price per vehicle spec (year|make|model|trim)
- Calculates relative percentage vs median for each listing
- Scores dealers based on pricing below/above market median

### Distance Calculation
- Driving distance and time from White Plains, NY 10601
- 30-minute strict cutoff
- Proximity score: 0-100 based on driving time

## Performance

- **Scraping**: 417 URLs processed in ~7-10 minutes
- **Dealer Name Extraction**: 100% success rate
- **Full Price Extraction**: ~99.5% coverage
- **Lease Price Extraction**: ~29.4% coverage (TrueCar limitation)
- **Error Rate**: 0%

## Output Files

- `scraped_car_data.xlsx`: Complete scraped vehicle data
- `ranked_dealers.xlsx`: Ranked dealer table with all scores
- `dealer_info_cache.json`: Cached dealer info (addresses, reviews, distances)

## Configuration

- **Concurrent Browsers**: 2 (optimized for memory)
- **Rate Limiting**: 2.0 seconds between requests
- **Timeout**: 120 seconds per page
- **Checkpoint**: Saves progress every 10 URLs

## Known Limitations

- **Lease Price Coverage**: Only ~29.4% of listings display lease prices (TrueCar limitation)
- **Address Extraction**: 37.5% coverage (Google Maps extraction limitations)
- **Review Counts**: 20.8% coverage (Google search extraction limitations)

## License

This project is for personal/educational use. Please respect TrueCar's terms of service and rate limits.

## Author

Akibalogh

## Repository

https://github.com/Akibalogh/car-search
