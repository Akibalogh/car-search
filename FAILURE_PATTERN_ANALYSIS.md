# Failure Pattern Analysis Guide

## URL Patterns Found in Input Files

Based on analysis of the 417 input URLs:

### Key Observations:
1. **All URLs are `new-cars`** (not `used-cars`)
2. **All URLs have query parameters**: `?buildId=...&paymentPreference=lease&position=...&returnTo=...`
3. **Year distribution**:
   - 2025: 249 URLs (59.7%)
   - 2026: 168 URLs (40.3%)
4. **Make distribution**:
   - Honda (Accord): 98 URLs (23.5%)
   - Nissan (Altima): 92 URLs (22.1%)
   - Mazda (Mazda3): 80 URLs (19.2%)
   - Toyota (Camry): 76 URLs (18.2%)
   - Subaru (Impreza): 71 URLs (17.0%)

### URL Structure:
All URLs follow this pattern:
```
https://www.truecar.com/new-cars-for-sale/listing/{VIN}/{YEAR}-{MAKE}-{MODEL}/?buildId={ID}&paymentPreference=lease&position={N}&returnTo={URL}
```

## Common Failure Patterns to Look For

When analyzing failed URLs, check for these patterns:

### 1. **Error Type Patterns**
- `'NoneType' object is not subscriptable` - Extraction failures (regex didn't match)
- `TimeoutError` - Page load timeout (120s)
- `TargetClosedError` - Browser/page closed unexpectedly
- `NetworkError` - Network connectivity issues
- Authentication errors - Session expired or invalid

### 2. **URL-Specific Patterns**

#### By Make:
- Do certain makes fail more often? (e.g., Honda vs Subaru)
- Are failures evenly distributed across makes?

#### By Year:
- Do 2025 URLs fail more than 2026 URLs?
- Or vice versa?

#### By Query Parameters:
- Do URLs with certain `buildId` values fail?
- Do certain `position` values correlate with failures?

#### By Source File:
- Do URLs from certain Excel files fail more?
  - Accord.xlsx (Honda)
  - Altima.xlsx (Nissan)
  - Camry.xlsx (Toyota)
  - impreza.xlsx (Subaru)
  - Mazda3.xlsx (Mazda)

### 3. **Expected Failure Patterns**

Based on common scraping issues:

1. **Timeouts**: 
   - Slow-loading pages
   - Network issues
   - TrueCar rate limiting
   
2. **Extraction Failures**:
   - Pages with missing data
   - Different page layouts
   - Dynamic content not loaded
   
3. **Session Issues**:
   - Expired session cookies
   - Authentication failures
   - Dealer info not visible (requires login)

## How to Analyze Failures

### Step 1: Run the Analysis Script
Once `scraped_car_data.xlsx` exists, run:
```bash
python3 analyze_failures.py
```

Or use the progress checker:
```bash
python3 check_progress.py
```

### Step 2: Look for Patterns

1. **Check error type distribution**
   - What's the most common error?
   - Is it consistent or varied?

2. **Compare failure rates by category**:
   ```python
   # Example analysis
   - Honda URLs: X failed out of 98 (Y% failure rate)
   - Nissan URLs: X failed out of 92 (Y% failure rate)
   - etc.
   ```

3. **Check for URL-specific issues**:
   - Are failures clustered (same buildId)?
   - Are failures sequential (position 0, 1, 2...)?
   - Are failures by year (all 2025 or all 2026)?

4. **Examine sample failed URLs**:
   - Manually visit failed URLs
   - Check if they load correctly
   - Check if dealer info is visible
   - Check if data structure is different

### Step 3: Identify Root Causes

Common root causes:

1. **Session Expired**
   - Solution: Re-run `simple_login.py` to refresh session
   
2. **Page Load Timeout**
   - Solution: Increase timeout or retry logic
   
3. **Different Page Layout**
   - Solution: Add alternative extraction patterns
   
4. **Rate Limiting**
   - Solution: Increase delay between requests
   
5. **Missing Data on Page**
   - Solution: Handle gracefully, mark as missing data (not error)

## Example Analysis Output

When you run the analysis, you should see something like:

```
=== FAILED URL PATTERN ANALYSIS ===

Total records: 417
Failed: 63 (15.1%)
Success: 354 (84.9%)

ERROR TYPES:
'NoneType' object is not subscriptable: 45
TimeoutError: 12
NetworkError: 6

FAILED URL EXAMPLES (first 20):
1. https://www.truecar.com/new-cars-for-sale/listing/...
2. ...

PATTERN ANALYSIS:
Failed URLs - Make breakdown:
   honda: 18
   nissan: 15
   toyota: 12
   mazda: 10
   subaru: 8

Failure Rate by Make:
   honda: 18/98 (18.4%)
   nissan: 15/92 (16.3%)
   ...
```

## Next Steps After Analysis

1. **If errors are evenly distributed**: Likely systematic issue (timeout, session, etc.)
2. **If errors cluster by make/year**: Likely page structure differences
3. **If errors are specific URLs**: Likely those URLs have issues (removed listings, etc.)
4. **If errors are timeouts**: Increase timeout or reduce concurrency
5. **If errors are extraction failures**: Refine regex patterns or add alternative patterns



