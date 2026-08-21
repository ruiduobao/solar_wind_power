# -*- coding: utf-8 -*-
"""
Calculate soil carbon loss for solar farm sites (Soil Carbon Loss Calculation)
Author: 锐多宝 (Trae AI)
Date: 2026-01-27

Function:
1. Read the solar land use analysis result (Solar_Analysis_Decoded_Merged.csv) - to obtain land class weights
2. Read the solar slope statistics result (Solar_Slope_Merged.csv) - to compute the disturbance coefficient K_Poly
3. Read the solar farm vector (solarpower.shp) - to extract background soil carbon values
4. Read the global soil carbon density data (Global_Soil_Carbon_Mosaic.tif)
5. Compute the soil carbon loss for each site according to the "spatial denoising", "type-weight re-allocation" and "slope disturbance loss" algorithms in 公式计算2.md.

Input:
- CSV: Solar_Analysis_Decoded_Merged.csv (land class area)
- CSV: Solar_Slope_Merged.csv (slope class counts)
- SHP: solarpower.shp (geometry)
- Raster: Global_Soil_Carbon_Mosaic.tif (soil carbon density, unit assumed to be tC/ha)

Output:
- CSV: Solar_Soil_Loss_Result.csv
"""

import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
import os
from shapely.geometry import mapping

# ================= Configuration section =================

# 1. Input file paths
CSV_LC_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\风电和光伏统计\SOLAR_FROM_2017_2024_LandCover_Summary.csv"
CSV_SLOPE_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\结果数据\计算土壤碳\光伏坡度相关数据\Solar_Slope_Merged.csv"
SHP_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\光伏数据\solarpower_WGS84.shp"
SOIL_RASTER_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\土壤碳\Global_Soil_Carbon_Mosaic.tif"

# 2. Output directory
OUTPUT_DIR_BASE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.1.1光伏土壤碳损失"

# 3. Parameter settings
# The unit of the soil carbon density data needs confirmation. SoilGrids is usually tC/ha (0-30cm). We assume the TIF is already in tC/ha.
# If the TIF is in another unit such as dg/kg, conversion is required here.
# Assumption: TIF values are tC/ha
PIXEL_AREA_HA = 1.0 # Only for rough estimation; actual calculation uses the vector area

# 4. Land class weight table (soil weight W_Soil, from 公式计算.md)
# Corresponding CSV column names: 'pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops'

# FROM-GLC10 Class Definitions
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

WEIGHTS_SOIL = {
    'Trees': 90,
    'Grass': 70,
    'Shrub': 60,
    'Crops': 50,
    'Wetland': 120, 
    'Bare': 0
}

