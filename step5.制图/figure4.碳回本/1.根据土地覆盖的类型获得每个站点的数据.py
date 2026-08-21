# -*- coding: utf-8 -*-
"""
1. Get the data of each site by land cover type.py
Functions:
1. Based on the land cover data, determine the dominant land cover type (largest area) of each site (fid).
2. Match the carbon payback time (CPT) data.
3. Convert CPT from years to days.
4. Extract the CPT data of solar and wind by land type (Bareland, Grass, Cropland, Shrub, Forest).
5. Output as CSV, one column per combination of type and technology for the CPT distribution.

Input:
- SOLAR_FROM_2017_2024_LandCover_Summary.csv
- Solar_Carbon_Payback_Time.csv
- WIND_FROM_2017_2024_LandCover_Summary.csv
- Wind_Carbon_Payback_Time.csv

Output:
- LandCover_CPT_Distribution.csv

Author: 锐多宝
Date: 2026-02-07
"""

import pandas as pd
import os
import sys

# ================= Configuration =================
BASE_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure4_全球碳回本\匹配风机光伏的各类地物的碳汇本时间"

SOLAR_LC_PATH = os.path.join(BASE_DIR, "SOLAR_FROM_2017_2024_LandCover_Summary.csv")
SOLAR_CPT_PATH = os.path.join(BASE_DIR, "Solar_Carbon_Payback_Time.csv")

WIND_LC_PATH = os.path.join(BASE_DIR, "WIND_FROM_2017_2024_LandCover_Summary.csv")
WIND_CPT_PATH = os.path.join(BASE_DIR, "Wind_Carbon_Payback_Time.csv")

OUTPUT_FILE = os.path.join(BASE_DIR, "LandCover_CPT_Distribution.csv")

TARGET_CLASSES = ['Bareland', 'Grass', 'Cropland', 'Shrub', 'Forest']

# ================= Functions =================

def get_cpt_distribution(lc_path, cpt_path, tech_prefix):
    """
    Extract the CPT distribution by land type for the given technology
    """
    print(f"Processing {tech_prefix} data...")
    
    # 1. Read the land cover data
    if not os.path.exists(lc_path):
        print(f"Error: file not found {lc_path}")
        return {}
    df_lc = pd.read_csv(lc_path)
    
    # 2. Determine the dominant land type of each site
    # Sort by fid and area_sqm in descending order
    df_lc_sorted = df_lc.sort_values(['fid', 'area_sqm'], ascending=[True, False])
    # Keep the first row of each fid (i.e. the row with the largest area)
    df_dominant = df_lc_sorted.drop_duplicates(subset=['fid'], keep='first')[['fid', 'class_name']]
    
    print(f"  - Total sites: {len(df_dominant)}")
    
    # 3. Read the CPT data
    if not os.path.exists(cpt_path):
        print(f"Error: file not found {cpt_path}")
        return {}
    df_cpt = pd.read_csv(cpt_path)
    
    # 4. Merge the data
    # inner join keeps only the sites that have CPT data
    df_merged = df_cpt.merge(df_dominant, on='fid', how='inner')
    print(f"  - Sites matched with CPT: {len(df_merged)}")
    
    # 5. Convert the CPT unit (years -> days)
    df_merged['CPT_Days'] = df_merged['CPT_Years'] * 365.25
    
    # 6. Extract the data by type
    results = {}
    for cls in TARGET_CLASSES:
        # Filter by the given land type
        subset = df_merged[df_merged['class_name'] == cls]
        count = len(subset)
        avg_cpt = subset['CPT_Days'].mean() if count > 0 else 0
        
        print(f"    - {cls}: {count} sites, avg CPT: {avg_cpt:.2f} days")
        
        # Store as a Series
        col_name = f"{tech_prefix}_{cls}_CPTDays"
        results[col_name] = subset['CPT_Days'].values
        
    return results

def main():
    print("Starting to extract data...")
    
    # Get the wind data
    wind_data = get_cpt_distribution(WIND_LC_PATH, WIND_CPT_PATH, "风机")
    
    # Get the solar data
    solar_data = get_cpt_distribution(SOLAR_LC_PATH, SOLAR_CPT_PATH, "光伏")
    
    # Combine the data
    # In the order requested by the user: 风机_Bareland, 光伏_Bareland, 风机_Grass, 光伏_Grass...
    combined_data = {}
    
    for cls in TARGET_CLASSES:
        wind_key = f"风机_{cls}_CPTDays"
        solar_key = f"光伏_{cls}_CPTDays"
        
        if wind_key in wind_data:
            combined_data[wind_key] = pd.Series(wind_data[wind_key])
        else:
            combined_data[wind_key] = pd.Series([], dtype=float)
            
        if solar_key in solar_data:
            combined_data[solar_key] = pd.Series(solar_data[solar_key])
        else:
            combined_data[solar_key] = pd.Series([], dtype=float)
            
    # Create the DataFrame
    df_out = pd.DataFrame(combined_data)
    
    # Save
    df_out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\nResults saved to: {OUTPUT_FILE}")
    print("Column name preview:")
    print(df_out.columns.tolist())

if __name__ == "__main__":
    main()
