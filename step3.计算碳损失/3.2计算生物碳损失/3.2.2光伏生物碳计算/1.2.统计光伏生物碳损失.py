# -*- coding: utf-8 -*-
"""
Solar Biomass Carbon Loss Statistics and Mapping
Author: 锐多宝 (Trae AI)
Date: 2026-01-07
Description:
    Read Solar_Biomass_Loss_Result.csv and perform multi-dimensional
    statistics and analysis of biomass carbon loss.

    Main figures:
    1. [Global Distribution] Spatial distribution of biomass carbon loss (Scatter Map)
    2. [Country Ranking] Total biomass carbon loss ranking by country (Bar Chart)
    3. [Land Cover Contribution] Carbon loss contribution by land cover type (Stacked Bar / Pie)
    4. [Loss Intensity] Carbon loss per unit area distribution (KDE / Histogram)
    5. [Temporal Trend] Annual newly added biomass carbon loss trend (Bar Chart)
"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import LogNorm

# ================= Configuration =================

# Input data
INPUT_CSV = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\结果数据\计算生物碳损失\Solar_Biomass_Loss_Result.csv"

# Try to obtain the world map path
try:
    WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')
except AttributeError:
    # Fallback url or path
    WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.2.1光伏生物碳损失"

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

def export_plot_data(df, filename):
    csv_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '.csv'))
    try:
        df.to_csv(csv_path, index=True, encoding='utf-8-sig')
        print(f"Data exported: {csv_path}")
    except Exception as e:
        print(f"Export failed: {e}")

# ================= Data loading =================

def load_data():
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV)
    
    # Supplement longitude/latitude info (needs to link the original SHP or obtain from Solar_Power_Potential.csv)
    # Here we assume we can get it from INPUT_CSV, or join through fid
    # Since INPUT_CSV is a calculation result, it may not contain longitude/latitude.
    # We try to read Solar_Power_Potential.csv to obtain longitude/latitude
    
    potential_csv = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Solar_Power_Potential.csv"
    if os.path.exists(potential_csv):
        print("Joining longitude/latitude info...")
        # Additionally read the area column
        loc_df = pd.read_csv(potential_csv)[['fid', 'lon', 'lat', 'country', 'area_m2']]
        df = df.merge(loc_df, on='fid', how='left')
        # Rename the area column to total_area_m2 to fit the code
        if 'area_m2' in df.columns and 'total_area_m2' not in df.columns:
            df['total_area_m2'] = df['area_m2']
    else:
        print("Warning: Solar_Power_Potential.csv not found, cannot plot the map.")
        df['lon'] = 0
        df['lat'] = 0
        df['country'] = df['country_iso_a3'] # Fallback
    
    # Fill missing values
    df['Loss_Bio_tC'] = df['Loss_Bio_tC'].fillna(0)
    
    # Clean the year
    df['year'] = df['installation_year'].fillna(2017).astype(int)
    df.loc[df['year'] < 2010, 'year'] = 2010
    
    print(f"Data loaded, {len(df)} records in total.")
    return df

# ================= Plotting functions =================

def plot_loss_map(df):
    """1. Global biomass carbon loss distribution map"""
    print("Plotting 1. biomass carbon loss map...")
    
    try:
        world = gpd.read_file(WORLD_SHP)
    except:
        world = None
        
    fig, ax = plt.subplots(figsize=(15, 8))
    
    if world is not None:
        world.plot(ax=ax, color='#f0f0f0', edgecolor='white')
        
    # Filter out zero values
    plot_df = df[df['Loss_Bio_tC'] > 0].sort_values('Loss_Bio_tC')
    
    sc = ax.scatter(
        plot_df['lon'], plot_df['lat'],
        c=plot_df['Loss_Bio_tC'],
        s=plot_df['Loss_Bio_tC'] / plot_df['Loss_Bio_tC'].max() * 50 + 2, # Size scales with loss
        cmap='Reds',
        norm=LogNorm(vmin=plot_df['Loss_Bio_tC'].quantile(0.05), vmax=plot_df['Loss_Bio_tC'].quantile(0.99)),
        alpha=0.8,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label='Biomass Carbon Loss (tC)', fraction=0.02, pad=0.04)
    plt.title("Global Distribution of Solar-Induced Biomass Carbon Loss", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    filename = "1_Map_Biomass_Loss.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(plot_df[['fid', 'lon', 'lat', 'Loss_Bio_tC']], filename)

def plot_country_ranking(df):
    """2. Biomass carbon loss ranking by country"""
    print("Plotting 2. country ranking...")
    
    # Aggregate by country
    cnt_stats = df.groupby('country')['Loss_Bio_tC'].sum().sort_values(ascending=False).head(20)
    # Convert to ktC (thousand tonnes)
    cnt_stats_kt = cnt_stats / 1000
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=cnt_stats_kt.values, y=cnt_stats_kt.index, palette='Reds_r')
    
    plt.title("Top 20 Countries by Total Biomass Carbon Loss", fontsize=16, fontweight='bold')
    plt.xlabel("Total Biomass Carbon Loss (ktC)", fontsize=12)
    plt.ylabel("")
    
    # Add value labels
    for i, v in enumerate(cnt_stats_kt.values):
        plt.text(v + v*0.01, i, f"{v:.1f}", va='center', fontsize=10)
        
    filename = "2_Bar_Country_Ranking.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(cnt_stats, filename)

def plot_land_type_contribution(df):
    """3. Loss contribution by land cover type"""
    print("Plotting 3. land cover type contribution...")
    
    cols = ['Loss_Bio_Trees_tC', 'Loss_Bio_Grass_tC', 'Loss_Bio_Shrub_tC', 'Loss_Bio_Crops_tC']
    labels = ['Forest', 'Grassland', 'Shrubland', 'Cropland']
    
    sums = [df[c].sum() for c in cols]
    
    # Pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(sums, labels=labels, autopct='%1.1f%%', startangle=90, 
            colors=['#2ca02c', '#98df8a', '#d62728', '#ff7f0e'],
            textprops={'fontsize': 12})
            
    plt.title("Contribution of Land Cover Types to Total Carbon Loss", fontsize=16, fontweight='bold')
    
    filename = "3_Pie_LandType_Contribution.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(pd.DataFrame({'Type': labels, 'Loss_tC': sums}), filename)

def plot_temporal_trend(df):
    """4. Annual loss trend"""
    print("Plotting 4. annual trend...")
    
    # Filter 2010-2024
    plot_df = df[(df['year'] >= 2010) & (df['year'] <= 2024)]
    
    yr_stats = plot_df.groupby('year')['Loss_Bio_tC'].sum() / 1000 # ktC
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(yr_stats.index, yr_stats.values, color='#d62728', alpha=0.7)
    
    plt.title("Annual Solar-Induced Biomass Carbon Loss (2010-2024)", fontsize=16, fontweight='bold')
    plt.ylabel("Annual Carbon Loss (ktC)", fontsize=12)
    plt.xlabel("Year", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    # Trend line
    z = np.polyfit(yr_stats.index, yr_stats.values, 1)
    p = np.poly1d(z)
    plt.plot(yr_stats.index, p(yr_stats.index), "k--", alpha=0.5, label='Trend')
    
    filename = "4_Bar_Annual_Trend.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(yr_stats, filename)

def plot_loss_intensity_dist(df):
    """5. Loss intensity distribution (tC/ha)"""
    print("Plotting 5. loss intensity distribution...")
    
    # Calculate intensity: loss / total area (ha)
    # Note that total_area_ha may be 0
    df['Loss_Intensity'] = df['Loss_Bio_tC'] / (df['total_area_m2'] / 10000)
    
    # Filter outliers
    plot_df = df[(df['Loss_Intensity'] > 0) & (df['Loss_Intensity'] < 100)] # 100 tC/ha is already extremely high for forest
    
    plt.figure(figsize=(10, 6))
    sns.histplot(plot_df['Loss_Intensity'], bins=50, kde=True, color='brown')
    
    plt.title("Distribution of Biomass Carbon Loss Intensity", fontsize=16, fontweight='bold')
    plt.xlabel("Carbon Loss Intensity (tC/ha)", fontsize=12)
    plt.ylabel("Count of Solar Sites", fontsize=12)
    
    # Add statistics
    mean_val = plot_df['Loss_Intensity'].mean()
    median_val = plot_df['Loss_Intensity'].median()
    plt.axvline(mean_val, color='k', linestyle='--', label=f'Mean: {mean_val:.2f}')
    plt.axvline(median_val, color='b', linestyle='-.', label=f'Median: {median_val:.2f}')
    plt.legend()
    
    filename = "5_Hist_Loss_Intensity.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(plot_df['Loss_Intensity'].describe(), filename)

# ================= Main program =================

def main():
    ensure_dir(OUTPUT_DIR)
    
    try:
        df = load_data()
        
        # Overall summary
        total_loss_mt = df['Loss_Bio_tC'].sum() / 1e6
        print(f"\n>>> Overall statistics: total solar biomass carbon loss = {total_loss_mt:.4f} MtC")
        
        plot_loss_map(df)
        plot_country_ranking(df)
        plot_land_type_contribution(df)
        plot_temporal_trend(df)
        plot_loss_intensity_dist(df)
        
        print(f"\nAll analysis figures have been generated at: {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
