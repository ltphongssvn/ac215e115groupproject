#!/usr/bin/env python3
# File path: ~/code/ltphongssvn/ac215e115groupproject/data-pipeline/fix_rice_extraction.py
# Test proper column extraction

import pandas as pd

excel_path = 'data/raw/external_rice_market/worldbank_pink_sheet/CMO-Historical-Data-Monthly_20251009.xlsx'
df = pd.read_excel(excel_path, sheet_name='Monthly Prices', header=4)

print("Rice columns found:")
for i, col in enumerate(df.columns):
    if 'Rice' in str(col):
        print(f"  Index {i}: {col}")

# Show actual structure
date_col = df.columns[0]
df['Date'] = pd.to_datetime(df[date_col], format='%YM%m', errors='coerce')
df = df[df['Date'] >= '2008-01-01']

# Correctly map columns
rice_cols = {
    'Thai 5%': 'Rice, Thai 5% ',
    'Thai 25%': 'Rice, Thai 25% ',
    'Thai A.1': 'Rice, Thai A.1',
    'Vietnamese 5%': 'Rice, Viet Namese 5%'
}

for label, col_name in rice_cols.items():
    if col_name in df.columns:
        print(f"✓ Found {label}: column '{col_name}'")
        print(f"  Sample values: {df[col_name].iloc[:3].tolist()}")
