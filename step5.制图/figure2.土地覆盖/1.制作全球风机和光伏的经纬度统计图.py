# -*- coding: utf-8 -*-
"""
Script name: 1.制作全球风机和光伏的经纬度统计图.py
Function description:
    1. Read global solar (polygon) and wind (point) data.
    2. Reproject all data to WGS84 (EPSG:4326).
    3. Compute latitude/longitude distributions at 5-degree intervals.
    4. Draw 4 figures: solar latitude, solar longitude, wind latitude, wind longitude.
    5. Strictly control the figure aspect ratio: keep the length ratio of longitude (360 degrees) to latitude (150 degrees, -60~90) consistent.
    6. Use only the Times New Roman font.
Author: 锐多宝
Date: 2026-02-02
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Configure the font as Times New Roman
plt.rcParams['font.family'] = 'Times New Roman'
# Fix the minus sign display issue
plt.rcParams['axes.unicode_minus'] = False

def main():
    # ================= Configure paths =================
    base_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据"
    solar_path = os.path.join(base_dir, "solarpower.shp")
    wind_path = os.path.join(base_dir, "windpower.shp")
    
    # Output directory
    output_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure2_全球光伏风电土地利用\子图"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Output directory created: {output_dir}")

    output_csv = os.path.join(output_dir, "Distribution_Stats_5deg.csv")
    
    # Figure paths
    img_solar_lat = os.path.join(output_dir, "Solar_Lat_Dist.png")
    img_solar_lon = os.path.join(output_dir, "Solar_Lon_Dist.png")
    img_wind_lat = os.path.join(output_dir, "Wind_Lat_Dist.png")
    img_wind_lon = os.path.join(output_dir, "Wind_Lon_Dist.png")

    # ================= 1. Read data and unify the coordinate system =================
    print("Reading solar data...")
    if not os.path.exists(solar_path):
        print(f"Error: file not found {solar_path}")
        return
    gdf_solar = gpd.read_file(solar_path)
    
    if gdf_solar.crs is None or gdf_solar.crs.to_string() != 'EPSG:4326':
        print(f"Solar data CRS is {gdf_solar.crs}; converting to EPSG:4326...")
        gdf_solar = gdf_solar.to_crs('EPSG:4326')
    
    print("Reading wind data...")
    if not os.path.exists(wind_path):
        print(f"Error: file not found {wind_path}")
        return
    gdf_wind = gpd.read_file(wind_path)
    
    if gdf_wind.crs is None or gdf_wind.crs.to_string() != 'EPSG:4326':
        print(f"Wind data CRS is {gdf_wind.crs}; converting to EPSG:4326...")
        gdf_wind = gdf_wind.to_crs('EPSG:4326')

    # ================= 2. Data processing and statistics (5-degree intervals) =================
    print("Processing data statistics...")
    bin_size = 5

    # --- 2.1 Solar processing (area statistics) ---
    area_col = None
    for col in gdf_solar.columns:
        if col.lower() == 'area':
            area_col = col
            break
            
    if area_col:
        gdf_solar[area_col] = pd.to_numeric(gdf_solar[area_col], errors='coerce').fillna(0)
        gdf_solar['area_km2'] = gdf_solar[area_col] / 1e6
    else:
        print("Warning: no 'area' field found in the solar data; area statistics are impossible!")
        gdf_solar['area_km2'] = 0

    # Extract longitude/latitude
    gdf_solar = gdf_solar[gdf_solar.geometry.notnull() & gdf_solar.geometry.is_valid]
    import warnings
    warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")
    
    gdf_solar['lat'] = gdf_solar.geometry.centroid.y
    gdf_solar['lon'] = gdf_solar.geometry.centroid.x
    
    # 5-degree binning
    gdf_solar['lat_bin'] = (np.floor(gdf_solar['lat'] / bin_size) * bin_size).astype(int)
    gdf_solar['lon_bin'] = (np.floor(gdf_solar['lon'] / bin_size) * bin_size).astype(int)
    
    solar_lat_stats = gdf_solar.groupby('lat_bin')['area_km2'].sum()
    solar_lon_stats = gdf_solar.groupby('lon_bin')['area_km2'].sum()

    # --- 2.2 Wind processing (count statistics) ---
    gdf_wind = gdf_wind[gdf_wind.geometry.notnull() & gdf_wind.geometry.is_valid]
    gdf_wind['lat'] = gdf_wind.geometry.y
    gdf_wind['lon'] = gdf_wind.geometry.x
    
    gdf_wind['lat_bin'] = (np.floor(gdf_wind['lat'] / bin_size) * bin_size).astype(int)
    gdf_wind['lon_bin'] = (np.floor(gdf_wind['lon'] / bin_size) * bin_size).astype(int)
    
    wind_lat_stats = gdf_wind.groupby('lat_bin').size()
    wind_lon_stats = gdf_wind.groupby('lon_bin').size()

    # --- 2.3 Merge data and save the CSV ---
    lat_range = range(-90, 91, bin_size)
    df_lat = pd.DataFrame({'lat_bin': lat_range})
    df_lat = df_lat.merge(solar_lat_stats.rename('solar_area_km2'), on='lat_bin', how='left').fillna(0)
    df_lat = df_lat.merge(wind_lat_stats.rename('wind_count'), on='lat_bin', how='left').fillna(0)
    
    lon_range = range(-180, 181, bin_size)
    df_lon = pd.DataFrame({'lon_bin': lon_range})
    df_lon = df_lon.merge(solar_lon_stats.rename('solar_area_km2'), on='lon_bin', how='left').fillna(0)
    df_lon = df_lon.merge(wind_lon_stats.rename('wind_count'), on='lon_bin', how='left').fillna(0)
    
    with open(output_csv, 'w', encoding='utf-8-sig') as f:
        f.write("=== Latitude Stats (5-deg bins) ===\n")
        df_lat.to_csv(f, index=False, lineterminator='\n')
        f.write("\n=== Longitude Stats (5-deg bins) ===\n")
        df_lon.to_csv(f, index=False, lineterminator='\n')
    print(f"Statistics table saved: {output_csv}")

    # ================= 3. Plotting =================
    print("Plotting...")
    # User-specified colors
    # Solar: 255, 0, 197 -> #FF00C5
    color_solar = '#FF00C5' 
    # Wind: 33, 133, 78 -> #21854E
    color_wind = '#21854E'
    
    def setup_plot_style(ax):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        # Force the Times New Roman font
        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
            label.set_fontname('Times New Roman')
            label.set_fontsize(10)
        ax.set_xlabel(ax.get_xlabel(), fontname='Times New Roman', fontsize=12)
        ax.set_ylabel(ax.get_ylabel(), fontname='Times New Roman', fontsize=12)
        ax.set_title(ax.get_title(), fontname='Times New Roman', fontsize=14)

    # --- Ratio calculation ---
    # Latitude range: -60 to 90 -> 150 degrees
    # Longitude range: -180 to 180 -> 360 degrees
    # Ratio ratio = 360 / 150 = 2.4
    # Assume 1 degree = X pixels (or inches)
    # Latitude figure height = 150 * X
    # Longitude figure width = 360 * X
    
    # Base unit length (inches/degree)
    unit_per_deg = 0.05 
    
    # Compute the canvas size
    lat_height = 150 * unit_per_deg  # 150 degrees * 0.05 = 7.5 inches
    lon_width = 360 * unit_per_deg   # 360 degrees * 0.05 = 18 inches
    
    bar_width = 3 # The other dimension of the figure (fixed value, e.g. the length direction of the statistic bars)

    # --- 3.1 Solar-latitude (vertical) ---
    # Height determined by the latitude span (7.5 inch), width fixed (3 inch)
    fig1, ax1 = plt.subplots(figsize=(bar_width, lat_height), dpi=300)
    ax1.barh(df_lat['lat_bin'], df_lat['solar_area_km2'], height=bin_size*0.8, color=color_solar, alpha=0.8)
    ax1.set_ylabel('Latitude (deg)')
    ax1.set_xlabel('Solar Area (km^2)')
    ax1.set_ylim(-60, 90) # 150-degree span
    # ax1.set_title('Global Solar Area by Latitude')
    setup_plot_style(ax1)
    plt.tight_layout()
    plt.savefig(img_solar_lat)
    plt.close(fig1)
    print(f"Generated: {img_solar_lat}")

    # --- 3.2 Solar-longitude (horizontal) ---
    # Width determined by the longitude span (18 inch), height fixed (3 inch)
    fig2, ax2 = plt.subplots(figsize=(lon_width, bar_width), dpi=300)
    ax2.bar(df_lon['lon_bin'], df_lon['solar_area_km2'], width=bin_size*0.8, color=color_solar, alpha=0.8)
    ax2.set_xlabel('Longitude (deg)')
    ax2.set_ylabel('Solar Area (km^2)')
    ax2.set_xlim(-180, 180) # 360-degree span
    # ax2.set_title('Global Solar Area by Longitude')
    setup_plot_style(ax2)
    plt.tight_layout()
    plt.savefig(img_solar_lon)
    plt.close(fig2)
    print(f"Generated: {img_solar_lon}")

    # --- 3.3 Wind-latitude (vertical) ---
    fig3, ax3 = plt.subplots(figsize=(bar_width, lat_height), dpi=300)
    # Direction reversed: latitude statistics growing to the left is positive -> invert the xlim
    ax3.barh(df_lat['lat_bin'], df_lat['wind_count'], height=bin_size*0.8, color=color_wind, alpha=0.8)
    ax3.set_ylabel('Latitude (deg)')
    ax3.set_xlabel('Wind Turbine Count')
    ax3.set_ylim(-60, 90)
    
    # Key modification: invert the X axis so that leftward is positive
    ax3.invert_xaxis()
    # Move the Y axis to the right; when growing leftward, the axis usually looks better on the right, or it can stay on the left
    # The user said "leftward is positive", which usually means the left is the growth direction.
    # We can put the spine on the right, or keep the default. Here we only invert the X axis.
    # To match "leftward", moving the Y axis to the right may be more intuitive (as a right-side histogram),
    # but the user did not specify the position, only the direction. We invert the axis first.
    ax3.yaxis.tick_right()
    ax3.yaxis.set_label_position("right")
    
    # ax3.set_title('Global Wind Count by Latitude')
    setup_plot_style(ax3)
    # Because of the inversion, we need to re-show the left spine (now it should be the right one?)
    # setup_plot_style hides top and right.
    # If the Y axis is on the right, we need to show the right spine and hide the left spine
    ax3.spines['left'].set_visible(False)
    ax3.spines['right'].set_visible(True)
    
    plt.tight_layout()
    plt.savefig(img_wind_lat)
    plt.close(fig3)
    print(f"Generated: {img_wind_lat}")

    # --- 3.4 Wind-longitude (horizontal) ---
    fig4, ax4 = plt.subplots(figsize=(lon_width, bar_width), dpi=300)
    # Direction reversed: longitude statistics growing downward is positive -> invert the ylim
    ax4.bar(df_lon['lon_bin'], df_lon['wind_count'], width=bin_size*0.8, color=color_wind, alpha=0.8)
    ax4.set_xlabel('Longitude (deg)')
    ax4.set_ylabel('Wind Turbine Count')
    ax4.set_xlim(-180, 180)
    
    # Key modification: invert the Y axis so that downward is positive
    ax4.invert_yaxis()
    # Move the X axis to the top; when growing downward, the axis is usually at the top
    ax4.xaxis.tick_top()
    ax4.xaxis.set_label_position("top")
    
    # ax4.set_title('Global Wind Count by Longitude')
    setup_plot_style(ax4)
    # If the X axis is on the top, we need to show the top spine (but setup_plot_style hides top)
    # Need to show top, hide bottom
    ax4.spines['bottom'].set_visible(False)
    ax4.spines['top'].set_visible(True)
    
    plt.tight_layout()
    plt.savefig(img_wind_lon)
    plt.close(fig4)
    print(f"Generated: {img_wind_lon}")

    print("All done!")

if __name__ == "__main__":
    main()
