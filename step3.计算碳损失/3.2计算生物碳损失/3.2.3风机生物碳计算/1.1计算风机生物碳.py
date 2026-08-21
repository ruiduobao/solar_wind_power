# -*- coding: utf-8 -*-
"""
Compute wind farm biomass carbon loss (Wind Biomass Carbon Loss Calculation)
Author: 锐多宝 (Trae AI)
Date: 2026-01-27

Functions:
1. Read the wind power land use analysis result (WIND_FROM_2017_LandCover_Summary.csv)
2. Read the wind farm vector (风机80米缓冲区.shp) - used to extract the biomass background value and year
3. Read the global biomass carbon density data (ESA CCI Biomass)
4. Compute the biomass carbon loss.
   - Spatial Denoising: remove background noise
   - Categorical Re-allocation: refine carbon stock allocation
   - Loss calculation: use a fixed disturbance coefficient (K_Wind = 0.1)

Inputs:
- CSV: WIND_FROM_2017_LandCover_Summary.csv (land class areas)
- SHP: 风机80米缓冲区.shp (geometry, constructi year)
- Raster: ESACCI_Biomass_2017_100m.tif (biomass density, Mg/ha)

Outputs:
- CSV: Wind_Biomass_Loss_Result.csv
"""

import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
import os
from shapely.geometry import mapping

# ================= Configuration area =================

# 1. Input file paths
CSV_LC_PATH_WIND = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\合并结果\WIND_FROM_2017_2024_LandCover_Summary.csv"

# Prefer the file named with WIND
if os.path.exists(CSV_LC_PATH_WIND):
    CSV_LC_PATH = CSV_LC_PATH_WIND
    print(f"Using the automatically matched wind data: {CSV_LC_PATH}")
else:
    CSV_LC_PATH = CSV_LC_PATH_USER
    print(f"WIND-prefixed file not found, using the user-provided path: {CSV_LC_PATH}")

SHP_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机80米缓冲区.shp"
BIOMASS_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\地面碳数据\ESACCI_Biomass_2017_100m.tif"

# 2. Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.2.2风电生物碳损失"

# 3. Parameter settings
CARBON_FRACTION = 0.47  # Biomass -> carbon conversion coefficient (IPCC)
PIXEL_AREA_HA = 1.0     # Only used for rough estimation

# 4. Land class weight table (biomass weight W_Bio)
WEIGHTS_BIO = {
    'Trees': 100,
    'Grass': 6,
    'Shrub': 20,
    'Crops': 5,
    'Wetland': 15,
    'Bareland': 0,
    'Background':0,
}

# 5. Wind disturbance coefficient (K_Wind)
# Assume 10% of the area is completely disturbed
K_WIND_DEFAULT = 0.1 

# ================= Core functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_zonal_stats_biomass(shp_gdf, raster_path):
    """
    Compute the mean biomass density (Mg/ha) of each polygon
    """
    print(f"Reading biomass data: {raster_path}")
    
    results = []
    
    # Preprocessing
    initial_len = len(shp_gdf)
    shp_gdf = shp_gdf[~shp_gdf.geometry.is_empty & shp_gdf.geometry.notna()]
    filtered_len = len(shp_gdf)
    if initial_len != filtered_len:
        print(f"    [Note] Removed {initial_len - filtered_len} invalid/empty geometries.")
    
    try:
        with rasterio.open(raster_path) as src:
            print(f"    Raster Profile: {src.profile}")
            print(f"    CRS: {src.crs}")
            
            # Ensure the SHP and Raster projections match
            if shp_gdf.crs != src.crs:
                print("    Projection mismatch, reprojecting the SHP...")
                shp_gdf = shp_gdf.to_crs(src.crs)
            
            total = len(shp_gdf)
            print(f"    Start processing {total} polygons (Windowed Reading)...")
            
            count = 0
            for idx, row in shp_gdf.iterrows():
                count += 1
                fid = row['fid']
                
                try:
                    geom = row['geometry']
                    
                    if geom is None or geom.is_empty:
                        results.append({'fid': fid, 'mean_biomass_density_mg_ha': 0.0})
                        continue

                    geom_mapping = [mapping(geom)]
                    
                    # Mask extraction
                    # all_touched=True is important for small buffers
                    out_image, out_transform = mask(src, geom_mapping, crop=True, nodata=0, all_touched=True)
                    data = out_image[0]
                    
                    # Filter valid values
                    valid_data = data[data > 0]
                    
                    if valid_data.size > 0:
                        mean_density = np.mean(valid_data)
                    else:
                        mean_density = 0.0
                        
                    results.append({'fid': fid, 'mean_biomass_density_mg_ha': mean_density})
                    
                except Exception as e:
                    # print(f"    [ERROR] FID {fid}: {e}")
                    results.append({'fid': fid, 'mean_biomass_density_mg_ha': 0.0})
                
                if count % 5000 == 0:
                    print(f"    Processed {count}/{total}")
                    
    except Exception as e:
        print(f"[ERROR] Failed to open or read the raster file: {e}")
        return pd.DataFrame(columns=['fid', 'mean_biomass_density_mg_ha'])
        
    return pd.DataFrame(results)

