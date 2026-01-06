#!/usr/bin/env python3
"""Check if scraper output exists."""
from pathlib import Path
import pandas as pd

f = Path('scraped_car_data.xlsx')
print('=== SCRAPER RESULTS ===')
print(f'Output file exists: {f.exists()}')

if f.exists():
    df = pd.read_excel(f)
    print(f'Total records: {len(df)}')
    print(f'Columns: {len(df.columns)}')
    print(f'\nFirst 3 records:')
    print(df.head(3))
else:
    print('Output file not found - scraper may still be running or failed')

