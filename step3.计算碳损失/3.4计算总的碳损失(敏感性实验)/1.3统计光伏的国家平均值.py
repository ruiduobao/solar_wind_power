# -*- coding: utf-8 -*-
"""
1.3 统计光伏的国家平均值.py
Function: compute the LULC carbon loss (soil + biomass) and manufacturing carbon emissions of solar
PV by country under three scenarios, and calculate the percentages.
Input: Solar_Total_Carbon_Debt_Result.csv under each scenario
Output: Solar_Country_Stats.csv under each scenario
Author: 锐多宝
Date: 2026-02-07
"""

import pandas as pd
import os
import sys
import geopandas as gpd
import matplotlib.pyplot as plt

# Set font to support CJK display
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']  # prefer SimHei, fall back to Arial
plt.rcParams['axes.unicode_minus'] = False  # fix negative sign display

# Set working directory
# Assume the script is located in: ...\代码\step3.计算碳损失\3.4计算总的碳损失(敏感性实验)\
# Need to walk back up to find the figure folder
# User path: Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.4.1光伏碳债务合并损失\
base_output_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.4.1光伏碳债务合并损失"
WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\行政区划\natural-earth-vector-master\10m_cultural\ne_10m_admin_0_countries.shp"

# Define the scenario list
scenarios = ["标准场景", "乐观场景", "悲观场景"]

# Country name correction dict (CSV Name -> Shapefile ADMIN Name)
# For ne_10m_admin_0_countries.shp (10m resolution usually uses full names)
NAME_CORRECTION = {
    "United States": "United States of America",
    "Tanzania": "United Republic of Tanzania",
    "Congo, Dem. Rep.": "Democratic Republic of the Congo",
    "Congo, Rep.": "Republic of the Congo",
    "Serbia": "Republic of Serbia",
    "Bahamas": "The Bahamas",
    "México": "Mexico",
    "Swaziland": "eSwatini",
    "Czech Republic": "Czechia",
    "Macedonia": "North Macedonia",
    "Timor-Leste": "East Timor",
    # The mappings below apply to 110m resolution but are not needed at 10m (10m uses full names)
    # "Bosnia and Herzegovina": "Bosnia and Herz.",
    # "Dominican Republic": "Dominican Rep.",
    # "Central African Republic": "Central African Rep.",
    # "South Sudan": "S. Sudan",
    # "Equatorial Guinea": "Eq. Guinea",
    # "Solomon Islands": "Solomon Is."
}

