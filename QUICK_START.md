# Quick Start Guide

## For Google Colab (Recommended)

### Step 1: Upload Files to Colab

1. Go to https://colab.research.google.com/
2. Create new notebook
3. Upload these files:
   - `full_scraper.py`
   - `simple_login.py` (if you need to create new session)
   - `truecar_session.json` (your saved session)
   - All 5 Excel files: `Accord.xlsx`, `Altima.xlsx`, `Camry.xlsx`, `impreza.xlsx`, `Mazda3.xlsx`

### Step 2: Install Dependencies

```python
!pip install playwright pandas openpyxl
!playwright install chromium
```

### Step 3: Run the Scraper

```python
!python full_scraper.py
```

That's it! The scraper will:
- Process all 417 URLs from the 5 Excel files
- Use 3 concurrent browsers for faster scraping
- Save progress periodically
- Deduplicate results
- Generate `scraped_car_data.xlsx` with all results

## For Local (Once Browser Works)

### Step 1: Ensure Session Exists

```bash
# If you don't have a session file yet
python3 simple_login.py
# Log in manually, press ENTER to save
```

### Step 2: Run Full Scraper

```bash
python3 full_scraper.py
```

## What the Full Scraper Does

1. **Reads all 5 Excel files** (417 URLs total)
2. **Uses saved session** for authentication
3. **Scrapes concurrently** with 3 browsers
4. **Saves progress** every 10 URLs (checkpoint)
5. **Deduplicates** results (VIN-first, then other factors)
6. **Generates Excel file** with all data

## Output File: `scraped_car_data.xlsx`

Columns (in order of importance):
- `make`, `model`, `trim`, `year`
- `dealer_name`, `dealer_address`, `lease_monthly` ⭐ (primary requirements)
- `vin`, `stock_number`
- `msrp`, `list_price`, `dealer_discount`, `cash_price`, `finance_monthly`
- `exterior_color`, `interior_color`, `mpg`
- `source_file`, `url`, `scrape_timestamp`, `error`

## Estimated Runtime

- **417 URLs** with 1.5s delay: ~10-15 minutes
- **With 3 concurrent browsers**: ~3-5 minutes
- Plus time for data processing and Excel writing

## Configuration

Edit `full_scraper.py` to change:
- `CONCURRENT_BROWSERS = 3` (1-5 recommended)
- `DELAY_BETWEEN_REQUESTS = 1.5` (seconds)
- `CHECKPOINT_INTERVAL = 10` (save every N URLs)

## Troubleshooting

### Session File Not Found
- Run `python3 simple_login.py` first
- Make sure `truecar_session.json` exists

### Browser Issues
- Use Google Colab (recommended)
- Or try different machine

### Partial Results
- Checkpoint file (`scraping_checkpoint.json`) saves progress
- Resume by running again (will skip processed URLs)
- Delete checkpoint file to restart from beginning

## Success Criteria

✅ All 5 Excel files processed
✅ Dealer name and address extracted (requires login)
✅ Lease pricing captured
✅ No duplicate vehicles
✅ Excel file with all required columns

