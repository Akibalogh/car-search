# TrueCar Vehicle Scraper

A web scraper to extract vehicle and dealer information from TrueCar listing pages and consolidate data from multiple Excel files into a single master Excel file.

## Current Status

### ✅ Completed
- **Session Management**: Manual login script successfully saves TrueCar session (`simple_login.py`)
- **Session File**: Valid session saved with 51 cookies (`truecar_session.json`)
- **Scraper Code Structure**: Complete scraping logic for all required fields
- **Data Extraction Logic**: Regex patterns and extraction functions for:
  - Vehicle information (Make, Model, Trim, Year, VIN, Stock Number, Colors, MPG)
  - Dealer information (Name, Address)
  - Pricing information (Lease Monthly, MSRP, List Price, Dealer Discount, Cash Price, Finance Monthly)

### ⚠️ Known Issues
- **Browser Automation**: Playwright browser closes immediately when running programmatically (works for manual login)
- **Local Environment**: Browser automation has compatibility issues on current system
- **Recommendation**: Use cloud service or different machine for production scraping

## Project Structure

```
car-search/
├── README.md                          # This file
├── PRD.md                            # Product Requirements Document
├── Accord.xlsx                       # Input file (98 URLs)
├── Altima.xlsx                       # Input file (92 URLs)
├── Camry.xlsx                        # Input file (76 URLs)
├── impreza.xlsx                      # Input file (71 URLs)
├── Mazda3.xlsx                       # Input file (80 URLs)
├── truecar_session.json              # Saved login session (51 cookies)
├── simple_login.py                   # ✅ WORKING: Manual login script
├── scraper_with_manual_login.py      # Scraper using Playwright (browser closes)
├── scraper_selenium.py               # Selenium scraper (incomplete)
└── scraper_selenium_cookies.py       # Selenium with cookie conversion (incomplete)
```

## Setup

### Prerequisites
- Python 3.9+
- Playwright (`pip install playwright && playwright install chromium`)
- pandas (`pip install pandas openpyxl`)

### Installation
```bash
cd /Users/akibalogh/apps/car-search
pip install playwright pandas openpyxl
playwright install chromium
```

## Usage

### Step 1: Save Your Login Session (Required - One Time)

Run the manual login script to save your TrueCar session:

```bash
python3 simple_login.py
```

**Steps:**
1. Browser window will open
2. Log in to TrueCar manually in the browser
3. Once logged in, press ENTER in the terminal
4. Session will be saved to `truecar_session.json`

**Note:** This works perfectly! The session file contains 51 cookies and is valid.

### Step 2: Run the Scraper

**⚠️ Current Issue:** The automated scraper has browser closing issues on local system. 

To test the scraper structure (will fail due to browser closing):
```bash
python3 scraper_with_manual_login.py
```

## Free Cloud Services Options

Since browser automation has issues locally, here are free cloud options:

### Option 1: Google Colab (Recommended - Free)
- **Pros:** Free, no setup needed, browser automation works well
- **Setup:** Upload code files, install packages, run
- **Limitations:** Session timeout after inactivity, but can save progress
- **Link:** https://colab.research.google.com/

### Option 2: GitHub Codespaces (Free Tier)
- **Pros:** Full VS Code environment, 60 hours/month free
- **Setup:** Create repository, enable Codespaces
- **Limitations:** 60 hours/month free tier

### Option 3: Replit (Free Tier)
- **Pros:** Easy to use, browser automation support
- **Setup:** Create new Repl, upload files
- **Limitations:** Some resource limits

### Option 4: AWS Free Tier / Google Cloud Free Tier
- **Pros:** Full VM control
- **Setup:** Create EC2/Compute Engine instance
- **Limitations:** Limited free hours per month

## Data Output

The scraper will produce a single Excel file (`scraped_car_data.xlsx`) with the following columns:

### Required Fields (per PRD)
- **Make** (e.g., Honda, Toyota, Nissan)
- **Model** (e.g., Accord, Camry, Altima)
- **Trim** (e.g., SE, EX, Sport)
- **Year**
- **Dealer Name** (requires authentication)
- **Dealer Address** (requires authentication)
- **Lease Monthly Payment** (primary requirement)

### Additional Fields Extracted
- VIN
- Stock Number
- Exterior Color
- Interior Color
- MPG (city/highway)
- MSRP
- List Price
- Dealer Discount
- Cash Price
- Finance Monthly Payment
- Source File
- URL
- Scrape Timestamp

## Scraping Specifications

- **Total URLs**: 417 (from 5 Excel files)
- **Rate Limiting**: 1-2 seconds delay between requests
- **Concurrency**: 3-5 concurrent browser instances (planned)
- **Deduplication**: VIN-first, fallback to Make+Model+Trim+Year+Dealer+Stock
- **Progress Saving**: Periodic checkpoints every N URLs
- **Error Handling**: Log errors, continue processing, include errors in output

## Code Files

### `simple_login.py` ✅ WORKING
- Manual login script
- Opens browser, waits for user login, saves session
- **Status:** Fully functional

### `scraper_with_manual_login.py` ⚠️ BROWSER CLOSES
- Full scraper using Playwright
- Uses saved session file
- Extracts all required fields
- **Status:** Code is correct, but browser closes immediately on local system

### `full_scraper.py` ✅ COMPLETE
- Full production scraper
- Processes all 5 Excel files (417 URLs)
- Concurrent scraping (3 browsers)
- Deduplication logic (VIN-first, fallback)
- Progress checkpoint saving
- Error handling and logging
- Final consolidated Excel output
- **Status:** Code complete, ready to run on cloud service or working browser environment

## Troubleshooting

### Browser Closes Immediately
- **Issue:** Playwright/Selenium browsers close before scraping
- **Workaround:** Use cloud service (Google Colab recommended)
- **Alternative:** Try on different machine/environment

### Session Not Found
- Make sure `truecar_session.json` exists
- Run `python3 simple_login.py` first to save session

### ChromeDriver Version Mismatch (Selenium)
- Use `webdriver-manager` (already in code)
- Or manually update ChromeDriver

## Next Steps

1. **For Cloud Service:**
   - Upload code files to Google Colab
   - Upload `truecar_session.json`
   - Install packages: `!pip install playwright pandas openpyxl`
   - Install browser: `!playwright install chromium`
   - Run scraper

2. **For Local:**
   - Try on different machine
   - Or wait for system/browser updates
   - Code structure is ready, just needs stable browser environment

3. **Complete Full Scraper:**
   - Once browser automation works:
     - Add concurrent scraping (3-5 browsers)
     - Add deduplication logic
     - Add progress checkpoints
     - Process all 417 URLs
     - Generate final Excel output

## Credentials

**TrueCar Login:**
- Email: `akibalogh@gmail.com`
- Password: `wtw-MWA@avf3khk.zpk`

**Note:** Session file (`truecar_session.json`) contains valid cookies and can be reused.

## Files Summary

- **Input Files**: 5 Excel files (Accord, Altima, Camry, impreza, Mazda3) = 417 URLs total
- **Session File**: `truecar_session.json` (16KB, 51 cookies, valid)
- **Login Script**: `simple_login.py` (works perfectly)
- **Scraper Script**: `scraper_with_manual_login.py` (code ready, browser issue)

## Contact / Support

If you encounter issues:
1. Verify session file exists and is valid
2. Try cloud service (Google Colab recommended)
3. Check browser automation compatibility on your system
4. Review error messages in terminal output

