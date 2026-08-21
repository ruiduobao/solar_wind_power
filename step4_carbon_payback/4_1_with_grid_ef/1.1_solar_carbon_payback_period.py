# -*- coding: utf-8 -*-
"""
Solar carbon payback time (CPT) computation - multi-scenario version
Author: 锐多宝 (Trae AI)
Date: 2026-02-06

Functions:
1. Iterate over three scenarios (optimistic, standard, pessimistic)
2. Read the solar total carbon debt results of each scenario (Solar_Total_Carbon_Debt_Result.csv)
3. Read the solar power potential results (Solar_Power_Potential.csv)
4. Merge the data (based on fid)
5. Compute the carbon payback time (Carbon Payback Time, CPT)
   Formula: CPT (Years) = Total_Debt_tCO2 / Avoided_CO2_Annual_ton
6. Output the results to the corresponding scenario folder

Inputs:
- Carbon debt: 制图\4.4.1光伏碳债务合并损失\[场景名]\Solar_Total_Carbon_Debt_Result.csv
- Power potential: 制图\3.1光伏发电潜力计算\Solar_Power_Potential.csv

Outputs:
- 制图\5.1.光伏碳回本周期\[场景名]\Solar_Carbon_Payback_Time.csv
- 制图\5.1.光伏碳回本周期\[场景名]\Solar_CPT_Calculation_Log.txt
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# ================= Configuration =================

# Scenario list
SCENARIOS = ['乐观场景', '标准场景', '悲观场景']

# Base input paths
BASE_DEBT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.4.1光伏碳债务合并损失"
POTENTIAL_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.1光伏发电潜力计算\Solar_Power_Potential.csv"

# Base output path
BASE_OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\5.1.光伏碳回本周期"

# ================= Utility functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def log_message(message, log_path=None):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{time_str}] {message}"
    print(full_message)
    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(full_message + "\n")

def calc_cpt(row):
    debt = row['Total_Debt_tCO2']
    avoided = row['avoided_co2_ton']
    
    if pd.isna(avoided) or avoided <= 0:
        return np.nan # cannot pay back (or missing data)
    
    if pd.isna(debt):
        return np.nan

    return debt / avoided

# ================= Process a single scenario =================

def process_scenario(scenario_name, df_pot):
    """
    Process the computation of a single scenario
    """
    # Path construction
    debt_csv = os.path.join(BASE_DEBT_DIR, scenario_name, "Solar_Total_Carbon_Debt_Result.csv")
    output_dir = os.path.join(BASE_OUTPUT_DIR, scenario_name)
    output_csv = os.path.join(output_dir, "Solar_Carbon_Payback_Time.csv")
    log_path = os.path.join(output_dir, "Solar_CPT_Calculation_Log.txt")
    
    ensure_dir(output_dir)
    if os.path.exists(log_path):
        os.remove(log_path)
        
    log_message(f"=== Start processing scenario: {scenario_name} ===", log_path)
    
    # 1. Read the carbon debt data
    if not os.path.exists(debt_csv):
        log_message(f"Error: carbon debt file not found: {debt_csv}", log_path)
        return

    log_message(f"Reading the carbon debt file: {debt_csv}", log_path)
    df_debt = pd.read_csv(debt_csv)
    log_message(f"Number of carbon debt records: {len(df_debt)}", log_path)
    
    # Ensure fid is int
    if 'fid' in df_debt.columns:
        df_debt['fid'] = df_debt['fid'].astype(int)
    else:
        log_message("Error: the carbon debt file is missing the 'fid' column", log_path)
        return

    # 2. Merge the data (Left Join based on Debt data)
    log_message("Merging the data (Left Join based on Debt data)...", log_path)
    # Use debt as the base, because we need to compute the payback time of these sites
    df_merged = pd.merge(df_debt, df_pot, on='fid', how='left', suffixes=('', '_pot'))
    
    # Handle the column name conflicts after the merge
    if 'country_pot' in df_merged.columns:
        if 'country_final' not in df_merged.columns:
            df_merged['country_final'] = df_merged['country_pot']
        else:
            df_merged['country_final'] = df_merged['country_final'].fillna(df_merged['country_pot'])
        df_merged.drop(columns=['country_pot'], inplace=True)

    log_message(f"Number of records after the merge: {len(df_merged)}", log_path)
    
    # 3. Compute the CPT
    # Check the required fields
    if 'Total_Debt_tCO2' not in df_merged.columns or 'avoided_co2_ton' not in df_merged.columns:
        log_message("Error: the merged data is missing the Total_Debt_tCO2 or avoided_co2_ton fields.", log_path)
        return

    # Fill the missing values (only Total_Debt_tCO2 is filled with 0; a missing avoided_co2_ton means it cannot be computed)
    df_merged['Total_Debt_tCO2'] = df_merged['Total_Debt_tCO2'].fillna(0)
    
    df_merged['CPT_Years'] = df_merged.apply(calc_cpt, axis=1)
    
    # Statistics of the valid computation results
    valid_cpt = df_merged['CPT_Years'].dropna()
    log_message(f"Number of sites with successfully computed CPT: {len(valid_cpt)}", log_path)
    
    if len(valid_cpt) > 0:
        log_message(f"CPT mean: {valid_cpt.mean():.2f} years", log_path)
        log_message(f"CPT median: {valid_cpt.median():.2f} years", log_path)
        log_message(f"CPT minimum: {valid_cpt.min():.2f} years", log_path)
        log_message(f"CPT maximum: {valid_cpt.max():.2f} years", log_path)
    else:
        log_message("Warning: no site has successfully computed a CPT.", log_path)
        
    # 4. Output the results
    # Keep the key columns
    out_cols = [
        'fid', 'country_final', 'installation_year', 
        'Total_Debt_tCO2', 
        'annual_gen_mwh', 'grid_ef', 'avoided_co2_ton', 
        'pvout_daily_kwh_kwp', # solar-specific
        'CPT_Years'
    ]
    
    # Ensure the columns exist
    out_cols = [c for c in out_cols if c in df_merged.columns]
    
    df_merged[out_cols].to_csv(output_csv, index=False, encoding='utf-8-sig')
    log_message(f"Results saved: {output_csv}", log_path)
    
    # Extra output: sites that cannot be computed
    invalid_df = df_merged[df_merged['CPT_Years'].isna()]
    if not invalid_df.empty:
        invalid_path = os.path.join(output_dir, "Solar_Invalid_CPT.csv")
        invalid_df[out_cols].to_csv(invalid_path, index=False, encoding='utf-8-sig')
        log_message(f"Warning: {len(invalid_df)} sites cannot compute a CPT, see details at: {invalid_path}", log_path)

    log_message(f"=== Scenario {scenario_name} processing completed ===\n", log_path)


# ================= Main program =================

def main():
    print(f">>> Start the multi-scenario solar carbon payback time (CPT) computation")
    
    # 1. Read the power potential data in advance (shared by all scenarios)
    print(f"Reading the shared power potential file: {POTENTIAL_CSV}")
    if not os.path.exists(POTENTIAL_CSV):
        print("Error: power potential file not found.")
        return
        
    df_pot = pd.read_csv(POTENTIAL_CSV)
    print(f"Number of power potential records: {len(df_pot)}")
    
    if 'fid' in df_pot.columns:
        df_pot['fid'] = df_pot['fid'].astype(int)
    else:
        print("Error: the power potential file is missing the 'fid' column")
        return
        
    # 2. Iterate over the scenarios
    for scenario in SCENARIOS:
        process_scenario(scenario, df_pot)
        
    print(">>> All scenarios processed.")

if __name__ == "__main__":
    main()
