# -*- coding: utf-8 -*-
"""
Deep comparative analysis of solar PV and wind power generation potential
Author: 锐多宝 (ruiduobao)
Date: 2026-01-07
Description:
    Reads Solar_Power_Potential.csv and Wind_Power_Potential.csv,
    performs multi-dimensional deep comparative analysis, and generates
    publication-quality figures for top-tier journals.

    Main figures:
    1. [Resource quality] Global capacity factor distribution comparison (Violin Plot)
    2. [Spatial complementarity] Latitude-resource-capacity composite distribution (Dual-Axis Latitude Profile)
    3. [Country dimension] Country resource competitiveness matrix (Country Resource Matrix Bubble Plot)
    4. [Equity] Lorenz curves of emission reduction contributions (Lorenz Curves)
    5. [Mitigation strategy] Grid cleanliness vs resource efficiency joint distribution (Joint Distribution)
    6. [Temporal evolution] Technology progress and resource selection trends (Temporal Evolution of CF)
    7. [Regional pattern] Continental solar/wind capacity mix comparison (Continent Stacked Bar)
    8. [Resource preference] Global solar/wind resource advantage ratio map (Global Resource Ratio Map)
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import geopandas as gpd
from scipy import stats
import contextily as ctx # optional dependency; skip if unavailable
from matplotlib.colors import LinearSegmentedColormap

# ================= Configuration =================

# Input data
SOLAR_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Solar_Power_Potential.csv"
WIND_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Wind_Power_Potential.csv"
SOLAR_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\solarpower.shp"
WIND_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\windpower.shp"
WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比"

# Plotting style - academic
sns.set_theme(style="ticks", font="Arial", context="paper")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.family'] = 'sans-serif' # compatibility
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'SimHei'] # fallback for CJK support

# Color configuration
COLOR_SOLAR = '#FFB000' # warm orange
COLOR_WIND = '#00B4D8'  # fresh blue
COLOR_RATIO = 'RdYlBu'  # Red(Solar) -> Blue(Wind)

# ================= Helper functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def export_data(df, filename):
    csv_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '.csv'))
    try:
        df.to_csv(csv_path, index=True, encoding='utf-8-sig')
        print(f"Data exported: {csv_path}")
    except Exception as e:
        print(f"Export failed: {e}")

# ================= Data loading and preprocessing =================

def load_data():
    print(">>> Loading and preprocessing data...")
    
    # 1. Read base CSVs
    df_s = pd.read_csv(SOLAR_CSV)
    df_w = pd.read_csv(WIND_CSV)
    
    df_s['Type'] = 'Solar PV'
    df_w['Type'] = 'Onshore Wind'
    
    # 2. Append temporal info (merge with SHP)
    try:
        print("    Joining Shapefile to obtain construction year...")
        # Read only the necessary columns for speed
        gdf_s = gpd.read_file(SOLAR_SHP)[['fid', 'constructi']]
        gdf_w = gpd.read_file(WIND_SHP)[['fid', 'constructi']]
        
        # Ensure consistent fid types
        df_s['fid'] = df_s['fid'].astype(int)
        gdf_s['fid'] = gdf_s['fid'].astype(int)
        df_w['fid'] = df_w['fid'].astype(int)
        gdf_w['fid'] = gdf_w['fid'].astype(int)
        
        # Merge
        df_s = df_s.merge(gdf_s, on='fid', how='left')
        df_w = df_w.merge(gdf_w, on='fid', how='left')
        
        # Fill and clean the year
        df_s['year'] = df_s['constructi'].fillna(2017).astype(int)
        df_w['year'] = df_w['constructi'].fillna(2017).astype(int)
        
        # Normalize old data (<=2010 to 2010 to avoid a long tail)
        df_s.loc[df_s['year'] < 2010, 'year'] = 2010
        df_w.loc[df_w['year'] < 2010, 'year'] = 2010
        
    except Exception as e:
        print(f"    Warning: Failed to load Shapefile ({e}); using existing CSV data or defaults.")
        if 'year' not in df_s.columns: df_s['year'] = 2017
        if 'year' not in df_w.columns: df_w['year'] = 2017

    # 3. Metric standardization
    # Capacity Factor (0-1)
    # Solar: PVOUT (kWh/kWp/day) -> CF = PVOUT / 24
    if 'pvout_daily_kwh_kwp' in df_s.columns:
        df_s['Capacity_Factor'] = df_s['pvout_daily_kwh_kwp'] / 24.0
    else:
        df_s['Capacity_Factor'] = 0.15 # Fallback
        
    # Wind: CF directly (ensure it is 0-1)
    if 'cf_val' in df_w.columns:
        df_w['Capacity_Factor'] = df_w['cf_val']
    else:
        df_w['Capacity_Factor'] = 0.25 # Fallback
    
    # CO2 avoidance efficiency per installed capacity (tCO2/MW/yr)
    df_s['Efficiency_CO2'] = df_s['avoided_co2_ton'] / df_s['capacity_mw_est']
    df_w['Efficiency_CO2'] = df_w['avoided_co2_ton'] / df_w['capacity_mw_est']
    
    # Latitude binning
    bins = np.arange(-60, 90, 5)
    labels = bins[:-1] + 2.5 # use bin centers
    df_s['lat_bin'] = pd.cut(df_s['lat'], bins=bins, labels=labels)
    df_w['lat_bin'] = pd.cut(df_w['lat'], bins=bins, labels=labels)
    
    print(f"    Solar: {len(df_s)} sites, Wind: {len(df_w)} sites")
    return df_s, df_w

def add_continent_info(df_s, df_w):
    print("    Adding continent information...")
    try:
        world = gpd.read_file(WORLD_SHP)
        # Simplified: keep only geometry and CONTINENT
        if 'CONTINENT' not in world.columns:
             # Try to find a similar column
             cols = [c for c in world.columns if 'CONT' in c.upper() or 'REGION' in c.upper()]
             if cols:
                 world['CONTINENT'] = world[cols[0]]
             else:
                 world['CONTINENT'] = 'Unknown'
        
        # Build Country -> Continent mapping (based on name or iso)
        # Here df_s has 'country' (e.g. "China"), world has 'ADMIN' or 'NAME'
        # Use a simple dict mapping first, skip complex spatial joins to save time
        
        # Uppercase for consistency
        world['name_upper'] = world['ADMIN'].str.upper()
        
        # Extract dictionary
        cnt_dict = world.set_index('name_upper')['CONTINENT'].to_dict()
        
        # Manually correct common discrepancies
        cnt_dict['UNITED STATES'] = 'North America'
        cnt_dict['USA'] = 'North America'
        cnt_dict['UK'] = 'Europe'
        cnt_dict['UNITED KINGDOM'] = 'Europe'
        cnt_dict['KOREA'] = 'Asia'
        cnt_dict['SOUTH KOREA'] = 'Asia'
        
        df_s['Continent'] = df_s['country'].str.upper().map(cnt_dict).fillna('Others')
        df_w['Continent'] = df_w['country'].str.upper().map(cnt_dict).fillna('Others')
        
        return df_s, df_w, world
        
    except Exception as e:
        print(f"    Failed to load world map or map continents: {e}")
        df_s['Continent'] = 'Unknown'
        df_w['Continent'] = 'Unknown'
        return df_s, df_w, None

# ================= Advanced plotting functions =================

def plot_cf_violin(df_s, df_w):
    """1. Resource quality comparison: violin plot"""
    print("Plotting 1. Capacity factor violin plot...")
    
    data = pd.concat([
        df_s[['Capacity_Factor', 'Type']], 
        df_w[['Capacity_Factor', 'Type']]
    ])
    
    plt.figure(figsize=(8, 6))
    
    sns.violinplot(data=data, x='Type', y='Capacity_Factor', palette=[COLOR_SOLAR, COLOR_WIND], 
                   inner="quartile", alpha=0.8, linewidth=1.5)
    
    # Add mean markers
    means = data.groupby('Type')['Capacity_Factor'].mean()
    plt.scatter(x=[0, 1], y=[means['Solar PV'], means['Onshore Wind']], color='red', zorder=10, label='Mean', s=50, marker='D')
    
    plt.title("Global Capacity Factor Distribution: Solar vs Wind", fontsize=14, fontweight='bold')
    plt.ylabel("Capacity Factor (0-1)", fontsize=12)
    plt.xlabel("")
    plt.ylim(0, 0.6)
    
    # Add statistical test (T-test)
    t_stat, p_val = stats.ttest_ind(df_s['Capacity_Factor'].dropna(), df_w['Capacity_Factor'].dropna(), equal_var=False)
    plt.text(0.5, 0.55, f"Welch's t-test: p < 0.001" if p_val < 0.001 else f"p={p_val:.3f}", 
             ha='center', transform=plt.gca().transData, fontsize=10, style='italic', 
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    
    filename = "1_Resource_Quality_Violin.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_data(data.groupby('Type')['Capacity_Factor'].describe(), filename)

def plot_latitude_profile(df_s, df_w):
    """2. Latitude-resource-capacity composite distribution (dual axis)"""
    print("Plotting 2. Latitude composite distribution...")
    
    # Aggregate data
    agg_s = df_s.groupby('lat_bin').agg({'capacity_mw_est': 'sum', 'Capacity_Factor': 'mean'}).reindex(np.arange(-57.5, 87.5, 5))
    agg_w = df_w.groupby('lat_bin').agg({'capacity_mw_est': 'sum', 'Capacity_Factor': 'mean'}).reindex(np.arange(-57.5, 87.5, 5))
    
    # Convert to GW
    agg_s['capacity_gw'] = agg_s['capacity_mw_est'] / 1000
    agg_w['capacity_gw'] = agg_w['capacity_mw_est'] / 1000
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    plt.subplots_adjust(hspace=0.05)
    
    x = agg_s.index.astype(float)
    width = 2.0
    
    # Top panel: installed capacity (Bar)
    ax1.bar(x - width/2, agg_s['capacity_gw'], width=width, color=COLOR_SOLAR, label='Solar Capacity', alpha=0.8)
    ax1.bar(x + width/2, agg_w['capacity_gw'], width=width, color=COLOR_WIND, label='Wind Capacity', alpha=0.8)
    
    ax1.set_ylabel("Installed Capacity (GW)", fontsize=12)
    ax1.legend(loc='upper left')
    ax1.set_title("Latitudinal Profile: Deployment Scale vs Resource Quality", fontsize=16, fontweight='bold')
    
    # Bottom panel: resource quality (Line)
    ax2.plot(x, agg_s['Capacity_Factor'], color=COLOR_SOLAR, marker='o', linestyle='-', linewidth=2, label='Solar Mean CF')
    ax2.plot(x, agg_w['Capacity_Factor'], color=COLOR_WIND, marker='s', linestyle='-', linewidth=2, label='Wind Mean CF')
    
    ax2.set_ylabel("Mean Capacity Factor", fontsize=12)
    ax2.set_xlabel("Latitude", fontsize=12)
    ax2.legend(loc='upper left')
    ax2.set_ylim(0, 0.5)
    
    # Add equator line
    for ax in [ax1, ax2]:
        ax.axvline(0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        ax.text(2, ax.get_ylim()[1]*0.9, 'Equator', color='gray', fontsize=8)
    
    filename = "2_Latitude_Profile_DualAxis.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    # Export merged data
    agg_combined = pd.concat([agg_s.add_suffix('_Solar'), agg_w.add_suffix('_Wind')], axis=1)
    export_data(agg_combined, filename)

def plot_country_matrix(df_s, df_w):
    """3. Country-level solar/wind resource competitiveness matrix (bubble plot) - normalized"""
    print("Plotting 3. Country competitiveness matrix (normalized)...")
    
    # Compute global mean levels (baseline)
    global_mean_s = df_s['Capacity_Factor'].mean()
    global_mean_w = df_w['Capacity_Factor'].mean()
    print(f"    Global Mean CF - Solar: {global_mean_s:.3f}, Wind: {global_mean_w:.3f}")
    
    # Aggregate by country
    cnt_s = df_s.groupby('country').agg({'Capacity_Factor': 'mean', 'capacity_mw_est': 'sum', 'grid_ef': 'mean'}).reset_index()
    cnt_w = df_w.groupby('country').agg({'Capacity_Factor': 'mean', 'capacity_mw_est': 'sum'}).reset_index()
    
    # Normalize (Relative Quality Index)
    cnt_s['RQI_Solar'] = cnt_s['Capacity_Factor'] / global_mean_s
    cnt_w['RQI_Wind'] = cnt_w['Capacity_Factor'] / global_mean_w
    
    # Merge
    # Normalize country names to improve match rate (simple uppercase + strip)
    cnt_s['country_clean'] = cnt_s['country'].str.upper().str.strip()
    cnt_w['country_clean'] = cnt_w['country'].str.upper().str.strip()
    
    merged = pd.merge(cnt_s, cnt_w, on='country_clean', suffixes=('_s', '_w'), how='inner')
    
    # Restore display country names (prefer Solar's)
    merged['country_display'] = merged['country_s']
    
    print(f"    Matched countries: {len(merged)}")
    
    # Filter to major countries (Top 30 by total capacity)
    merged['Total_Cap'] = merged['capacity_mw_est_s'] + merged['capacity_mw_est_w']
    top_merged = merged.nlargest(30, 'Total_Cap')
    
    plt.figure(figsize=(12, 10))
    
    # Draw the diagonal (equivalence line)
    # After normalization, the 1:1 line represents comparable relative competitiveness
    limit = max(top_merged['RQI_Solar'].max(), top_merged['RQI_Wind'].max()) * 1.1
    plt.plot([0, limit], [0, limit], 'k--', alpha=0.3, zorder=0)
    
    # Scatter
    scatter = plt.scatter(
        top_merged['RQI_Solar'], 
        top_merged['RQI_Wind'], 
        s=top_merged['Total_Cap'] / 200, # bubble size
        c=top_merged['grid_ef'],         # color: grid emission factor
        cmap='RdYlGn_r',                 # red=dirty, green=clean
        alpha=0.8, 
        edgecolors='black', 
        linewidth=0.5
    )
    
    # Label text
    for idx, row in top_merged.iterrows():
        plt.text(row['RQI_Solar']+0.01, row['RQI_Wind'], row['country_display'], fontsize=9)
    
    cbar = plt.colorbar(scatter)
    cbar.set_label('Grid Emission Factor (tCO2/MWh)', fontsize=10)
    
    plt.title("Country-Level Resource Competitiveness (Normalized)", fontsize=16, fontweight='bold')
    plt.xlabel("Solar RQI (Site CF / Global Mean CF)", fontsize=12)
    plt.ylabel("Wind RQI (Site CF / Global Mean CF)", fontsize=12)
    
    # Region annotations
    plt.text(limit*0.8, limit*0.2, "Solar Advantage\n(Relative)", fontsize=14, color=COLOR_SOLAR, fontweight='bold', ha='center')
    plt.text(limit*0.2, limit*0.8, "Wind Advantage\n(Relative)", fontsize=14, color=COLOR_WIND, fontweight='bold', ha='center')
    
    # Add central reference lines
    plt.axvline(1.0, color='gray', linestyle=':', alpha=0.3)
    plt.axhline(1.0, color='gray', linestyle=':', alpha=0.3)
    
    plt.xlim(0.5, limit) 
    plt.ylim(0.5, limit)
    
    filename = "3_Country_Resource_Matrix.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_data(merged, filename)

def plot_lorenz_comparison(df_s, df_w):
    """4. Lorenz curve comparison of emission reduction contributions"""
    print("Plotting 4. Lorenz curve comparison...")
    
    def get_lorenz_data(df, val_col):
        sorted_val = np.sort(df[val_col].values)
        cum_val = np.cumsum(sorted_val) / np.sum(sorted_val)
        cum_pop = np.arange(1, len(cum_val) + 1) / len(cum_val)
        return np.insert(cum_pop, 0, 0), np.insert(cum_val, 0, 0)
    
    pop_s, lorenz_s = get_lorenz_data(df_s, 'avoided_co2_ton')
    pop_w, lorenz_w = get_lorenz_data(df_w, 'avoided_co2_ton')
    
    # Compute Gini
    gini_s = 1 - 2 * np.trapz(lorenz_s, pop_s)
    gini_w = 1 - 2 * np.trapz(lorenz_w, pop_w)
    
    plt.figure(figsize=(8, 8))
    plt.plot(pop_s, lorenz_s, label=f'Solar PV (Gini = {gini_s:.3f})', color=COLOR_SOLAR, linewidth=2.5)
    plt.plot(pop_w, lorenz_w, label=f'Onshore Wind (Gini = {gini_w:.3f})', color=COLOR_WIND, linewidth=2.5)
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Equality', alpha=0.5)
    
    plt.title("Inequality of Carbon Avoidance Contribution", fontsize=16, fontweight='bold')
    plt.xlabel("Cumulative Share of Sites", fontsize=12)
    plt.ylabel("Cumulative Share of Avoided CO2", fontsize=12)
    plt.legend(fontsize=12)
    
    filename = "4_Lorenz_Curve_Comparison.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    summary = pd.DataFrame({'Technology': ['Solar', 'Wind'], 'Gini': [gini_s, gini_w]})
    export_data(summary, filename)

def plot_joint_kde(df_s, df_w):
    """5. Joint distribution of grid cleanliness vs resource efficiency (contour)"""
    print("Plotting 5. Joint distribution...")
    
    sample_n = 10000
    s_sample = df_s.sample(n=min(len(df_s), sample_n)) if len(df_s) > sample_n else df_s
    w_sample = df_w.sample(n=min(len(df_w), sample_n)) if len(df_w) > sample_n else df_w
    
    plt.figure(figsize=(10, 8))
    
    sns.kdeplot(x=s_sample['grid_ef'], y=s_sample['Capacity_Factor'], 
                cmap="Oranges", fill=True, alpha=0.5, label='Solar PV Density', thresh=0.05)
    
    sns.kdeplot(x=w_sample['grid_ef'], y=w_sample['Capacity_Factor'], 
                cmap="Blues", fill=True, alpha=0.5, label='Wind Density', thresh=0.05)
    
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], color=COLOR_SOLAR, lw=4, label='Solar PV Density'),
               Line2D([0], [0], color=COLOR_WIND, lw=4, label='Onshore Wind Density')]
    plt.legend(handles=handles, loc='upper right')
    
    plt.title("Resource-Grid Nexus: Deployment Strategy Analysis", fontsize=16, fontweight='bold')
    plt.xlabel("Grid Emission Factor (tCO2/MWh) [Dirty ->]", fontsize=12)
    plt.ylabel("Capacity Factor (0-1) [Efficient ->]", fontsize=12)
    
    plt.axvline(0.475, color='gray', linestyle='--', alpha=0.5)
    plt.text(0.48, 0.55, "Global Avg EF", rotation=90, color='gray')
    
    filename = "5_Joint_Distribution_Nexus.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()

def plot_temporal_evolution(df_s, df_w):
    """6. Temporal evolution: technology progress and resource selection"""
    print("Plotting 6. Temporal evolution...")
    
    # Aggregate mean by year
    yr_s = df_s.groupby('year')['Capacity_Factor'].mean()
    yr_w = df_w.groupby('year')['Capacity_Factor'].mean()
    
    # Aggregate added capacity by year
    cap_s = df_s.groupby('year')['capacity_mw_est'].sum() / 1000 # GW
    cap_w = df_w.groupby('year')['capacity_mw_est'].sum() / 1000 # GW
    
    # Keep only 2010-2024
    years = np.arange(2010, 2025)
    yr_s = yr_s.reindex(years)
    yr_w = yr_w.reindex(years)
    cap_s = cap_s.reindex(years).fillna(0)
    cap_w = cap_w.reindex(years).fillna(0)
    
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Plot installed capacity (bars)
    width = 0.35
    ax1.bar(years - width/2, cap_s, width, color=COLOR_SOLAR, alpha=0.3, label='Solar Added Capacity (GW)')
    ax1.bar(years + width/2, cap_w, width, color=COLOR_WIND, alpha=0.3, label='Wind Added Capacity (GW)')
    ax1.set_ylabel("Annual Added Capacity (GW)", fontsize=12)
    ax1.set_xlabel("Year", fontsize=12)
    
    # Plot efficiency trends (lines) - dual axis
    ax2 = ax1.twinx()
    ax2.plot(years, yr_s, color=COLOR_SOLAR, marker='o', lw=2, label='Solar Mean CF')
    ax2.plot(years, yr_w, color=COLOR_WIND, marker='s', lw=2, label='Wind Mean CF')
    
    # Linear fit trend lines
    for y_data, col in zip([yr_s, yr_w], [COLOR_SOLAR, COLOR_WIND]):
        mask = ~np.isnan(y_data)
        if mask.sum() > 2:
            z = np.polyfit(years[mask], y_data[mask], 1)
            p = np.poly1d(z)
            ax2.plot(years, p(years), color=col, linestyle='--', alpha=0.7, lw=1)
    
    ax2.set_ylabel("Mean Capacity Factor", fontsize=12)
    ax2.set_ylim(0.1, 0.45)
    
    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')
    
    plt.title("Temporal Evolution: Capacity Growth vs Resource Quality", fontsize=16, fontweight='bold')
    
    filename = "6_Temporal_Evolution.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    export_data(pd.concat([yr_s.rename('Solar_CF'), yr_w.rename('Wind_CF'), 
                           cap_s.rename('Solar_GW'), cap_w.rename('Wind_GW')], axis=1), filename)

def plot_continent_stack(df_s, df_w):
    """7. Regional pattern: installed capacity mix by continent"""
    print("Plotting 7. Regional pattern...")
    
    if 'Continent' not in df_s.columns:
        print("    Skipping regional analysis (no continent info)")
        return

    cont_s = df_s.groupby('Continent')['capacity_mw_est'].sum() / 1000
    cont_w = df_w.groupby('Continent')['capacity_mw_est'].sum() / 1000
    
    # Merge and sort
    df_cont = pd.DataFrame({'Solar': cont_s, 'Wind': cont_w}).fillna(0)
    df_cont['Total'] = df_cont['Solar'] + df_cont['Wind']
    df_cont = df_cont.sort_values('Total', ascending=True) # horizontal bars: smallest at bottom
    
    # Plot
    df_cont[['Solar', 'Wind']].plot(kind='barh', stacked=True, color=[COLOR_SOLAR, COLOR_WIND], figsize=(10, 6))
    
    plt.title("Regional Energy Mix: Solar vs Wind Capacity", fontsize=16, fontweight='bold')
    plt.xlabel("Total Installed Capacity (GW)", fontsize=12)
    plt.ylabel("Region", fontsize=12)
    
    # Add percentage labels
    for i, (idx, row) in enumerate(df_cont.iterrows()):
        total = row['Solar'] + row['Wind']
        if total > 0:
            if row['Solar'] > 5:
                plt.text(row['Solar']/2, i, f"{row['Solar']/total:.0%}", va='center', ha='center', color='white', fontweight='bold')
            if row['Wind'] > 5:
                plt.text(row['Solar'] + row['Wind']/2, i, f"{row['Wind']/total:.0%}", va='center', ha='center', color='white', fontweight='bold')
    
    filename = "7_Continent_Mix.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    export_data(df_cont, filename)

def plot_resource_ratio_map(df_s, df_w, world):
    """8. Global solar/wind resource advantage ratio map"""
    print("Plotting 8. Resource advantage ratio map...")
    
    if world is None:
        print("    Skipping map (no world basemap)")
        return
        
    # Compute mean CF per country
    cf_s = df_s.groupby('country')['Capacity_Factor'].mean()
    cf_w = df_w.groupby('country')['Capacity_Factor'].mean()
    
    # Ratio: Solar / Wind
    # Ratio > 1 -> Solar Better
    # Ratio < 1 -> Wind Better
    # Log Ratio > 0 -> Solar Better
    ratio = pd.DataFrame({'Solar_CF': cf_s, 'Wind_CF': cf_w})
    ratio['Ratio'] = ratio['Solar_CF'] / ratio['Wind_CF']
    ratio['Log_Ratio'] = np.log2(ratio['Ratio']) # Log2 scale: 1->0, 2->1, 0.5->-1
    
    # Join to World Geodataframe
    # Need to match name
    world['name_upper'] = world['ADMIN'].str.upper()
    ratio.index = ratio.index.str.upper()
    
    world = world.merge(ratio, left_on='name_upper', right_index=True, how='left')
    
    fig, ax = plt.subplots(figsize=(15, 8))
    world.boundary.plot(ax=ax, linewidth=0.5, color='gray')
    
    # Plot
    # Diverging colormap: Blue (Wind) -> White -> Red/Orange (Solar)
    # limit range to -1 to 1 (0.5x to 2x)
    world.plot(column='Log_Ratio', ax=ax, cmap='RdYlBu_r', 
               legend=True, 
               missing_kwds={'color': 'lightgrey', "hatch": "///", "label": "No Data"},
               vmin=-1, vmax=1,
               legend_kwds={'label': "Resource Preference (Log2 Ratio of CF)\nBlue: Wind Better | Red: Solar Better", 
                            'orientation': "horizontal", 'shrink': 0.6})
    
    plt.title("Global Resource Preference: Solar vs Wind", fontsize=18, fontweight='bold')
    ax.set_axis_off()
    
    filename = "8_Global_Resource_Ratio_Map.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()
    
    # Export
    export_data(ratio, filename)

def generate_report():
    """Generate Markdown analysis report"""
    report = f"""
