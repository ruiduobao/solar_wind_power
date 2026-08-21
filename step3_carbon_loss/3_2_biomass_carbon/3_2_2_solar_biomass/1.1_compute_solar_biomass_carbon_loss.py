# -*- coding: utf-8 -*-
"""
Biomass carbon loss calculation for solar PV plants (Biomass Carbon Loss Calculation)
Author: 锐多宝 (Trae AI)
Date: 2026-01-07

Functions:
1. Read the solar PV land use analysis result (Solar_Analysis_Decoded_Merged.csv)
2. Read the solar PV plant vector (solarpower.shp)
3. Read the global biomass carbon density data (ESA CCI Biomass)
4. Calculate the biomass carbon loss for each plant following the "spatial denoising" and
   "type weight re-allocation" algorithms in 《公式计算2.md》.

Input:
- CSV: Solar_Analysis_Decoded_Merged.csv (contains area and loss area by land type)
- SHP: solarpower.shp (contains plant geometry, used to extract biomass background values)
- Raster: ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv6.0.nc (biomass density, Mg/ha)

Output:
- CSV: Solar_Biomass_Loss_Result.csv (contains biomass carbon loss in tC per FID)
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
# Modify the absolute paths as needed
CSV_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\合并结果\SOLAR_FROM_2017_2024_LandCover_Summary.csv"
SHP_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\光伏数据\solarpower_WGS84.shp"
BIOMASS_PATH = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\地面碳数据\ESACCI_Biomass_2017_100m.tif"

# 2. Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.2.1光伏生物碳损失"

# 3. Parameter settings
CARBON_FRACTION = 0.47  # biomass -> carbon conversion factor (IPCC)
PIXEL_AREA_HA = 1.0     # ESA CCI 100m pixel is about 1 ha (simplified; strictly it varies with latitude)

# 4. Land type weight table (from 公式计算2.md)
# Corresponds to CSV columns: 'pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops'
WEIGHTS = {
    'Trees': 100,
    'Grass': 6,
    'Shrub': 20,
    'Crops': 5,
    'Bare': 0
}

# ================= Core functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_zonal_stats_biomass(shp_gdf, raster_path):
    """
    Compute the mean biomass density (Mg/ha) for each polygon
    Optimized for large files (10GB+): uses rasterio windowed reading, no manual chunking needed.
    """
    print(f"Reading biomass data: {raster_path}")
    
    results = []
    
    # Preprocessing: drop invalid geometries
    # This step is critical to avoid the 'NoneType' object has no attribute '__geo_interface__' error
    initial_len = len(shp_gdf)
    shp_gdf = shp_gdf[~shp_gdf.geometry.is_empty & shp_gdf.geometry.notna()]
    filtered_len = len(shp_gdf)
    if initial_len != filtered_len:
        print(f"    [Info] Removed {initial_len - filtered_len} invalid/empty geometries.")
    
    try:
        # Open the large file with rasterio; it handles chunked reading automatically and avoids running out of memory
        with rasterio.open(raster_path) as src:
            print(f"    Raster Profile: {src.profile}")
            print(f"    CRS: {src.crs}")
            
            # Ensure SHP and Raster share the same projection
            if shp_gdf.crs != src.crs:
                print("    CRS mismatch; reprojecting SHP...")
                shp_gdf = shp_gdf.to_crs(src.crs)
            
            total = len(shp_gdf)
            print(f"    Processing {total} polygons (large-file mode, windowed reading)...")
            
            count = 0
            for idx, row in shp_gdf.iterrows():
                count += 1
                fid = row['fid']
                
                try:
                    geom = row['geometry']
                    
                    # Double-check geometry validity
                    if geom is None or geom.is_empty:
                        results.append({'fid': fid, 'mean_biomass_density_mg_ha': 0.0})
                        continue

                    # Convert geometry format
                    geom_mapping = [mapping(geom)]
                    
                    # Mask extraction (rasterio only reads data within the bounding box)
                    # crop=True ensures only the local window is read; this is key for handling 14GB files
                    out_image, out_transform = mask(src, geom_mapping, crop=True, nodata=0)
                    data = out_image[0] # read the first band
                    
                    # Filter valid values
                    valid_data = data[data > 0]
                    
                    if valid_data.size > 0:
                        mean_density = np.mean(valid_data) # Mg/ha
                    else:
                        mean_density = 0.0
                        
                    results.append({'fid': fid, 'mean_biomass_density_mg_ha': mean_density})
                    
                except (ValueError, AttributeError, TypeError) as e:
                    # Catch geometry errors or disjoint errors
                    # print(f"    [WARN] FID {fid} failed: {e}") # too many errors would flood the console; commented out for now
                    results.append({'fid': fid, 'mean_biomass_density_mg_ha': 0.0})
                except Exception as e:
                    print(f"    [ERROR] FID {fid} unknown error: {e}")
                    results.append({'fid': fid, 'mean_biomass_density_mg_ha': 0.0})
                
                if count % 1000 == 0:
                    print(f"    Processed {count}/{total}")
                    
    except Exception as e:
        print(f"[ERROR] Failed to open or read the raster file: {e}")
        return pd.DataFrame(columns=['fid', 'mean_biomass_density_mg_ha'])
        
    return pd.DataFrame(results)

def calculate_biomass_loss(df_merged, df_biomass, loss_ratio=1.0):
    """
    Execute Stage 2 (denoising) & Stage 3 (allocation) & Stage 4 (loss)
    loss_ratio: loss ratio (0.25, 0.5, 1.0)
    """
    print(f"Running allocation calculation (loss ratio: {loss_ratio})...")
    
    # 1. Merge data
    # Note: fid in the CSV may be int or float, and so is the fid in the SHP.
    # Types must be consistent for a correct merge.
    # The CSV was read without enforcing types before; here we uniformly convert to int.
    
    # Check CSV column names
    if 'fid' not in df_merged.columns:
        # Sometimes the CSV may not have an explicit fid column, or it is named differently, e.g. 'id', 'FID'
        # Based on the preview of Solar_Analysis_Decoded_Merged.csv, the first column is indeed 'fid'
        print("[ERROR] Missing 'fid' column in CSV; cannot merge.")
        return pd.DataFrame()

    df_merged['fid'] = df_merged['fid'].astype(int)
    df_biomass['fid'] = df_biomass['fid'].astype(int)
    
    df = pd.merge(df_merged, df_biomass, on='fid', how='inner') # inner join ensures only matched records are computed
    df['mean_biomass_density_mg_ha'] = df['mean_biomass_density_mg_ha'].fillna(0)
    
    print(f"    Records after merge: {len(df)} (original CSV: {len(df_merged)}, biomass data: {len(df_biomass)})")
    # Formula: mean density(Mg/ha) * total area(m2 -> ha) * carbon fraction
    df['total_area_ha'] = df['total_area_m2'] / 10000.0
    df['SUM_Bio_GIS'] = df['mean_biomass_density_mg_ha'] * df['total_area_ha'] * CARBON_FRACTION
    
    # 3. Compute the ecological validity ratio (Ratio_Eco) - Stage 2
    # Numerator: sum of ecological land areas (Trees + Grass + Shrub + Crops + Wetland)
    # Denominator: total area (including Bare, Water, Built)
    # CSV columns: pre_Trees, pre_Grass, pre_Shrub, pre_Crops
    eco_cols = ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops']
    
    df['Area_Eco_m2'] = df[eco_cols].sum(axis=1)
    df['Ratio_Eco'] = df['Area_Eco_m2'] / df['total_area_m2']
    
    # Clip Ratio_Eco to 0-1 (floating point errors)
    df['Ratio_Eco'] = df['Ratio_Eco'].clip(0, 1)
    
    # 4. Compute corrected total carbon (Corrected Total)
    df['SUM_Bio_Corrected'] = df['SUM_Bio_GIS'] * df['Ratio_Eco']
    
    # 5. Compute the theoretical score (Score_Bio) - Stage 3
    # Score = Area_Type * Weight_Type
    # Note: Area units are uniformly m2 because the Factor is a ratio later
    score = 0
    for col in eco_cols:
        land_type = col.replace('pre_', '') # Trees, Grass...
        weight = WEIGHTS.get(land_type, 0)
        score += df[col] * weight
    
    df['Score_Bio'] = score
    
    # 6. Compute the allocation factor (Factor_Bio)
    # Factor = SUM_Corrected / Score
    # Avoid division by zero
    df['Factor_Bio'] = df.apply(lambda row: row['SUM_Bio_Corrected'] / row['Score_Bio'] if row['Score_Bio'] > 0 else 0, axis=1)
    
    # 7. Compute the biomass carbon loss (Loss_Bio) - Stage 4
    # Loss = Sum(Area_Loss_Type * Weight_Type * Factor_Bio)
    # CSV loss columns: loss_Trees_to_Built, ...
    
    df['Loss_Bio_tC'] = 0.0
    
    loss_cols = {
        'Trees': 'loss_Trees_to_Built',
        'Grass': 'loss_Grass_to_Built',
        'Shrub': 'loss_Shrub_to_Built',
        'Crops': 'loss_Crops_to_Built'
    }
    
    for land_type, col_name in loss_cols.items():
        if col_name in df.columns:
            weight = WEIGHTS.get(land_type, 0)
            # Loss_Item = Area_Loss * Weight * Factor * Loss_Ratio
            loss_item = df[col_name] * weight * df['Factor_Bio'] * loss_ratio
            df['Loss_Bio_tC'] += loss_item
            
            # Optional: record itemized losses
            df[f'Loss_Bio_{land_type}_tC'] = loss_item
            
    return df

def preprocess_landcover_data(df):
    """
    Convert the long-format summary CSV to wide format and compute total_area_m2 and pre_X, loss_X fields
    """
    print("Preprocessing land cover data...")
    # 1. Pivot table
    # pivot columns: fid, class_name, values: area_sqm
    # Aggregation: sum (in case multiple rows per class per fid)
    df_pivot = df.pivot_table(index='fid', columns='class_name', values='area_sqm', aggfunc='sum', fill_value=0).reset_index()
    
    # 2. Rename columns
    rename_map = {
        'Forest': 'pre_Trees',
        'Grass': 'pre_Grass',
        'Shrub': 'pre_Shrub',
        'Cropland': 'pre_Crops',
        'Wetland': 'pre_Wetland',
    }
    # Handle missing columns safely
    for src, dst in rename_map.items():
        if src in df_pivot.columns:
            df_pivot.rename(columns={src: dst}, inplace=True)
        else:
            df_pivot[dst] = 0.0
            
    # Ensure all pre_ columns exist
    for col in ['pre_Trees', 'pre_Grass', 'pre_Shrub', 'pre_Crops']:
        if col not in df_pivot.columns:
            df_pivot[col] = 0.0

    # 3. Calculate total_area_m2
    # Sum of all numeric columns except fid
    total_area = df.groupby('fid')['area_sqm'].sum().reset_index()
    total_area.rename(columns={'area_sqm': 'total_area_m2'}, inplace=True)
    
    df_merged = pd.merge(df_pivot, total_area, on='fid')
    
    # 4. Create loss columns (Assuming Loss = Pre)
    df_merged['loss_Trees_to_Built'] = df_merged['pre_Trees']
    df_merged['loss_Grass_to_Built'] = df_merged['pre_Grass']
    df_merged['loss_Shrub_to_Built'] = df_merged['pre_Shrub']
    df_merged['loss_Crops_to_Built'] = df_merged['pre_Crops']
    
    return df_merged

def main():
    ensure_dir(OUTPUT_DIR)
    
    # 1. Read CSV
    print(f"Reading CSV: {CSV_PATH}")
    df_raw = pd.read_csv(CSV_PATH)
    
    # Preprocess data
    df_merged = preprocess_landcover_data(df_raw)
    
    # 2. Read SHP
    print(f"Reading SHP: {SHP_PATH}")
    gdf = gpd.read_file(SHP_PATH)
    
    # Adjust according to the actual SHP column names
    # Actual columns are 'fid_1', 'layer', 'COUNTRY', 'constructi'...
    if 'fid_1' in gdf.columns:
        gdf = gdf.rename(columns={'fid_1': 'fid', 'COUNTRY': 'country_iso_a3', 'constructi': 'installation_year'})
    
    # Ensure metadata columns exist
    meta_cols = ['fid', 'country_iso_a3', 'installation_year']
    for c in meta_cols:
        if c not in gdf.columns:
            gdf[c] = None
            
    # Ensure consistent fid types
    gdf['fid'] = gdf['fid'].astype(int)
    df_merged['fid'] = df_merged['fid'].astype(int)
    
    # Merge metadata into df_merged
    # Note: assume the fid in the SHP is unique and corresponds to the CSV
    df_merged = pd.merge(df_merged, gdf[meta_cols], on='fid', how='left')
    
    # Keep only geometry for zonal stats
    gdf = gdf[['fid', 'geometry']]
    
    # 3. Compute Zonal Stats (Biomass Density)
    df_biomass = get_zonal_stats_biomass(gdf, BIOMASS_PATH)
    
    if df_biomass.empty:
        print("[Warning] Biomass data extraction failed or is empty; cannot proceed with calculations.")
        return

    # 4. Multi-scenario calculation and output
    scenarios = {
        '悲观场景': 1.0,
        '标准场景': 0.5,
        '乐观场景': 0.25
    }

    for scenario_name, ratio in scenarios.items():
        print(f"\n>>> Processing scenario: {scenario_name} (loss ratio: {ratio})")
        
        # Compute losses
        df_result = calculate_biomass_loss(df_merged, df_biomass, loss_ratio=ratio)
        
        # Create scenario subdirectory
        scenario_dir = os.path.join(OUTPUT_DIR, scenario_name)
        ensure_dir(scenario_dir)
        
        # Output results
        out_csv = os.path.join(scenario_dir, "Solar_Biomass_Loss_Result.csv")
        
        # Select output columns
        out_cols = [
            'fid', 'country_iso_a3', 'installation_year', 
            'mean_biomass_density_mg_ha', 'SUM_Bio_GIS', 'Ratio_Eco', 'SUM_Bio_Corrected', 
            'Factor_Bio', 'Loss_Bio_tC',
            'Loss_Bio_Trees_tC', 'Loss_Bio_Grass_tC', 'Loss_Bio_Shrub_tC', 'Loss_Bio_Crops_tC'
        ]
        # Keep only existing columns
        out_cols = [c for c in out_cols if c in df_result.columns]
        
        df_result[out_cols].to_csv(out_csv, index=False)
        print(f"Results saved: {out_csv}")
        
        # Simple statistics
        total_loss = df_result['Loss_Bio_tC'].sum()
        print(f"{scenario_name} - Global solar biomass carbon loss: {total_loss/1e6:.2f} MtC")

if __name__ == "__main__":
    main()
