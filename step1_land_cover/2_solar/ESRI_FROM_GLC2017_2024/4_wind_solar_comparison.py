# -*- coding: utf-8 -*-
"""
Comparative analysis of land source between solar and wind power
Author: 锐多宝 (ruiduobao)
Date: 2026-01-06
Description: 
    Compare the similarities and differences between solar and wind power in land occupation, including:
    1. Relative quantity comparison (share of each land cover type)
    2. Absolute quantity comparison (total area occupied by each land cover type)
    3. Spatial distribution comparison (latitude distribution differences)
    4. Trend comparison over time
"""

import os
import sys
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import concurrent.futures
import warnings

# Ignore specific warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*Geometry is in a geographic CRS.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*observed=False.*")

# ================= Log configuration =================
class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding='utf-8')
 
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
 
    def flush(self):
        pass

# ================= Configuration =================

# Wind data paths
WIND_ESRI_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\WIND_ESRI_2017_LandCover_Summary.csv"
WIND_FROM_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\WIND_FROM_2017_LandCover_Summary.csv"
WIND_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机80米缓冲区_2017年之后的风机缓冲区.shp"

# Solar data paths
SOLAR_ESRI_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\SOLAR_ESRI_2017_LandCover_Summary.csv"
SOLAR_FROM_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\SOLAR_FROM_2017_LandCover_Summary.csv"
SOLAR_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\solarpower.shp"

# World map path
WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\代码\结果数据\3.1光伏发电潜力计算\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\\1.土地来源分析\光伏和风电对比"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Set plot style
sns.set_theme(style="whitegrid", font="SimHei")
plt.rcParams['axes.unicode_minus'] = False

# Unified color mapping (based on ESRI)
ESRI_COLORS = {
    "Water": "#1A5BAB",
    "Trees": "#358221",
    "Flooded Vegetation": "#87D19E",
    "Crops": "#FFDB5C",
    "Built Area": "#ED022A",
    "Bare Ground": "#EDE9E4",
    "Snow/Ice": "#F2FAFF",
    "Clouds": "#C8C8C8",
    "Rangeland": "#C6AD8D",
    "Unknown": "#000000"
}

# ================= Data loading functions =================

def load_data(csv_path, shp_path, label):
    """Load and merge data"""
    print(f"Loading {label} data...")
    df = pd.read_csv(csv_path)
    
    # Read SHP to obtain spatial information
    # Only read the required columns to speed up
    gdf = gpd.read_file(shp_path)
    
    # Reproject to compute lon/lat
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    gdf['lat'] = gdf.geometry.centroid.y
    gdf['lon'] = gdf.geometry.centroid.x
    gdf['fid'] = gdf['fid'].astype(int)
    
    # Merge
    merged = df.merge(gdf[['fid', 'lat', 'constructi']], on='fid', how='inner')
    merged['type'] = label
    
    return merged

# ================= Plotting functions =================