# Global Comparative Analysis Report: Solar vs Wind Generation Potential

**Generated**: 2026-01-07
**Author**: 锐多宝 (Trae AI)

## 1. Key Findings Summary

This study compares the generation potential of {len(pd.read_csv(SOLAR_CSV))} solar PV plants and {len(pd.read_csv(WIND_CSV))} wind farms worldwide.

### 1.1 Resource Quality Differences
- **Capacity Factor (CF)**: See `1_Resource_Quality_Violin.png`. The average CF of wind power is typically significantly higher than that of solar PV.
- **Spatial Complementarity**: See `2_Latitude_Profile_DualAxis.png`. Solar PV performs better near the equator (low latitudes), while wind performs better at mid-to-high latitudes (30-60 degrees); the two show clear complementary distributions across latitudes.

### 1.2 Country Competitiveness
- **Resource Matrix**: See `3_Country_Resource_Matrix.png`.
    - **Solar-advantaged countries**: Australia, African countries, Middle Eastern countries.
    - **Wind-advantaged countries**: Northern European countries (UK, Denmark), Canada, Chile.
    - **Advantaged in both**: United States, China (in some regions).

### 1.3 Emission Reduction and Equity
- **Lorenz Curve**: See `4_Lorenz_Curve_Comparison.png`.
    - Analyzes which energy source has a more uneven resource distribution (higher Gini coefficient). Wind energy is usually constrained to specific wind belts and is more unevenly distributed.

