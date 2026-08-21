# -*- coding: utf-8 -*-
"""
Wind soil carbon loss calculation (Wind Soil Carbon Loss Calculation)
Author: 锐多宝 (Trae AI)
Date: 2026-01-27

Functions:
1. Read the wind farm land use analysis result (WIND_FROM_2017_LandCover_Summary.csv)
2. Read the wind farm vector (风机80米缓冲区.shp) - used to extract soil carbon background values and years
3. Read the global soil carbon density data (Global_Soil_Carbon_Mosaic.tif)
4. Calculate the soil carbon loss.
   - Spatial Denoising: remove background noise
   - Categorical Re-allocation: refine carbon stock allocation
   - Loss calculation: use a fixed disturbance coefficient (K_Wind)

Input:
- CSV: WIND_FROM_2017_LandCover_Summary.csv (land type areas)
- SHP: 风机80米缓冲区.shp (geometry, constructi year)
- Raster: Global_Soil_Carbon_Mosaic.tif (soil carbon density, unit tC/ha)

Output:
- CSV: Wind_Soil_Loss_Result.csv
"""

import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
import os
from shapely.geometry import mapping

# ================= Configuration =================

# 1. Input file paths
CSV_LC_PATH_WIND = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\合并结果\WIND_FROM_2017_2024_LandCover_Summary.csv"

# Prefer the file named with WIND
if os.path.exists(CSV_LC_PATH_WIND):
    CSV_LC_PATH = CSV_LC_PATH_WIND
    print(f"Using auto-matched wind data: {CSV_LC_PATH}")
else:
    CSV_LC_PATH = CSV_LC_PATH_USER
    print(f"WIND-prefixed file not found; using user-provided path: {CSV_LC_PATH}")

SHP_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机80米缓冲区.shp"
SOIL_RASTER_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\土壤碳\Global_Soil_Carbon_Mosaic.tif"

# 2. Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.1.2风电土壤碳损失"

# 3. Parameter settings
# Assumption: TIF values are already in tC/ha
PIXEL_AREA_HA = 1.0 

# 4. Land type weight table (soil weight W_Soil)
WEIGHTS_SOIL = {
    'Trees': 90,
    'Grass': 70,
    'Shrub': 60,
    'Crops': 50,
    'Bare': 0
}
FROM_CLASS_MAP = {
    0: "Background",
    10: "Cropland",
    20: "Forest",
    30: "Grass",
    40: "Shrub",
    60: "Water",
    80: "Impervious",
    90: "Bareland",
    100: "Snow/Ice",
    120: "Cloud"
}
# 5. Wind disturbance coefficient (K_Wind)
# Per the user's instruction, slope effects are ignored; directly define the occupation
# coefficient for the three scenarios.
# Optimistic: 0.05 (5%)
# Standard: 0.10 (10%)
# Pessimistic: 0.20 (20%)

SCENARIO_FACTORS = {
    '乐观': 0.05,
    '标准': 0.10,
    '悲观': 0.20
}

# ================= Core functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_zonal_stats_soil(shp_gdf, raster_path):
    """
    Compute the mean soil carbon density of each polygon
    """
    print(f"Reading soil carbon data: {raster_path}")
    
    results = []
    
    # Preprocessing: drop invalid geometries
    initial_len = len(shp_gdf)
    shp_gdf = shp_gdf[~shp_gdf.geometry.is_empty & shp_gdf.geometry.notna()]
    filtered_len = len(shp_gdf)
    if initial_len != filtered_len:
        print(f"    [Info] Removed {initial_len - filtered_len} invalid/empty geometries.")
    
    try:
        with rasterio.open(raster_path) as src:
            print(f"    Raster Profile: {src.profile}")
            
            # Ensure SHP and Raster share the same projection
            if shp_gdf.crs != src.crs:
                print("    CRS mismatch; reprojecting SHP...")
                shp_gdf = shp_gdf.to_crs(src.crs)
            
            total = len(shp_gdf)
            print(f"    Processing {total} polygons (Windowed Reading)...")
            
            count = 0
            for idx, row in shp_gdf.iterrows():
                count += 1
                fid = row['fid']
                
                try:
                    geom = row['geometry']
                    
                    if geom is None or geom.is_empty:
                        results.append({'fid': fid, 'mean_soil_density_tC_ha': 0.0})
                        continue

                    geom_mapping = [mapping(geom)]
                    
                    # Mask extraction
                    # Note: wind turbine buffers can be very small; if the pixels are too large,
                    # values may not be extracted. all_touched=True ensures small polygons still get values
                    out_image, out_transform = mask(src, geom_mapping, crop=True, nodata=-9999, all_touched=True)
                    
                    nodata_val = src.nodata if src.nodata is not None else -9999
                    data = out_image[0]
                    
                    valid_data = data[(data != nodata_val) & (data >= 0)]
                    
                    if valid_data.size > 0:
                        mean_density = np.mean(valid_data)
                    else:
                        mean_density = 0.0
                        
                    results.append({'fid': fid, 'mean_soil_density_tC_ha': mean_density})
                    
                except Exception as e:
                    results.append({'fid': fid, 'mean_soil_density_tC_ha': 0.0})
                
                if count % 5000 == 0:
                    print(f"    Processed {count}/{total}")
                    
    except Exception as e:
        print(f"[ERROR] Failed to open or read the raster file: {e}")
        return pd.DataFrame(columns=['fid', 'mean_soil_density_tC_ha'])
        
    return pd.DataFrame(results)

