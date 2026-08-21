# -*- coding: utf-8 -*-
"""
Wind carbon payback time (CPT) visualization - multi-scenario version
Author: 锐多宝 (Trae AI)
Date: 2026-02-06

Functions:
1. Iterate over three scenarios (optimistic, standard, pessimistic)
2. Read the wind CPT results of each scenario (Wind_Carbon_Payback_Time.csv)
3. Generate statistical charts and save them to the corresponding scenario folder:
   - CPT frequency distribution histogram
   - CPT vs CF scatter plot
   - CPT vs Grid EF scatter plot
   - Country average CPT ranking (Bar Plot)
   - Global CPT distribution map (Scatter Plot)
   - [New] Country average CPT map (Choropleth Map)
4. Export the statistics corresponding to the charts
   - [New] Country average CPT statistics table

Input:
- 制图\5.2.风机碳回本周期\[scenario]\Wind_Carbon_Payback_Time.csv

Output:
- 制图\5.2.风机碳回本周期\[scenario]\charts...
- Run log
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

# Scenario list
SCENARIOS = ['乐观场景', '标准场景', '悲观场景']

# Base paths
BASE_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\5.2.风机碳回本周期"
POWER_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Wind_Power_Potential.csv" # used to get lon/lat

# World map Shapefile
try:
    # Prefer the local path
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

def export_plot_data(df, filename, output_dir, log_path):
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
    sns.histplot(plot_df['CPT_Years'], bins=50, kde=True, color='#1f77b4')
    
    plt.title("Distribution of Wind Carbon Payback Time (CPT)", fontsize=16, fontweight='bold')
    plt.xlabel("Carbon Payback Time (Years)", fontsize=12)
    plt.ylabel("Count of Wind Sites", fontsize=12)
    
    # Add mean line
    mean_val = plot_df['CPT_Years'].mean()
    plt.axvline(mean_val, color='r', linestyle='--', label=f'Mean: {mean_val:.2f} yrs')
    plt.legend()
    
    filename = "1_Hist_CPT_Distribution.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(plot_df['CPT_Years'].describe(), filename, output_dir, log_path)

def plot_cpt_vs_cf(df, output_dir, log_path):
    """CPT vs Capacity Factor scatter plot"""
    log_message("Plotting 2. CPT vs Capacity Factor scatter plot...", log_path)
    
    if 'capacity_factor' not in df.columns:
        log_message("Warning: missing Capacity Factor data; skipping plot.", log_path)
        return

    plot_df = df[df['CPT_Years'] <= 20].copy()
    
    plt.figure(figsize=(10, 6))
    # Use Hexbin
    plt.hexbin(plot_df['capacity_factor'], plot_df['CPT_Years'], gridsize=50, cmap='Blues', mincnt=1)
    cb = plt.colorbar(label='Count of Sites')
    
    plt.title("Wind CPT vs. Resource Potential (Capacity Factor)", fontsize=16, fontweight='bold')
    plt.xlabel("Capacity Factor (0-1)", fontsize=12)
    plt.ylabel("Carbon Payback Time (Years)", fontsize=12)
    
    filename = "2_Scatter_CPT_vs_CF.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(plot_df[['capacity_factor', 'CPT_Years']], filename, output_dir, log_path)

def plot_cpt_vs_grid_ef(df, output_dir, log_path):
    """CPT vs Grid EF scatter plot"""
    log_message("Plotting 3. CPT vs Grid EF scatter plot...", log_path)
    
    if 'grid_ef' not in df.columns:
        log_message("Warning: missing Grid EF data; skipping plot.", log_path)
        return

    plot_df = df[df['CPT_Years'] <= 20].copy()
    
    plt.figure(figsize=(10, 6))
    plt.hexbin(plot_df['grid_ef'], plot_df['CPT_Years'], gridsize=50, cmap='Purples', mincnt=1)
    cb = plt.colorbar(label='Count of Sites')
    
    plt.title("Wind CPT vs. Grid Emission Factor", fontsize=16, fontweight='bold')
    plt.xlabel("Grid Emission Factor (tCO2/MWh)", fontsize=12)
    plt.ylabel("Carbon Payback Time (Years)", fontsize=12)
    
    filename = "3_Scatter_CPT_vs_GridEF.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(plot_df[['grid_ef', 'CPT_Years']], filename, output_dir, log_path)

def plot_country_ranking(df, output_dir, log_path):
    """Country average CPT ranking (Ascending - shorter is better)"""
    log_message("Plotting 4. Country CPT ranking...", log_path)
    
    # Filter countries with enough records (e.g. > 50 sites)
    cnt_counts = df['country_final'].value_counts()
    valid_countries = cnt_counts[cnt_counts >= 50].index
    
    plot_df = df[df['country_final'].isin(valid_countries)].copy()
    
    # Compute the average CPT
    cnt_stats = plot_df.groupby('country_final')['CPT_Years'].mean().sort_values(ascending=True).head(20)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=cnt_stats.values, y=cnt_stats.index, palette='RdYlGn_r') # shorter is greener
    
    plt.title("Top 20 Countries with Shortest Wind Carbon Payback Time (Avg)", fontsize=16, fontweight='bold')
    plt.xlabel("Average CPT (Years)", fontsize=12)
    plt.ylabel("")
    
    for i, v in enumerate(cnt_stats.values):
        plt.text(v + 0.05, i, f"{v:.2f}", va='center', fontsize=10)
        
    filename = "4_Bar_Country_CPT_Ranking.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(cnt_stats, filename, output_dir, log_path)

def plot_cpt_map(df, output_dir, log_path):
    """Global CPT distribution map (Scatter)"""
    log_message("Plotting 5. Global CPT distribution map (scatter)...", log_path)
    
    # Need lon/lat
    if not os.path.exists(POWER_CSV):
        log_message("Warning: Power CSV not found; cannot get lon/lat; skipping map.", log_path)
        return
        
    try:
        loc_df = pd.read_csv(POWER_CSV)[['fid', 'lon', 'lat']]
        # Ensure consistent fid types
        loc_df['fid'] = loc_df['fid'].astype(int)
        df['fid'] = df['fid'].astype(int)
        
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
        s=15,
        cmap='RdYlGn_r', # shorter is greener, longer is redder
        norm=Normalize(vmin=0, vmax=3), # wind usually pays back fast; highlight 0-3 years
        alpha=0.8,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label='Carbon Payback Time (Years)', fraction=0.02, pad=0.04)
    plt.title("Global Distribution of Wind Carbon Payback Time", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    filename = "5_Map_Global_CPT.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    export_plot_data(df_map[['fid', 'lon', 'lat', 'CPT_Years']], filename, output_dir, log_path)

def export_country_stats(df, output_dir, log_path):
    """Compute and export the country average CPT"""
    log_message("Computing country average CPT statistics...", log_path)
    
    # Group by country
    stats = df.groupby('country_final')['CPT_Years'].agg(['mean', 'median', 'min', 'max', 'count']).reset_index()
    stats.columns = ['Country', 'Avg_CPT', 'Median_CPT', 'Min_CPT', 'Max_CPT', 'Site_Count']
    stats = stats.sort_values('Avg_CPT')
    
    # Save CSV
    filename = "Country_Average_CPT_Stats.csv"
    csv_path = os.path.join(output_dir, filename)
    stats.to_csv(csv_path, index=False, encoding='utf-8-sig')
    log_message(f"Country average CPT statistics exported: {csv_path}", log_path)
    return stats

def plot_country_avg_map(stats_df, output_dir, log_path):
    """Country average CPT map (Choropleth)"""
    log_message("Plotting 6. Country average CPT map (Choropleth)...", log_path)
    
    try:
        world = gpd.read_file(WORLD_SHP)
    except Exception as e:
        log_message(f"Failed to load map data: {e}", log_path)
        return

    # Merge stats with world map
    # Try to unify the column name for merging
    # Prefer ADMIN; fall back to name
    merge_col = 'ADMIN' if 'ADMIN' in world.columns else 'name'
    if merge_col not in world.columns:
        log_message("Warning: no country name column (ADMIN or name) found in the map data; skipping country map.", log_path)
        return
        
    world_merged = world.merge(stats_df, left_on=merge_col, right_on='Country', how='left')
    
    # Filter out Antarctica
    world_merged = world_merged[world_merged[merge_col] != 'Antarctica']
    
    fig, ax = plt.subplots(figsize=(15, 8))
    
    world_merged.plot(
        column='Avg_CPT',
        ax=ax,
        legend=True,
        legend_kwds={'label': "Average Carbon Payback Time (Years)", 'orientation': "horizontal", 'fraction': 0.05, 'pad': 0.05},
        cmap='RdYlGn_r', # shorter is greener
        missing_kwds={'color': 'lightgrey'},
        edgecolor='black',
        linewidth=0.5,
        vmax=3 # Cap visual range at 3 years
    )
    
    plt.title("Global Average Wind Carbon Payback Time by Country", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    filename = "6_Map_Country_Avg_CPT.png"
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()
    
    log_message(f"Country average CPT map saved: {filename}", log_path)


# ================= Scenario processing =================

def process_scenario(scenario_name):
    # Path construction
    input_csv = os.path.join(BASE_DIR, scenario_name, "Wind_Carbon_Payback_Time.csv")
    output_dir = os.path.join(BASE_DIR, scenario_name)
    log_path = os.path.join(output_dir, "Wind_CPT_Viz_Log.txt")
    
    ensure_dir(output_dir)
    if os.path.exists(log_path):
        os.remove(log_path)
        
    log_message(f"=== Starting visualization for scenario: {scenario_name} ===", log_path)
    
    # 1. Load data
    if not os.path.exists(input_csv):
        log_message(f"Error: input file not found {input_csv}", log_path)
        return
        
    df = pd.read_csv(input_csv)
    log_message(f"Loaded records: {len(df)}", log_path)
    
    # Filter invalid CPT (e.g. NaN or negative)
    df = df[df['CPT_Years'] > 0].dropna(subset=['CPT_Years'])
    log_message(f"Valid CPT records: {len(df)}", log_path)
    
    if df.empty:
        log_message("Warning: no valid data; skipping plots.", log_path)
        return

    # 2. Plot
    plot_cpt_distribution(df, output_dir, log_path)
    plot_cpt_vs_cf(df, output_dir, log_path)
    plot_cpt_vs_grid_ef(df, output_dir, log_path)
    plot_country_ranking(df, output_dir, log_path)
    plot_cpt_map(df, output_dir, log_path)
    
    # 3. New: country average statistics and map
    stats_df = export_country_stats(df, output_dir, log_path)
    plot_country_avg_map(stats_df, output_dir, log_path)
    
    log_message(f"=== Visualization for scenario {scenario_name} complete ===\n", log_path)


def main():
    print(">>> Starting multi-scenario wind CPT visualization ...")
    
    for scenario in SCENARIOS:
        process_scenario(scenario)
        
    print(">>> All scenario visualizations complete.")

if __name__ == "__main__":
    main()
