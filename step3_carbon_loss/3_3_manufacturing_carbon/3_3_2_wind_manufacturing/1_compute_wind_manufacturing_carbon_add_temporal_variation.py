# -*- coding: utf-8 -*-
"""
Wind manufacturing carbon loss calculation (Wind Manufacturing Carbon Debt Calculation)
Author: 锐多宝 (Trae AI)
Date: 2026-02-05
Update: introduced dynamic manufacturing carbon intensity (Dynamic Manufacturing Carbon Intensity)

Function:
1. Read the wind turbine vector data (Shapefile) to obtain the construction year (constructi) and country information (COUNTRY).
2. Match the mainstream rated power (Rated Power) and manufacturing carbon intensity (tCO2e/MW) for each year according to the "wind technology evolution parameter table" in the outline.
   - Rated power varies by year (2.2MW - 4.5MW).
   - Manufacturing carbon intensity fluctuates by year (480 - 550 tCO2e/MW), including the embodied carbon of nacelle, tower and foundation materials.
3. Compute the manufacturing carbon debt of each wind farm site.
   Formula: Mfg Carbon (tCO2e) = Rated Power (MW) * Carbon Intensity (tCO2e/MW)
4. Generate statistics figures and CSV results.

Input:
- 风机80米缓冲区.shp (fid, constructi, COUNTRY)

Output:
- Wind_Manufacturing_Carbon_Result.csv
- Statistics figures (annual trend, country ranking, intensity distribution, etc.)
"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ================= Configuration =================

# Input file
WIND_SHP_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机80米缓冲区.shp"

# Output directory
OUTPUT_DIR_BASE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.3.2风电制造碳损失"

# Wind technology evolution parameter table
# Source: outline section 3.1 wind technology evolution parameter table
# Year -> rated power (MW)
WIND_SPECS = {
    'default': 2.2, # <= 2017
    2018: 2.4,
    2019: 2.6,
    2020: 3.0,
    2021: 3.4,
    2022: 3.8,
    2023: 4.2,
    2024: 4.5
}

# Manufacturing carbon intensity table (tCO2e/MW) - includes nacelle + tower + foundation materials (excluding LUC/construction)
# Source: supplementary table S1
# Rationale: 250 is too low and covers only the nacelle; 480-550 includes the tower and foundation materials, reflecting the non-linear material increase with upscaling
MFG_INTENSITY_STD = {
    'default': 480, # <= 2017
    2018: 490,
    2019: 500,
    2020: 520,
    2021: 550, # Rising raw material prices / taller towers
    2022: 540,
    2023: 520,
    2024: 500  # Green steel adoption / efficiency gains
}

# Plot style
sns.set_theme(style="ticks", font="Arial", context="paper")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.sans-serif'] = ['Arial', 'SimHei'] # Supports Chinese display
plt.rcParams['axes.unicode_minus'] = False

# ================= Helper functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_param(year, param_dict):
    """Get the parameter by year"""
    try:
        y = int(year)
        if y <= 2017:
            return param_dict['default']
        elif y in param_dict:
            return param_dict[y]
        else:
            # Future years; assume the 2024 standard continues
            if y > 2024:
                return param_dict[2024]
            return param_dict['default']
    except:
        return param_dict['default']

# ================= Main program =================

def run_scenario(scenario_name, intensity_factor, df_base):
    """
    Run the computation for the given scenario
    :param scenario_name: scenario name (标准/乐观/悲观)
    :param intensity_factor: carbon intensity factor (1.0/0.8/1.2)
    :param df_base: base dataframe
    """
    print(f"\n>>> Processing: {scenario_name} scenario (factor={intensity_factor})...")
    
    # Create the output directory
    out_dir = os.path.join(OUTPUT_DIR_BASE, scenario_name + "场景")
    if scenario_name == "标准": # Compatible with the previous path convention
         out_dir = os.path.join(OUTPUT_DIR_BASE, "标准场景")
         
    ensure_dir(out_dir)
    
    df = df_base.copy()
    
    # Adjust the carbon intensity dictionary
    intensity_dict = {k: v * intensity_factor for k, v in MFG_INTENSITY_STD.items()}
    
    # 3. Compute the manufacturing carbon debt
    print("  Computing manufacturing carbon debt...")
    
    # Get the rated power (MW)
    df['Rated_Power_MW'] = df['year'].apply(lambda y: get_param(y, WIND_SPECS))
    
    # Get the manufacturing carbon intensity (tCO2e/MW) - apply the factor
    df['Mfg_Intensity_tCO2_MW'] = df['year'].apply(lambda y: get_param(y, intensity_dict))
    
    # Compute the total carbon (tCO2e)
    # Total_Debt = Rated_Power * Intensity
    df['Loss_Mfg_tCO2'] = df['Rated_Power_MW'] * df['Mfg_Intensity_tCO2_MW']
    
    # 4. Export the results
    out_csv = os.path.join(out_dir, "Wind_Manufacturing_Carbon_Result.csv")
    # Keep the key columns
    out_cols = ['fid', 'year', 'country', 'Rated_Power_MW', 'Mfg_Intensity_tCO2_MW', 'Loss_Mfg_tCO2']
    df[out_cols].to_csv(out_csv, index=False, encoding='utf-8-sig')
    print(f"  Results exported: {out_csv}")
    
    # 5. Statistics and plotting
    total_loss_mt = df['Loss_Mfg_tCO2'].sum() / 1e6
    total_capacity_gw = df['Rated_Power_MW'].sum() / 1000
    print(f"  Statistics: Global wind installed capacity = {total_capacity_gw:.4f} GW")
    print(f"  Statistics: Manufacturing carbon emissions = {total_loss_mt:.4f} MtCO2e")
    
    # Figure 1: annual manufacturing carbon emission trend
    plot_annual_trend(df, out_dir, intensity_dict)
    
    # Figure 2: manufacturing carbon emission ranking by country
    plot_country_ranking(df, out_dir)
    
    # Figure 3: emission composition
    plot_period_dist(df, out_dir)
    
    print(f"  Figures generated.")

def main():
    print(">>> Starting wind manufacturing carbon loss calculation (Spatially Explicit Mode - Multi Scenario)...")
    
    # 1. Load data
    print(f"Reading wind turbine vector data: {WIND_SHP_PATH}")
    if not os.path.exists(WIND_SHP_PATH):
        print(f"Error: file not found {WIND_SHP_PATH}")
        return

    try:
        # Read only the needed columns for speed
        gdf = gpd.read_file(WIND_SHP_PATH, ignore_geometry=True)
    except TypeError:
        # Older geopandas may not support ignore_geometry
        gdf = gpd.read_file(WIND_SHP_PATH)
        gdf = pd.DataFrame(gdf.drop(columns='geometry'))
    except Exception as e:
        print(f"Failed to read SHP: {e}")
        return

    print(f"Data loading complete; {len(gdf)} records in total.")

    # 2. Data cleaning
    df_base = pd.DataFrame(gdf)
    
    # Check the required columns
    required_cols = ['fid', 'constructi']
    for col in required_cols:
        if col not in df_base.columns:
            print(f"Error: '{col}' column missing in the SHP file")
            return

    # Rename columns for processing
    df_base = df_base.rename(columns={'constructi': 'year', 'COUNTRY': 'country'})
    
    # Fill missing values
    missing_year_count = df_base['year'].isna().sum()
    if missing_year_count > 0:
        print(f"Notice: {missing_year_count} records are missing the year and will default to 2017.")
        df_base['year'] = df_base['year'].fillna(2017)
    
    if 'country' not in df_base.columns:
        df_base['country'] = 'Unknown'
    else:
        df_base['country'] = df_base['country'].fillna('Unknown')

    df_base['year'] = df_base['year'].astype(int)
    
    # Run the three scenarios
    # Standard scenario: 1.0
    run_scenario("标准", 1.0, df_base)
    
    # Optimistic scenario: 0.8
    run_scenario("乐观", 0.8, df_base)
    
    # Pessimistic scenario: 1.2
    run_scenario("悲观", 1.2, df_base)

    print("\n>>> All scenarios completed.")

def plot_annual_trend(df, out_dir, intensity_dict):
    """Plot the annual manufacturing carbon emission trend"""
    
    # Filter 2000-2024
    plot_df = df[(df['year'] >= 2000) & (df['year'] <= 2024)]
    
    yr_stats = plot_df.groupby('year')['Loss_Mfg_tCO2'].sum() / 1e6 # MtCO2
    
    plt.figure(figsize=(12, 6))
    ax1 = plt.gca()
    
    bars = ax1.bar(yr_stats.index, yr_stats.values, color='#1f77b4', alpha=0.7, label='Total Manufacturing Emissions')
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Annual Manufacturing Carbon (MtCO2e)", fontsize=12, color='#1f77b4')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    
    # Add dual lines: per-turbine power (left/right axis?) and carbon intensity (right axis)
    ax2 = ax1.twinx()
    
    years = sorted(yr_stats.index.unique())
    powers = [get_param(y, WIND_SPECS) for y in years]
    intensities = [get_param(y, intensity_dict) for y in years]
    
    l1 = ax2.plot(years, powers, 'g-o', linewidth=2, label='Rated Power (MW)')
    l2 = ax2.plot(years, intensities, 'r--x', linewidth=2, label='Carbon Intensity (tCO2e/MW)')
    
    ax2.set_ylabel("Technical Parameters", fontsize=12, color='k')
    ax2.tick_params(axis='y', labelcolor='k')
    
    # Merge legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')
    
    plt.title("Annual Wind Manufacturing Carbon Emissions & Technology Evolution", fontsize=16, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    
    filename = "1_Bar_Annual_Mfg_Carbon.png"
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

def plot_country_ranking(df, out_dir):
    """Manufacturing carbon emission ranking by country"""
    
    cnt_stats = df.groupby('country')['Loss_Mfg_tCO2'].sum().sort_values(ascending=False).head(20)
    cnt_stats_mt = cnt_stats / 1e6 # MtCO2
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=cnt_stats_mt.values, y=cnt_stats_mt.index, palette='Blues_r')
    
    plt.title("Top 20 Countries by Wind Manufacturing Carbon Emissions", fontsize=16, fontweight='bold')
    plt.xlabel("Total Manufacturing Carbon (MtCO2e)", fontsize=12)
    plt.ylabel("")
    
    for i, v in enumerate(cnt_stats_mt.values):
        plt.text(v + v*0.01, i, f"{v:.2f}", va='center', fontsize=10)
        
    filename = "2_Bar_Country_Mfg_Ranking.png"
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

def plot_period_dist(df, out_dir):
    """Distribution by period"""
    
    def get_period(y):
        if y <= 2017: return 'Legacy (<=2017)'
        elif y <= 2020: return 'Early Expansion (2018-2020)'
        else: return 'Recent Boom (2021-2024)'
        
    df['Period'] = df['year'].apply(get_period)
    
    period_stats = df.groupby('Period')['Loss_Mfg_tCO2'].sum()
    
    plt.figure(figsize=(8, 8))
    plt.pie(period_stats.values, labels=period_stats.index, autopct='%1.1f%%', 
            colors=['#999999', '#2ca02c', '#1f77b4'], startangle=140)
            
    plt.title("Share of Manufacturing Carbon Debt by Installation Period", fontsize=16, fontweight='bold')
    
    filename = "3_Pie_Period_Contribution.png"
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

if __name__ == "__main__":
    main()
