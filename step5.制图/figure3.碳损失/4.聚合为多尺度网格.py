"""
Aggregate the 0.1-degree grid carbon debt statistics into multi-scale grids (0.5, 0.75, 1.0, 1.5, 2.0 degrees) - multi-scenario version
Author: 锐多宝 (ruiduobao)
Date: 2026-02-06
Purpose: based on the existing 0.1-degree statistics, aggregate and generate grid data at different scales (multi-scenario supported)
Optimization: supports non-integer scaling factors (e.g. 0.75 degrees), using a floor-based classification method
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box
import os
import time

SCENARIOS = ['乐观场景', '标准场景', '悲观场景']

def aggregate_grid(df_01, target_size, output_dir, scenario_name):
    """
    Aggregate the grid to the specified size
    """
    print(f"\nProcessing the {target_size}-degree grid aggregation ({scenario_name})...")
    
    # Compute the scaling factor (0.1-degree base)
    # Use float division instead of converting to int, to support non-integer multiples such as 0.75
    scale = target_size / 0.1
    # print(f"  Scaling factor: {scale:.2f} (i.e. about {scale}x{scale} base grids aggregated)")
    
    # Copy the data to avoid modifying the original data
    df_agg = df_01.copy()
    
    # Compute the new grid indices (use np.floor for float division)
    # Note: this causes a slight fluctuation in the size of non-integer-multiple grids (e.g. 0.75 degrees) (sawtooth effect), which is an inevitable result of grid-based aggregation
    df_agg['lon_index_new'] = np.floor(df_agg['lon_index'] / scale).astype(int)
    df_agg['lat_index_new'] = np.floor(df_agg['lat_index'] / scale).astype(int)
    
    # Compute the new grid parameters
    lon_min = -180
    lat_min = -90
    # Compute the new number of latitude-direction grids (round up to cover the globe)
    n_lat_new = int(np.ceil(180 / target_size))
    
    # Compute the new grid_id
    df_agg['grid_id_new'] = df_agg['lon_index_new'] * n_lat_new + df_agg['lat_index_new']
    
    # Aggregate the data
    # print("  Aggregating the data...")
    agg_cols = ['Loss_Bio_tCO2', 'Loss_Soil_tCO2', 'Loss_Mfg_tCO2', 'Total_Debt_tCO2', 'Loss_LUC']
    
    # Group by the new grid_id and sum
    df_result = df_agg.groupby(['grid_id_new', 'lon_index_new', 'lat_index_new'])[agg_cols].sum().reset_index()
    
    # Compute the new indicators
    # print("  Computing the ratio indicators...")
    df_result['Ratio_LUC'] = 0.0
    df_result['Ratio_Mfg'] = 0.0
    
    mask = df_result['Total_Debt_tCO2'] > 0
    df_result.loc[mask, 'Ratio_LUC'] = df_result.loc[mask, 'Loss_LUC'] / df_result.loc[mask, 'Total_Debt_tCO2']
    df_result.loc[mask, 'Ratio_Mfg'] = df_result.loc[mask, 'Loss_Mfg_tCO2'] / df_result.loc[mask, 'Total_Debt_tCO2']
    
    # print(f"  Number of generated grids: {len(df_result)}")
    
    # Generate the geometries
    # print("  Generating the geometries...")
    
    # Compute the bounds
    lefts = lon_min + df_result['lon_index_new'] * target_size
    bottoms = lat_min + df_result['lat_index_new'] * target_size
    rights = lefts + target_size
    tops = bottoms + target_size
    
    # Add the coordinate columns
    df_result['left'] = lefts
    df_result['right'] = rights
    df_result['bottom'] = bottoms
    df_result['top'] = tops
    df_result['center_lon'] = lefts + target_size / 2
    df_result['center_lat'] = bottoms + target_size / 2
    
    # Create the Polygons
    geometries = [box(l, b, r, t) for l, b, r, t in zip(lefts, bottoms, rights, tops)]
    
    # Create the GeoDataFrame
    gdf_result = gpd.GeoDataFrame(df_result, geometry=geometries, crs='EPSG:4326')
    
    # Export the results
    # print(f"  Saving the results...")
    output_shp = os.path.join(output_dir, f"全球{target_size}度网格_碳债务统计_{scenario_name}.shp")
    output_csv = os.path.join(output_dir, f"全球{target_size}度网格_碳债务统计_{scenario_name}.csv")
    
    # Save the CSV
    df_export = pd.DataFrame(gdf_result.drop(columns='geometry'))
    df_export.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"    CSV: {os.path.basename(output_csv)}")
    
    # Rename the columns to fit the Shapefile
    rename_dict = {
        'Loss_Bio_tCO2': 'Bio_CO2',
        'Loss_Soil_tCO2': 'Soil_CO2',
        'Loss_Mfg_tCO2': 'Mfg_CO2',
        'Total_Debt_tCO2': 'Total_CO2',
        'Loss_LUC': 'LUC_CO2',
        'Ratio_LUC': 'Rate_LUC',
        'Ratio_Mfg': 'Rate_Mfg',
        'lon_index_new': 'lon_idx',
        'lat_index_new': 'lat_idx',
        'grid_id_new': 'grid_id'
    }
    
    gdf_shp = gdf_result.rename(columns=rename_dict)
    
    # Save the Shapefile
    gdf_shp.to_file(output_shp, driver='ESRI Shapefile', encoding='utf-8')
    print(f"    Shapefile: {os.path.basename(output_shp)}")

def main():
    start_time = time.time()
    
    # Base paths
    base_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24"
    data_dir = os.path.join(base_dir, r"制图\figure3_全球碳债务构成\数据")
    
    print("="*60)
    print("Multi-scale grid aggregation program (multi-scenario version)")
    print("="*60)
    
    # Loop over each scenario
    for scenario in SCENARIOS:
        print(f"\n>>> Processing scenario: {scenario}")
        
        # Input file (0.1-degree grid statistics result)
        input_csv = os.path.join(data_dir, f"全球0.1度网格_碳债务统计_{scenario}.csv")
        
        if not os.path.exists(input_csv):
            print(f"Error: input file not found {input_csv}")
            continue
            
        # Read the 0.1-degree statistics result
        print(f"Reading the base data: {os.path.basename(input_csv)}")
        df_01 = pd.read_csv(input_csv)
        
        # Filter out the rows without data
        if 'Total_Debt_tCO2' in df_01.columns:
            df_01 = df_01[df_01['Total_Debt_tCO2'] > 0].copy()
        
        print(f"Number of base data rows: {len(df_01)}")
        
        # Loop to generate the grids at different scales
        target_sizes = [0.5, 0.75, 1.0, 1.5, 2.0]
        
        for size in target_sizes:
            aggregate_grid(df_01, size, data_dir, scenario)
    
    print("-" * 60)
    print(f"All processing completed! Total time: {time.time() - start_time:.2f} s")

if __name__ == "__main__":
    main()
