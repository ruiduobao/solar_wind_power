# -*- coding: utf-8 -*-
"""
Solar manufacturing carbon debt calculation (Solar Manufacturing Carbon Debt Calculation)
Author: 锐多宝 (Trae AI)
Date: 2026-02-05
Update: introduce dynamic power density for spatially explicit calculation

Functions:
1. Read the solar generation potential data (Solar_Power_Potential.csv) to get the area (area_m2).
2. Read the solar biomass carbon loss data (Solar_Biomass_Loss_Result.csv) to get the installation year (installation_year).
3. Match the annual manufacturing carbon intensity (tCO2e/MW) and power density (MW/km²) per the
   "solar technology evolution parameter table" in the outline.
4. Compute the installed capacity (Capacity) and manufacturing carbon debt of each solar plant.
   Formula:
   Capacity (MW) = Area (km²) * Power Density (MW/km²)
   Mfg Carbon (tCO2e) = Capacity (MW) * Carbon Intensity (tCO2e/MW)
5. Generate statistical charts and CSV results.

Input:
- Solar_Power_Potential.csv (fid, area_m2, country)
- Solar_Biomass_Loss_Result.csv (fid, installation_year)

Output:
- Solar_Manufacturing_Carbon_Result.csv
- Statistical charts
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ================= Configuration =================

# Input files
# Note: adjust the paths according to the actual situation
POWER_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.1光伏发电潜力计算\Solar_Power_Potential.csv"
BIO_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.2.1光伏生物碳损失\Solar_Biomass_Loss_Result.csv"

# Output directory
OUTPUT_DIR_BASE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.3.1光伏制造碳损失"

# Manufacturing carbon intensity table (tCO2e/MW) - industrial manufacturing only (excluding LUC/construction)
# Source: Supplementary Table S1
MFG_INTENSITY_STD = {
    'default': 800, # <= 2017
    2018: 770,
    2019: 740,
    2020: 710,
    2021: 680,
    2022: 660,
    2023: 630,
    2024: 600
}

# Solar power density table (MW/km²)
# Source: Supplementary Table S2 (module efficiency improvement: 17% -> 24%)
# 2017: ~32 MW/km², 2024: ~48 MW/km²
POWER_DENSITY = {
    'default': 32.0, # <= 2017
    2018: 34.3,
    2019: 36.6,
    2020: 38.9,
    2021: 41.1,
    2022: 43.4,
    2023: 45.7,
    2024: 48.0
}

# Plotting style
sns.set_theme(style="ticks", font="Arial", context="paper")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# ================= Helper functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_param(year, param_dict):
    """Get the parameter by year (intensity or density)"""
    try:
        y = int(year)
        if y <= 2017:
            return param_dict['default']
        elif y in param_dict:
            return param_dict[y]
        else:
            # Future years: use the 2024 value
            if y > 2024:
                return param_dict[2024]
            return param_dict['default']
    except:
        return param_dict['default']

# ================= Main program =================

def run_scenario(scenario_name, intensity_factor, df_base):
    """
    Run the calculation for the specified scenario
    :param scenario_name: scenario name (standard/optimistic/pessimistic)
    :param intensity_factor: carbon intensity factor (1.0/0.8/1.2)
    :param df_base: base dataframe
    """
    print(f"\n>>> Processing: {scenario_name} scenario (factor={intensity_factor})...")
    
    # Create the output directory
    out_dir = os.path.join(OUTPUT_DIR_BASE, scenario_name + "场景")
    if scenario_name == "标准": # keep compatibility with the previous path convention
         out_dir = os.path.join(OUTPUT_DIR_BASE, "标准场景")
         
    ensure_dir(out_dir)
    
    df = df_base.copy()
    
    # Adjust the carbon intensity dict
    intensity_dict = {k: v * intensity_factor for k, v in MFG_INTENSITY_STD.items()}
    
    # 3. Compute the manufacturing carbon debt
    print("  Computing manufacturing carbon debt...")
    
    # 3.1 Convert the area unit: m2 -> km2
    df['Area_km2'] = df['area_m2'] / 1e6
    
    # 3.2 Get the yearly power density (MW/km2)
    df['Power_Density_MW_km2'] = df['year'].apply(lambda y: get_param(y, POWER_DENSITY))
    
    # 3.3 Compute the dynamic installed capacity (MW)
    # Capacity = Area * Density
    df['Capacity_MW_Dynamic'] = df['Area_km2'] * df['Power_Density_MW_km2']
    
    # 3.4 Get the yearly manufacturing carbon intensity (tCO2e/MW) - apply the factor
    df['Mfg_Intensity_tCO2_MW'] = df['year'].apply(lambda y: get_param(y, intensity_dict))
    
    # 3.5 Compute the manufacturing carbon emissions (tCO2e)
    # Total_Debt = Capacity_Dynamic * Intensity
    df['Loss_Mfg_tCO2'] = df['Capacity_MW_Dynamic'] * df['Mfg_Intensity_tCO2_MW']
    
    # 4. Export the results
    out_csv = os.path.join(out_dir, "Solar_Manufacturing_Carbon_Result.csv")
    cols_to_save = ['fid', 'country', 'year', 'area_m2', 'Area_km2', 
                    'Power_Density_MW_km2', 'Capacity_MW_Dynamic', 
                    'Mfg_Intensity_tCO2_MW', 'Loss_Mfg_tCO2']
    
    df[cols_to_save].to_csv(out_csv, index=False, encoding='utf-8-sig')
    print(f"  Results exported: {out_csv}")
    
    # 5. Statistics and plots
    total_loss_mt = df['Loss_Mfg_tCO2'].sum() / 1e6
    total_capacity_gw = df['Capacity_MW_Dynamic'].sum() / 1000
    print(f"  Stats: global solar capacity = {total_capacity_gw:.4f} GW")
    print(f"  Stats: manufacturing carbon emissions = {total_loss_mt:.4f} MtCO2e")
    
    # Chart 1: annual manufacturing carbon emission trend
    plot_annual_trend(df, out_dir, intensity_dict)
    
    # Chart 2: manufacturing carbon emissions ranking by country
    plot_country_ranking(df, out_dir)
    
    # Chart 3: intensity distribution
    plot_intensity_dist(df, out_dir)
    
    print(f"  Charts generated.")

def main():
    print(">>> Starting solar manufacturing carbon calculation (Spatially Explicit Mode - Multi Scenario)...")
    
    # 1. Load data (read only once)
    print(f"Reading generation potential data: {POWER_CSV}")
    if not os.path.exists(POWER_CSV):
        print(f"Error: file not found {POWER_CSV}")
        return

    df_power = pd.read_csv(POWER_CSV)
    if 'area_m2' not in df_power.columns:
        print("Error: missing 'area_m2' column in Solar_Power_Potential.csv")
        return
        
    print(f"Reading biomass carbon data (to get year): {BIO_CSV}")
    if not os.path.exists(BIO_CSV):
        print(f"Error: file not found {BIO_CSV}")
        return
        
    df_bio = pd.read_csv(BIO_CSV)
    if 'installation_year' not in df_bio.columns:
        if 'year' in df_bio.columns:
            df_bio['installation_year'] = df_bio['year']
        else:
            print("Error: missing 'installation_year' column in Solar_Biomass_Loss_Result.csv")
            return
             
    # 2. Merge data
    print("Merging base data...")
    df_year = df_bio[['fid', 'installation_year']].drop_duplicates(subset=['fid'])
    df_base = df_power.merge(df_year, on='fid', how='left')
    
    missing_year_count = df_base['installation_year'].isna().sum()
    if missing_year_count > 0:
        print(f"Info: {missing_year_count} records are missing the year and will default to 2017.")
        df_base['installation_year'] = df_base['installation_year'].fillna(2017)
        
    df_base['year'] = df_base['installation_year'].astype(int)
    
    # Run the three scenarios
    # Standard scenario: 1.0
    run_scenario("标准", 1.0, df_base)
    
    # Optimistic scenario: 0.8
    run_scenario("乐观", 0.8, df_base)
    
    # Pessimistic scenario: 1.2
    run_scenario("悲观", 1.2, df_base)

    print("\n>>> All scenario calculations complete.")

def plot_annual_trend(df, out_dir, intensity_dict):
    """Plot the annual manufacturing carbon emission trend"""
    
    plot_df = df[(df['year'] >= 2010) & (df['year'] <= 2024)]
    
    yr_stats = plot_df.groupby('year')['Loss_Mfg_tCO2'].sum() / 1e6 # MtCO2
    
    plt.figure(figsize=(12, 6))
    ax1 = plt.gca()
    
    bars = ax1.bar(yr_stats.index, yr_stats.values, color='#ff7f0e', alpha=0.7, label='Total Manufacturing Emissions')
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Annual Manufacturing Carbon (MtCO2e)", fontsize=12, color='#ff7f0e')
    ax1.tick_params(axis='y', labelcolor='#ff7f0e')
    
    ax2 = ax1.twinx()
    years = sorted(yr_stats.index.unique())
    intensities = [get_param(y, intensity_dict) for y in years]
    
    l1 = ax2.plot(years, intensities, 'b-o', linewidth=2, label='Carbon Intensity (tCO2e/MW)')
    ax2.set_ylabel("Carbon Intensity (tCO2e/MW)", fontsize=12, color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    
    plt.title("Annual Solar Manufacturing Carbon Emissions & Intensity Trend", fontsize=16, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    
    filename = "1_Bar_Annual_Mfg_Carbon.png"
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

def plot_country_ranking(df, out_dir):
    """Manufacturing carbon emissions ranking by country"""
    
    cnt_stats = df.groupby('country')['Loss_Mfg_tCO2'].sum().sort_values(ascending=False).head(20)
    cnt_stats_mt = cnt_stats / 1e6 # MtCO2
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=cnt_stats_mt.values, y=cnt_stats_mt.index, palette='Oranges_r')
    
    plt.title("Top 20 Countries by Solar Manufacturing Carbon Emissions", fontsize=16, fontweight='bold')
    plt.xlabel("Total Manufacturing Carbon (MtCO2e)", fontsize=12)
    plt.ylabel("")
    
    for i, v in enumerate(cnt_stats_mt.values):
        plt.text(v + v*0.01, i, f"{v:.2f}", va='center', fontsize=10)
        
    filename = "2_Bar_Country_Mfg_Ranking.png"
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

def plot_intensity_dist(df, out_dir):
    """Carbon emission distribution by installation period"""
    
    def get_period(y):
        if y <= 2017: return 'Legacy (<=2017)'
        elif y <= 2020: return 'Early Expansion (2018-2020)'
        else: return 'Recent Boom (2021-2024)'
        
    df['Period'] = df['year'].apply(get_period)
    
    period_stats = df.groupby('Period')['Loss_Mfg_tCO2'].sum()
    
    plt.figure(figsize=(8, 8))
    plt.pie(period_stats.values, labels=period_stats.index, autopct='%1.1f%%', 
            colors=['#ffcc00', '#999999', '#ff7f0e'], startangle=140)
            
    plt.title("Share of Manufacturing Carbon Debt by Installation Period", fontsize=16, fontweight='bold')
    
    filename = "3_Pie_Period_Contribution.png"
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

if __name__ == "__main__":
    main()
