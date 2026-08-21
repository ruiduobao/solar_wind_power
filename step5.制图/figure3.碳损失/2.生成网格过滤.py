"""
Filter the global 0.1-degree grid based on wind and solar power plant points
Author: 锐多宝（ruiduobao）
Date: 2026-02-03
Purpose: keep only grid cells that contain wind or solar power points for subsequent analysis
Optimization: compute grid indices directly from point coordinates and generate the corresponding grid, avoiding reading the huge full-grid file
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box
import os
import time
from datetime import datetime

def get_grid_indices_from_points(shp_path, grid_size=0.1, lon_min=-180, lat_min=-90):
    """
    Read point data and compute the grid indices where the points are located
    """
    print(f"Reading point data: {shp_path}")
    try:
        # Read only the geometry column to save memory (although the file is not large)
        gdf = gpd.read_file(shp_path)
        
        # Ensure the CRS is WGS84
        if gdf.crs != 'EPSG:4326':
            print(f"Converting CRS {gdf.crs} -> EPSG:4326")
            gdf = gdf.to_crs('EPSG:4326')
            
        # Get coordinates
        x = gdf.geometry.x
        y = gdf.geometry.y
        
        # Compute indices
        # Use floor to round down
        lon_indices = np.floor((x - lon_min) / grid_size).astype(int)
        lat_indices = np.floor((y - lat_min) / grid_size).astype(int)
        
        # Create DataFrame
        df = pd.DataFrame({
            'lon_index': lon_indices,
            'lat_index': lat_indices
        })
        
        # Filter out out-of-range points (if any)
        n_lon = int(360 / grid_size)
        n_lat = int(180 / grid_size)
        mask = (df['lon_index'] >= 0) & (df['lon_index'] < n_lon) & \
               (df['lat_index'] >= 0) & (df['lat_index'] < n_lat)
        
        valid_count = mask.sum()
        total_count = len(df)
        if valid_count < total_count:
            print(f"Warning: filtered out {total_count - valid_count} points outside the global grid extent")
            df = df[mask]
            
        return df
        
    except Exception as e:
        print(f"Error reading or processing file {shp_path}: {str(e)}")
        return pd.DataFrame(columns=['lon_index', 'lat_index'])

def main():
    start_time = time.time()
    
    # Input file paths
    wind_points_path = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风机缓冲区\风机点数据.shp"
    solar_points_path = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\光伏分年份数据\光伏点数据2017-2024.shp"
    
    # Output path
    output_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure3_全球碳债务构成\数据"
    output_shp = os.path.join(output_dir, "全球0.1度网格_有电站.shp")
    
    # Grid parameters
    grid_size = 0.1
    lon_min = -180
    lat_min = -90
    n_lat = int(180 / grid_size)  # 1800
    
    print("="*60)
    print("Grid filtering program")
    print("="*60)
    
    # 1. Get grid indices of wind points
    df_wind = get_grid_indices_from_points(wind_points_path)
    print(f"Number of grids containing wind points: {len(df_wind)}")
    
    # 2. Get grid indices of solar points
    df_solar = get_grid_indices_from_points(solar_points_path)
    print(f"Number of grids containing solar points: {len(df_solar)}")
    
    # 3. Concatenate and deduplicate
    print("Merging grid indices...")
    df_all = pd.concat([df_wind, df_solar], ignore_index=True)
    df_unique = df_all.drop_duplicates(subset=['lon_index', 'lat_index']).copy()
    
    print(f"Total unique valid grids after deduplication: {len(df_unique)}")
    
    # 4. Generate grid geometries
    print("Generating grid geometries...")
    
    # Vectorized coordinate computation
    lon_idxs = df_unique['lon_index'].values
    lat_idxs = df_unique['lat_index'].values
    
    lefts = lon_min + lon_idxs * grid_size
    bottoms = lat_min + lat_idxs * grid_size
    rights = lefts + grid_size
    tops = bottoms + grid_size
    
    # Create Polygon
    geometries = [box(l, b, r, t) for l, b, r, t in zip(lefts, bottoms, rights, tops)]
    
    # 5. Build GeoDataFrame
    gdf_out = gpd.GeoDataFrame(df_unique, geometry=geometries, crs='EPSG:4326')
    
    # Add other attributes
    gdf_out['left'] = lefts
    gdf_out['right'] = rights
    gdf_out['bottom'] = bottoms
    gdf_out['top'] = tops
    gdf_out['center_lon'] = lefts + grid_size / 2
    gdf_out['center_lat'] = bottoms + grid_size / 2
    
    # Compute the global Grid ID (consistent with the full grid: lon_idx * n_lat + lat_idx)
    # Note: in previous scripts, the lat loop is inner and the lon loop is outer
    # grid_id = lon_index * n_lat + lat_index
    gdf_out['grid_id'] = gdf_out['lon_index'] * n_lat + gdf_out['lat_index']
    
    # Reorder columns
    cols = ['grid_id', 'lon_index', 'lat_index', 'left', 'right', 'bottom', 'top', 
            'center_lon', 'center_lat', 'geometry']
    gdf_out = gdf_out[cols]
    
    # Sort by Grid ID
    gdf_out = gdf_out.sort_values('grid_id')
    
    # 6. Save
    print(f"Saving results to: {output_shp}")
    os.makedirs(os.path.dirname(output_shp), exist_ok=True)
    
    gdf_out.to_file(output_shp, driver='ESRI Shapefile', encoding='utf-8')
    
    print("-" * 60)
    print(f"Processing completed!")
    print(f"Total time: {time.time() - start_time:.2f} seconds")
    print(f"Output file: {output_shp}")
    print(f"Number of grids: {len(gdf_out)}")

if __name__ == "__main__":
    main()
