# -*- coding: utf-8 -*-
"""
Merge solar slope statistics
Author: 锐多宝 (Trae AI)
Date: 2026-01-27
Features:
    1. Read all solar slope statistics CSV files in the directory (exported by GEE)
    2. Parse the graded statistics data in JSON format
    3. Map Level 1/2/3 to specific slope range columns
    4. Merge and output as one summary table

Data source format:
    fid, avg_slope, slope_hist_json
    slope_hist_json example: [{"level":1,"sum":64.0...}, {"level":2,"sum":2.1...}]

Grade definitions (reference 0.1下载光伏的坡度.js):
    Level 1: < 5°
    Level 2: 5° - 15°
    Level 3: > 15°
"""

import pandas as pd
import glob
import os
import json

def parse_hist_json(row):
    """
    Parse the slope_hist_json column and return the pixel counts of each Level
    """
    try:
        json_str = row['slope_hist_json']
        if pd.isna(json_str) or json_str == '':
            return pd.Series([0.0, 0.0, 0.0])
        
        data = json.loads(json_str)
        
        # Initialize counts
        c1, c2, c3 = 0.0, 0.0, 0.0
        
        for item in data:
            lvl = item.get('level')
            val = item.get('sum', 0.0)
            
            if lvl == 1:
                c1 = val
            elif lvl == 2:
                c2 = val
            elif lvl == 3:
                c3 = val
                
        return pd.Series([c1, c2, c3])
    except Exception as e:
        print(f"Parse error FID {row.get('fid')}: {e}")
        return pd.Series([0.0, 0.0, 0.0])

def main():
    # 1. Set paths
    base_dir = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\结果数据\计算土壤碳\光伏坡度相关数据"
    output_csv = os.path.join(base_dir, "Solar_Slope_Merged.csv")
    
    if not os.path.exists(base_dir):
        print(f"Error: input directory does not exist {base_dir}")
        return

    # 2. Get all CSV files (recursive search)
    csv_files = glob.glob(os.path.join(base_dir, "**", "*.csv"), recursive=True)
    # Exclude an existing merged result file to prevent duplicate reading
    csv_files = [f for f in csv_files if "Solar_Slope_Merged" not in f]
    
    print(f"Found {len(csv_files)} CSV files, starting merge...")
    
    if not csv_files:
        print("No CSV files found.")
        return

    # 3. Read and merge
    df_list = []
    for f in csv_files:
        try:
            # Read csv, keep fid consistent as string or number; assume fid may be int
            df_chunk = pd.read_csv(f)
            df_list.append(df_chunk)
        except Exception as e:
            print(f"Failed to read file {f}: {e}")
            
    if not df_list:
        return

    full_df = pd.concat(df_list, ignore_index=True)
    print(f"Initial merge completed, {len(full_df)} rows in total. Starting JSON parsing...")

    # 4. Parse JSON data
    # Apply the function and assign the results to new columns
    # Level 1: < 5°
    # Level 2: 5-15°
    # Level 3: > 15°
    
    level_cols = ['count_slope_lt_5', 'count_slope_5_15', 'count_slope_gt_15']
    full_df[level_cols] = full_df.apply(parse_hist_json, axis=1)
    
    # 5. Compute total pixel count and percentages (optional, for checking)
    full_df['total_pixels'] = full_df[level_cols].sum(axis=1)
    
    # Prevent division by zero
    full_df['pct_slope_lt_5'] = full_df['count_slope_lt_5'] / full_df['total_pixels'] * 100
    full_df['pct_slope_5_15'] = full_df['count_slope_5_15'] / full_df['total_pixels'] * 100
    full_df['pct_slope_gt_15'] = full_df['count_slope_gt_15'] / full_df['total_pixels'] * 100
    
    # Fill NaN with 0 (if total_pixels is 0)
    full_df.fillna(0, inplace=True)

    # 6. Save results
    # Keep only useful columns
    out_columns = [
        'fid', 'avg_slope', 
        'count_slope_lt_5', 'count_slope_5_15', 'count_slope_gt_15',
        'pct_slope_lt_5', 'pct_slope_5_15', 'pct_slope_gt_15',
        'total_pixels'
    ]
    
    # Ensure columns exist (in case some columns were not generated)
    final_cols = [c for c in out_columns if c in full_df.columns]
    
    full_df[final_cols].to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"Processing completed!")
    print(f"Output file: {output_csv}")
    print(f"Included columns: {final_cols}")
    print(f"Total records: {len(full_df)}")

if __name__ == "__main__":
    main()
