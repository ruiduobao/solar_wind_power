# -*- coding: utf-8 -*-
"""
Solar Carbon Payback Time (CPT) visualization - multi-scenario version
Author: 锐多宝 (Trae AI)
Date: 2026-02-06

Features:
1. Iterate over three scenarios (Optimistic, Standard, Pessimistic)
2. Read solar CPT calculation results (Solar_Carbon_Payback_Time.csv)
3. Generate statistical charts:
   - CPT frequency distribution histogram
   - CPT vs PVOUT scatter plot
   - CPT vs Grid EF scatter plot
   - Country average CPT ranking
   - Global CPT distribution map
   - CPT vs total carbon debt scatter plot
4. Export the statistics corresponding to each chart

Input:
- 制图\5.1.光伏碳回本周期\[场景名]\Solar_Carbon_Payback_Time.csv

Output:
- 制图\5.1.光伏碳回本周期\[场景名]\统计图表 (.png)
- 制图\5.1.光伏碳回本周期\[场景名]\统计数据 (.csv)
- 制图\5.1.光伏碳回本周期\[场景名]\Solar_CPT_Viz_Log.txt
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from matplotlib.colors import LogNorm, Normalize
from datetime import datetime

# ================= Configuration =================

SCENARIOS = ['乐观场景', '标准场景', '悲观场景']
BASE_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\5.1.光伏碳回本周期"
POWER_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.1光伏发电潜力计算\Solar_Power_Potential.csv" # used to obtain lon/lat

# World map Shapefile (for map plotting)
try:
    # Prefer the local path first
    WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\行政区划\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"
    if not os.path.exists(WORLD_SHP):
        WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')
except:
    WORLD_SHP = None

# Plotting style
sns.set_theme(style="ticks", font="Arial", context="paper")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.sans-serif'] = ['Arial', 'SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

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

def export_plot_data(df, filename, output_dir, log_path=None):
    csv_path = os.path.join(output_dir, filename.replace('.png', '.csv'))
    df.to_csv(csv_path, index=True, encoding='utf-8-sig')
    log_message(f"Chart data exported: {csv_path}", log_path)

# ================= Plotting functions =================

def plot_cpt_distribution(df, output_dir, log_path):
    """CPT frequency distribution histogram"""
    log_message("Plotting 1. CPT distribution histogram...", log_path)
    
    # Filter extreme values (e.g. > 20 years) to show the main body
    plot_df = df[df['CPT_Years'] <= 20].copy()
    
    plt.figure(figsize=(10, 6))
    sns.histplot(plot_df['CPT_Years'], bins=50, kde=True, color='#2ca02c')
    
    plt.title("Distribution of Solar Carbon Payback Time (CPT)", fontsize=16, fontweight='bold')
    plt.xlabel("Carbon Payback Time (Years)", fontsize=12)
    plt.ylabel("Count of Solar Sites", fontsize=12)
    
    # Add mean line
    mean_val = plot_df['CPT_Years'].mean()
    plt.axvline(mean_val, color='r', linestyle='--', label=f'Mean: {mean_val:.2f} yrs')
    plt.legend()
    
    filename = "1_Hist_CPT_Distribution.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(plot_df['CPT_Years'].describe(), filename, output_dir, log_path)

def plot_cpt_vs_pvout(df, output_dir, log_path):
    """CPT vs PVOUT scatter plot"""
    log_message("Plotting 2. CPT vs PVOUT scatter plot...", log_path)
    
    if 'pvout_daily_kwh_kwp' not in df.columns:
        log_message("Warning: PVOUT data missing, skipping plot.", log_path)
        return

    plot_df = df[df['CPT_Years'] <= 20].copy()
    
    plt.figure(figsize=(10, 6))
    # Use Hexbin or Scatter
    plt.hexbin(plot_df['pvout_daily_kwh_kwp'], plot_df['CPT_Years'], gridsize=50, cmap='Greens', mincnt=1)
    cb = plt.colorbar(label='Count of Sites')
    
    plt.title("Solar CPT vs. Resource Potential (PVOUT)", fontsize=16, fontweight='bold')
    plt.xlabel("PVOUT (kWh/kWp/day)", fontsize=12)
    plt.ylabel("Carbon Payback Time (Years)", fontsize=12)
    
    filename = "2_Scatter_CPT_vs_PVOUT.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(plot_df[['pvout_daily_kwh_kwp', 'CPT_Years']], filename, output_dir, log_path)

def plot_cpt_vs_grid_ef(df, output_dir, log_path):
    """CPT vs Grid EF scatter plot"""
    log_message("Plotting 3. CPT vs Grid EF scatter plot...", log_path)
    
    if 'grid_ef' not in df.columns:
        log_message("Warning: Grid EF data missing, skipping plot.", log_path)
        return

    plot_df = df[df['CPT_Years'] <= 20].copy()
    
    plt.figure(figsize=(10, 6))
    plt.hexbin(plot_df['grid_ef'], plot_df['CPT_Years'], gridsize=50, cmap='Blues', mincnt=1)
    cb = plt.colorbar(label='Count of Sites')
    
    plt.title("Solar CPT vs. Grid Emission Factor", fontsize=16, fontweight='bold')
    plt.xlabel("Grid Emission Factor (tCO2/MWh)", fontsize=12)
    plt.ylabel("Carbon Payback Time (Years)", fontsize=12)
    
    filename = "3_Scatter_CPT_vs_GridEF.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(plot_df[['grid_ef', 'CPT_Years']], filename, output_dir, log_path)

def plot_country_ranking(df, output_dir, log_path):
    """Country average CPT ranking (Ascending - shorter is better)"""
    log_message("Plotting 4. Country CPT ranking...", log_path)
    
    # Keep countries with enough records (e.g. > 50 sites)
    cnt_counts = df['country_final'].value_counts()
    valid_countries = cnt_counts[cnt_counts >= 50].index
    
    plot_df = df[df['country_final'].isin(valid_countries)].copy()
    
    # Compute mean CPT
    cnt_stats = plot_df.groupby('country_final')['CPT_Years'].mean().sort_values(ascending=True).head(20)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=cnt_stats.values, y=cnt_stats.index, palette='RdYlGn_r') # shorter is greener
    
    plt.title("Top 20 Countries with Shortest Carbon Payback Time (Avg)", fontsize=16, fontweight='bold')
    plt.xlabel("Average CPT (Years)", fontsize=12)
    plt.ylabel("")
    
    for i, v in enumerate(cnt_stats.values):
        plt.text(v + 0.05, i, f"{v:.2f}", va='center', fontsize=10)
        
    filename = "4_Bar_Country_CPT_Ranking.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(cnt_stats, filename, output_dir, log_path)

def plot_cpt_map(df, output_dir, log_path):
    """Global CPT distribution map"""
    log_message("Plotting 5. Global CPT distribution map...", log_path)
    
    # Lon/lat needed
    # Try to load lon/lat from POWER_CSV
    if not os.path.exists(POWER_CSV):
        log_message("Warning: Power CSV not found, cannot get lon/lat, skipping map plot.", log_path)
        return
        
    try:
        loc_df = pd.read_csv(POWER_CSV)[['fid', 'lon', 'lat']]
        # Note: ensure consistent fid types when merging
        if df['fid'].dtype != loc_df['fid'].dtype:
             loc_df['fid'] = loc_df['fid'].astype(df['fid'].dtype)
             
        df_map = df.merge(loc_df, on='fid', how='inner')
    except Exception as e:
        log_message(f"Failed to read lon/lat: {e}", log_path)
        return
        
    # Filter extreme values
    df_map = df_map[df_map['CPT_Years'] <= 10] # focus on within 10 years
    
    try:
        world = gpd.read_file(WORLD_SHP)
    except:
        world = None
        
    fig, ax = plt.subplots(figsize=(15, 8))
    if world is not None:
        world.plot(ax=ax, color='#f0f0f0', edgecolor='white')
        
    sc = ax.scatter(
        df_map['lon'], df_map['lat'],
        c=df_map['CPT_Years'],
        s=10,
        cmap='RdYlGn_r', # shorter is greener, longer is redder
        norm=Normalize(vmin=0, vmax=5), # emphasize differences within 0-5 years
        alpha=0.8,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label='Carbon Payback Time (Years)', fraction=0.02, pad=0.04)
    plt.title("Global Distribution of Solar Carbon Payback Time", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    filename = "5_Map_Global_CPT.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(df_map[['fid', 'lon', 'lat', 'CPT_Years']], filename, output_dir, log_path)

def process_scenario(scenario_name):
    """Process a single scenario"""
    output_dir = os.path.join(BASE_DIR, scenario_name)
    input_csv = os.path.join(output_dir, "Solar_Carbon_Payback_Time.csv")
    log_path = os.path.join(output_dir, "Solar_CPT_Viz_Log.txt")
    
    ensure_dir(output_dir)
    if os.path.exists(log_path):
        os.remove(log_path)
        
    log_message(f"=== Start plotting scenario: {scenario_name} ===", log_path)
    
    if not os.path.exists(input_csv):
        log_message(f"Error: input file not found {input_csv}", log_path)
        return

    df = pd.read_csv(input_csv)
    log_message(f"Records loaded: {len(df)}", log_path)
    
    # Filter invalid CPT (e.g. NaN or negative)
    df = df[df['CPT_Years'] > 0].dropna(subset=['CPT_Years'])
    log_message(f"Valid CPT records: {len(df)}", log_path)
    
    # Plotting
    plot_cpt_distribution(df, output_dir, log_path)
    plot_cpt_vs_pvout(df, output_dir, log_path)
    plot_cpt_vs_grid_ef(df, output_dir, log_path)
    plot_country_ranking(df, output_dir, log_path)
    plot_cpt_map(df, output_dir, log_path)
    
    log_message(f"=== Scenario {scenario_name} plotting completed ===\n", log_path)

def main():
    print(">>> Starting multi-scenario solar CPT visualization ...")
    for scenario in SCENARIOS:
        process_scenario(scenario)
    print(">>> All scenario visualizations completed.")

if __name__ == "__main__":
    main()