def process_scenario(scenario_name):
    """
    Process the data of a single scenario
    """
    print(f"Processing scenario: {scenario_name}...")
    
    # Build the input file path
    input_dir = os.path.join(base_output_dir, scenario_name)
    input_file = os.path.join(input_dir, "Solar_Total_Carbon_Debt_Result.csv")
    
    if not os.path.exists(input_file):
        print(f"Warning: File does not exist {input_file}")
        return

    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Check whether the required columns exist
        required_cols = [
            'country_final', 'Loss_Bio_tC', 'Loss_Soil_tC', 
            'Loss_Mfg_tCO2', 'Loss_Bio_tCO2', 'Loss_Soil_tCO2', 
            'Total_Debt_tCO2'
        ]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Error: Missing required columns {missing_cols}")
            return

        # Group by country and sum
        # Use groupby and agg for aggregation
        agg_dict = {
            'Loss_Bio_tC': 'sum',
            'Loss_Soil_tC': 'sum',
            'Loss_Mfg_tCO2': 'sum',
            'Loss_Bio_tCO2': 'sum',
            'Loss_Soil_tCO2': 'sum',
            'Total_Debt_tCO2': 'sum'
        }
        
        # Group by country_final for statistics
        country_stats = df.groupby('country_final').agg(agg_dict).reset_index()
        
        # Compute total LULC carbon emissions (Bio + Soil)
        country_stats['LULC_Total_tCO2'] = country_stats['Loss_Bio_tCO2'] + country_stats['Loss_Soil_tCO2']
        
        # Compute percentages
        # Avoid division by zero
        country_stats['Total_Debt_tCO2'] = country_stats['Total_Debt_tCO2'].replace(0, 1e-9) # avoid zero denominator; a zero total debt is rare and meaningless
        
        country_stats['LULC_Pct'] = (country_stats['LULC_Total_tCO2'] / country_stats['Total_Debt_tCO2']) * 100
        country_stats['Mfg_Pct'] = (country_stats['Loss_Mfg_tCO2'] / country_stats['Total_Debt_tCO2']) * 100
        
        # New: compute the soil and biomass loss percentages
        country_stats['Soil_Pct'] = (country_stats['Loss_Soil_tCO2'] / country_stats['Total_Debt_tCO2']) * 100
        country_stats['Bio_Pct'] = (country_stats['Loss_Bio_tCO2'] / country_stats['Total_Debt_tCO2']) * 100
        
        # Format percentage columns to 2 decimals (optional; CSV usually keeps full precision)
        # Rounding would make the table prettier, but keep precision for later analysis
        
        # Sort by Total_Debt_tCO2 in descending order
        country_stats = country_stats.sort_values(by='Total_Debt_tCO2', ascending=False)
        
        # Rename columns for clarity (optional)
        # Keep the existing column naming style and add descriptions
        
        # ---------------------------------------------------------
        # Try to match ISO codes and optimize country name matching
        # ---------------------------------------------------------
        country_stats['ISO_A3'] = None  # initialize the ISO code column
        
        if os.path.exists(WORLD_SHP):
            try:
                gdf = gpd.read_file(WORLD_SHP)
                
                # 1. Apply name corrections
                # Create a temporary column for matching, keep the original country_final
                country_stats['match_name'] = country_stats['country_final'].replace(NAME_CORRECTION)
                
                # 2. Get ISO codes from the Shapefile
                # Assume the Shapefile has ADMIN and ISO_A3 columns
                if 'ADMIN' in gdf.columns and 'ISO_A3' in gdf.columns:
                    # Create a name -> iso mapping
                    name_to_iso = dict(zip(gdf['ADMIN'], gdf['ISO_A3']))
                    country_stats['ISO_A3'] = country_stats['match_name'].map(name_to_iso)
                    
                    # Print match results
                    matched_iso = country_stats['ISO_A3'].notna().sum()
                    print(f"ISO code match rate: {matched_iso}/{len(country_stats)}")
                    
                    # Print unmatched countries
                    unmatched = country_stats[country_stats['ISO_A3'].isna()]['country_final'].tolist()
                    if unmatched:
                        print(f"Countries without matching ISO code ({len(unmatched)}; mostly small island nations or name differences):")
                        print(unmatched[:20]) # print only the first 20
                        if len(unmatched) > 20:
                            print("...")
                
            except Exception as e:
                print(f"Error while matching ISO codes: {str(e)}")
        
        # Output file path
        output_file = os.path.join(input_dir, "Solar_Country_Stats.csv")
        
        # Reorder columns, placing new metrics in appropriate positions
        cols_order = [
            'country_final', 'ISO_A3', # add ISO_A3
            'Total_Debt_tCO2', 'Loss_Mfg_tCO2', 'Mfg_Pct',
            'LULC_Total_tCO2', 'LULC_Pct',
            'Loss_Soil_tCO2', 'Soil_Pct',
            'Loss_Bio_tCO2', 'Bio_Pct',
            'Loss_Bio_tC', 'Loss_Soil_tC' # raw carbon amounts last
        ]
        # Ensure all columns exist in the DataFrame
        cols_to_save = [c for c in cols_order if c in country_stats.columns]
        country_stats_to_save = country_stats[cols_to_save]
        
        # Save as CSV
        country_stats_to_save.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Statistics saved successfully to: {output_file}")
        
        # Print a preview of the first rows
        print("Result preview (Top 5):")
        print(country_stats_to_save[['country_final', 'ISO_A3', 'LULC_Pct', 'Soil_Pct', 'Bio_Pct']].head())
        print("-" * 50)

        # ---------------------------------------------------------
        # Draw maps (loop over multiple metrics)
        # ---------------------------------------------------------
        if os.path.exists(WORLD_SHP):
            try:
                # Note: gdf was read above, but check here for logical independence
                if 'gdf' not in locals():
                     gdf = gpd.read_file(WORLD_SHP)
                
                # Try to merge data
                # Merge using match_name and ADMIN
                merged = gdf.merge(country_stats, left_on='ADMIN', right_on='match_name', how='left')
                
                # Define the metrics to plot: (field name, legend title, output filename)
                maps_to_plot = [
                    ('LULC_Pct', "LULC Carbon Debt Percentage (%)", "Solar_LULC_Pct_Map.png"),
                    ('Soil_Pct', "Soil Carbon Debt Percentage (%)", "Solar_Soil_Pct_Map.png"),
                    ('Bio_Pct', "Biomass Carbon Debt Percentage (%)", "Solar_Bio_Pct_Map.png"),
                    ('Loss_Soil_tCO2', "Soil Carbon Debt (tCO2)", "Solar_Soil_Debt_Map.png"),
                    ('Loss_Bio_tCO2', "Biomass Carbon Debt (tCO2)", "Solar_Bio_Debt_Map.png")
                ]
                
                print(f"Plotting maps ({len(maps_to_plot)} figures)...")
                
                for col, legend_label, filename in maps_to_plot:
                    try:
                        # Check whether the data is entirely empty
                        if merged[col].isna().all():
                            print(f"Skipping map for {col} because there is no data.")
                            continue
                            
                        fig, ax = plt.subplots(1, 1, figsize=(15, 8))
                        
                        # LogNorm might be better for absolute values, but keep linear here or handle simply
                        # For absolute values with large ranges, consider noting it in the title
                        
                        merged.plot(column=col, ax=ax, legend=True,
                                    legend_kwds={'label': legend_label, 'orientation': "horizontal", 'shrink': 0.6},
                                    cmap='YlOrRd', missing_kwds={'color': 'lightgrey'})
                        
                        ax.set_title(f"Solar {col} by Country ({scenario_name})", fontsize=16)
                        ax.set_axis_off()
                        
                        map_output = os.path.join(input_dir, filename)
                        plt.savefig(map_output, dpi=300, bbox_inches='tight')
                        plt.close()
                        print(f"  -> Saved: {filename}")
                        
                    except Exception as sub_e:
                        print(f"  -> Failed to plot {col}: {str(sub_e)}")

            except Exception as e:
                print(f"Overall error while plotting maps: {str(e)}")
        else:
            print(f"Warning: Map file not found {WORLD_SHP}; skipping map plotting.")

    except Exception as e:
        print(f"Error while processing scenario {scenario_name}: {str(e)}")

def main():
    print("Starting to aggregate solar PV carbon debt by country for each scenario...")
    for scenario in scenarios:
        process_scenario(scenario)
    print("All scenarios processed.")

if __name__ == "__main__":
    main()
