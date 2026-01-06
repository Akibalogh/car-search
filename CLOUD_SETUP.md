# Cloud Setup Guide - Google Colab (Recommended)

This guide will help you run the TrueCar scraper on Google Colab (free cloud service) where browser automation works reliably.

## Why Google Colab?

- ✅ **Free** - No credit card required
- ✅ **Browser Automation Works** - Playwright/Selenium work reliably
- ✅ **Easy Setup** - Just upload files and run
- ✅ **No Local Issues** - Avoids browser compatibility problems

## Step-by-Step Setup

### 1. Prepare Your Files

You'll need these files ready to upload:
- `simple_login.py` (optional - can login in Colab)
- `scraper_with_manual_login.py`
- `truecar_session.json` (your saved session)
- Input Excel files (Accord.xlsx, Altima.xlsx, Camry.xlsx, impreza.xlsx, Mazda3.xlsx)

### 2. Create a New Colab Notebook

1. Go to https://colab.research.google.com/
2. Click "New Notebook"
3. Name it "TrueCar Scraper"

### 3. Upload Files to Colab

```python
# Run this in a Colab cell to upload files
from google.colab import files
uploaded = files.upload()
```

Upload:
- `truecar_session.json`
- `Accord.xlsx`, `Altima.xlsx`, `Camry.xlsx`, `impreza.xlsx`, `Mazda3.xlsx`
- `scraper_with_manual_login.py`

### 4. Install Dependencies

Create a new cell and run:

```python
!pip install playwright pandas openpyxl
!playwright install chromium
```

### 5. Login to TrueCar (If Needed)

If your session file doesn't work or expires, you can login in Colab:

**Option A: Use Existing Session File**
- Just make sure `truecar_session.json` is uploaded

**Option B: Create New Session in Colab**
- Use `simple_login.py` but note that Colab doesn't have a display, so you'd need to adapt it

### 6. Test Single URL

Create a new cell with:

```python
# Test scraper on one URL
exec(open('scraper_with_manual_login.py').read())
```

Or run it as a Python script:
```python
import subprocess
subprocess.run(['python3', 'scraper_with_manual_login.py'])
```

### 7. Run Full Scraper (Once Single URL Works)

You'll need to create the full scraper script that:
- Processes all 5 Excel files
- Handles concurrent scraping
- Saves progress periodically
- Generates final output

## Alternative: GitHub Codespaces

### Setup Codespaces

1. Create a GitHub repository
2. Upload your code files
3. Go to repository → Code → Codespaces → Create codespace
4. Free tier: 60 hours/month

### In Codespaces Terminal

```bash
# Install dependencies
pip install playwright pandas openpyxl
playwright install chromium

# Run scraper
python3 scraper_with_manual_login.py
```

**Advantage:** Full VS Code environment, can save session files easily

## Alternative: Replit

### Setup Replit

1. Go to https://replit.com/
2. Create new Repl (Python)
3. Upload files via file explorer
4. Install packages in Shell:
   ```bash
   pip install playwright pandas openpyxl
   playwright install chromium
   ```

**Note:** Replit may have resource limits, but should work for testing

## Recommended Approach

**For Now (Testing):**
- Use Google Colab for single URL test
- Verify scraper logic works
- Debug any extraction issues

**For Production (All 417 URLs):**
- Use GitHub Codespaces (full environment, can run longer)
- Or use a small cloud VM (AWS/GCP free tier)
- Or run on a different local machine

## Notes

- **Session File**: Your `truecar_session.json` should work in cloud (cookies are portable)
- **Browser Automation**: Works much better in cloud environments
- **Long Running**: For 417 URLs, expect 10-30 minutes depending on rate limiting
- **Progress Saving**: Make sure to save progress periodically in case of timeout

## Expected Runtime

- Single URL: ~5-10 seconds
- 417 URLs with 1.5s delay: ~10-15 minutes
- With 3-5 concurrent browsers: ~3-5 minutes
- Plus time for data extraction and Excel writing

