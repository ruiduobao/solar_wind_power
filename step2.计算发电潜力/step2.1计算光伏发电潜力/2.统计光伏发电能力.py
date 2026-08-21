# -*- coding: utf-8 -*-
"""
Solar Power Capacity Statistical Analysis and Mapping (Enhanced)
Author: 锐多宝 (ruiduobao)
Date: 2026-01-06
Description:
    Read Solar_Power_Potential.csv and the solar Shapefile for multi-dimensional statistical analysis and visualization.
    Includes:
    1. Global distribution map
    2. Country-level statistics
    3. Latitude gradient analysis
    4. Resource-emission mismatch analysis
    5. [New] Time dimension analysis (annual/quarterly trends)
    6. [New] Spatiotemporal evolution analysis
    7. [New] Advanced statistics (Lorenz curve)
    
    All plotting data are also exported as CSV files with the same names.
"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import LogNorm
import rasterio
from rasterio.plot import show

# ================= Configuration =================

# Input data
INPUT_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.1光伏发电潜力计算\Solar_Power_Potential.csv"
SOLAR_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\solarpower.shp"
PVOUT_TIF = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\光伏发电潜力\World_PVOUT_GISdata_LTAy_AvgDailyTotals_GlobalSolarAtlas-v2_GEOTIFF\PVOUT.tif"

# Try to obtain the world map path
try:
    WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')
except AttributeError:
    WORLD_SHP = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.1光伏发电潜力计算"

# Plot style settings
sns.set_theme(style="whitegrid", font="Arial") 
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

# ================= Helper functions =================

def export_plot_data(df, filename):
    """Export plotting data as CSV"""
    csv_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '.csv'))
    df.to_csv(csv_path, index=True, encoding='utf-8-sig')
    print(f"Data exported: {csv_path}")

def plot_global_map(df, value_col, title, filename, cmap='viridis', log_scale=False):
    """Plot a global scatter map"""
    try:
        world = gpd.read_file(WORLD_SHP)
    except Exception as e:
        print(f"Failed to load world map basemap ({e}); only scatter points will be plotted.")
        world = None
    
    fig, ax = plt.subplots(figsize=(15, 8))
    
    if world is not None:
        world.plot(ax=ax, color='lightgrey', edgecolor='white')
    else:
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_aspect('equal')
    
    df_sorted = df.sort_values(value_col)
    
    if log_scale:
        norm = LogNorm(vmin=df[value_col].replace(0, np.nan).min(), vmax=df[value_col].max())
    else:
        norm = None
        
    sc = ax.scatter(df_sorted['lon'], df_sorted['lat'], 
                    c=df_sorted[value_col], 
                    s=2, 
                    cmap=cmap, 
                    alpha=0.7,
                    norm=norm)
    
    plt.colorbar(sc, label=value_col, fraction=0.02, pad=0.04)
    plt.title(title, fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(df_sorted[['lon', 'lat', value_col]], filename)

def plot_top_countries(df, value_col, title, filename, top_n=15, color='steelblue'):
    """Plot a bar chart of the top N countries"""
    country_stats = df.groupby('country')[value_col].sum().sort_values(ascending=False).head(top_n)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(x=country_stats.index, y=country_stats.values, color=color)
    
    plt.title(title, fontsize=16)
    plt.xlabel("Country", fontsize=12)
    plt.ylabel(value_col, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_plot_data(country_stats, filename)

def plot_latitude_gradient(df, value_col, title, filename):
    """Plot a latitude gradient box plot"""
    df['lat_bin'] = pd.cut(df['lat'], bins=np.arange(-60, 90, 10))
    
    plt.figure(figsize=(14, 6))
    sns.boxplot(x='lat_bin', y=value_col, data=df, palette="coolwarm", showfliers=False)
    
    plt.title(title, fontsize=16)
    plt.xlabel("Latitude Zone", fontsize=12)
    plt.ylabel(value_col, fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    # Export aggregate data (box plot data is complex; export summary statistics)
    stats = df.groupby('lat_bin')[value_col].describe()
    export_plot_data(stats, filename)

def plot_resource_mismatch(df):
    """Plot the resource-emission mismatch scatter plot"""
    plt.figure(figsize=(12, 8))
    
    country_agg = df.groupby('country').agg({
        'grid_ef': 'mean',
        'pvout_daily_kwh_kwp': 'mean',
        'capacity_mw_est': 'sum',
        'avoided_co2_ton': 'sum'
    }).reset_index()
    
    country_agg = country_agg[country_agg['capacity_mw_est'] > 100]
    
    sc = plt.scatter(
        country_agg['grid_ef'], 
        country_agg['pvout_daily_kwh_kwp'], 
        s=country_agg['capacity_mw_est'] / 10,
        c=country_agg['avoided_co2_ton'],
        cmap='RdYlGn_r',
        alpha=0.7,
        edgecolors='grey'
    )
    
    top_countries = country_agg.nlargest(10, 'capacity_mw_est')['country'].tolist()
    for i, row in country_agg.iterrows():
        if row['country'] in top_countries:
            plt.text(row['grid_ef'], row['pvout_daily_kwh_kwp'], row['country'], fontsize=9)
            
    plt.colorbar(sc, label='Total Avoided CO2 (ton/yr)')
    
    plt.title("Global Solar Resource vs. Grid Carbon Intensity\n(Bubble Size = Total Capacity)", fontsize=16)
    plt.xlabel("Grid Emission Factor (tCO2/MWh) - Dirty -> Clean", fontsize=12)
    plt.ylabel("Solar Potential (PVOUT, kWh/kWp/day) - Low -> High", fontsize=12)
    
    plt.axvline(x=0.475, color='gray', linestyle='--', alpha=0.5)
    plt.axhline(y=4.0, color='gray', linestyle='--', alpha=0.5)
    
    plt.text(0.8, 5.0, "High Impact Zone", color='green', ha='center')
    plt.text(0.2, 3.0, "Low Impact Zone", color='red', ha='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Resource_Mismatch_Analysis.png"))
    plt.close()
    
    export_plot_data(country_agg, "Resource_Mismatch_Analysis.png")

# ================= New analysis functions =================

def load_and_merge_data():
    """Load the CSV and merge time fields from the Shapefile"""
    print("Loading CSV data...")
    df = pd.read_csv(INPUT_CSV)
    
    print("Loading time fields from Shapefile...")
    # Read only the necessary columns for speed
    gdf = gpd.read_file(SOLAR_SHP)[['fid', 'constructi', 'construc_1']]
    
    # Ensure consistent fid types
    df['fid'] = df['fid'].astype(int)
    gdf['fid'] = gdf['fid'].astype(int)
    
    print("Merging data...")
    merged = df.merge(gdf, on='fid', how='left')
    
    # Clean time data
    # Rule: values <= 2017 are set to 2017 Q4
    merged['year'] = merged['constructi'].fillna(2017).astype(int)
    merged['quarter'] = merged['construc_1'].fillna(4).astype(int)
    
    # Correction logic
    mask_old = merged['year'] <= 2017
    merged.loc[mask_old, 'year'] = 2017
    merged.loc[mask_old, 'quarter'] = 4
    
    # Create a time index (YYYY-QX)
    merged['time_str'] = merged['year'].astype(str) + '-Q' + merged['quarter'].astype(str)
    
    # Create a numeric time for sorting (Year + Quarter/4)
    merged['time_val'] = merged['year'] + (merged['quarter'] - 1) / 4
    
    print(f"Merge complete; {len(merged)} records in total.")
    return merged

def plot_temporal_trends(df):
    """Plot annual and quarterly new capacity trends"""
    # 1. Annual new capacity (Bar)
    yearly_stats = df[df['year'] > 2017].groupby('year')['capacity_mw_est'].sum()
    # Add 2017 (as the existing stock baseline, shown separately or annotated)
    stock_2017 = df[df['year'] == 2017]['capacity_mw_est'].sum()
    
    plt.figure(figsize=(10, 6))
    ax = yearly_stats.plot(kind='bar', color='orange', alpha=0.8)
    plt.title("Annual Newly Installed Solar Capacity (2018-2024)", fontsize=16)
    plt.ylabel("Capacity (MW)", fontsize=12)
    plt.xlabel("Year", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    # Add the 2017 stock annotation
    plt.text(0, yearly_stats.max(), f"Pre-2018 Stock:\n{stock_2017/1000:.1f} GW", 
             bbox=dict(facecolor='lightgrey', alpha=0.5))
    
    plt.tight_layout()
    filename = "Temporal_Annual_New_Capacity.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(yearly_stats, filename)
    
    # 2. Quarterly new capacity trend (Line/Area) - only 2018-2024
    q_stats = df[df['year'] > 2017].groupby(['year', 'quarter'])['capacity_mw_est'].sum().reset_index()
    q_stats['time_label'] = q_stats['year'].astype(str) + '-Q' + q_stats['quarter'].astype(str)
    
    plt.figure(figsize=(14, 6))
    plt.plot(q_stats['time_label'], q_stats['capacity_mw_est'], marker='o', linestyle='-', color='darkorange')
    plt.fill_between(q_stats['time_label'], q_stats['capacity_mw_est'], color='orange', alpha=0.3)
    
    plt.title("Quarterly Newly Installed Solar Capacity (2018-2024)", fontsize=16)
    plt.ylabel("Capacity (MW)", fontsize=12)
    plt.xlabel("Quarter", fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    filename = "Temporal_Quarterly_Trend.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(q_stats, filename)

def plot_spatiotemporal_heatmap(df):
    """Plot a latitude-year heatmap (showing the shift of the solar centroid)"""
    # Analyze only 2018-2024 new capacity
    df_new = df[df['year'] > 2017].copy()
    
    # Latitude binning
    df_new['lat_bin'] = pd.cut(df_new['lat'], bins=np.arange(-60, 90, 5), labels=np.arange(-57.5, 87.5, 5))
    
    # Aggregate: year x latitude -> capacity
    pivot = df_new.pivot_table(index='lat_bin', columns='year', values='capacity_mw_est', aggfunc='sum', fill_value=0)
    
    # Normalize (by year, to view the distribution centroid of each year)
    pivot_norm = pivot.div(pivot.sum(axis=0), axis=1)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot_norm, cmap='Oranges', cbar_kws={'label': 'Proportion of Annual Capacity'})
    
    plt.title("Spatiotemporal Evolution of Solar Installation (Latitude vs Year)", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Latitude", fontsize=12)
    plt.gca().invert_yaxis() # Northern hemisphere on top
    plt.tight_layout()
    
    filename = "Spatiotemporal_Heatmap.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(pivot, filename)

def plot_efficiency_evolution(df):
    """Plot the evolution of resource efficiency and emission-reduction efficiency over time"""
    # Compute the weighted average PVOUT and Grid EF for each year
    # Weight: Capacity
    
    def weighted_avg(x, val_col, weight_col):
        try:
            return np.average(x[val_col], weights=x[weight_col])
        except ZeroDivisionError:
            return 0

    years = sorted(df['year'].unique())
    res = []
    
    for y in years:
        sub = df[df['year'] == y]
        avg_pvout = weighted_avg(sub, 'pvout_daily_kwh_kwp', 'capacity_mw_est')
        avg_ef = weighted_avg(sub, 'grid_ef', 'capacity_mw_est')
        res.append({'year': y, 'avg_pvout': avg_pvout, 'avg_ef': avg_ef})
        
    df_evo = pd.DataFrame(res)
    # Exclude 2017 (baseline) if only incremental changes are wanted; kept here for comparison
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:orange'
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Avg. PVOUT (kWh/kWp/day)', color=color, fontsize=12)
    ax1.plot(df_evo['year'], df_evo['avg_pvout'], marker='o', color=color, linewidth=2, label='Resource Quality')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()  
    color = 'tab:gray'
    ax2.set_ylabel('Avg. Grid Emission Factor (tCO2/MWh)', color=color, fontsize=12)
    ax2.plot(df_evo['year'], df_evo['avg_ef'], marker='s', color=color, linestyle='--', linewidth=2, label='Grid Carbon Intensity')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title("Evolution of Solar Siting Efficiency (2017-2024)\nAre we moving to sunnier or dirtier places?", fontsize=16)
    plt.grid(True, alpha=0.3)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    filename = "Evolution_Efficiency.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(df_evo, filename)

def plot_lorenz_curve(df):
    """Plot the Lorenz curve (assessing the inequality of solar emission-reduction contributions)"""
    # Sort by Avoided CO2
    sorted_df = df.sort_values('avoided_co2_ton')
    
    # Compute cumulative percentages
    cum_sites = np.arange(1, len(df) + 1) / len(df)
    cum_co2 = sorted_df['avoided_co2_ton'].cumsum() / sorted_df['avoided_co2_ton'].sum()
    
    # Compute the Gini coefficient
    gini = 1 - 2 * np.trapz(cum_co2, cum_sites)
    
    plt.figure(figsize=(8, 8))
    plt.plot(cum_sites, cum_co2, label=f'Avoided CO2 (Gini = {gini:.3f})', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Equality')
    
    plt.title("Lorenz Curve of Solar Carbon Avoidance", fontsize=16)
    plt.xlabel("Cumulative Share of Solar Sites", fontsize=12)
    plt.ylabel("Cumulative Share of Avoided CO2", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    filename = "Lorenz_Curve_CO2.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    lorenz_data = pd.DataFrame({'cum_sites': cum_sites, 'cum_co2': cum_co2})
    # Downsample for export to avoid an oversized CSV
    export_plot_data(lorenz_data.iloc[::100, :], filename)

def plot_pvout_raster():
    """Render and save the PVOUT raster map"""
    print(f"Reading raster file: {PVOUT_TIF} ...")
    try:
        with rasterio.open(PVOUT_TIF) as src:
            # Read data (first band)
            data = src.read(1)
            
            # Set nodata values to NaN for transparent display
            data = data.astype('float32')
            data[data == src.nodata] = np.nan
            
            fig, ax = plt.subplots(figsize=(15, 8))
            
            # Use rasterio.plot.show to render, or imshow directly
            # We use imshow here for better colorbar control
            im = ax.imshow(data, cmap='plasma', extent=[src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top])
            
            # Add world map boundaries (optional, enhances the effect)
            try:
                world = gpd.read_file(WORLD_SHP)
                world.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5, alpha=0.5)
            except:
                pass

            plt.colorbar(im, label='PVOUT (kWh/kWp/day)', fraction=0.02, pad=0.04)
            plt.title("Global Photovoltaic Power Potential (PVOUT)", fontsize=16)
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            
            plt.tight_layout()
            filename = "Map_Raster_PVOUT.png"
            plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
            plt.close()
            print(f"Raster map saved: {filename}")
            
    except Exception as e:
        print(f"Failed to render raster map: {e}")

def plot_grid_ef_map(df):
    """Plot the country-level grid emission factor map (country polygon data)"""
    print("Plotting the grid emission factor map...")
    try:
        # Load world map
        try:
            world = gpd.read_file(WORLD_SHP)
        except Exception as e:
            print(f"Failed to load world map basemap ({e}); skipping the polygon map.")
            return

        # Prepare data: average emission factor per country
        # Note: we aggregate from df here, ensuring country names match
        country_ef = df.groupby('country')['grid_ef'].mean().reset_index()
        
        # For a better match, country names may need alignment
        # We make a simplified assumption here: the country column in INPUT_CSV is already standardized, or approximately matches world.name
        # In practice, fuzzy matching may be required. We first try a direct merge, then supplement with point plots
        
        # Unify column names for merging
        # The world shp usually has 'name' or 'NAME'
        world_cols = world.columns.str.lower()
        if 'name' in world_cols:
            left_on = 'name'
        elif 'admin' in world_cols:
            left_on = 'admin'
        else:
            print("Cannot find a country name column in the world map; skipping.")
            return
            
        # Simple name mapping corrections (based on experience)
        name_map = {
            'United States': 'United States of America',
            'China': 'China',
            # Add more as needed
        }
        country_ef['match_name'] = country_ef['country'].replace(name_map)
        
        # Merge
        world_data = world.merge(country_ef, left_on=world.columns[world_cols == left_on][0], right_on='match_name', how='left')
        
        # Plot
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Plot background (all countries)
        world.plot(ax=ax, color='lightgrey', edgecolor='white')
        
        # Plot countries with data
        world_data.dropna(subset=['grid_ef']).plot(column='grid_ef', ax=ax, legend=True,
                                                   legend_kwds={'label': "Grid Emission Factor (tCO2/MWh)", 'orientation': "vertical"},
                                                   cmap='RdYlGn_r', # Red (high) -> Green (low)
                                                   edgecolor='black', linewidth=0.5)
        
        plt.title("Global Grid Emission Factors by Country", fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        
        filename = "Map_Global_Grid_EF.png"
        plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
        plt.close()
        print(f"Grid emission factor map saved: {filename}")
        
        export_plot_data(country_ef, filename)
        
    except Exception as e:
        print(f"Failed to plot the grid emission factor map: {e}")

# ================= Main program =================

def main():
    # 1. Data preparation
    df = load_and_merge_data()
    
    # Data cleaning
    df = df[df['pvout_daily_kwh_kwp'] > 0]
    print(f"Valid data rows: {len(df)}")
    
    # 2. Basic statistics (original functions)
    print(">>> Plotting basic statistics...")
    plot_global_map(df, 'pvout_daily_kwh_kwp', 'Global Solar Power Potential (PVOUT)', 'Map_Global_PVOUT.png', cmap='plasma')
    plot_global_map(df, 'avoided_co2_ton', 'Global Annual Avoided CO2 Emissions', 'Map_Global_Avoided_CO2.png', cmap='RdYlGn_r', log_scale=True)
    plot_top_countries(df, 'capacity_mw_est', 'Top 15 Countries by Estimated Solar Capacity (MW)', 'Bar_Top15_Capacity.png')
    plot_latitude_gradient(df, 'pvout_daily_kwh_kwp', 'Solar Potential Distribution by Latitude', 'Box_Latitude_PVOUT.png')
    
    # Try to plot the resource mismatch map; skip if the file is occupied
    try:
        plot_resource_mismatch(df)
    except Exception as e:
        print(f"Failed to plot the resource mismatch map (file may be occupied): {e}")
    
    # 3. New statistics (time/spatiotemporal)
    print(">>> Plotting temporal and spatiotemporal analysis figures...")
    plot_temporal_trends(df)
    plot_spatiotemporal_heatmap(df)
    plot_efficiency_evolution(df)
    plot_lorenz_curve(df)
    
    # 4. Plot the PVOUT raster basemap
    print(">>> Plotting the PVOUT raster map...")
    plot_pvout_raster()

    # 5. Plot the grid emission factor map
    plot_grid_ef_map(df)

    # 6. Output summary
    summary_path = os.path.join(OUTPUT_DIR, "Statistical_Summary_Enhanced.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=== Global Solar Power Analysis Summary (Enhanced) ===\n\n")
        f.write(f"Total Sites Analyzed: {len(df)}\n")
        f.write(f"Total Capacity: {df['capacity_mw_est'].sum()/1000:.2f} GW\n")
        f.write(f"  - Pre-2018 Stock: {df[df['year']==2017]['capacity_mw_est'].sum()/1000:.2f} GW\n")
        f.write(f"  - 2018-2024 New: {df[df['year']>2017]['capacity_mw_est'].sum()/1000:.2f} GW\n")
        f.write(f"Total Avoided CO2: {df['avoided_co2_ton'].sum()/1e6:.2f} Mt/yr\n\n")
        
        f.write("--- Yearly New Capacity (MW) ---\n")
        f.write(df[df['year']>2017].groupby('year')['capacity_mw_est'].sum().to_string())
        f.write("\n")
        
    print(f"\nAll analysis complete! Results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
