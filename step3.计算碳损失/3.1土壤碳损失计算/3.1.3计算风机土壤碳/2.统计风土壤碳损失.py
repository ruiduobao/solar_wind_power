# -*- coding: utf-8 -*-
"""
Wind-induced soil carbon loss statistical analysis and mapping
Author: 锐多宝 (Trae AI)
Date: 2026-01-27
Description:
    Read Wind_Soil_Loss_Result.csv and perform multi-dimensional statistical analysis of soil carbon loss.
    
    Main charts:
    1. [Global distribution] Soil carbon loss spatial distribution map (Scatter Map)
    2. [Country ranking] Total soil carbon loss ranking by country (Bar Chart)
    3. [Land cover contribution] Carbon loss contribution by land cover type (Stacked Bar / Pie)
    4. [Loss intensity] Carbon loss intensity per unit area (KDE / Histogram)
    5. [Temporal trend] Annual new soil carbon loss trend (Bar Chart)
    6. [Ecological background] Ecological background purity histogram
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
INPUT_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.1.2风电土壤碳损失\Wind_Soil_Loss_Result.csv"
SHP_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机80米缓冲区.shp"

# Try to obtain the world map path
try:
    # Try to read the local ne_110m_admin_0_countries.shp
    WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"
    if not os.path.exists(WORLD_SHP):
         WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')
except:
    WORLD_SHP = None

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.1.2风电土壤碳损失"

# Plotting style
sns.set_theme(style="whitegrid", font="Arial", context="paper")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.unicode_minus'] = False

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

# ================= Load data =================

def load_data():
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV)
    
    # Supplement lon/lat from the vector file (more accurate than the CSV join)
    if os.path.exists(SHP_PATH):
        print("Extracting lon/lat from SHP file...")
        try:
            gdf = gpd.read_file(SHP_PATH)
            
            # Ensure consistent fid types
            if 'fid_1' in gdf.columns:
                gdf.rename(columns={'fid_1': 'fid'}, inplace=True)
            
            # If no fid, use the index
            if 'fid' not in gdf.columns:
                gdf['fid'] = gdf.index
                
            gdf['fid'] = gdf['fid'].astype(int)
            df['fid'] = df['fid'].astype(int)
            
            # Extract centroid
            if gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
                
            gdf['lon'] = gdf.geometry.centroid.x
            gdf['lat'] = gdf.geometry.centroid.y
            
            # Merge lon/lat
            country_col = 'country' if 'country' in gdf.columns else 'COUNTRY'
            if country_col not in gdf.columns:
                 gdf['country'] = 'Unknown'
                 country_col = 'country'
            
            loc_df = gdf[['fid', 'lon', 'lat', country_col]].rename(columns={country_col: 'country'})
            
            # If the original table already has lon/lat/country, delete them first to avoid duplicates
            for col in ['lon', 'lat', 'country']:
                if col in df.columns:
                    del df[col]
                    
            df = df.merge(loc_df, on='fid', how='left')
            print("Lon/lat join succeeded.")
            
        except Exception as e:
            print(f"Failed to read SHP: {e}")
    else:
        print("SHP file not found")
        
    # Check whether total_area_m2 exists
    if 'total_area_m2' not in df.columns:
        if 'total_area_ha' in df.columns:
            df['total_area_m2'] = df['total_area_ha'] * 10000
        else:
            print("Error: area column not found (total_area_m2 or total_area_ha)")
    
    # Fill missing values
    df['Loss_Soil_tC'] = df['Loss_Soil_tC'].fillna(0)
    
    # Clean year
    if 'installation_year' not in df.columns:
        if 'constructi' in df.columns:
             df['year'] = df['constructi'].fillna(2017).astype(int)
        else:
             df['year'] = 2017
    else:
        df['year'] = df['installation_year'].fillna(2017).astype(int)
        
    # Assign all data before 2017 to 2017
    df.loc[df['year'] < 2017, 'year'] = 2017
    
    print(f"Data loaded, {len(df)} records in total.")
    return df

# ================= Plotting functions =================

def plot_loss_map(df):
    """1. Global soil carbon loss distribution map"""
    print("Plotting 1. Soil carbon loss map...")
    
    try:
        world = gpd.read_file(WORLD_SHP)
    except:
        world = None
        
    fig, ax = plt.subplots(figsize=(15, 8))
    
    if world is not None:
        world.plot(ax=ax, color='#f0f0f0', edgecolor='white')
        
    # Filter out 0 values
    plot_df = df[df['Loss_Soil_tC'] > 0].sort_values('Loss_Soil_tC')
    
    if plot_df.empty:
        print("No data with loss greater than 0, skipping plot")
        return

    sc = ax.scatter(
        plot_df['lon'], plot_df['lat'],
        c=plot_df['Loss_Soil_tC'],
        s=plot_df['Loss_Soil_tC'] / plot_df['Loss_Soil_tC'].max() * 50 + 2, 
        cmap='Blues', # blue colormap for wind to distinguish from solar
        norm=LogNorm(vmin=plot_df['Loss_Soil_tC'].quantile(0.05), vmax=plot_df['Loss_Soil_tC'].quantile(0.99)),
        alpha=0.8,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label='Soil Carbon Loss (tC)', fraction=0.02, pad=0.04)
    plt.title("Global Distribution of Wind-Induced Soil Carbon Loss", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    filename = "1_Map_Wind_Soil_Loss.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(plot_df[['fid', 'lon', 'lat', 'Loss_Soil_tC']], filename)

def plot_country_ranking(df):
    """2. Country-level soil carbon loss ranking"""
    print("Plotting 2. Country ranking...")
    
    # Aggregate by country
    if 'country' not in df.columns:
        print("Missing country information, skipping ranking plot")
        return

    cnt_stats = df.groupby('country')['Loss_Soil_tC'].sum().sort_values(ascending=False).head(20)
    cnt_stats_kt = cnt_stats / 1000
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=cnt_stats_kt.values, y=cnt_stats_kt.index, palette='Blues_r')
    
    plt.title("Top 20 Countries by Wind Soil Carbon Loss", fontsize=16, fontweight='bold')
    plt.xlabel("Total Soil Carbon Loss (ktC)", fontsize=12)
    plt.ylabel("")
    
    for i, v in enumerate(cnt_stats_kt.values):
        plt.text(v + v*0.01, i, f"{v:.1f}", va='center', fontsize=10)
        
    filename = "2_Bar_Country_Ranking.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(cnt_stats, filename)

def plot_land_type_contribution(df):
    """3. Loss contribution by land cover type"""
    print("Plotting 3. Land type contribution...")
    
    cols = ['Trees', 'Grass', 'Shrub', 'Crops']
    sums = []
    labels = ['Forest', 'Grassland', 'Shrubland', 'Cropland']
    
    for c in cols:
        stock_col = f'Stock_Soil_{c}'
        if stock_col in df.columns and 'K_Wind' in df.columns:
            loss_est = (df[stock_col] * df['K_Wind']).sum()
            sums.append(loss_est)
        else:
            sums.append(0)
    
    # Pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(sums, labels=labels, autopct='%1.1f%%', startangle=90, 
            colors=['#2ca02c', '#98df8a', '#d62728', '#ff7f0e'],
            textprops={'fontsize': 12})
            
    plt.title("Contribution of Land Cover Types to Wind Soil Carbon Loss", fontsize=16, fontweight='bold')
    
    filename = "3_Pie_LandType_Contribution.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(pd.DataFrame({'Type': labels, 'Loss_tC': sums}), filename)

def plot_temporal_trend(df):
    """4. Annual loss trend"""
    print("Plotting 4. Annual trend...")
    
    plot_df = df[(df['year'] >= 2017) & (df['year'] <= 2024)]
    
    yr_stats = plot_df.groupby('year')['Loss_Soil_tC'].sum() / 1000 # ktC
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(yr_stats.index, yr_stats.values, color='#1f77b4', alpha=0.7)
    
    plt.title("Annual Wind-Induced Soil Carbon Loss (2017-2024)", fontsize=16, fontweight='bold')
    plt.ylabel("Annual Soil Carbon Loss (ktC)", fontsize=12)
    plt.xlabel("Year", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    if len(yr_stats) > 1:
        z = np.polyfit(yr_stats.index, yr_stats.values, 1)
        p = np.poly1d(z)
        plt.plot(yr_stats.index, p(yr_stats.index), "k--", alpha=0.5, label='Trend')
    
    filename = "4_Bar_Annual_Trend.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(yr_stats, filename)

def plot_loss_intensity_dist(df):
    """5. Loss intensity distribution (tC/ha)"""
    print("Plotting 5. Loss intensity distribution...")
    
    df['Loss_Intensity'] = df['Loss_Soil_tC'] / (df['total_area_m2'] / 10000)
    
    plot_df = df[(df['Loss_Intensity'] > 0) & (df['Loss_Intensity'] < 200)]
    
    plt.figure(figsize=(10, 6))
    sns.histplot(plot_df['Loss_Intensity'], bins=50, kde=True, color='blue')
    
    plt.title("Distribution of Wind Soil Carbon Loss Intensity", fontsize=16, fontweight='bold')
    plt.xlabel("Soil Carbon Loss Intensity (tC/ha)", fontsize=12)
    plt.ylabel("Count of Wind Sites", fontsize=12)
    
    mean_val = plot_df['Loss_Intensity'].mean()
    median_val = plot_df['Loss_Intensity'].median()
    plt.axvline(mean_val, color='k', linestyle='--', label=f'Mean: {mean_val:.2f}')
    plt.axvline(median_val, color='r', linestyle='-.', label=f'Median: {median_val:.2f}')
    plt.legend()
    
    filename = "5_Hist_Loss_Intensity.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(plot_df['Loss_Intensity'].describe(), filename)

def plot_ratio_eco_hist(df):
    """6. Ecological background purity histogram"""
    print("Plotting 6. Ratio_Eco histogram...")
    
    plt.figure(figsize=(10, 6))
    sns.histplot(df['Ratio_Eco'], bins=20, kde=False, color='#2ca02c', stat='percent')
    
    plt.title("Distribution of Ecological Validity Ratio (Ratio_Eco)", fontsize=16, fontweight='bold')
    plt.xlabel("Ecological Ratio (Eco Area / Total Area)", fontsize=12)
    plt.ylabel("Percentage of Sites (%)", fontsize=12)
    plt.xlim(0, 1.05)
    
    mean_val = df['Ratio_Eco'].mean()
    plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
    plt.legend()
    
    filename = "6_Hist_Ratio_Eco.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(df['Ratio_Eco'].describe(), filename)

# ================= Main program =================

def main():
    ensure_dir(OUTPUT_DIR)
    
    try:
        df = load_data()
        
        # Overall summary
        total_loss_mt = df['Loss_Soil_tC'].sum() / 1e6
        print(f"\n>>> Overall statistics: total global wind-induced soil carbon loss = {total_loss_mt:.4f} MtC")
        
        plot_loss_map(df)
        plot_country_ranking(df)
        plot_land_type_contribution(df)
        plot_temporal_trend(df)
        plot_loss_intensity_dist(df)
        plot_ratio_eco_hist(df)
        
        print(f"\nAll analysis charts generated at: {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
