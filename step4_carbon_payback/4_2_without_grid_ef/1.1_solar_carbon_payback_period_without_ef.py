# -*- coding: utf-8 -*-
"""
Solar Carbon Payback Time (CPT) Calculation - Without Grid Emission Factors (Using Global Average)
Author: 锐多宝 (Trae AI)
Date: 2026-01-28

Functions:
1. Read the total solar carbon debt result (Solar_Total_Carbon_Debt_Result.csv)
2. Read the solar power potential result (Solar_Power_Potential.csv)
3. Recalculate the annual avoided CO2 (Avoided_CO2) using a fixed global average
   emission factor (0.475 tCO2/MWh)
4. Calculate the carbon payback time (CPT)
   Formula: CPT (Years) = Total_Debt_tCO2 / (Annual_Gen_MWh * GLOBAL_AVG_EF)
5. Output the result to CSV

Input:
- Carbon debt: Solar_Total_Carbon_Debt_Result.csv
- Power potential: Solar_Power_Potential.csv

Output:
- Solar_CPT_No_Grid_EF.csv
- Run log
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# ================= Configuration =================

# Input file paths
DEBT_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.4.1光伏碳债务合并损失\Solar_Total_Carbon_Debt_Result.csv"
POTENTIAL_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.1光伏发电潜力计算\Solar_Power_Potential.csv"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\6.1.光伏碳回本周期(不考虑排放因子)"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "Solar_CPT_No_Grid_EF.csv")
LOG_PATH = os.path.join(OUTPUT_DIR, "Solar_CPT_No_Grid_EF_Calculation_Log.txt")

# Global average grid emission factor (tCO2/MWh)
GLOBAL_AVG_EF = 0.475

# ================= Utility functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def log_message(message):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{time_str}] {message}"
    print(full_message)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

# ================= Main program =================

def main():
    ensure_dir(OUTPUT_DIR)
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    
    log_message(">>> Start calculating solar carbon payback time (CPT) - without grid emission factors ...")
    log_message(f"Using global average emission factor: {GLOBAL_AVG_EF} tCO2/MWh")
    
    # 1. Read carbon debt data
    log_message(f"Reading carbon debt file: {DEBT_CSV}")
    if not os.path.exists(DEBT_CSV):
        log_message("Error: carbon debt file not found.")
        return
        
    df_debt = pd.read_csv(DEBT_CSV)
    log_message(f"Carbon debt records: {len(df_debt)}")
    
    # 2. Read power potential data
    log_message(f"Reading power potential file: {POTENTIAL_CSV}")
    if not os.path.exists(POTENTIAL_CSV):
        log_message("Error: power potential file not found.")
        return
        
    df_pot = pd.read_csv(POTENTIAL_CSV)
    log_message(f"Power potential records: {len(df_pot)}")
    
    # Ensure fid is int
    df_debt['fid'] = df_debt['fid'].astype(int)
    df_pot['fid'] = df_pot['fid'].astype(int)
    
    # 3. Merge data
    log_message("Merging data (Left Join based on Debt data)...")
    df_merged = pd.merge(df_debt, df_pot, on='fid', how='left', suffixes=('', '_pot'))
    
    # Handle column name conflicts after merging
    if 'country_pot' in df_merged.columns:
        if 'country_final' not in df_merged.columns:
            df_merged['country_final'] = df_merged['country_pot']
        else:
            df_merged['country_final'] = df_merged['country_final'].fillna(df_merged['country_pot'])
        df_merged.drop(columns=['country_pot'], inplace=True)
        
    log_message(f"Records after merge: {len(df_merged)}")
    
    # 4. Calculate CPT (without per-country EF, uniformly using GLOBAL_AVG_EF)
    # CPT = Total_Debt / (Annual_Gen * Global_Avg_EF)
    
    # Check required fields
    if 'Total_Debt_tCO2' not in df_merged.columns or 'annual_gen_mwh' not in df_merged.columns:
        log_message("Error: missing Total_Debt_tCO2 or annual_gen_mwh fields after merge.")
        return

    # Fill missing values
    df_merged['Total_Debt_tCO2'] = df_merged['Total_Debt_tCO2'].fillna(0)
    df_merged['annual_gen_mwh'] = df_merged['annual_gen_mwh'].fillna(0)
    
    # Calculate new annual avoided emissions (Global Avg)
    df_merged['Avoided_CO2_GlobalAvg_ton'] = df_merged['annual_gen_mwh'] * GLOBAL_AVG_EF
    
    def calc_cpt(row):
        debt = row['Total_Debt_tCO2']
        avoided = row['Avoided_CO2_GlobalAvg_ton']
        
        if avoided <= 0:
            return np.nan # cannot pay back
        
        return debt / avoided
        
    df_merged['CPT_Years_NoEF'] = df_merged.apply(calc_cpt, axis=1)
    
    # Statistics of valid results
    valid_cpt = df_merged['CPT_Years_NoEF'].dropna()
    log_message(f"Sites with successfully calculated CPT: {len(valid_cpt)}")
    if len(valid_cpt) > 0:
        log_message(f"CPT mean: {valid_cpt.mean():.2f} years")
        log_message(f"CPT median: {valid_cpt.median():.2f} years")
        log_message(f"CPT min: {valid_cpt.min():.2f} years")
        log_message(f"CPT max: {valid_cpt.max():.2f} years")
    else:
        log_message("Warning: no site produced a valid CPT.")
    
    # 5. Output results
    out_cols = [
        'fid', 'country_final', 'installation_year', 
        'Total_Debt_tCO2', 
        'annual_gen_mwh', 
        'Avoided_CO2_GlobalAvg_ton', # new avoided emissions
        'pvout_daily_kwh_kwp', 
        'CPT_Years_NoEF'
    ]
    
    # Ensure columns exist
    out_cols = [c for c in out_cols if c in df_merged.columns]
    
    df_merged[out_cols].to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    log_message(f"Result saved: {OUTPUT_CSV}")
    
    # 6. Additionally output invalid sites
    invalid_df = df_merged[df_merged['CPT_Years_NoEF'].isna()]
    if not invalid_df.empty:
        invalid_path = os.path.join(OUTPUT_DIR, "Solar_Invalid_CPT_NoEF.csv")
        invalid_df[out_cols].to_csv(invalid_path, index=False, encoding='utf-8-sig')
        log_message(f"Warning: {len(invalid_df)} sites could not calculate CPT, see details at: {invalid_path}")

if __name__ == "__main__":
    main()