# 5. Slope disturbance coefficients (for K_Poly computation)
# K_L1 (<5°), K_L2 (5-15°), K_L3 (>15°)
# Define the coefficients for the three scenarios
SCENARIO_FACTORS = {
    '乐观': {
        'L1': 0.05, # < 5°: 5%
        'L2': 0.20, # 5-15°: 20%
        'L3': 0.30  # > 15°: 30%
    },
    '标准': {
        'L1': 0.10, # < 5°: 10%
        'L2': 0.40, # 5-15°: 40%
        'L3': 0.60  # > 15°: 60%
    },
    '悲观': {
        'L1': 0.20, # < 5°: 20%
        'L2': 0.80, # 5-15°: 80%
        'L3': 1.00  # > 15°: 100%
    }
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
    
    # Preprocessing: remove invalid geometries
    initial_len = len(shp_gdf)
    shp_gdf = shp_gdf[~shp_gdf.geometry.is_empty & shp_gdf.geometry.notna()]
    filtered_len = len(shp_gdf)
    if initial_len != filtered_len:
        print(f"    [Notice] Removed {initial_len - filtered_len} invalid/empty geometry objects.")
    
    try:
        with rasterio.open(raster_path) as src:
            print(f"    Raster Profile: {src.profile}")
            print(f"    CRS: {src.crs}")
            
            # Ensure SHP and Raster have consistent projections
            if shp_gdf.crs != src.crs:
                print("    Projections differ; reprojecting SHP...")
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
                    out_image, out_transform = mask(src, geom_mapping, crop=True, nodata=-9999) # Assumes nodata is -9999; adjust as needed
                    # Prefer src.nodata if available
                    nodata_val = src.nodata if src.nodata is not None else -9999
                    
                    data = out_image[0]
                    
                    # Filter valid values
                    valid_data = data[(data != nodata_val) & (data >= 0)] # Soil carbon should not be negative
                    
                    if valid_data.size > 0:
                        mean_density = np.mean(valid_data)
                    else:
                        mean_density = 0.0
                        
                    results.append({'fid': fid, 'mean_soil_density_tC_ha': mean_density})
                    
                except Exception as e:
                    # print(f"    [ERROR] FID {fid}: {e}")
                    results.append({'fid': fid, 'mean_soil_density_tC_ha': 0.0})
                
                if count % 2000 == 0:
                    print(f"    Processed {count}/{total}")
                    
    except Exception as e:
        print(f"[ERROR] Failed to open or read the raster file: {e}")
        return pd.DataFrame(columns=['fid', 'mean_soil_density_tC_ha'])
        
    return pd.DataFrame(results)

def calculate_soil_loss(df_merged, scenario_name):
    """
    Execute Stage 2 (Denoising) & Stage 3 (Allocation) & Stage 4 (Loss)
    """
    print(f"Starting soil carbon loss calculation (Scenario: {scenario_name})...")
    
    k_factors = SCENARIO_FACTORS[scenario_name]
    df = df_merged.copy()
    
    # 1. Basic computation
    # Total area (ha)
    if 'total_area_m2' not in df.columns and 'area_m2' in df.columns:
         df['total_area_m2'] = df['area_m2']
         
    df['total_area_ha'] = df['total_area_m2'] / 10000.0
    
    # GIS raw total SUM_Soil_GIS = density * area
    df['SUM_Soil_GIS'] = df['mean_soil_density_tC_ha'] * df['total_area_ha']
    
    # ================= Stage 2: Spatial Denoising =================
    # Ratio_Eco = Sum(Area_Eco) / Total_Area
    # CSV column names: pre_Trees, pre_Grass, pre_Shrub, pre_Crops
    eco_cols = ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops']
    # Note: Wetland may not be in the CSV; add it if present
    if 'pre_Wetland' in df.columns:
        eco_cols.append('pre_Wetland')
        
    # Compute the total ecological land area
    df['Area_Eco_m2'] = df[eco_cols].sum(axis=1)
    
    # Ratio_Eco
    df['Ratio_Eco'] = df['Area_Eco_m2'] / df['total_area_m2']
    df['Ratio_Eco'] = df['Ratio_Eco'].fillna(0).clip(0, 1)
    
    # SUM_Soil_Corrected
    df['SUM_Soil_Corrected'] = df['SUM_Soil_GIS'] * df['Ratio_Eco']
    
    # ================= Stage 3: Categorical Re-allocation =================
    # Score_Soil = Sum(N_Type * W_Soil_Type) -> here area replaces the pixel count N
    
    score = 0
    for col in eco_cols:
        land_type = col.replace('pre_', '')
        weight = WEIGHTS_SOIL.get(land_type, 0)
        score += df[col] * weight
        
    df['Score_Soil'] = score
    
    # Factor_Soil = SUM_Corrected / Score
    df['Factor_Soil'] = df.apply(lambda row: row['SUM_Soil_Corrected'] / row['Score_Soil'] if row['Score_Soil'] > 0 else 0, axis=1)
    
    # Compute the true soil carbon stock for each ecological type (Stock_Soil_Type)
    # Stock = Area * Weight * Factor
    df['Total_Eco_Soil'] = 0.0 # Step A: compute the total soil stock of the ecological area
    
    for col in eco_cols:
        land_type = col.replace('pre_', '')
        weight = WEIGHTS_SOIL.get(land_type, 0)
        
        stock_col = f'Stock_Soil_{land_type}'
        df[stock_col] = df[col] * weight * df['Factor_Soil']
        
        df['Total_Eco_Soil'] += df[stock_col]
        
    # ================= Stage 4: Loss Accounting =================
    # Step B: compute the composite disturbance coefficient K_Poly
    # K_Poly = (N_L1*K1 + N_L2*K2 + N_L3*K3) / N_Total
    # Slope CSV column names: count_slope_lt_5, count_slope_5_15, count_slope_gt_15, total_pixels
    
    # Handle missing slope data (fillna 0)
    slope_cols = ['count_slope_lt_5', 'count_slope_5_15', 'count_slope_gt_15', 'total_pixels']
    for c in slope_cols:
        if c not in df.columns:
            df[c] = 0
    
    # Compute the weighted K
    # Numerator
    numerator = (df['count_slope_lt_5'] * k_factors['L1'] + 
                 df['count_slope_5_15'] * k_factors['L2'] + 
                 df['count_slope_gt_15'] * k_factors['L3'])
    
    # Denominator (total_pixels)
    # Guard against a zero denominator
    df['K_Poly'] = numerator / df['total_pixels']
    df['K_Poly'] = df['K_Poly'].fillna(0) # If there is no slope data, assume no loss? Or take the average? 0 is safer here, or a default of 0.2
    
    # If total_pixels is 0 (slope data matching failed), K_Poly defaults to 0 (no data, no loss)
    
    # Step C: compute the final soil loss
    # Loss_Soil = Total_Eco_Soil * K_Poly
    df['Loss_Soil_tC'] = df['Total_Eco_Soil'] * df['K_Poly']
    
    return df

def main():
    ensure_dir(OUTPUT_DIR_BASE)
    
    print("=== 1. Loading data ===")
    
    # Read the Land Cover CSV (FROM-GLC10 Long Format)
    print(f"Reading LandCover: {CSV_LC_PATH}")
    df_lc_raw = pd.read_csv(CSV_LC_PATH)
    if 'fid' not in df_lc_raw.columns and 'FID' in df_lc_raw.columns:
        df_lc_raw.rename(columns={'FID': 'fid'}, inplace=True)
    
    # Convert to Wide Format
    print("Converting LandCover data format (Long -> Wide)...")
    # Pivot: index='fid', columns='class_name', values='area_sqm'
    df_lc = df_lc_raw.pivot_table(index='fid', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Rename columns to match the downstream logic
    # FROM-GLC Class Names: Forest, Grass, Shrub, Cropland, Wetland, Water, Impervious, Bareland, Snow/Ice, Cloud
    rename_map = {
        'Forest': 'pre_Trees',
        'Grass': 'pre_Grass',
        'Shrub': 'pre_Shrub',
        'Cropland': 'pre_Crops',
        'Wetland': 'pre_Wetland' # If present
    }
    df_lc.rename(columns=rename_map, inplace=True)
    
    # Compute the total area
    # Note: after pivoting, df_lc contains all FROM-GLC classes (including Noise)
    # total_area_m2 = Sum of all columns
    df_lc['total_area_m2'] = df_lc.sum(axis=1)
    
    # Reset the index so that fid becomes a column again
    df_lc.reset_index(inplace=True)
    df_lc['fid'] = df_lc['fid'].astype(int)
    
    # Ensure all required columns exist (in case some classes are entirely absent)
    for col in ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops', 'pre_Wetland']:
        if col not in df_lc.columns:
            df_lc[col] = 0.0

    # Read the Slope CSV
    print(f"Reading Slope: {CSV_SLOPE_PATH}")
    df_slope = pd.read_csv(CSV_SLOPE_PATH)
    df_slope['fid'] = df_slope['fid'].astype(int)
    # Keep only the needed columns
    slope_cols = ['fid', 'avg_slope', 'count_slope_lt_5', 'count_slope_5_15', 'count_slope_gt_15', 'total_pixels']
    df_slope = df_slope[[c for c in slope_cols if c in df_slope.columns]]
    
    # Read the SHP
    print(f"Reading SHP: {SHP_PATH}")
    gdf = gpd.read_file(SHP_PATH)
    if 'fid_1' in gdf.columns:
        gdf = gdf.rename(columns={'fid_1': 'fid'})
    gdf['fid'] = gdf['fid'].astype(int)
    
    # Extract the constructi year information from the SHP
    if 'constructi' in gdf.columns:
        # Create a year mapping table
        year_map = gdf[['fid', 'constructi']].copy()
        # Fill missing values with 2017 (assumption)
        year_map['constructi'] = year_map['constructi'].fillna(2017).astype(int)
        # Correct years before 2017
        year_map.loc[year_map['constructi'] < 2017, 'constructi'] = 2017
    else:
        print("Warning: constructi field not found in SHP; year will default to 2017")
        year_map = gdf[['fid']].copy()
        year_map['constructi'] = 2017
    
    # Merge LC and Slope
    print("Merging tabular data...")
    df_merged = pd.merge(df_lc, df_slope, on='fid', how='inner')
    
    # Attach the year information
    df_merged = pd.merge(df_merged, year_map, on='fid', how='left')
    
    print(f"Records after merge: {len(df_merged)}")
    
    print("=== 2. Extracting background soil carbon values ===")
    df_soil_stats = get_zonal_stats_soil(gdf[['fid', 'geometry']], SOIL_RASTER_PATH)
    df_soil_stats['fid'] = df_soil_stats['fid'].astype(int)
    
    # Merge soil statistics
    df_final_input = pd.merge(df_merged, df_soil_stats, on='fid', how='inner')
    print(f"Records after attaching soil data: {len(df_final_input)}")
    
    print("=== 3. Computing multi-scenario losses ===")
    
    scenarios = ['乐观', '标准', '悲观']
    
    for scenario in scenarios:
        print(f"\n--- Processing scenario: {scenario} ---")
        
        # Determine the output subdirectory
        out_subdir = os.path.join(OUTPUT_DIR_BASE, f"{scenario}场景")
        if scenario == '标准': # Compatible with the old path
             out_subdir = os.path.join(OUTPUT_DIR_BASE, "标准场景")
        ensure_dir(out_subdir)
        
        df_result = calculate_soil_loss(df_final_input, scenario)
        
        # Output
        out_csv = os.path.join(out_subdir, "Solar_Soil_Loss_Result.csv")
        
        # Select output columns
        # Rename constructi to installation_year
        if 'constructi' in df_result.columns:
            df_result.rename(columns={'constructi': 'installation_year'}, inplace=True)
        
        base_cols = ['fid', 'country_iso_a3', 'installation_year', 'total_area_ha']
        soil_cols = [
            'mean_soil_density_tC_ha', 'SUM_Soil_GIS', 
            'Ratio_Eco', 'SUM_Soil_Corrected', 
            'Score_Soil', 'Factor_Soil', 
            'Total_Eco_Soil', 
            'avg_slope', 'K_Poly', 
            'Loss_Soil_tC'
        ]
        # Add the Stock columns of each class
        stock_cols = [c for c in df_result.columns if c.startswith('Stock_Soil_')]
        
        final_cols = base_cols + soil_cols + stock_cols
        # Filter out non-existent columns
        final_cols = [c for c in final_cols if c in df_result.columns]
        
        df_result[final_cols].to_csv(out_csv, index=False)
        
        print(f"Scenario {scenario} calculation complete!")
        print(f"Output file: {out_csv}")
        print(f"Global solar-induced soil carbon total loss: {df_result['Loss_Soil_tC'].sum() / 1e6:.4f} MtC")
    
    print("\n>>> All scenarios processed.")

if __name__ == "__main__":
    main()
