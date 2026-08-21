"""
Generate a global 0.5-degree hexagonal grid and compute carbon payback periods (based on full-grid generation and spatial join)
Author: 锐多宝 (ruiduobao)
Date: 2026-02-09
Purpose:
1. Generate a 0.5-degree regular hexagon grid covering the globe (WGS84 coordinate system)
2. Attach wind/solar point locations to the grid via spatial join
3. Compute the average CPT_Days of each grid for the three scenarios
4. Output the results to the corresponding scenario folders
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import os
import math

# --- Configuration ---
# Circumradius of the hexagon (degrees)
# If the height of the hexagon (pointy-topped) should be 0.5 degrees, then R = 0.5 / 2 = 0.25
HEX_RADIUS = 0.25 

BASE_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24"
DATA_PATH = os.path.join(BASE_PATH, "数据")
CHART_PATH = os.path.join(BASE_PATH, "制图")

WIND_SHP_PATH = os.path.join(DATA_PATH, "windpower.shp")
SOLAR_SHP_PATH = os.path.join(DATA_PATH, "solarpower.shp")

SCENARIOS = {
    "标准场景": "Standard",
    "乐观场景": "Optimistic",
    "悲观场景": "Pessimistic"
}

def create_hex_grid(radius, lon_min=-180, lon_max=180, lat_min=-90, lat_max=90):
    """
    Generate a pointy-topped regular hexagon grid covering the given extent
    """
    print(f"Generating the full hexagon grid (R={radius} deg)...")
    
    # Pointy-topped hexagon parameters
    # Height H = 2 * R
    # Width W = sqrt(3) * R
    # Vertical spacing (row distance) vert_dist = 3/4 * H = 1.5 * R
    # Horizontal spacing (column distance) horiz_dist = W = sqrt(3) * R
    
    H = 2 * radius
    W = math.sqrt(3) * radius
    
    vert_dist = 1.5 * radius
    horiz_dist = W
    
    # Compute the number of rows and columns
    n_rows = int(np.ceil((lat_max - lat_min) / vert_dist))
    n_cols = int(np.ceil((lon_max - lon_min) / horiz_dist))
    
    print(f"  Estimated grid dimensions: {n_rows} rows x {n_cols} columns (about {n_rows * n_cols} grids)")
    
    polygons = []
    ids = []
    
    # Generate the vertex offsets of the hexagon
    # Angles: 30, 90, 150, 210, 270, 330
    angles = np.deg2rad([30, 90, 150, 210, 270, 330])
    x_offset = radius * np.cos(angles)
    y_offset = radius * np.sin(angles)
    
    count = 0
    
    for row in range(n_rows):
        y = lat_min + row * vert_dist
        
        # Even-row offset
        x_start = lon_min
        if row % 2 == 1:
            x_start += horiz_dist / 2.0
            
        for col in range(n_cols):
            x = x_start + col * horiz_dist
            
            # Simple boundary check (center within range is enough, or slightly relaxed)
            if x > lon_max + horiz_dist: # Slightly relaxed
                continue
                
            # Generate the polygon
            poly_x = x + x_offset
            poly_y = y + y_offset
            poly = Polygon(zip(poly_x, poly_y))
            
            polygons.append(poly)
            ids.append(f"{row}_{col}")
            count += 1
            
    # Create the GeoDataFrame
    gdf = gpd.GeoDataFrame({'hex_id': ids}, geometry=polygons, crs="EPSG:4326")
    print(f"  Full grid generated; {len(gdf)} hexagons in total.")
    return gdf

def process_scenario(points_gdf, hex_grid, type_name, scenario_cn):
    """
    Process a single scenario: read the CSV, attach to the points, spatial join to the grid, and compute the mean
    """
    print(f"  Processing: {type_name} - {scenario_cn}")
    
    # 1. Read the CSV
    if type_name == "Wind":
        csv_path = os.path.join(CHART_PATH, "5.2.风机碳回本周期", scenario_cn, "Wind_Carbon_Payback_Time.csv")
    else:
        csv_path = os.path.join(CHART_PATH, "5.1.光伏碳回本周期", scenario_cn, "Solar_Carbon_Payback_Time.csv")
        
    if not os.path.exists(csv_path):
        print(f"    Warning: file not found {csv_path}")
        return
        
    df_csv = pd.read_csv(csv_path)
    
    # 2. Check the required fields
    if 'fid' not in df_csv.columns or 'CPT_Years' not in df_csv.columns:
        print(f"    Error: the CSV is missing required fields (fid, CPT_Years)")
        return
        
    # 3. Compute the days and attach them to the point data
    df_csv['fid'] = df_csv['fid'].astype(int)
    df_csv['CPT_Days'] = df_csv['CPT_Years'] * 365.25
    
    # Keep only the records with point data
    points_with_data = points_gdf.merge(df_csv[['fid', 'CPT_Days']], on='fid', how='inner')
    
    if len(points_with_data) == 0:
        print(f"    Warning: the match between points and CSV data is empty")
        return

    # 4. Spatial join: attach the points to the hexagons
    # op='within' checks whether a point is inside a hexagon
    print(f"    Performing the spatial join (Points -> HexGrid)...")
    # Using sjoin while keeping hex_grid geometry (left join) does not work; we want the grid containing each point
    # The other way: join points to grid?
    # Better: sjoin(points, grid) -> get the hex_id for each point
    
    # Note: sjoin may be slow if there are many grids. But the rtree index is used here, so it should be acceptable.
    # Ensure the grid has an index
    # hex_grid.sindex 
    
    joined = gpd.sjoin(points_with_data, hex_grid, how='inner', predicate='within')
    
    # 5. Compute the mean of each grid
    print(f"    Computing grid means...")
    stats = joined.groupby('hex_id')['CPT_Days'].mean().reset_index()
    stats.rename(columns={'CPT_Days': 'Avg_CPT'}, inplace=True)
    
    # 6. Merge the statistics back to the hexagon geometries
    result_gdf = hex_grid.merge(stats, on='hex_id', how='inner') # Inner join automatically filters out grids without data
    
    print(f"    The result contains {len(result_gdf)} grids with data")
    
    # 7. Save
    out_dir = os.path.dirname(csv_path)
    out_name = f"{type_name}_Hex_Grid_0.5deg.shp"
    out_path = os.path.join(out_dir, out_name)
    
    print(f"    Saving to: {out_path}")
    result_gdf.to_file(out_path, driver='ESRI Shapefile', encoding='utf-8')

def main():
    # 1. Generate the full global grid (only once)
    global_hex_grid = create_hex_grid(HEX_RADIUS)
    
    # 2. Read the point data (only once)
    print("\nReading the base vector data...")
    
    # Wind
    print(f"  Reading wind: {WIND_SHP_PATH}")
    wind_gdf = gpd.read_file(WIND_SHP_PATH)
    if wind_gdf.crs != 'EPSG:4326':
        print(f"    Converting CRS {wind_gdf.crs} -> EPSG:4326")
        wind_gdf = wind_gdf.to_crs('EPSG:4326')
    if 'fid' in wind_gdf.columns:
        wind_gdf['fid'] = wind_gdf['fid'].astype(int)
    
    # Solar
    print(f"  Reading solar: {SOLAR_SHP_PATH}")
    solar_gdf = gpd.read_file(SOLAR_SHP_PATH)
    if solar_gdf.crs != 'EPSG:4326':
        print(f"    Converting CRS {solar_gdf.crs} -> EPSG:4326")
        solar_gdf = solar_gdf.to_crs('EPSG:4326')
    if 'fid' in solar_gdf.columns:
        solar_gdf['fid'] = solar_gdf['fid'].astype(int)
    
    # Convert solar polygons to points
    if solar_gdf.geom_type[0] in ['Polygon', 'MultiPolygon']:
        print("  Converting solar polygons to centroid points...")
        solar_gdf['geometry'] = solar_gdf.geometry.centroid
        
    # 3. Loop over the scenarios
    for scenario_cn, scenario_en in SCENARIOS.items():
        print(f"\n>>> Processing scenario: {scenario_cn}")
        
        # Wind
        process_scenario(wind_gdf, global_hex_grid, "Wind", scenario_cn)
        
        # Solar
        process_scenario(solar_gdf, global_hex_grid, "Solar", scenario_cn)
        
    print("\nAll processing complete!")

if __name__ == "__main__":
    main()
