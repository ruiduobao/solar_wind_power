# -*- coding: utf-8 -*-
"""
Wind Carbon Payback Time (CPT) Visualization - Without Grid Emission Factors
Author: 锐多宝 (Trae AI)
Date: 2026-01-28

Functions:
1. Read the wind CPT results (Wind_CPT_No_Grid_EF.csv)
2. Generate statistical charts:
   - CPT frequency distribution histogram
   - CPT vs Capacity Factor scatter plot
   - Average CPT ranking by country
   - Global CPT distribution map
3. Export the statistics corresponding to each chart

Input:
- Wind_CPT_No_Grid_EF.csv

Output:
- Statistical charts (.png)
- Statistical data (.csv)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from matplotlib.colors import Normalize
from datetime import datetime

# ================= Configuration =================

OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\6.2.风机碳回本周期(不考虑排放因子)"
INPUT_CSV = os.path.join(OUTPUT_DIR, "Wind_CPT_No_Grid_EF.csv")
LOG_PATH = os.path.join(OUTPUT_DIR, "Wind_CPT_No_Grid_EF_Viz_Log.txt")
POWER_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Wind_Power_Potential.csv" # Used to get the longitude/latitude

# World map Shapefile
try:
    WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\行政区划\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"
    if not os.path.exists(WORLD_SHP):
        WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')
except:
    WORLD_SHP = None

# Plot style
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

def log_message(message):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{time_str}] {message}"
    print(full_message)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def export_plot_data(df, filename):
    csv_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '.csv'))
    df.to_csv(csv_path, index=True, encoding='utf-8-sig')
    log_message(f"Chart data exported: {csv_path}")

# ================= Plotting functions =================

def plot_cpt_distribution(df):
    """CPT frequency distribution histogram"""
    log_message("Plotting 1. CPT distribution histogram...")
    
    plot_df = df[df['CPT_Years_NoEF'] <= 20].copy()
    
    plt.figure(figsize=(10, 6))
    sns.histplot(plot_df['CPT_Years_NoEF'], bins=50, kde=True, color='#1f77b4')
    
    plt.title("Distribution of Wind CPT (Global Avg Grid EF)", fontsize=16, fontweight='bold')
    plt.xlabel("Carbon Payback Time (Years)", fontsize=12)
    plt.ylabel("Count of Wind Sites", fontsize=12)
    
    mean_val = plot_df['CPT_Years_NoEF'].mean()
    plt.axvline(mean_val, color='r', linestyle='--', label=f'Mean: {mean_val:.2f} yrs')
    plt.legend()
    
    filename = "1_Hist_CPT_Distribution.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(plot_df['CPT_Years_NoEF'].describe(), filename)

def plot_cpt_vs_cf(df):
    """CPT vs Capacity Factor scatter plot"""
    log_message("Plotting 2. CPT vs Capacity Factor scatter plot...")
    
    if 'cf_val' not in df.columns:
        log_message("Warning: Capacity Factor data is missing, skipping plot.")
        return

    plot_df = df[df['CPT_Years_NoEF'] <= 20].copy()
    
    plt.figure(figsize=(10, 6))
    plt.hexbin(plot_df['cf_val'], plot_df['CPT_Years_NoEF'], gridsize=50, cmap='Blues', mincnt=1)
    cb = plt.colorbar(label='Count of Sites')
    
    plt.title("Wind CPT vs. Resource Potential (CF) - No Grid EF Bias", fontsize=16, fontweight='bold')
    plt.xlabel("Capacity Factor (0-1)", fontsize=12)
    plt.ylabel("Carbon Payback Time (Years)", fontsize=12)
    
    filename = "2_Scatter_CPT_vs_CF.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(plot_df[['cf_val', 'CPT_Years_NoEF']], filename)

def plot_country_ranking(df):
    """Average CPT ranking by country (Ascending - shorter is better)"""
    log_message("Plotting 3. Country CPT ranking...")
    
    cnt_counts = df['country_final'].value_counts()
    valid_countries = cnt_counts[cnt_counts >= 50].index
    
    plot_df = df[df['country_final'].isin(valid_countries)].copy()
    
    cnt_stats = plot_df.groupby('country_final')['CPT_Years_NoEF'].mean().sort_values(ascending=True).head(20)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=cnt_stats.values, y=cnt_stats.index, palette='RdYlGn_r')
    
    plt.title("Top 20 Countries with Shortest Wind CPT (Global Avg Grid EF)", fontsize=16, fontweight='bold')
    plt.xlabel("Average CPT (Years)", fontsize=12)
    plt.ylabel("")
    
    for i, v in enumerate(cnt_stats.values):
        plt.text(v + 0.05, i, f"{v:.2f}", va='center', fontsize=10)
        
    filename = "3_Bar_Country_CPT_Ranking.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(cnt_stats, filename)

def plot_cpt_map(df):
    """Global CPT distribution map"""
    log_message("Plotting 4. Global CPT distribution map...")
    
    if not os.path.exists(POWER_CSV):
        log_message("Warning: Power CSV not found, cannot get longitude/latitude, skipping map plot.")
        return
        
    try:
        loc_df = pd.read_csv(POWER_CSV)[['fid', 'lon', 'lat']]
        df_map = df.merge(loc_df, on='fid', how='inner')
    except Exception as e:
        log_message(f"Failed to read longitude/latitude: {e}")
        return
        
    df_map = df_map[df_map['CPT_Years_NoEF'] <= 10]
    
    try:
        world = gpd.read_file(WORLD_SHP)
    except:
        world = None
        
    fig, ax = plt.subplots(figsize=(15, 8))
    if world is not None:
        world.plot(ax=ax, color='#f0f0f0', edgecolor='white')
        
    sc = ax.scatter(
        df_map['lon'], df_map['lat'],
        c=df_map['CPT_Years_NoEF'],
        s=15,
        cmap='RdYlGn_r', 
        norm=Normalize(vmin=0, vmax=3), 
        alpha=0.8,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label='Carbon Payback Time (Years)', fraction=0.02, pad=0.04)
    plt.title("Global Distribution of Wind CPT (Global Avg Grid EF)", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    filename = "4_Map_Global_CPT.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(df_map[['fid', 'lon', 'lat', 'CPT_Years_NoEF']], filename)

def main():
    ensure_dir(OUTPUT_DIR)
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
        
    log_message(">>> Start plotting wind CPT charts (without emission factors) ...")
    
    if not os.path.exists(INPUT_CSV):
        log_message(f"Error: input file not found {INPUT_CSV}")
        return
        
    df = pd.read_csv(INPUT_CSV)
    log_message(f"Loaded records: {len(df)}")
    
    # Filter out invalid CPT
    df = df[df['CPT_Years_NoEF'] > 0].dropna(subset=['CPT_Years_NoEF'])
    log_message(f"Valid CPT records: {len(df)}")
    
    plot_cpt_distribution(df)
    plot_cpt_vs_cf(df)
    plot_country_ranking(df)
    plot_cpt_map(df)
    
    log_message("All charts plotted.")

if __name__ == "__main__":
    main()
