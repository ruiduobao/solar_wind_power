# -*- coding: utf-8 -*-
"""
Wind-induced biomass carbon loss statistical analysis and mapping
Author: 锐多宝 (Trae AI)
Date: 2026-01-27
Description:
    Read Wind_Biomass_Loss_Result.csv for multi-dimensional statistical analysis of biomass carbon loss.
    
    Main figures:
    1. [Global distribution] Spatial distribution map of biomass carbon loss (Scatter Map)
    2. [Country ranking] Ranking of total biomass carbon loss by country (Bar Chart)
    3. [Land type contribution] Carbon loss contribution of different land use types (Stacked Bar / Pie)
    4. [Loss intensity] Distribution of carbon loss per unit area (KDE / Histogram)
    5. [Temporal change] Annual trend of new biomass carbon loss (Bar Chart)
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
INPUT_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.2.2风电生物碳损失\Wind_Biomass_Loss_Result.csv"

# Try to obtain the world map path
try:
    WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')
except AttributeError:
    # Fallback url or path
    WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"

# Wind turbine vector path (used to obtain longitude/latitude and country information)
WIND_SHP_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机80米缓冲区.shp"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.2.2风电生物碳损失"

# Plot style
sns.set_theme(style="ticks", font="Arial", context="paper")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# ================= Helper functions =================

def ensure_dir(path):
    """Ensure the directory exists"""
    if not os.path.exists(path):
        os.makedirs(path)

def export_plot_data(df, filename):
    """Export the chart data as a CSV file"""
    csv_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '.csv'))
    try:
        df.to_csv(csv_path, index=True, encoding='utf-8-sig')
        print(f"Data exported: {csv_path}")
    except Exception as e:
        print(f"Export failed: {e}")

# ================= Data loading =================

def load_data():
    """Load the wind biomass carbon loss data"""
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV)
    
    # Supplement longitude/latitude information (obtained from the SHP)
    if os.path.exists(WIND_SHP_PATH):
        print(f"Reading the wind turbine vector file for location information: {WIND_SHP_PATH}")
        try:
            gdf = gpd.read_file(WIND_SHP_PATH)
            
            # Ensure it is in a geographic projection
            if gdf.crs and gdf.crs.to_string() != 'EPSG:4326':
                print("    Reprojecting to EPSG:4326...")
                gdf = gdf.to_crs(epsg=4326)
            
            # Compute centroids
            print("    Computing centroid coordinates...")
            gdf['lon'] = gdf.geometry.centroid.x
            gdf['lat'] = gdf.geometry.centroid.y
            
            # Extract the needed columns
            # Note: fid in the SHP is float while it may be int in the CSV; they need to be unified
            gdf['fid'] = gdf['fid'].astype(int)
            
            # Prepare the DataFrame for merging
            loc_df = gdf[['fid', 'lon', 'lat', 'COUNTRY']]
            loc_df = loc_df.rename(columns={'COUNTRY': 'country'})
            
            # Merge
            print("    Merging location information...")
            df = df.merge(loc_df, on='fid', how='left')
            
        except Exception as e:
            print(f"Failed to read SHP: {e}")
            df['lon'] = 0
            df['lat'] = 0
            df['country'] = 'Unknown'
    else:
        print(f"Warning: {WIND_SHP_PATH} not found; the map cannot be plotted.")
        df['lon'] = 0
        df['lat'] = 0
        df['country'] = 'Unknown'
    
    # Fill missing values
    df['Loss_Bio_tC'] = df['Loss_Bio_tC'].fillna(0)
    df['country'] = df['country'].fillna('Unknown')
    
    # Clean the year
    df['year'] = df['installation_year'].fillna(2017).astype(int)
    df.loc[df['year'] < 2010, 'year'] = 2010
    
    print(f"Data loading complete; {len(df)} records in total.")
    return df

# ================= Plotting functions =================

def plot_loss_map(df):
    """1. Global biomass carbon loss distribution map"""
    print("Plotting 1. Biomass carbon loss map...")
    
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
        s=plot_df['Loss_Bio_tC'] / plot_df['Loss_Bio_tC'].max() * 50 + 2, # Size varies with loss
        cmap='Blues',  # Use the blue scheme for wind power
        norm=LogNorm(vmin=plot_df['Loss_Bio_tC'].quantile(0.05), vmax=plot_df['Loss_Bio_tC'].quantile(0.99)),
        alpha=0.8,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label='Biomass Carbon Loss (tC)', fraction=0.02, pad=0.04)
    plt.title("Global Distribution of Wind-Induced Biomass Carbon Loss", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    filename = "1_Map_Biomass_Loss.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(plot_df[['fid', 'lon', 'lat', 'Loss_Bio_tC']], filename)

def plot_country_ranking(df):
    """2. Biomass carbon loss ranking by country"""
    print("Plotting 2. Country ranking...")
    
    # Aggregate by country
    cnt_stats = df.groupby('country')['Loss_Bio_tC'].sum().sort_values(ascending=False).head(20)
    # Convert to ktC (kilotonnes)
    cnt_stats_kt = cnt_stats / 1000
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x=cnt_stats_kt.values, y=cnt_stats_kt.index, palette='Blues_r')  # Use the blue scheme
    
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
    """3. Loss contribution by land type"""
    print("Plotting 3. Land type contribution...")
    
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
    print("Plotting 4. Annual trend...")
    
    # Filter 2010-2024
    plot_df = df[(df['year'] >= 2010) & (df['year'] <= 2024)]
    
    yr_stats = plot_df.groupby('year')['Loss_Bio_tC'].sum() / 1000 # ktC
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(yr_stats.index, yr_stats.values, color='#1f77b4', alpha=0.7)  # Use blue
    
    plt.title("Annual Wind-Induced Biomass Carbon Loss (2010-2024)", fontsize=16, fontweight='bold')
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
    print("Plotting 5. Loss intensity distribution...")
    
    # Compute intensity: loss / total area (ha)
    # Note: total_area_ha may be 0
    df['Loss_Intensity'] = df['Loss_Bio_tC'] / df['total_area_ha']
    
    # Filter outliers
    plot_df = df[(df['Loss_Intensity'] > 0) & (df['Loss_Intensity'] < 100)] # 100 tC/ha is already an extremely high forest value
    
    plt.figure(figsize=(10, 6))
    sns.histplot(plot_df['Loss_Intensity'], bins=50, kde=True, color='blue')
    
    plt.title("Distribution of Biomass Carbon Loss Intensity", fontsize=16, fontweight='bold')
    plt.xlabel("Carbon Loss Intensity (tC/ha)", fontsize=12)
    plt.ylabel("Count of Wind Sites", fontsize=12)
    
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

def plot_biomass_density_vs_loss(df):
    """6. Biomass density vs loss relationship plot"""
    print("Plotting 6. Biomass density vs loss relationship...")
    
    # Filter out zero values
    plot_df = df[(df['mean_biomass_density_mg_ha'] > 0) & (df['Loss_Bio_tC'] > 0)]
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=plot_df, x='mean_biomass_density_mg_ha', y='Loss_Bio_tC', 
                   alpha=0.6, s=50, color='darkblue')
    
    # Add a trend line
    z = np.polyfit(plot_df['mean_biomass_density_mg_ha'], plot_df['Loss_Bio_tC'], 1)
    p = np.poly1d(z)
    plt.plot(plot_df['mean_biomass_density_mg_ha'], p(plot_df['mean_biomass_density_mg_ha']), 
             "r--", alpha=0.8, label=f'Trend: y = {z[0]:.4f}x + {z[1]:.2f}')
    
    plt.title("Relationship Between Biomass Density and Carbon Loss", fontsize=16, fontweight='bold')
    plt.xlabel("Mean Biomass Density (Mg/ha)", fontsize=12)
    plt.ylabel("Carbon Loss (tC)", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    filename = "6_Scatter_Biomass_Density_vs_Loss.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(plot_df[['mean_biomass_density_mg_ha', 'Loss_Bio_tC']], filename)

def plot_correction_factor_analysis(df):
    """7. Correction factor analysis plot"""
    print("Plotting 7. Correction factor analysis...")
    
    # Filter out zero values
    plot_df = df[(df['Ratio_Eco'] > 0) & (df['Loss_Bio_tC'] > 0)]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Subplot 1: Ratio_Eco vs Loss_Bio_tC
    sns.scatterplot(data=plot_df, x='Ratio_Eco', y='Loss_Bio_tC', 
                   alpha=0.6, s=50, color='green', ax=ax1)
    ax1.set_title("Ecological Ratio vs Carbon Loss", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Ecological Ratio (Area_Eco/Total_Area)", fontsize=12)
    ax1.set_ylabel("Carbon Loss (tC)", fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: SUM_Bio_Corrected vs SUM_Bio_GIS
    sns.scatterplot(data=plot_df, x='SUM_Bio_GIS', y='SUM_Bio_Corrected', 
                   alpha=0.6, s=50, color='orange', ax=ax2)
    # Add the diagonal line
    min_val = min(plot_df['SUM_Bio_GIS'].min(), plot_df['SUM_Bio_Corrected'].min())
    max_val = max(plot_df['SUM_Bio_GIS'].max(), plot_df['SUM_Bio_Corrected'].max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='Perfect Correction')
    ax2.set_title("Corrected vs Original Biomass Stock", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Original Biomass Stock (tC)", fontsize=12)
    ax2.set_ylabel("Corrected Biomass Stock (tC)", fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    filename = "7_Correction_Factor_Analysis.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    # Export the statistics data
    stats_df = pd.DataFrame({
        'Mean_Ratio_Eco': [plot_df['Ratio_Eco'].mean()],
        'Mean_Sum_Bio_GIS': [plot_df['SUM_Bio_GIS'].mean()],
        'Mean_Sum_Bio_Corrected': [plot_df['SUM_Bio_Corrected'].mean()],
        'Correction_Efficiency': [plot_df['SUM_Bio_Corrected'].mean() / plot_df['SUM_Bio_GIS'].mean()]
    })
    export_plot_data(stats_df, filename)

# ================= Main program =================

def main():
    """Main program"""
    ensure_dir(OUTPUT_DIR)
    
    try:
        df = load_data()
        
        # Overall summary
        total_loss_mt = df['Loss_Bio_tC'].sum() / 1e6
        print(f"\n>>> Overall statistics: Global wind-induced biomass carbon total loss = {total_loss_mt:.4f} MtC")
        
        # Plot all figures
        plot_loss_map(df)
        plot_country_ranking(df)
        plot_land_type_contribution(df)
        plot_temporal_trend(df)
        plot_loss_intensity_dist(df)
        plot_biomass_density_vs_loss(df)
        plot_correction_factor_analysis(df)
        
        print(f"\nAll analysis figures generated at: {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