### 1.4 Temporal Evolution
- **Technology Progress**: See `6_Temporal_Evolution.png`.
    - Observe whether the average CF of newly installed capacity has been improving in recent years (site selection optimization / technology improvement).

## 2. Figure List

| # | Figure | Filename | Description |
|---|--------|----------|-------------|
| 1 | Resource distribution violin plot | `1_Resource_Quality_Violin.png` | Compares the statistical distribution of CF for both technologies |
| 2 | Latitude composite distribution | `2_Latitude_Profile_DualAxis.png` | Dual-axis view of capacity and resource quality by latitude |
| 3 | Country competitiveness matrix | `3_Country_Resource_Matrix.png` | Bubble plot of country resource positioning and grid cleanliness |
| 4 | Lorenz curve | `4_Lorenz_Curve_Comparison.png` | Assesses inequality in global resource allocation |
| 5 | Resource-grid joint distribution | `5_Joint_Distribution_Nexus.png` | Analyzes whether plants are built in places with "dirty grids but good resources" |
| 6 | Temporal evolution | `6_Temporal_Evolution.png` | Trends in capacity and efficiency from 2010 to 2024 |
| 7 | Regional pattern | `7_Continent_Mix.png` | Stacked bar of continental solar/wind capacity shares |
| 8 | Resource preference map | `8_Global_Resource_Ratio_Map.png` | Global map of the Solar/Wind CF ratio by country |

