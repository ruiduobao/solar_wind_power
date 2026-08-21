# -*- coding: utf-8 -*-
"""
Script name: 2.统计风机和光伏每一年的累计个数.py
Description: 
    1. Read the solar and wind power Shapefile data.
    2. Compute the yearly newly added amount based on the 'constructi' field (year).
    3. Solar statistics: cumulative area (km²).
    4. Wind statistics: cumulative count.
    5. Plot a dual-axis bar chart: solar area (left axis) vs wind count (right axis).
    6. [New] Plot the 2018-2024 growth rate line chart.
    7. Use the Times New Roman font and specified colors.
Author: 锐多宝
Date: 2026-02-02
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Configure fonts
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.unicode_minus'] = False

def main():
    # ================= Path configuration =================
    base_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据"
    solar_path = os.path.join(base_dir, "solarpower.shp")
    wind_path = os.path.join(base_dir, "windpower.shp")
    
    # Output directory
    output_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure2_全球光伏风电土地利用\子图"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_csv = os.path.join(output_dir, "Yearly_Cumulative_Stats.csv")
    output_csv_growth = os.path.join(output_dir, "Yearly_Growth_Rate_2018_2024.csv")
    output_img_cum = os.path.join(output_dir, "Yearly_Cumulative_Trend.png")
    output_img_growth = os.path.join(output_dir, "Yearly_Growth_Rate_2018_2024.png")

    # Specified colors
    color_solar = '#FF00C5' 
    color_wind = '#21854E'

    # ================= 1. Read data =================
    print("Reading solar data...")
    try:
        gdf_solar = gpd.read_file(solar_path)
    except Exception as e:
        print(f"Failed to read solar data: {e}")
        return

    print("Reading wind data...")
    try:
        gdf_wind = gpd.read_file(wind_path)
    except Exception as e:
        print(f"Failed to read wind data: {e}")
        return

    # ================= 2. Data processing =================
    print("Computing yearly statistics...")
    
    # --- Process solar (statistics on area) ---
    def process_solar(gdf):
        # Find the year column
        year_col = None
        for col in gdf.columns:
            if col.lower().startswith('construct'):
                year_col = col
                break
        if year_col is None:
            print("Warning: no year field found in the solar data!")
            return pd.DataFrame()
            
        # Find the area column
        area_col = None
        for col in gdf.columns:
            if col.lower() == 'area':
                area_col = col
                break
        
        # Process the year
        gdf['year'] = pd.to_numeric(gdf[year_col], errors='coerce')
        gdf = gdf.dropna(subset=['year'])
        gdf = gdf[(gdf['year'] > 1900) & (gdf['year'] <= 2026)]
        gdf['year'] = gdf['year'].astype(int)
        
        # Process the area
        if area_col:
            gdf['area_km2'] = pd.to_numeric(gdf[area_col], errors='coerce').fillna(0) / 1e6
        else:
            print("Warning: no 'area' field found in the solar data, the area cannot be computed; the default area is 0")
            gdf['area_km2'] = 0
            
        # Compute the yearly newly added area
        yearly_stats = gdf.groupby('year')['area_km2'].sum().reset_index()
        yearly_stats = yearly_stats.sort_values('year')
        
        # Compute the cumulative area
        yearly_stats['cumulative_area_km2'] = yearly_stats['area_km2'].cumsum()
        return yearly_stats

    # --- Process wind (statistics on count) ---
    def process_wind(gdf):
        year_col = None
        for col in gdf.columns:
            if col.lower().startswith('construct'):
                year_col = col
                break
        if year_col is None:
            print("Warning: no year field found in the wind data!")
            return pd.DataFrame()
            
        gdf['year'] = pd.to_numeric(gdf[year_col], errors='coerce')
        gdf = gdf.dropna(subset=['year'])
        gdf = gdf[(gdf['year'] > 1900) & (gdf['year'] <= 2026)]
        gdf['year'] = gdf['year'].astype(int)
        
        # Compute the yearly count
        yearly_stats = gdf.groupby('year').size().reset_index(name='count')
        yearly_stats = yearly_stats.sort_values('year')
        
        # Compute the cumulative count
        yearly_stats['cumulative_count'] = yearly_stats['count'].cumsum()
        return yearly_stats

    df_solar = process_solar(gdf_solar)
    df_wind = process_wind(gdf_wind)
    
    if df_solar.empty and df_wind.empty:
        print("No valid data, cannot plot.")
        return

    # ================= 3. Merge the statistics tables =================
    min_year = min(df_solar['year'].min() if not df_solar.empty else 9999, 
                   df_wind['year'].min() if not df_wind.empty else 9999)
    max_year = max(df_solar['year'].max() if not df_solar.empty else 0, 
                   df_wind['year'].max() if not df_wind.empty else 0)
    
    all_years = pd.DataFrame({'year': range(min_year, max_year + 1)})
    
    # Merge solar
    final_df = all_years.merge(df_solar[['year', 'area_km2', 'cumulative_area_km2']], on='year', how='left')
    final_df.rename(columns={'area_km2': 'solar_new_area_km2', 'cumulative_area_km2': 'solar_cumulative_area_km2'}, inplace=True)
    
    # Merge wind
    final_df = final_df.merge(df_wind[['year', 'count', 'cumulative_count']], on='year', how='left')
    final_df.rename(columns={'count': 'wind_new_count', 'cumulative_count': 'wind_cumulative_count'}, inplace=True)
    
    # Fill
    final_df['solar_new_area_km2'] = final_df['solar_new_area_km2'].fillna(0)
    final_df['wind_new_count'] = final_df['wind_new_count'].fillna(0)
    
    final_df['solar_cumulative_area_km2'] = final_df['solar_cumulative_area_km2'].ffill().fillna(0)
    final_df['wind_cumulative_count'] = final_df['wind_cumulative_count'].ffill().fillna(0)
    
    # Save CSV
    final_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Statistics table saved: {output_csv}")

    # ================= 4. Plot 1: cumulative count/area trend chart =================
    print("Plotting the cumulative trend chart...")
    
    fig1, ax1 = plt.subplots(figsize=(12, 6), dpi=300)
    
    years = final_df['year']
    bar_width = 0.4
    
    # Left axis: solar cumulative area
    p1 = ax1.bar(years - bar_width/2, final_df['solar_cumulative_area_km2'], width=bar_width, color=color_solar, label='Solar Cumulative Area (km²)', alpha=0.9)
    
    ax1.set_xlabel('Year', fontsize=12, fontname='Times New Roman')
    ax1.set_ylabel('Solar Cumulative Area (km²)', color=color_solar, fontsize=12, fontname='Times New Roman')
    ax1.tick_params(axis='y', labelcolor=color_solar)
    
    # Right axis: wind cumulative count
    ax2 = ax1.twinx()
    p2 = ax2.bar(years + bar_width/2, final_df['wind_cumulative_count'], width=bar_width, color=color_wind, label='Wind Cumulative Count', alpha=0.9)
    
    ax2.set_ylabel('Wind Cumulative Count', color=color_wind, fontsize=12, fontname='Times New Roman')
    ax2.tick_params(axis='y', labelcolor=color_wind)
    
    ax1.set_title('Global Cumulative Solar Area and Wind Power Plants Count', fontsize=14, fontname='Times New Roman')
    
    # Fonts
    for ax in [ax1, ax2]:
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontname('Times New Roman')
            
    if len(years) > 20:
        ax1.set_xticks(years[::5])
    else:
        ax1.set_xticks(years)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', prop={'family': 'Times New Roman', 'size': 10})

    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_img_cum)
    plt.close(fig1)
    print(f"Chart saved: {output_img_cum}")

    # ================= 5. [New] Plot 2: 2018-2024 growth percentage =================
    print("Plotting the 2018-2024 growth rate chart...")
    
    # Filter the 2018-2024 data
    df_growth = final_df[(final_df['year'] >= 2018) & (final_df['year'] <= 2024)].copy()
    
    # Compute the annual growth rate: (new in this year / cumulative of last year) * 100%
    # Note: the base here is the cumulative value of last year.
    # Or the growth rate is usually defined as: (cumulative of this year - cumulative of last year) / cumulative of last year = new / cumulative of last year
    
    # Get the cumulative value of the previous year
    # To compute the 2018 growth rate, we need the 2017 cumulative value
    # So the data needs to be taken from the original df
    years_needed = range(2017, 2025) # 2017-2024
    df_calc = final_df[final_df['year'].isin(years_needed)].copy().set_index('year')
    
    growth_data = []
    for year in range(2018, 2025):
        if year not in df_calc.index or (year - 1) not in df_calc.index:
            continue
            
        prev_solar_cum = df_calc.loc[year-1, 'solar_cumulative_area_km2']
        curr_solar_cum = df_calc.loc[year, 'solar_cumulative_area_km2']
        
        prev_wind_cum = df_calc.loc[year-1, 'wind_cumulative_count']
        curr_wind_cum = df_calc.loc[year, 'wind_cumulative_count']
        
        # Compute the growth rate
        if prev_solar_cum > 0:
            solar_growth = (curr_solar_cum - prev_solar_cum) / prev_solar_cum * 100
        else:
            solar_growth = 0
            
        if prev_wind_cum > 0:
            wind_growth = (curr_wind_cum - prev_wind_cum) / prev_wind_cum * 100
        else:
            wind_growth = 0
            
        growth_data.append({
            'year': year,
            'solar_growth': solar_growth,
            'wind_growth': wind_growth
        })
    
    df_growth_plot = pd.DataFrame(growth_data)
    
    if df_growth_plot.empty:
        print("Warning: unable to compute the 2018-2024 growth rate (possibly missing data).")
        return

    # Save the growth rate CSV
    df_growth_plot.to_csv(output_csv_growth, index=False, encoding='utf-8-sig')
    print(f"Growth rate statistics table saved: {output_csv_growth}")

    # Plot
    # 3. The length and height of the figure are 1:2 (width 5, height 10)
    fig2, ax = plt.subplots(figsize=(5, 10), dpi=600)
    
    # Draw the lines
    # Fewer markers -> use a simple marker 'o', or none, or only at key points
    # Larger font -> increase fontsize
    
    # Solar line
    ax.plot(df_growth_plot['year'], df_growth_plot['solar_growth'], 
            color=color_solar, linewidth=3, marker='o', markersize=8, label='Solar Area Growth (%)')
    
    # Wind line
    ax.plot(df_growth_plot['year'], df_growth_plot['wind_growth'], 
            color=color_wind, linewidth=3, marker='s', markersize=8, label='Wind Count Growth (%)')
    
    # Set styles
    ax.set_xlabel('Year', fontsize=26, fontname='Times New Roman')
    ax.set_ylabel('Annual Growth Rate (%)', fontsize=26, fontname='Times New Roman')
    # ax.set_title('Annual Growth Rate of Solar and Wind (2018-2024)', fontsize=18, fontname='Times New Roman', pad=20)
    
    # Tick settings
    ax.set_xticks(df_growth_plot['year'])
    
    # 2. Increase the interval of the vertical axis (reduce the number of ticks)
    import matplotlib.ticker as ticker
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
    
    ax.tick_params(axis='y', which='major', labelsize=26)
    ax.tick_params(axis='x', which='major', labelsize=23, rotation=45)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname('Times New Roman')
        
    # 1. Remove the legend
    # ax.legend(prop={'family': 'Times New Roman', 'size': 14}, loc='upper right', frameon=False)
    
    # 5. Remove the grid
    # ax.grid(axis='y', linestyle='--', alpha=0.3)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add value labels (optional: if "fewer markers" means less cluttered information, they can be omitted; if it means fewer markers, already handled)
    # For clarity, the values are still added
    # for i, row in df_growth_plot.iterrows():
    #     ax.annotate(f"{row['solar_growth']:.1f}%", (row['year'], row['solar_growth']), 
    #                 textcoords="offset points", xytext=(0, 10), ha='center', 
    #                 color=color_solar, fontsize=12, fontname='Times New Roman')
    #     ax.annotate(f"{row['wind_growth']:.1f}%", (row['year'], row['wind_growth']), 
    #                 textcoords="offset points", xytext=(0, -20), ha='center', 
    #                 color=color_wind, fontsize=12, fontname='Times New Roman')

    plt.tight_layout()
    # 4. The output image should be transparent
    plt.savefig(output_img_growth, transparent=True)
    plt.close(fig2)
    print(f"Growth rate chart saved: {output_img_growth}")

if __name__ == "__main__":
    main()