def calculate_biomass_loss(df_merged, df_biomass, k_wind=0.1):
    """
    Execute Stage 2 (Denoising) & Stage 3 (Allocation) & Stage 4 (Loss)
    k_wind: wind disturbance coefficient
    """
    print(f"Start computing the biomass carbon loss (K_Wind={k_wind})...")
    
    # 1. Merge data
    if 'fid' not in df_merged.columns:
        print("[ERROR] Missing 'fid' column in the CSV.")
        return pd.DataFrame()

    df_merged['fid'] = df_merged['fid'].astype(int)
    df_biomass['fid'] = df_biomass['fid'].astype(int)
    
    df = pd.merge(df_merged, df_biomass, on='fid', how='inner')
    df['mean_biomass_density_mg_ha'] = df['mean_biomass_density_mg_ha'].fillna(0)
    
    print(f"    Data size after merge: {len(df)}")
    
    # 2. GIS original total SUM_Bio_GIS
    # Formula: mean density(Mg/ha) * total area(ha) * carbon coefficient(0.47)
    # Total area
    if 'total_area_m2' not in df.columns and 'area_m2' in df.columns:
         df['total_area_m2'] = df['area_m2']
         
    df['total_area_ha'] = df['total_area_m2'] / 10000.0
    df['SUM_Bio_GIS'] = df['mean_biomass_density_mg_ha'] * df['total_area_ha'] * CARBON_FRACTION
    
    # ================= Stage 2: Spatial Denoising =================
    eco_cols = ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops']
    if 'pre_Wetland' in df.columns:
        eco_cols.append('pre_Wetland')
    
    # Compute the total ecological land area
    df['Area_Eco_m2'] = df[eco_cols].sum(axis=1)
    
    # Ratio_Eco
    df['Ratio_Eco'] = df['Area_Eco_m2'] / df['total_area_m2']
    df['Ratio_Eco'] = df['Ratio_Eco'].fillna(0).clip(0, 1)
    
    # SUM_Bio_Corrected
    df['SUM_Bio_Corrected'] = df['SUM_Bio_GIS'] * df['Ratio_Eco']
    
    # ================= Stage 3: Categorical Re-allocation =================
    score = 0
    for col in eco_cols:
        land_type = col.replace('pre_', '')
        weight = WEIGHTS_BIO.get(land_type, 0)
        score += df[col] * weight
        
    df['Score_Bio'] = score
    
    # Factor_Bio
    df['Factor_Bio'] = df.apply(lambda row: row['SUM_Bio_Corrected'] / row['Score_Bio'] if row['Score_Bio'] > 0 else 0, axis=1)
    
    # Compute the real biomass carbon stock of each ecological type (Stock_Bio_Type)
    df['Total_Eco_Bio'] = 0.0
    
    for col in eco_cols:
        land_type = col.replace('pre_', '')
        weight = WEIGHTS_BIO.get(land_type, 0)
        
        stock_col = f'Stock_Bio_{land_type}'
        df[stock_col] = df[col] * weight * df['Factor_Bio']
        
        df['Total_Eco_Bio'] += df[stock_col]
        
    # ================= Stage 4: Loss Accounting =================
    # Use the K_Wind coefficient method (similar to soil carbon, because there is no pixel-level change detection)
    df['K_Wind'] = k_wind
    
    df['Loss_Bio_tC'] = df['Total_Eco_Bio'] * df['K_Wind']
    
    # Estimate the itemized loss (for reference only)
    for col in eco_cols:
        land_type = col.replace('pre_', '')
        stock_col = f'Stock_Bio_{land_type}'
        loss_col = f'Loss_Bio_{land_type}_tC'
        df[loss_col] = df[stock_col] * df['K_Wind']
            
    return df