def plot_relative_comparison(wind_df, solar_df, color_map, dataset_name):
    """Relative quantity comparison (percentage stacked bar chart) - with data table"""
    # Merge data
    df = pd.concat([wind_df, solar_df])
    
    # Aggregate
    pivot = df.pivot_table(index='type', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Compute percentages
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 8)) # Increase height to accommodate the table
    pivot_pct.plot(kind='barh', stacked=True, ax=ax, color=[color_map.get(c, '#000000') for c in pivot_pct.columns])
    
    plt.title(f"Land cover composition comparison between Solar and Wind (Relative - {dataset_name})", fontsize=16)
    plt.xlabel("Share (%)", fontsize=12)
    plt.ylabel("Energy type", fontsize=12)
    plt.legend(title="Land cover type", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add table
    table_data = pivot_pct.round(2)
    # Transpose to display at the bottom (columns as energy types, rows as land cover types) - or keep as is
    # Keep as is here: rows as Wind/Solar, columns as land cover types. 
    # If there are too many columns, it may not fit. ESRI has about 10 classes.
    
    table = plt.table(cellText=table_data.values,
                      rowLabels=table_data.index,
                      colLabels=table_data.columns,
                      loc='bottom',
                      bbox=[0.0, -0.35, 1.0, 0.25]) # [left, bottom, width, height]
    
    # Adjust layout
    plt.subplots_adjust(left=0.1, bottom=0.3, right=0.85, top=0.9)
    
    # Save figure
    plt.savefig(os.path.join(OUTPUT_DIR, f"Relative_Comparison_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, f"Relative_Comparison_{dataset_name}.csv")
    pivot_pct.to_csv(csv_path)
    print(f"Relative comparison data saved to: {csv_path}")

def plot_absolute_comparison(wind_df, solar_df, color_map, dataset_name):
    """Absolute quantity comparison (grouped bar chart) - with data table"""
    # Aggregate total area of each class
    wind_sum = wind_df.groupby('class_name')['area_sqm'].sum() / 1e6 # Convert to square kilometers
    solar_sum = solar_df.groupby('class_name')['area_sqm'].sum() / 1e6
    
    # Merge
    df = pd.DataFrame({'Wind': wind_sum, 'Solar': solar_sum}).fillna(0)
    
    # Sort
    df['total'] = df['Wind'] + df['Solar']
    df = df.sort_values('total', ascending=False).drop('total', axis=1)
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    df.plot(kind='bar', ax=ax, width=0.8)
    
    plt.title(f"Total area occupied by each land cover type (Absolute - {dataset_name})", fontsize=16)
    plt.xlabel("Land cover type", fontsize=12)
    plt.ylabel("Occupied area (km2)", fontsize=12)
    plt.legend(title="Energy type")
    plt.xticks(rotation=45)
    
    # Add table
    table_data = df.T.round(2) # Transpose: rows as Wind/Solar, columns as land cover types
    
    table = plt.table(cellText=table_data.values,
                      rowLabels=table_data.index,
                      colLabels=table_data.columns,
                      loc='bottom',
                      bbox=[0.0, -0.45, 1.0, 0.25])
                      
    plt.subplots_adjust(bottom=0.35)
    
    # Save figure
    plt.savefig(os.path.join(OUTPUT_DIR, f"Absolute_Comparison_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, f"Absolute_Comparison_{dataset_name}.csv")
    df.to_csv(csv_path)
    print(f"Absolute comparison data saved to: {csv_path}")

def plot_latitude_comparison(wind_df, solar_df, dataset_name):
    """Latitude distribution comparison (KDE plot) - with distribution statistics table"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot wind latitude distribution
    sns.kdeplot(data=wind_df, x='lat', weights='area_sqm', label='Wind', fill=True, alpha=0.3, color='blue', ax=ax)
    # Plot solar latitude distribution
    sns.kdeplot(data=solar_df, x='lat', weights='area_sqm', label='Solar', fill=True, alpha=0.3, color='orange', ax=ax)
    
    plt.title(f"Latitude distribution comparison of land occupation between Solar and Wind ({dataset_name})", fontsize=16)
    plt.xlabel("Latitude", fontsize=12)
    plt.ylabel("Density (area-weighted)", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Compute zonal statistics table
    bins = range(-60, 91, 15) # 15 degrees per zone
    labels = [f"{i}~{i+15}" for i in bins[:-1]]
    
    # Use temporary copies to avoid modifying the original data
    w_df = wind_df.copy()
    s_df = solar_df.copy()
    
    w_df['lat_bin'] = pd.cut(w_df['lat'], bins=bins, labels=labels)
    s_df['lat_bin'] = pd.cut(s_df['lat'], bins=bins, labels=labels)
    
    w_dist = w_df.groupby('lat_bin')['area_sqm'].sum() / 1e6
    s_dist = s_df.groupby('lat_bin')['area_sqm'].sum() / 1e6
    
    table_df = pd.DataFrame({'Wind': w_dist, 'Solar': s_dist}).fillna(0).T.round(1)
    
    # Select non-zero columns or merge for display to avoid an overly long table
    # Only the main latitude bands are shown here, or shrink the font if there are too many columns
    # Filter out all-zero columns
    table_df = table_df.loc[:, (table_df != 0).any(axis=0)]
    
    table = plt.table(cellText=table_df.values,
                      rowLabels=table_df.index,
                      colLabels=table_df.columns,
                      loc='bottom',
                      bbox=[0.0, -0.4, 1.0, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    
    plt.subplots_adjust(bottom=0.35)
    # Save figure
    plt.savefig(os.path.join(OUTPUT_DIR, f"Latitude_KDE_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, f"Latitude_Distribution_{dataset_name}.csv")
    table_df.to_csv(csv_path)
    print(f"Latitude distribution data saved to: {csv_path}")

def plot_yearly_comparison(wind_df, solar_df, dataset_name):
    """Annual newly added area comparison - with data table"""
    # Filter by year
    wind_valid = wind_df[(wind_df['constructi'] >= 2018) & (wind_df['constructi'] <= 2024)]
    solar_valid = solar_df[(solar_df['constructi'] >= 2018) & (solar_df['constructi'] <= 2024)]
    
    wind_yearly = wind_valid.groupby('constructi')['area_sqm'].sum() / 1e6
    solar_yearly = solar_valid.groupby('constructi')['area_sqm'].sum() / 1e6
    
    df = pd.DataFrame({'Wind': wind_yearly, 'Solar': solar_yearly}).fillna(0)
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    df.plot(kind='line', marker='o', linewidth=2, ax=ax)
    
    plt.title(f"Trend of newly added land area for Solar and Wind (2018-2024) ({dataset_name})", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Newly added area (km2)", fontsize=12)
    plt.grid(True)
    
    # Add table
    table_data = df.T.round(2)
    table = plt.table(cellText=table_data.values,
                      rowLabels=table_data.index,
                      colLabels=table_data.columns,
                      loc='bottom',
                      bbox=[0.0, -0.3, 1.0, 0.2])
                      
    plt.subplots_adjust(bottom=0.25)
    
    # Save figure
    plt.savefig(os.path.join(OUTPUT_DIR, f"Yearly_Trend_Comparison_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, f"Yearly_Trend_Comparison_{dataset_name}.csv")
    df.to_csv(csv_path)
    print(f"Annual trend data saved to: {csv_path}")

def plot_lat_landcover_heatmap(df, dataset_name, energy_type):
    """Plot latitude-land cover type heatmap"""
    # Latitude binning
    df['lat_bin'] = pd.cut(df['lat'], bins=np.arange(-60, 90, 5), labels=np.arange(-57.5, 87.5, 5))
    
    # Aggregate
    pivot = df.pivot_table(index='class_name', columns='lat_bin', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Normalize (optional: by row or by column; here normalize by column to show the dominant land cover in each latitude band)
    pivot_norm = pivot.div(pivot.sum(axis=0), axis=1)
    
    plt.figure(figsize=(15, 8))
    sns.heatmap(pivot_norm, cmap="YlGnBu", cbar_kws={'label': 'Share'})
    
    plt.title(f"Land use type heatmap by latitude band for {energy_type} ({dataset_name})", fontsize=16)
    plt.xlabel("Latitude", fontsize=12)
    plt.ylabel("Land cover type", fontsize=12)
    plt.tight_layout()
    # Save figure
    plt.savefig(os.path.join(OUTPUT_DIR, f"Lat_LandCover_Heatmap_{energy_type}_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV (save the original aggregated data)
    csv_path = os.path.join(OUTPUT_DIR, f"Lat_LandCover_Heatmap_{energy_type}_{dataset_name}.csv")
    pivot.to_csv(csv_path)
    print(f"Heatmap data saved to: {csv_path}")

def plot_global_distribution(wind_df, solar_df):
    """Plot global distribution scatter chart"""
    # Get world map background
    if os.path.exists(WORLD_SHP):
        world = gpd.read_file(WORLD_SHP)
    else:
        print(f"Warning: world map file not found {WORLD_SHP}, trying to download online...")
        try:
            # Fallback: try to read directly from the URL (if supported) or use a simple background
            # Simple handling here: if not found, use a simple rectangle or skip the background
            world = gpd.read_file("https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip")
        except Exception as e:
            print(f"Warning: failed to load world map background ({e}), scatter points will be plotted only.")
            world = None
    
    fig, ax = plt.subplots(figsize=(15, 10))
    
    if world is not None:
        world.plot(ax=ax, color='lightgrey', edgecolor='white')
    else:
        ax.set_facecolor('#f0f0f0') # Set light grey background
    
    # Plot points, deduplicate to avoid plotting the same site repeatedly
    wind_points = wind_df[['fid', 'lon', 'lat']].drop_duplicates(subset='fid')
    solar_points = solar_df[['fid', 'lon', 'lat']].drop_duplicates(subset='fid')
    
    # Plot
    plt.scatter(wind_points['lon'], wind_points['lat'], c='blue', s=2, alpha=0.5, label='Wind')
    plt.scatter(solar_points['lon'], solar_points['lat'], c='orange', s=2, alpha=0.5, label='Solar')
    
    plt.title("Global spatial distribution comparison of wind and solar power sites", fontsize=16)
    plt.legend(markerscale=5)
    plt.tight_layout()
    # Save figure
    plt.savefig(os.path.join(OUTPUT_DIR, "Global_Distribution_Map.png"), dpi=300)
    plt.close()

    # Save point data CSV (including fid, lon, lat, type)
    wind_points['type'] = 'Wind'
    solar_points['type'] = 'Solar'
    points_df = pd.concat([wind_points, solar_points])
    csv_path = os.path.join(OUTPUT_DIR, "Global_Distribution_Points.csv")
    points_df.to_csv(csv_path, index=False)
    print(f"Global distribution point data saved to: {csv_path}")

# ================= Main program =================

def main():
    # Redirect output to log
    log_file = os.path.join(OUTPUT_DIR, "process_log.txt")
    sys.stdout = Logger(log_file)
    print(f"Log will be saved to: {log_file}")

    print(">>> Start processing ESRI data comparison...")
    try:
        # Load data in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_wind = executor.submit(load_data, WIND_ESRI_CSV, WIND_SHP, "Wind")
            future_solar = executor.submit(load_data, SOLAR_ESRI_CSV, SOLAR_SHP, "Solar")
            wind_esri = future_wind.result()
            solar_esri = future_solar.result()
        
        plot_relative_comparison(wind_esri, solar_esri, ESRI_COLORS, "ESRI")
        plot_absolute_comparison(wind_esri, solar_esri, ESRI_COLORS, "ESRI")
        plot_latitude_comparison(wind_esri, solar_esri, "ESRI")
        plot_yearly_comparison(wind_esri, solar_esri, "ESRI")
        
        # New spatial analysis
        plot_lat_landcover_heatmap(wind_esri, "ESRI", "Wind")
        plot_lat_landcover_heatmap(solar_esri, "ESRI", "Solar")
        plot_global_distribution(wind_esri, solar_esri)
        
        print("ESRI data comparison completed.")
    except Exception as e:
        print(f"Error processing ESRI data: {e}")
        import traceback
        traceback.print_exc()

    print("\n>>> Start processing FROM-GLC data comparison...")
    # For simplicity, reuse the color mapping here or define FROM_COLORS
    # In practice, it is recommended to pass FROM_COLORS
    try:
        # Load data in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_wind = executor.submit(load_data, WIND_FROM_CSV, WIND_SHP, "Wind")
            future_solar = executor.submit(load_data, SOLAR_FROM_CSV, SOLAR_SHP, "Solar")
            wind_from = future_wind.result()
            solar_from = future_solar.result()
        
        # Simply define FROM colors (copy the previous definition if more precision is needed)
        FROM_COLORS = {
            "Cropland": "#A3FF73", "Forest": "#267300", "Grass": "#4CE600",
            "Shrub": "#70A800", "Water": "#005CFF", "Impervious": "#C500FF",
            "Bareland": "#FFAA00", "Snow/Ice": "#00FFC5", "Cloud": "#FFFFFF",
            "Background": "#000000", "Unknown": "#000000"
        }
        
        plot_relative_comparison(wind_from, solar_from, FROM_COLORS, "FROM-GLC")
        plot_absolute_comparison(wind_from, solar_from, FROM_COLORS, "FROM-GLC")
        plot_latitude_comparison(wind_from, solar_from, "FROM-GLC")
        plot_yearly_comparison(wind_from, solar_from, "FROM-GLC")
        
        print("FROM-GLC data comparison completed.")
    except Exception as e:
        print(f"Error processing FROM-GLC data: {e}")
        import traceback
        traceback.print_exc()

    print(f"\nAll comparative analyses completed! Results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
