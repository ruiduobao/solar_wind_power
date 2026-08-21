"""
Compute the land carbon and manufacturing carbon values of each grid - multi-scenario version
Author: 锐多宝 (ruiduobao)
Date: 2026-02-06
Purpose: based on the correspondence between points and grids, aggregate and compute the carbon debt within each grid (multi-scenario supported)
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import os
import time

SCENARIOS = ['乐观场景', '标准场景', '悲观场景']

def calculate_grid_id(x, y, grid_size=0.1, lon_min=-180, lat_min=-90, n_lat=1800):
    """Compute the grid ID based on coordinates
    Note: use a 1e-9 offset to avoid floor rounding errors caused by floating-point precision
    """
    lon_idx = np.floor((x - lon_min) / grid_size + 1e-9).astype(int)
    lat_idx = np.floor((y - lat_min) / grid_size + 1e-9).astype(int)
    return lon_idx * n_lat + lat_idx

def process_points(point_shp, csv_path, type_name, output_dir=None):
    """
    Process point data:
    1. Read the Shapefile and CSV
    2. Join the attributes
    3. Compute the grid ID
    4. Return a DataFrame with carbon data
    """
    print(f"Processing {type_name} data...")
    
    # Read the point data
    print(f"  Reading the point Shapefile: {os.path.basename(point_shp)}")
    gdf_points = gpd.read_file(point_shp)
    if gdf_points.crs != 'EPSG:4326':
        gdf_points = gdf_points.to_crs('EPSG:4326')
    
    # If it is polygon data, convert to centroid points
    # Check the geometry type of the first object
    if not gdf_points.empty:
        geom_type = gdf_points.geometry.iloc[0].geom_type
        if geom_type in ['Polygon', 'MultiPolygon']:
            print("  Polygon data detected, converting to centroid points...")
            gdf_points['geometry'] = gdf_points.geometry.centroid

    # Read the CSV data
    print(f"  Reading the carbon data CSV: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"  Error: CSV file not found {csv_path}")
        return pd.DataFrame()
        
    df_carbon = pd.read_csv(csv_path)
    
    # Filter the years 2017-2024
    if 'installation_year' in df_carbon.columns:
        df_carbon = df_carbon[(df_carbon['installation_year'] >= 2017) & (df_carbon['installation_year'] <= 2024)]
    
    # Ensure the fid types match
    gdf_points['fid'] = gdf_points['fid'].astype(int)
    df_carbon['fid'] = df_carbon['fid'].astype(int)
    
    # Join the data
    print("  Merging the spatial points and attribute data...")
    # Only keep the required columns
    carbon_cols = ['fid', 'Loss_Bio_tCO2', 'Loss_Soil_tCO2', 'Loss_Mfg_tCO2', 'Total_Debt_tCO2']
    
    # Check whether the CSV has all columns; fill with 0 if any are missing
    for col in carbon_cols:
        if col not in df_carbon.columns:
             if col == 'Loss_Bio_tCO2' and 'Loss_Bio_tC' in df_carbon.columns:
                 df_carbon[col] = df_carbon['Loss_Bio_tC'] * 3.67
             elif col == 'Loss_Soil_tCO2' and 'Loss_Soil_tC' in df_carbon.columns:
                 df_carbon[col] = df_carbon['Loss_Soil_tC'] * 3.67
             else:
                 df_carbon[col] = 0
    
    # Use an inner join to keep only the records that have both points and carbon data
    merged = pd.merge(gdf_points[['fid', 'geometry']], df_carbon[carbon_cols], on='fid', how='inner')
    # Convert back to GeoDataFrame to retain geometry capabilities
    merged = gpd.GeoDataFrame(merged, geometry='geometry', crs=gdf_points.crs)
    print(f"  Matched {len(merged)} points (total points: {len(gdf_points)})")
    
    if len(merged) == 0:
        print(f"  Warning: no carbon emission records matched for {type_name} data!")
        return pd.DataFrame(columns=['grid_id'] + carbon_cols[1:])

    # Compute the grid ID
    print("  Computing the grid IDs...")
    merged['grid_id'] = calculate_grid_id(merged.geometry.x, merged.geometry.y)
    
    # Save the matched point data
    if output_dir:
        rename_dict = {
            'Loss_Bio_tCO2': 'Bio_CO2',
            'Loss_Soil_tCO2': 'Soil_CO2',
            'Loss_Mfg_tCO2': 'Mfg_CO2',
            'Total_Debt_tCO2': 'Total_CO2'
        }
        points_to_save = merged.rename(columns=rename_dict)
        
        # Sanitize type_name for filename
        safe_name = type_name.replace('-', '_')
        out_shp_name = f"{safe_name}_matched_points.shp"
        out_shp_path = os.path.join(output_dir, out_shp_name)
        
        print(f"  Saving the matched point data: {out_shp_name}")
        try:
            points_to_save.to_file(out_shp_path, driver='ESRI Shapefile', encoding='utf-8')
        except Exception as e:
            print(f"  Failed to save the point data: {e}")
    
    # Aggregate by grid
    print("  Aggregating the data by grid...")
    agg_cols = ['Loss_Bio_tCO2', 'Loss_Soil_tCO2', 'Loss_Mfg_tCO2', 'Total_Debt_tCO2']
    grid_agg = merged.groupby('grid_id')[agg_cols].sum().reset_index()
    
    return grid_agg

def main():
    start_time = time.time()
    
    # Input file paths
    base_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24"
    grid_shp = os.path.join(base_dir, r"制图\figure3_全球碳债务构成\数据\全球0.1度网格_有电站.shp")
    
    wind_shp = os.path.join(base_dir, r"数据\风机缓冲区\风机点数据.shp")
    solar_shp = os.path.join(base_dir, r"数据\solarpower.shp")
    
    output_dir = os.path.join(base_dir, r"制图\figure3_全球碳债务构成\数据")
    
    print("="*60)
    print("Global grid carbon debt statistics program (multi-scenario version)")
    print("="*60)
    
    # Read the grid file (as the base)
    print(f"\nReading the grid file: {os.path.basename(grid_shp)}")
    gdf_grid = gpd.read_file(grid_shp)
    
    # Iterate over the scenarios
    for scenario in SCENARIOS:
        print(f"\n>>> Processing scenario: {scenario}")
        
        # Define the CSV paths for this scenario
        wind_csv = os.path.join(base_dir, r"制图\4.4.2风机碳债务合并损失", scenario, "Wind_Total_Carbon_Debt_Result.csv")
        solar_csv = os.path.join(base_dir, r"制图\4.4.1光伏碳债务合并损失", scenario, "Solar_Total_Carbon_Debt_Result.csv")
        
        # 1. Process the wind data
        wind_agg = process_points(wind_shp, wind_csv, f"风机-{scenario}", output_dir)
        
        # 2. Process the solar data
        solar_agg = process_points(solar_shp, solar_csv, f"光伏-{scenario}", output_dir)
        
        # 3. Merge the wind and solar aggregation results
        print(f"\nMerging the wind and solar data ({scenario})...")
        if wind_agg.empty and solar_agg.empty:
            print("Error: both the wind and solar data are empty, the statistics cannot be computed!")
            continue

        # Outer join
        total_agg = pd.merge(wind_agg, solar_agg, on='grid_id', how='outer', suffixes=('_wind', '_solar'))
        total_agg = total_agg.fillna(0)
        
        # Compute the sums
        cols = ['Loss_Bio_tCO2', 'Loss_Soil_tCO2', 'Loss_Mfg_tCO2', 'Total_Debt_tCO2']
        for col in cols:
            total_agg[col] = total_agg[f'{col}_wind'] + total_agg[f'{col}_solar']
        
        final_agg = total_agg[['grid_id'] + cols].copy()
        
        # 4. Compute the new indicators
        print("Computing the new indicators...")
        final_agg['Loss_LUC'] = final_agg['Loss_Bio_tCO2'] + final_agg['Loss_Soil_tCO2']
        final_agg['Ratio_LUC'] = 0.0
        final_agg['Ratio_Mfg'] = 0.0
        
        mask = final_agg['Total_Debt_tCO2'] > 0
        final_agg.loc[mask, 'Ratio_LUC'] = final_agg.loc[mask, 'Loss_LUC'] / final_agg.loc[mask, 'Total_Debt_tCO2']
        final_agg.loc[mask, 'Ratio_Mfg'] = final_agg.loc[mask, 'Loss_Mfg_tCO2'] / final_agg.loc[mask, 'Total_Debt_tCO2']
        
        # 5. Join to the grid and export
        print(f"Joining the statistics to the grid ({scenario})...")
        gdf_result = pd.merge(gdf_grid, final_agg, on='grid_id', how='left')
        
        # Fill the unmatched grids
        fill_cols = cols + ['Loss_LUC', 'Ratio_LUC', 'Ratio_Mfg']
        gdf_result[fill_cols] = gdf_result[fill_cols].fillna(0)
        
        # Export
        output_shp = os.path.join(output_dir, f"全球0.1度网格_碳债务统计_{scenario}.shp")
        output_csv = os.path.join(output_dir, f"全球0.1度网格_碳债务统计_{scenario}.csv")
        
        print(f"Saving the results ({scenario})...")
        df_export = pd.DataFrame(gdf_result.drop(columns='geometry'))
        df_export.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"  CSV saved: {os.path.basename(output_csv)}")
        
        # Rename the columns to fit the Shapefile
        rename_dict = {
            'Loss_Bio_tCO2': 'Bio_CO2',
            'Loss_Soil_tCO2': 'Soil_CO2',
            'Loss_Mfg_tCO2': 'Mfg_CO2',
            'Total_Debt_tCO2': 'Total_CO2',
            'Loss_LUC': 'LUC_CO2',
            'Ratio_LUC': 'Rate_LUC',
            'Ratio_Mfg': 'Rate_Mfg'
        }
        
        gdf_shp = gdf_result.rename(columns=rename_dict)
        gdf_shp.to_file(output_shp, driver='ESRI Shapefile', encoding='utf-8')
        print(f"  Shapefile saved: {os.path.basename(output_shp)}")

    print("-" * 60)
    print(f"All processing completed! Total time: {time.time() - start_time:.2f} s")

if __name__ == "__main__":
    main()
