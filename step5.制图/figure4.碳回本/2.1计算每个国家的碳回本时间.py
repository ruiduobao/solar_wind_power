# -*- coding: utf-8 -*-
"""
2.计算每个国家的碳回本时间.py
Functions:
1. Iterate over the three scenarios (standard, optimistic, pessimistic).
2. Read the carbon payback time data for wind and solar.
3. Calculate the average CPT (days) by country.
4. Merge all results and output a summary table with 6 columns.

Input:
- [scenario]/Wind_Carbon_Payback_Time.csv
- [scenario]/Solar_Carbon_Payback_Time.csv

Output:
- Country_Average_CPT_Scenarios.csv

Author: 锐多宝
Date: 2026-02-07
"""

import pandas as pd
import os
import sys

# ================= Configuration =================
BASE_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure4_全球碳回本\计算各国平均风机和光伏的碳回本时间"
OUTPUT_FILE = os.path.join(BASE_DIR, "Country_Average_CPT_Scenarios.csv")

# Scenario mapping (folder name -> output column prefix)
SCENARIOS = {
    "标准场景": "Standard",
    "乐观场景": "Optimistic",
    "悲观场景": "Pessimistic"
}

TECHS = ["Wind", "Solar"]

def main():
    print("Start calculating the average carbon payback time by country...")
    
    # List to store all Series
    series_list = []
    
    for scene_zh, scene_en in SCENARIOS.items():
        for tech in TECHS:
            file_name = f"{tech}_Carbon_Payback_Time.csv"
            file_path = os.path.join(BASE_DIR, scene_zh, file_name)
            
            col_name = f"{scene_en}_{tech}_CPTDays"
            print(f"Processing: {scene_zh} - {tech} -> {col_name}")
            
            if not os.path.exists(file_path):
                print(f"  Warning: file not found {file_path}")
                continue
                
            try:
                # Read data
                df = pd.read_csv(file_path)
                
                # Check required columns
                if 'country_final' not in df.columns or 'CPT_Years' not in df.columns:
                    print(f"  Error: {file_name} is missing required columns (country_final, CPT_Years)")
                    continue
                
                # Group by country and calculate the average
                # Note: this is the arithmetic mean
                avg_cpt_years = df.groupby('country_final')['CPT_Years'].mean()
                
                # Convert to days
                avg_cpt_days = avg_cpt_years * 365.25
                
                # Rename the Series
                avg_cpt_days.name = col_name
                
                series_list.append(avg_cpt_days)
                print(f"  - Includes {len(avg_cpt_days)} countries")
                
            except Exception as e:
                print(f"  Error while processing: {str(e)}")

    if not series_list:
        print("No data was processed successfully.")
        return

    print("Merging data...")
    # Merge all Series (automatically aligned by index, taking the union)
    result_df = pd.concat(series_list, axis=1)
    
    # Reset the index, turning country_final into a column
    result_df.index.name = 'country_final'
    result_df.reset_index(inplace=True)
    
    # Fill NaN (optional; NaN is kept here to indicate missing data)
    # result_df.fillna(0, inplace=True)
    
    # Reorder columns (by Standard, Optimistic, Pessimistic)
    desired_order = ['country_final']
    for scene_en in ["Standard", "Optimistic", "Pessimistic"]:
        for tech in ["Wind", "Solar"]:
            col = f"{scene_en}_{tech}_CPTDays"
            if col in result_df.columns:
                desired_order.append(col)
    
    result_df = result_df[desired_order]
    
    # Save
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Summary result saved to: {OUTPUT_FILE}")
    
    # Preview
    print("-" * 50)
    print("Result preview (Top 5):")
    print(result_df.head())
    print("-" * 50)

if __name__ == "__main__":
    main()
