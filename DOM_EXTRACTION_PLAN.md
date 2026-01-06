# DOM-Based Extraction Plan

## Current Approach (Regex on Text)
- Extracts text from `body` element
- Uses regex patterns to find data in text
- Error-prone, fragile to layout changes

## Proposed Approach (DOM Selectors + JSON-LD)
1. **JSON-LD Structured Data** (Most Reliable)
   - Extract `<script type="application/ld+json">` elements
   - Parse JSON-LD structured data
   - Extract dealer, vehicle, and pricing info from structured data

2. **DOM Selectors** (Fallback/Supplement)
   - Use CSS selectors to find specific elements
   - Extract text from targeted elements
   - More reliable than full-text regex

3. **Text/Regex** (Last Resort)
   - Only if DOM/JSON-LD fails
   - Current approach as fallback

## Implementation Strategy

### Step 1: Extract JSON-LD
```python
scripts = await page.locator('script[type="application/ld+json"]').all()
for script in scripts:
    data = json.loads(await script.inner_text())
    # Extract from structured data
```

### Step 2: Use DOM Selectors
- Dealer name: Look for specific heading/div near address
- Address: Look for `<address>` or elements with address-like classes
- Price: Look for price-related elements
- VIN: Look in specific code/pre elements or data attributes

### Step 3: Hybrid Approach
- Try JSON-LD first (most reliable)
- Try DOM selectors second
- Fall back to text/regex only if needed

## Benefits
- More reliable (structured data is standardized)
- Less error-prone (DOM structure is consistent)
- Faster (targeted extraction vs full-text search)
- Better handling of edge cases