def calculate_soil_loss(df_merged, scenario_name):
    """
    Execute Stage 2 (denoising) & Stage 3 (allocation) & Stage 4 (loss)
    """
    print(f"Running soil carbon loss calculation (scenario: {scenario_name})...")
    
    # Get the disturbance coefficient for the current scenario
    k_wind = SCENARIO_FACTORS.get(scenario_name, 0.10)
    
    df = df_merged.copy()
    
    # 1. Basic calculations
    # Total area (ha)
    if 'total_area_m2' not in df.columns and 'area_m2' in df.columns:
         df['total_area_m2'] = df['area_m2']
         
    df['total_area_ha'] = df['total_area_m2'] / 10000.0
    
    # GIS raw total SUM_Soil_GIS = density * area
    df['SUM_Soil_GIS'] = df['mean_soil_density_tC_ha'] * df['total_area_ha']
    
    # ================= Stage 2: Spatial Denoising =================
    eco_cols = ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops']
    # Removed Wetland check as per user instruction
        
    # Compute total ecological land area
    df['Area_Eco_m2'] = df[eco_cols].sum(axis=1)
    
    # Ratio_Eco
    df['Ratio_Eco'] = df['Area_Eco_m2'] / df['total_area_m2']
    df['Ratio_Eco'] = df['Ratio_Eco'].fillna(0).clip(0, 1)
    
    # SUM_Soil_Corrected
    df['SUM_Soil_Corrected'] = df['SUM_Soil_GIS'] * df['Ratio_Eco']
    
    # ================= Stage 3: Categorical Re-allocation =================
    score = 0
    for col in eco_cols:
        land_type = col.replace('pre_', '')
        weight = WEIGHTS_SOIL.get(land_type, 0)
        score += df[col] * weight
        
    df['Score_Soil'] = score
    
    # Factor_Soil
    df['Factor_Soil'] = df.apply(lambda row: row['SUM_Soil_Corrected'] / row['Score_Soil'] if row['Score_Soil'] > 0 else 0, axis=1)
    
    # Compute the true soil carbon stock of each ecological type
    df['Total_Eco_Soil'] = 0.0
    
    for col in eco_cols:
        land_type = col.replace('pre_', '')
        weight = WEIGHTS_SOIL.get(land_type, 0)
        
        stock_col = f'Stock_Soil_{land_type}'
        df[stock_col] = df[col] * weight * df['Factor_Soil']
        
        df['Total_Eco_Soil'] += df[stock_col]
        
    # ================= Stage 4: Loss Accounting =================
    # Step B: disturbance coefficient
    # Use the scenario coefficient
    df['K_Wind'] = k_wind
    
    # Step C: compute the final soil loss
    df['Loss_Soil_tC'] = df['Total_Eco_Soil'] * df['K_Wind']
    
    return df

