# -*- coding: utf-8 -*-
"""
Land source analysis script (solar power version)
Author: 锐多宝 (ruiduobao)
Date: 2026-01-06
Description: 
    Read the summarized land cover data and the solar power Shapefile, and perform multi-dimensional statistical analysis and visualization.
    Includes global statistics, country statistics, latitude distribution trends and temporal change trends.
"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import ListedColormap

# ================= Configuration =================
# Input files
ESRI_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\SOLAR_ESRI_2017_LandCover_Summary.csv"
FROM_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\SOLAR_FROM_2017_LandCover_Summary.csv"
SHP_FILE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\solarpower.shp"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\\1.土地来源分析\光伏"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Set plot style
sns.set_theme(style="whitegrid", font="SimHei") # use SimHei to support Chinese
plt.rcParams['axes.unicode_minus'] = False # fix the minus sign display issue

# ================= Color definitions =================

# ESRI color mapping
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

# FROM-GLC color mapping
FROM_COLORS = {
    "Cropland": "#A3FF73",
    "Forest": "#267300",
    "Grass": "#4CE600",
    "Shrub": "#70A800",
    "Water": "#005CFF",
    "Impervious": "#C500FF",
    "Bareland": "#FFAA00",
    "Snow/Ice": "#00FFC5",
    "Cloud": "#FFFFFF",
    "Background": "#000000",
    "Unknown": "#000000"
}

# ================= Helper functions =================

def load_and_merge_data(csv_path, shp_gdf, value_col='area_sqm'):
    """Load CSV and merge with the Shapefile"""
    print(f"Loading {os.path.basename(csv_path)} ...")
    df = pd.read_csv(csv_path)
    
    # Select the main columns
    df = df[['fid', 'class_name', value_col]]
    
    # Merge with the shp (left join to keep all csv records, but the shp attributes are needed)
    # Note: one fid may have multiple records in the csv (different land cover types), so this is a many-to-one merge
    merged = df.merge(shp_gdf[['fid', 'COUNTRY', 'constructi', 'lat', 'lon']], on='fid', how='inner')
    
    return merged

def plot_global_composition(df, color_map, dataset_name, value_col='area_sqm'):
    """Plot the global land cover composition pie chart"""
    # Aggregate the total area of each class
    summary = df.groupby('class_name')[value_col].sum().sort_values(ascending=False)
    
    # Prepare colors
    colors = [color_map.get(name, '#000000') for name in summary.index]
    
    plt.figure(figsize=(10, 8))
    
    # Draw a donut chart
    wedges, texts, autotexts = plt.pie(
        summary, 
        labels=summary.index, 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=colors,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )
    
    plt.setp(texts, size=12)
    plt.setp(autotexts, size=10, weight="bold")
    
    plt.title(f"Global land cover composition of solar farm occupation ({dataset_name})", fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"Global_Composition_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, f"Global_Composition_{dataset_name}.csv")
    summary.to_csv(csv_path)
    print(f"Global composition data saved to: {csv_path}")

def plot_country_analysis(df, color_map, dataset_name, top_n=10):
    """Plot the stacked bar chart of land cover for the top N countries"""
    # Compute the total area of each country and find the top N
    country_totals = df.groupby('COUNTRY')['area_sqm'].sum().sort_values(ascending=False)
    top_countries = country_totals.head(top_n).index.tolist()
    
    # Filter the data
    df_top = df[df['COUNTRY'].isin(top_countries)]
    
    # Pivot table: rows=countries, columns=land cover types, values=areas
    pivot = df_top.pivot_table(index='COUNTRY', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Sort countries by total area
    pivot = pivot.reindex(top_countries)
    
    # Compute percentages
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    
    # Plot
    ax = pivot_pct.plot(kind='bar', stacked=True, figsize=(12, 6), color=[color_map.get(c, '#000000') for c in pivot_pct.columns])
    
    plt.title(f"Land occupation share of the top {top_n} solar power countries ({dataset_name})", fontsize=16)
    plt.xlabel("Country", fontsize=12)
    plt.ylabel("Share (%)", fontsize=12)
    plt.legend(title="Land cover type", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"Country_Analysis_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV (save percentage data)
    csv_path = os.path.join(OUTPUT_DIR, f"Country_Analysis_{dataset_name}.csv")
    pivot_pct.to_csv(csv_path)
    print(f"Country analysis data saved to: {csv_path}")

def plot_latitude_distribution(df, color_map, dataset_name):
    """Plot the latitude distribution chart"""
    # Bin the latitude
    df['lat_bin'] = pd.cut(df['lat'], bins=np.arange(-60, 90, 5), labels=np.arange(-57.5, 87.5, 5))
    
    # Aggregate
    pivot = df.pivot_table(index='lat_bin', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Plot
    ax = pivot.plot(kind='bar', stacked=True, figsize=(15, 6), width=1.0, color=[color_map.get(c, '#000000') for c in pivot.columns])
    
    plt.title(f"Latitude distribution of solar farm land cover types ({dataset_name})", fontsize=16)
    plt.xlabel("Latitude (5-degree bins)", fontsize=12)
    plt.ylabel("Occupied area (m2)", fontsize=12)
    
    # Simplify X-axis labels, show every 2nd one
    ticks = ax.get_xticks()
    labels = [item.get_text() for item in ax.get_xticklabels()]
    n = 4
    for i, label in enumerate(ax.xaxis.get_ticklabels()):
        if i % n != 0:
            label.set_visible(False)
            
    plt.legend(title="Land cover type", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"Latitude_Distribution_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV (save the original area data)
    csv_path = os.path.join(OUTPUT_DIR, f"Latitude_Distribution_{dataset_name}.csv")
    pivot.to_csv(csv_path)
    print(f"Latitude distribution data saved to: {csv_path}")

def plot_yearly_trend(df, color_map, dataset_name):
    """Plot the land cover trend by construction year"""
    # Filter valid years (assume 2017-2024)
    df_valid = df[(df['constructi'] >= 2017) & (df['constructi'] <= 2024)]
    
    if df_valid.empty:
        print(f"Warning: no valid construction year data found for {dataset_name} between 2017-2024.")
        return

    pivot = df_valid.pivot_table(index='constructi', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Compute percentages
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    
    # Plot
    ax = pivot_pct.plot(kind='area', stacked=True, figsize=(10, 6), alpha=0.8, color=[color_map.get(c, '#000000') for c in pivot_pct.columns])
    
    plt.title(f"Land source changes of solar farms by construction year ({dataset_name})", fontsize=16)
    plt.xlabel("Construction year", fontsize=12)
    plt.ylabel("Share (%)", fontsize=12)
    plt.legend(title="Land cover type", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"Yearly_Trend_{dataset_name}.png"), dpi=300)
    plt.close()

    # Save CSV (save percentage data)
    csv_path = os.path.join(OUTPUT_DIR, f"Yearly_Trend_{dataset_name}.csv")
    pivot_pct.to_csv(csv_path)
    print(f"Yearly trend data saved to: {csv_path}")

# ================= Main program =================

def main():
    print("Reading Shapefile...")
    gdf = gpd.read_file(SHP_FILE)
    
    # Compute the centroid for latitude analysis
    # Note: if the geometry is a polygon, use the centroid
    # Reproject to WGS84 (EPSG:4326) to obtain lon/lat
    if gdf.crs != "EPSG:4326":
        print("Converting the Shapefile CRS to EPSG:4326 ...")
        gdf = gdf.to_crs("EPSG:4326")
        
    gdf['lat'] = gdf.geometry.centroid.y
    gdf['lon'] = gdf.geometry.centroid.x
    
    # Ensure fid has a unified float or int format to prevent merge failures
    # Assume the fid in the CSV is int, and the fid in the SHP may be float (e.g. 1.0)
    gdf['fid'] = gdf['fid'].astype(int)
    
    # ------------------- Analyze ESRI data -------------------
    print("\n>>> Start analyzing ESRI data...")
    esri_df = load_and_merge_data(ESRI_CSV, gdf)
    
    if not esri_df.empty:
        plot_global_composition(esri_df, ESRI_COLORS, "ESRI")
        plot_country_analysis(esri_df, ESRI_COLORS, "ESRI")
        plot_latitude_distribution(esri_df, ESRI_COLORS, "ESRI")
        plot_yearly_trend(esri_df, ESRI_COLORS, "ESRI")
    else:
        print("ESRI data is empty after merging, skipping the analysis.")

    # ------------------- Analyze FROM data -------------------
    print("\n>>> Start analyzing FROM-GLC data...")
    from_df = load_and_merge_data(FROM_CSV, gdf)
    
    if not from_df.empty:
        plot_global_composition(from_df, FROM_COLORS, "FROM-GLC")
        plot_country_analysis(from_df, FROM_COLORS, "FROM-GLC")
        plot_latitude_distribution(from_df, FROM_COLORS, "FROM-GLC")
        plot_yearly_trend(from_df, FROM_COLORS, "FROM-GLC")
    else:
        print("FROM-GLC data is empty after merging, skipping the analysis.")

    print(f"\nAnalysis completed! Charts saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
