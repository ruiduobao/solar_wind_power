# -*- coding: utf-8 -*-
"""
Wind power capacity statistical analysis and mapping
Author: 锐多宝 (ruiduobao)
Date: 2026-01-07
Description:
    Read Wind_Power_Potential.csv and the wind Shapefile for multi-dimensional statistical analysis and visualization.
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
INPUT_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Wind_Power_Potential.csv"
WIND_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\windpower.shp"
CF_TIF = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风力发电数据\cf_iec2_cog_100m.tif"

# Try to obtain the world map path
try:
    WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')
except AttributeError:
    WORLD_SHP = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算"

# Plot style settings
sns.set_theme(style="whitegrid", font="Arial") 
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

# ================= Helper functions =================

def export_plot_data(df, filename):
    """Export the plotting data as CSV"""
    csv_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '.csv'))
    try:
        df.to_csv(csv_path, index=True, encoding='utf-8-sig')
        print(f"Data exported: {csv_path}")
    except Exception as e:
        print(f"Failed to export CSV: {e}")

def plot_global_map(df, value_col, title, filename, cmap='viridis', log_scale=False):
    """Plot a global scatter map"""
    try:
        world = gpd.read_file(WORLD_SHP)
    except Exception as e:
        print(f"Failed to load the world map basemap ({e}); only scatter points will be plotted.")
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
    
    stats = df.groupby('lat_bin')[value_col].describe()
    export_plot_data(stats, filename)

def plot_resource_mismatch(df):
    """Plot the resource-emission mismatch scatter plot"""
    plt.figure(figsize=(12, 8))
    
    country_agg = df.groupby('country').agg({
        'grid_ef': 'mean',
        'cf_val': 'mean',
        'capacity_mw_est': 'sum',
        'avoided_co2_ton': 'sum'
    }).reset_index()
    
    country_agg = country_agg[country_agg['capacity_mw_est'] > 100]
    
    sc = plt.scatter(
        country_agg['grid_ef'], 
        country_agg['cf_val'], 
        s=country_agg['capacity_mw_est'] / 10,
        c=country_agg['avoided_co2_ton'],
        cmap='RdYlGn_r',
        alpha=0.7,
        edgecolors='grey'
    )
    
    # Annotate the Top 10
    top_countries = country_agg.nlargest(10, 'capacity_mw_est')['country'].tolist()
    for i, row in country_agg.iterrows():
        if row['country'] in top_countries:
            plt.text(row['grid_ef'], row['cf_val'], row['country'], fontsize=9)
            
    plt.colorbar(sc, label='Total Avoided CO2 (ton/yr)')
    
    plt.title("Global Wind Resource vs. Grid Carbon Intensity\n(Bubble Size = Total Capacity)", fontsize=16)
    plt.xlabel("Grid Emission Factor (tCO2/MWh) - Dirty -> Clean", fontsize=12)
    plt.ylabel("Wind Capacity Factor (0-1) - Low -> High", fontsize=12)
    
    # Add reference lines (CF mean about 0.3?, EF mean 0.475)
    plt.axvline(x=0.475, color='gray', linestyle='--', alpha=0.5)
    plt.axhline(y=0.30, color='gray', linestyle='--', alpha=0.5) # Assume 0.3 is a good CF
    
    plt.text(0.8, 0.45, "High Impact Zone", color='green', ha='center')
    plt.text(0.2, 0.15, "Low Impact Zone", color='red', ha='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Resource_Mismatch_Analysis.png"))
    plt.close()
    
    export_plot_data(country_agg, "Resource_Mismatch_Analysis.png")

# ================= New analysis functions =================

def load_and_merge_data():
    """Load the CSV and merge the time fields from the Shapefile"""
    print("Loading the CSV data...")
    df = pd.read_csv(INPUT_CSV)
    
    print("Loading the time fields from the Shapefile...")
    gdf = gpd.read_file(WIND_SHP)[['fid', 'constructi', 'construc_1']]
    
    df['fid'] = df['fid'].astype(int)
    gdf['fid'] = gdf['fid'].astype(int)
    
    print("Merging data...")
    merged = df.merge(gdf, on='fid', how='left')
    
    # Clean the time data
    merged['year'] = merged['constructi'].fillna(2017).astype(int)
    merged['quarter'] = merged['construc_1'].fillna(4).astype(int)
    
    mask_old = merged['year'] <= 2017
    merged.loc[mask_old, 'year'] = 2017
    merged.loc[mask_old, 'quarter'] = 4
    
    merged['time_str'] = merged['year'].astype(str) + '-Q' + merged['quarter'].astype(str)
    
    print(f"Merge complete; {len(merged)} records in total.")
    return merged

def plot_temporal_trends(df):
    """Plot the annual and quarterly new capacity trends"""
    yearly_stats = df[df['year'] > 2017].groupby('year')['capacity_mw_est'].sum()
    stock_2017 = df[df['year'] == 2017]['capacity_mw_est'].sum()
    
    plt.figure(figsize=(10, 6))
    ax = yearly_stats.plot(kind='bar', color='skyblue', alpha=0.8)
    plt.title("Annual Newly Installed Wind Capacity (2018-2024)", fontsize=16)
    plt.ylabel("Capacity (MW)", fontsize=12)
    plt.xlabel("Year", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    plt.text(0, yearly_stats.max(), f"Pre-2018 Stock:\n{stock_2017/1000:.1f} GW", 
             bbox=dict(facecolor='lightgrey', alpha=0.5))
    
    plt.tight_layout()
    filename = "Temporal_Annual_New_Capacity.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(yearly_stats, filename)
    
    q_stats = df[df['year'] > 2017].groupby(['year', 'quarter'])['capacity_mw_est'].sum().reset_index()
    q_stats['time_label'] = q_stats['year'].astype(str) + '-Q' + q_stats['quarter'].astype(str)
    
    plt.figure(figsize=(14, 6))
    plt.plot(q_stats['time_label'], q_stats['capacity_mw_est'], marker='o', linestyle='-', color='dodgerblue')
    plt.fill_between(q_stats['time_label'], q_stats['capacity_mw_est'], color='skyblue', alpha=0.3)
    
    plt.title("Quarterly Newly Installed Wind Capacity (2018-2024)", fontsize=16)
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
    """Plot a latitude-year heatmap"""
    df_new = df[df['year'] > 2017].copy()
    df_new['lat_bin'] = pd.cut(df_new['lat'], bins=np.arange(-60, 90, 5), labels=np.arange(-57.5, 87.5, 5))
    pivot = df_new.pivot_table(index='lat_bin', columns='year', values='capacity_mw_est', aggfunc='sum', fill_value=0)
    pivot_norm = pivot.div(pivot.sum(axis=0), axis=1)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot_norm, cmap='Blues', cbar_kws={'label': 'Proportion of Annual Capacity'})
    
    plt.title("Spatiotemporal Evolution of Wind Installation (Latitude vs Year)", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Latitude", fontsize=12)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    filename = "Spatiotemporal_Heatmap.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(pivot, filename)

def plot_efficiency_evolution(df):
    """Plot the evolution of resource efficiency and emission-reduction efficiency over time"""
    def weighted_avg(x, val_col, weight_col):
        try:
            return np.average(x[val_col], weights=x[weight_col])
        except ZeroDivisionError:
            return 0

    years = sorted(df['year'].unique())
    res = []
    
    for y in years:
        sub = df[df['year'] == y]
        avg_cf = weighted_avg(sub, 'cf_val', 'capacity_mw_est')
        avg_ef = weighted_avg(sub, 'grid_ef', 'capacity_mw_est')
        res.append({'year': y, 'avg_cf': avg_cf, 'avg_ef': avg_ef})
        
    df_evo = pd.DataFrame(res)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Avg. Capacity Factor (0-1)', color=color, fontsize=12)
    ax1.plot(df_evo['year'], df_evo['avg_cf'], marker='o', color=color, linewidth=2, label='Resource Quality')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()  
    color = 'tab:gray'
    ax2.set_ylabel('Avg. Grid Emission Factor (tCO2/MWh)', color=color, fontsize=12)
    ax2.plot(df_evo['year'], df_evo['avg_ef'], marker='s', color=color, linestyle='--', linewidth=2, label='Grid Carbon Intensity')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title("Evolution of Wind Siting Efficiency (2017-2024)", fontsize=16)
    plt.grid(True, alpha=0.3)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    filename = "Evolution_Efficiency.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_plot_data(df_evo, filename)

def plot_lorenz_curve(df):
    """Plot the Lorenz curve"""
    sorted_df = df.sort_values('avoided_co2_ton')
    cum_sites = np.arange(1, len(df) + 1) / len(df)
    cum_co2 = sorted_df['avoided_co2_ton'].cumsum() / sorted_df['avoided_co2_ton'].sum()
    gini = 1 - 2 * np.trapz(cum_co2, cum_sites)
    
    plt.figure(figsize=(8, 8))
    plt.plot(cum_sites, cum_co2, label=f'Avoided CO2 (Gini = {gini:.3f})', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Equality')
    
    plt.title("Lorenz Curve of Wind Carbon Avoidance", fontsize=16)
    plt.xlabel("Cumulative Share of Wind Sites", fontsize=12)
    plt.ylabel("Cumulative Share of Avoided CO2", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    filename = "Lorenz_Curve_CO2.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    lorenz_data = pd.DataFrame({'cum_sites': cum_sites, 'cum_co2': cum_co2})
    export_plot_data(lorenz_data.iloc[::100, :], filename)

def plot_cf_raster():
    """Render and save the CF raster map"""
    print(f"Reading the raster file: {CF_TIF} ...")
    try:
        with rasterio.open(CF_TIF) as src:
            # Downsample for reading to prevent memory overflow (30GB -> 300MB)
            scale_factor = 0.1
            new_height = int(src.height * scale_factor)
            new_width = int(src.width * scale_factor)
            
            data = src.read(
                1,
                out_shape=(new_height, new_width),
                resampling=rasterio.enums.Resampling.bilinear
            )
            
            # Handle nodata (usually < 0)
            data = data.astype('float32')
            # Assume the GWA nodata is -9999 or similar
            data[data < 0] = np.nan
            
            # If it is an integer 0-1000, convert to 0-1
            # Here we simply check the max
            if np.nanmax(data) > 10:
                data = data / 100.0 # Assume it is % ? GWA may be 0-1000? 
                # Let us assume > 1 means %
            
            fig, ax = plt.subplots(figsize=(15, 8))
            im = ax.imshow(data, cmap='viridis', extent=[src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top])
            
            try:
                world = gpd.read_file(WORLD_SHP)
                world.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5, alpha=0.5)
            except:
                pass

            plt.colorbar(im, label='Capacity Factor', fraction=0.02, pad=0.04)
            plt.title("Global Wind Power Capacity Factor (IEC2 100m)", fontsize=16)
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            
            plt.tight_layout()
            filename = "Map_Raster_CF.png"
            plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
            plt.close()
            print(f"Raster map saved: {filename}")
            
    except Exception as e:
        print(f"Failed to render the raster map: {e}")

def plot_grid_ef_map(df):
    """Plot the grid emission factor map by country"""
    print("Plotting the grid emission factor map...")
    try:
        try:
            world = gpd.read_file(WORLD_SHP)
        except Exception as e:
            return

        country_ef = df.groupby('country')['grid_ef'].mean().reset_index()
        
        world_cols = world.columns.str.lower()
        if 'name' in world_cols:
            left_on = 'name'
        elif 'admin' in world_cols:
            left_on = 'admin'
        else:
            return
            
        name_map = {
            'United States': 'United States of America',
            'China': 'China',
        }
        country_ef['match_name'] = country_ef['country'].replace(name_map)
        
        world_data = world.merge(country_ef, left_on=world.columns[world_cols == left_on][0], right_on='match_name', how='left')
        
        fig, ax = plt.subplots(figsize=(15, 8))
        world.plot(ax=ax, color='lightgrey', edgecolor='white')
        
        world_data.dropna(subset=['grid_ef']).plot(column='grid_ef', ax=ax, legend=True,
                                                   legend_kwds={'label': "Grid Emission Factor (tCO2/MWh)", 'orientation': "vertical"},
                                                   cmap='RdYlGn_r',
                                                   edgecolor='black', linewidth=0.5)
        
        plt.title("Global Grid Emission Factors by Country", fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        
        filename = "Map_Global_Grid_EF.png"
        plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
        plt.close()
        export_plot_data(country_ef, filename)
        
    except Exception as e:
        print(f"Failed to plot the grid emission factor map: {e}")

# ================= Main program =================

def main():
    # 1. Data preparation
    # If the CSV does not exist, remind the user to run step 1 first
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found. Please run '1.计算风电发电能力.py' first.")
        return

    df = load_and_merge_data()
    df = df[df['cf_val'] > 0]
    print(f"Valid data rows: {len(df)}")
    
    # 2. Basic statistics
    print(">>> Plotting the basic statistics figures...")
    plot_global_map(df, 'cf_val', 'Global Wind Capacity Factor (CF)', 'Map_Global_CF.png', cmap='viridis')
    plot_global_map(df, 'avoided_co2_ton', 'Global Annual Avoided CO2 Emissions (Wind)', 'Map_Global_Avoided_CO2.png', cmap='RdYlGn_r', log_scale=True)
    plot_top_countries(df, 'capacity_mw_est', 'Top 15 Countries by Estimated Wind Capacity (MW)', 'Bar_Top15_Capacity.png')
    plot_latitude_gradient(df, 'cf_val', 'Wind CF Distribution by Latitude', 'Box_Latitude_CF.png')
    
    try:
        plot_resource_mismatch(df)
    except Exception as e:
        print(f"Failed to plot the resource mismatch figure: {e}")
    
    # 3. New statistics
    print(">>> Plotting the temporal and spatiotemporal analysis figures...")
    plot_temporal_trends(df)
    plot_spatiotemporal_heatmap(df)
    plot_efficiency_evolution(df)
    plot_lorenz_curve(df)
    
    # 4. Plot the CF raster basemap
    print(">>> Plotting the CF raster map...")
    plot_cf_raster()
    
    # 5. Plot the grid emission factor map
    plot_grid_ef_map(df)

    # 6. Output the summary
    summary_path = os.path.join(OUTPUT_DIR, "Statistical_Summary_Wind.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=== Global Wind Power Analysis Summary ===\n\n")
        f.write(f"Total Sites Analyzed: {len(df)}\n")
        f.write(f"Total Capacity: {df['capacity_mw_est'].sum()/1000:.2f} GW\n")
        f.write(f"  - Pre-2018 Stock: {df[df['year']==2017]['capacity_mw_est'].sum()/1000:.2f} GW\n")
        f.write(f"  - 2018-2024 New: {df[df['year']>2017]['capacity_mw_est'].sum()/1000:.2f} GW\n")
        f.write(f"Total Avoided CO2: {df['avoided_co2_ton'].sum()/1e6:.2f} Mt/yr\n")
        f.write(f"Average Capacity Factor: {df['cf_val'].mean():.4f}\n\n")
        
        f.write("--- Yearly New Capacity (MW) ---\n")
        f.write(df[df['year']>2017].groupby('year')['capacity_mw_est'].sum().to_string())
        f.write("\n")
        
    print(f"\nAll analysis complete! Results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