def main():
    ensure_dir(OUTPUT_DIR)
    
    print("=== 1. Loading data ===")
    
    # Read the Land Cover CSV
    print(f"Reading LandCover: {CSV_LC_PATH}")
    df_lc_raw = pd.read_csv(CSV_LC_PATH)
    if 'fid' not in df_lc_raw.columns and 'FID' in df_lc_raw.columns:
        df_lc_raw.rename(columns={'FID': 'fid'}, inplace=True)
    
    # Convert to Wide Format
    print("Converting LandCover data format (Long -> Wide)...")
    df_lc = df_lc_raw.pivot_table(index='fid', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Rename columns
    rename_map = {
        'Forest': 'pre_Trees',
        'Grass': 'pre_Grass',
        'Shrub': 'pre_Shrub',
        'Cropland': 'pre_Crops'
    }
    df_lc.rename(columns=rename_map, inplace=True)
    
    # Compute total area
    df_lc['total_area_m2'] = df_lc.sum(axis=1)
    
    # Reset index
    df_lc.reset_index(inplace=True)
    df_lc['fid'] = df_lc['fid'].astype(int)
    
    # Ensure columns exist
    for col in ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops']:
        if col not in df_lc.columns:
            df_lc[col] = 0.0

    # Read the SHP
    print(f"Reading SHP: {SHP_PATH}")
    try:
        gdf = gpd.read_file(SHP_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to read SHP: {e}")
        return

    if 'fid_1' in gdf.columns:
        gdf = gdf.rename(columns={'fid_1': 'fid'})
    
    # Check the fid column
    if 'fid' not in gdf.columns:
        print("[ERROR] The SHP is missing the 'fid' column; cannot merge. Trying to use the index as FID.")
        gdf['fid'] = gdf.index
    
    gdf['fid'] = gdf['fid'].astype(int)
    
    # Extract the constructi year info from the SHP
    if 'constructi' in gdf.columns:
        year_map = gdf[['fid', 'constructi']].copy()
        year_map['constructi'] = year_map['constructi'].fillna(2017).astype(int)
        year_map.loc[year_map['constructi'] < 2017, 'constructi'] = 2017
    else:
        print("Warning: constructi field not found in SHP; the year will default to 2017")
        year_map = gdf[['fid']].copy()
        year_map['constructi'] = 2017
    
    # Merge LC and Year
    print("Merging tabular data...")
    df_merged = pd.merge(df_lc, year_map, on='fid', how='inner') # only compute records that have both year and LC
    
    print(f"Records after merge: {len(df_merged)}")
    
    print("=== 2. Extracting soil carbon background values ===")
    df_soil_stats = get_zonal_stats_soil(gdf[['fid', 'geometry']], SOIL_RASTER_PATH)
    df_soil_stats['fid'] = df_soil_stats['fid'].astype(int)
    
    # Merge soil statistics
    df_final_input = pd.merge(df_merged, df_soil_stats, on='fid', how='inner')
    print(f"Records after joining soil data: {len(df_final_input)}")
    
    print("=== 3. Computing multi-scenario losses ===")
    
    scenarios = ['乐观', '标准', '悲观']
    
    for scenario in scenarios:
        print(f"\n--- Processing scenario: {scenario} ---")
        
        # Determine the output subdirectory
        out_subdir = os.path.join(OUTPUT_DIR, f"{scenario}场景")
        ensure_dir(out_subdir)
        
        df_result = calculate_soil_loss(df_final_input, scenario)
        
        # Output
        out_csv = os.path.join(out_subdir, "Wind_Soil_Loss_Result.csv")
        
        # Rename the year column
        if 'constructi' in df_result.columns:
            df_result.rename(columns={'constructi': 'installation_year'}, inplace=True)
        
        base_cols = ['fid', 'installation_year', 'total_area_ha']
        soil_cols = [
            'mean_soil_density_tC_ha', 'SUM_Soil_GIS', 
            'Ratio_Eco', 'SUM_Soil_Corrected', 
            'Score_Soil', 'Factor_Soil', 
            'Total_Eco_Soil', 
            'K_Wind', 
            'Loss_Soil_tC'
        ]
        stock_cols = [c for c in df_result.columns if c.startswith('Stock_Soil_')]
        
        final_cols = base_cols + soil_cols + stock_cols
        # Filter
        final_cols = [c for c in final_cols if c in df_result.columns]
        
        df_result[final_cols].to_csv(out_csv, index=False)
        
        print(f"Scenario {scenario} calculation complete!")
        print(f"Output file: {out_csv}")
        print(f"Global wind soil carbon loss: {df_result['Loss_Soil_tC'].sum() / 1e6:.4f} MtC")
    
    print("\n>>> All scenarios processed.")

if __name__ == "__main__":
    main()
