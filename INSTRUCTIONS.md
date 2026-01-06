# Instructions for Manual Login

Since TrueCar's login form is dynamically loaded, we'll use a manual login approach:

## Step 1: Save Your Login Session

Run this command in your terminal:

```bash
python3 scraper_with_manual_login.py --login
```

**What will happen:**
1. A browser window will open (Chrome/Chromium)
2. You'll see TrueCar's homepage
3. **You manually log in** using your credentials:
   - Email: akibalogh@gmail.com
   - Password: wtw-MWA@avf3khk.zpk
4. Once you're logged in, **press ENTER** in the terminal
5. Your session will be saved to `truecar_session.json`

**Important:** Don't close the browser window until you've pressed ENTER and see the "Session saved" message.

## Step 2: Test Scraping (After Session is Saved)

Once your session is saved, you can test scraping a single URL:

```bash
python3 scraper_with_manual_login.py
```

This will:
- Load your saved session
- Scrape one test URL
- Save results to `test_scrape_result.xlsx`
- Show you the extracted data

## Next Steps

After we verify the test works, I'll create the full scraper that:
- Uses your saved session
- Processes all 417 URLs from the 5 Excel files
- Handles concurrent scraping (3-5 browsers)
- Deduplicates results
- Saves progress periodically
- Outputs final consolidated Excel file