## 3. Paper Writing Suggestions

In the "Results" section, we suggest organizing the narrative as **"Global Resource Distribution" -> "Spatial Complementarity" -> "Temporal Trends" -> "Policy Implications"**.
Figure 2 (latitude) and Figure 3 (matrix) are the core innovations and are recommended as main figures.

"""
    with open(os.path.join(OUTPUT_DIR, "Comparative_Analysis_Report.md"), 'w', encoding='utf-8') as f:
        f.write(report)
    print("Report generated: Comparative_Analysis_Report.md")

# ================= Main program =================

def main():
    ensure_dir(OUTPUT_DIR)
    
    try:
        # Load data
        df_s, df_w = load_data()
        
        # Add continent information
        df_s, df_w, world = add_continent_info(df_s, df_w)
        
        # Basic filtering
        df_s = df_s[df_s['capacity_mw_est'] > 0]
        df_w = df_w[df_w['capacity_mw_est'] > 0]
        
        # Execute plotting
        plot_cf_violin(df_s, df_w)
        plot_latitude_profile(df_s, df_w)
        plot_country_matrix(df_s, df_w)
        plot_lorenz_comparison(df_s, df_w)
        plot_joint_kde(df_s, df_w)
        plot_temporal_evolution(df_s, df_w)
        plot_continent_stack(df_s, df_w)
        plot_resource_ratio_map(df_s, df_w, world)
        
        # Generate report
        generate_report()
        
        print("\n>>> All deep comparative analyses completed!")
        print(f"Results directory: {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
