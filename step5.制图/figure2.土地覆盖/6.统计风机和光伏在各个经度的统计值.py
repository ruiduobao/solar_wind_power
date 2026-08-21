# -*- coding: utf-8 -*-
"""
Statistics of wind and solar values at each latitude (Latitudinal Gradient)
Author: 锐多宝
Date: 2026-02-02
Description: 
    Compute the land cover type distribution areas of global solar and wind power at different latitude bands.
    Generate curves similar to the "Latitudinal Gradient of Land Use" chart.
    
    Note:
    Although the file name contains "longitude", based on the reference chart provided by the user (Latitudinal Gradient),
    this script actually computes the "latitude" distribution.
"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.ndimage import gaussian_filter1d

# ================= Configuration =================

# 1. Data paths (FROM-GLC)
# Wind
WIND_FROM_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\WIND_FROM_2017_LandCover_Summary.csv"
WIND_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机80米缓冲区_2017年之后的风机缓冲区.shp"

# Solar
SOLAR_FROM_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2018_2024的数据在2017年的土地覆盖上\SOLAR_FROM_2017_LandCover_Summary.csv"
SOLAR_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\solarpower.shp"

# 2. Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure2_全球光伏风电土地利用\子图\随着经度变化的各个地物的曲线"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 3. Color definitions (FROM-GLC standard colors)
def rgba_to_hex(r, g, b, a):
    return f"#{r:02X}{g:02X}{b:02X}"

COLORS = {
    "Background": rgba_to_hex(0, 0, 0, 0),
    "Cropland": rgba_to_hex(163, 255, 115, 255),
    "Forest": rgba_to_hex(38, 115, 0, 255),
    "Grass": rgba_to_hex(76, 230, 0, 255),
    "Shrub": rgba_to_hex(112, 168, 0, 255),
    "Water": rgba_to_hex(0, 92, 255, 255),
    "Impervious": rgba_to_hex(197, 0, 255, 255),
    "Bareland": rgba_to_hex(255, 170, 0, 255),
    "Snow/Ice": rgba_to_hex(0, 255, 197, 255),
    "Cloud": rgba_to_hex(255, 255, 255, 255),
    "Unknown": "#000000"
}

# Plot style
sns.set_theme(style="ticks")
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.unicode_minus'] = False

# ================= Data processing functions =================

def load_data(csv_path, shp_path, label):
    """Load and merge data (obtain latitude)"""
    print(f"Loading {label} data...")
    
    # 1. Read CSV (land cover areas)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error: unable to read CSV {csv_path}: {e}")
        return pd.DataFrame()

    # 2. Read SHP (obtain latitude)
    print(f"  - Reading Shapefile: {os.path.basename(shp_path)}...")
    try:
        # Only read the geometry column to speed up, and compute the centroid later
        gdf = gpd.read_file(shp_path, columns=['fid'], ignore_geometry=False)
    except Exception as e:
        print(f"Error: unable to read SHP {shp_path}: {e}")
        return pd.DataFrame()
    
    # Reproject
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    # Compute the latitude
    print("  - Computing the centroid latitude...")
    gdf['lon'] = gdf.geometry.centroid.x
    gdf['lat'] = gdf.geometry.centroid.y
    
    # Ensure the fid types match
    # Assume the CSV fid is int
    gdf['fid'] = gdf['fid'].astype(int)
    if 'fid' in df.columns:
        df['fid'] = df['fid'].astype(int)
    
    # 3. Merge
    print("  - Merging data...")
    merged = df.merge(gdf[['fid', 'lat', 'lon']], on='fid', how='inner')
    merged['source_type'] = label
    
    print(f"  - {label} data loaded: {len(merged)} records")
    return merged

def process_gradient(combined_df, axis_col, bin_size=1.0, sigma=2.0, min_val=-60, max_val=90):
    """
    Compute the gradient distribution (latitude or longitude)
    axis_col: 'lat' or 'lon'
    bin_size: bin size (degrees)
    sigma: Gaussian smoothing parameter
    """
    print(f"\nStart computing the {axis_col} gradient distribution...")
    
    # 1. Binning
    bins = np.arange(min_val, max_val + bin_size, bin_size)
    
    col_bin = f'{axis_col}_bin'
    combined_df[col_bin] = pd.cut(combined_df[axis_col], bins=bins, labels=bins[:-1])
    
    # 2. Aggregate: sum the areas by bin and land cover type
    # Convert the area unit to square kilometers (km2) -> area_sqm / 1e6
    pivot = combined_df.pivot_table(
        index=col_bin, 
        columns='class_name', 
        values='area_sqm', 
        aggfunc='sum', 
        fill_value=0
    ) / 1e6
    
    # Ensure the index is numeric for plotting
    pivot.index = pivot.index.astype(float)
    
    # 3. Fill in the missing bins
    all_vals = bins[:-1]
    pivot = pivot.reindex(all_vals, fill_value=0)
    
    # 4. Smoothing (Gaussian Filter)
    print(f"Applying Gaussian smoothing (sigma={sigma})...")
    smoothed = pivot.copy()
    for col in pivot.columns:
        smoothed[col] = gaussian_filter1d(pivot[col], sigma=sigma)
        
    return pivot, smoothed

# ================= Plotting functions =================

def plot_gradient(df, smoothed_df, output_name, xlabel, x_min, x_max, x_step, x_label_fmt):
    """Plot the curve chart"""
    plt.figure(figsize=(12, 6))
    
    # Get the main land cover types (based on the columns present in the data)
    target_classes = ['Bareland', 'Cropland', 'Forest', 'Grass', 'Shrub', 'Water', 'Impervious']
    available_classes = [c for c in target_classes if c in smoothed_df.columns]
    
    # If no target column is found, plot all columns
    if not available_classes:
        available_classes = smoothed_df.columns.tolist()
    
    # Plot
    for col in available_classes:
        color = COLORS.get(col, "#333333")
        
        # Plot the smoothed curve
        plt.plot(smoothed_df.index, smoothed_df[col], label=col, color=color, linewidth=2.5)
        
    # Remove the title
    # plt.title(..., fontsize=25)
    
    plt.xlabel(xlabel, fontsize=30, fontname='Times New Roman')
    plt.ylabel("Area ($km^2$)", fontsize=30, fontname='Times New Roman')
    
    # Set the X-axis label format
    plt.xticks(
        np.arange(x_min, x_max + 1, x_step), 
        [x_label_fmt(x) for x in np.arange(x_min, x_max + 1, x_step)],
        fontsize=25, fontname='Times New Roman'
    )
    
    # Set the Y-axis label format (interval 100)
    import matplotlib.ticker as ticker
    ax = plt.gca()
    ax.yaxis.set_major_locator(ticker.MultipleLocator(100))
    plt.yticks(fontsize=25, fontname='Times New Roman')
    
    plt.xlim(x_min, x_max)
    plt.ylim(bottom=0)
    
    # Remove the legend
    # plt.legend(...)
    
    plt.grid(True, axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    out_png = os.path.join(OUTPUT_DIR, f"{output_name}.png")
    out_pdf = os.path.join(OUTPUT_DIR, f"{output_name}.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    print(f"Chart saved to: {out_png}")
    plt.close()

# ================= Main program =================

def main():
    # 1. Load data
    wind_df = load_data(WIND_FROM_CSV, WIND_SHP, "Wind")
    solar_df = load_data(SOLAR_FROM_CSV, SOLAR_SHP, "Solar")
    
    if wind_df.empty and solar_df.empty:
        print("Error: no data loaded.")
        return

    # 2. Merge
    print("Merging the solar and wind data...")
    combined_df = pd.concat([wind_df, solar_df], ignore_index=True)
    
    # ================= Latitudinal gradient =================
    # Use 1-degree bins and sigma=3 for smoothing
    raw_lat, smoothed_lat = process_gradient(combined_df, 'lat', bin_size=1.0, sigma=3.0, min_val=-60, max_val=90)
    
    # Export data
    smoothed_lat.to_csv(os.path.join(OUTPUT_DIR, "Latitudinal_Gradient_Data.csv"))
    
    # Plot
    plot_gradient(
        None, smoothed_lat, "Latitudinal_Gradient_Curve",
        xlabel="Latitude",
        x_min=-60, x_max=90, x_step=20,
        x_label_fmt=lambda x: f"{abs(x)}°{'S' if x<0 else 'N' if x>0 else ''}"
    )
    
    # ================= Longitudinal gradient =================
    # Use 1-degree bins and sigma=3 for smoothing (longitude range -180 to 180)
    raw_lon, smoothed_lon = process_gradient(combined_df, 'lon', bin_size=1.0, sigma=3.0, min_val=-180, max_val=180)
    
    # Export data
    smoothed_lon.to_csv(os.path.join(OUTPUT_DIR, "Longitudinal_Gradient_Data.csv"))
    
    # Plot
    plot_gradient(
        None, smoothed_lon, "Longitudinal_Gradient_Curve",
        xlabel="Longitude",
        x_min=-180, x_max=180, x_step=45, # 45-degree interval
        x_label_fmt=lambda x: f"{abs(x)}°{'W' if x<0 else 'E' if x>0 else ''}"
    )
    
    print("\nAll done!")

if __name__ == "__main__":
    main()