def main():
    ensure_dir(OUTPUT_DIR)
    
    print("=== 1. Load data ===")
    
    # Read the Land Cover CSV (Pivot Long -> Wide)
    print(f"Reading LandCover: {CSV_LC_PATH}")
    df_lc_raw = pd.read_csv(CSV_LC_PATH)
    if 'fid' not in df_lc_raw.columns and 'FID' in df_lc_raw.columns:
        df_lc_raw.rename(columns={'FID': 'fid'}, inplace=True)
    
    # Convert to Wide Format
    print("Converting the LandCover data format (Long -> Wide)...")
    df_lc = df_lc_raw.pivot_table(index='fid', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0)
    
    # Rename columns
    rename_map = {
        'Forest': 'pre_Trees',
        'Grass': 'pre_Grass',
        'Shrub': 'pre_Shrub',
        'Cropland': 'pre_Crops',
        'Wetland': 'pre_Wetland'
    }
    df_lc.rename(columns=rename_map, inplace=True)
    
    # Compute the total area
    df_lc['total_area_m2'] = df_lc.sum(axis=1)
    
    # Reset the index
    df_lc.reset_index(inplace=True)
    df_lc['fid'] = df_lc['fid'].astype(int)
    
    # Ensure the columns exist
    for col in ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops', 'pre_Wetland']:
        if col not in df_lc.columns:
            df_lc[col] = 0.0

    # Read the SHP
    print(f"Reading SHP: {SHP_PATH}")
    try:
        gdf = gpd.read_file(SHP_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to read the SHP: {e}")
        return

    if 'fid_1' in gdf.columns:
        gdf = gdf.rename(columns={'fid_1': 'fid'})
    
    if 'fid' not in gdf.columns:
        gdf['fid'] = gdf.index
    
    gdf['fid'] = gdf['fid'].astype(int)
    
    # Extract the constructi year information from the SHP
    if 'constructi' in gdf.columns:
        year_map = gdf[['fid', 'constructi']].copy()
        year_map['constructi'] = year_map['constructi'].fillna(2017).astype(int)
        year_map.loc[year_map['constructi'] < 2017, 'constructi'] = 2017
    else:
        year_map = gdf[['fid']].copy()
        year_map['constructi'] = 2017
    
    # Merge LC and Year
    print("Merging the table data...")
    df_merged = pd.merge(df_lc, year_map, on='fid', how='inner')
    
    print(f"Number of records after merge: {len(df_merged)}")
    
    # 2. Compute Zonal Stats
    print("=== 2. Extract biomass carbon background values ===")
    df_biomass = get_zonal_stats_biomass(gdf[['fid', 'geometry']], BIOMASS_PATH)
    
    if df_biomass.empty:
        print("[Warning] Biomass data extraction failed or is empty.")
        return

    # 3. Multi-scenario computation and output
    scenarios = {
        '悲观场景': 0.2,
        '标准场景': 0.1,
        '乐观场景': 0.05
    }

    for scenario_name, k_val in scenarios.items():
        print(f"\n>>> Processing scenario: {scenario_name} (K_Wind: {k_val})")
        
        # Compute the loss
        df_result = calculate_biomass_loss(df_merged, df_biomass, k_wind=k_val)
        
        # Create the scenario subdirectory
        scenario_dir = os.path.join(OUTPUT_DIR, scenario_name)
        ensure_dir(scenario_dir)
        
        # Output the results
        out_csv = os.path.join(scenario_dir, "Wind_Biomass_Loss_Result.csv")
        
        # Rename the year column
        if 'installation_year' not in df_result.columns and 'constructi' in df_result.columns:
            df_result.rename(columns={'constructi': 'installation_year'}, inplace=True)
        
        out_cols = [
            'fid', 'installation_year', 'total_area_ha',
            'mean_biomass_density_mg_ha', 'SUM_Bio_GIS', 'Ratio_Eco', 'SUM_Bio_Corrected', 
            'Factor_Bio', 'K_Wind', 'Loss_Bio_tC',
            'Loss_Bio_Trees_tC', 'Loss_Bio_Grass_tC', 'Loss_Bio_Shrub_tC', 'Loss_Bio_Crops_tC'
        ]
        
        out_cols = [c for c in out_cols if c in df_result.columns]
        
        df_result[out_cols].to_csv(out_csv, index=False)
        print(f"Results saved: {out_csv}")
        
        total_loss = df_result['Loss_Bio_tC'].sum()
        print(f"{scenario_name} - Global wind biomass carbon total loss: {total_loss/1e6:.4f} MtC")

if __name__ == "__main__":
    main()
