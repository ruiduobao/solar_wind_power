import pandas as pd
import geopandas as gpd
import os

# Define base paths
base_path = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24"
data_path = os.path.join(base_path, "数据")
chart_path = os.path.join(base_path, "制图")

# Define vector file paths
wind_shp_path = os.path.join(data_path, "windpower.shp")
solar_shp_path = os.path.join(data_path, "solarpower.shp")

# Define the scenario list
scenarios = {
    "标准场景": "Standard",
    "乐观场景": "Optimistic",
    "悲观场景": "Pessimistic"
}

# Read vector data (only once, for efficiency)
print(f"Reading Wind Shapefile: {wind_shp_path}")
wind_gdf = gpd.read_file(wind_shp_path)
print(f"Wind Shapefile loaded. Rows: {len(wind_gdf)}")

print(f"Reading Solar Shapefile: {solar_shp_path}")
solar_gdf = gpd.read_file(solar_shp_path)
print(f"Solar Shapefile loaded. Rows: {len(solar_gdf)}")

# Convert solar polygons to points (Centroid)
print("Converting Solar Polygons to Points (Centroids)...")
# Check whether the data is polygon
if solar_gdf.geom_type[0] == 'Polygon' or solar_gdf.geom_type[0] == 'MultiPolygon':
    solar_gdf['geometry'] = solar_gdf.geometry.centroid
    print("Conversion complete.")
else:
    print("Solar data is already points or other type.")

# Ensure the fid column types are consistent (convert to integer)
if 'fid' in wind_gdf.columns:
    wind_gdf['fid'] = wind_gdf['fid'].astype(int)
else:
    print("Warning: 'fid' column not found in Wind Shapefile!")

if 'fid' in solar_gdf.columns:
    solar_gdf['fid'] = solar_gdf['fid'].astype(int)
else:
    print("Warning: 'fid' column not found in Solar Shapefile!")

# Process each scenario
for scenario_cn, scenario_en in scenarios.items():
    print(f"\nProcessing Scenario: {scenario_cn} ({scenario_en})")
    
    # Define CSV paths
    wind_csv_path = os.path.join(chart_path, "5.2.风机碳回本周期", scenario_cn, "Wind_Carbon_Payback_Time.csv")
    solar_csv_path = os.path.join(chart_path, "5.1.光伏碳回本周期", scenario_cn, "Solar_Carbon_Payback_Time.csv")
    
    # ----------------- Process wind -----------------
    if os.path.exists(wind_csv_path):
        print(f"  Reading Wind CSV: {wind_csv_path}")
        wind_csv = pd.read_csv(wind_csv_path)
        
        # Ensure the CSV fid type is consistent
        if 'fid' in wind_csv.columns:
            wind_csv['fid'] = wind_csv['fid'].astype(int)
            
            # Calculate payback days (CPT_Days)
            if 'CPT_Years' in wind_csv.columns:
                wind_csv['CPT_Days'] = wind_csv['CPT_Years'] * 365.25
            else:
                print("  Warning: 'CPT_Years' column not found in Wind CSV!")

            # Merge data (Left Join: keep all vector geometries; unmatched rows are null)
            wind_merged = wind_gdf.merge(wind_csv, on='fid', how='left')
            
            # Output path
            output_wind_path = os.path.join(chart_path, "5.2.风机碳回本周期", scenario_cn, "Wind_CPBT_Vector.shp")
            print(f"  Saving Wind Vector to: {output_wind_path}")
            
            # Save as Shapefile
            # Note: field names may be truncated (Shapefile limit is 10 characters); GeoPandas handles or warns automatically
            try:
                wind_merged.to_file(output_wind_path, encoding='utf-8')
            except Exception as e:
                print(f"  Error saving Wind Shapefile: {e}")
        else:
            print(f"  Error: 'fid' column not found in Wind CSV!")
    else:
        print(f"  Warning: Wind CSV not found: {wind_csv_path}")

    # ----------------- Process solar -----------------
    if os.path.exists(solar_csv_path):
        print(f"  Reading Solar CSV: {solar_csv_path}")
        solar_csv = pd.read_csv(solar_csv_path)
        
        # Ensure the CSV fid type is consistent
        if 'fid' in solar_csv.columns:
            solar_csv['fid'] = solar_csv['fid'].astype(int)
            
            # Calculate payback days (CPT_Days)
            if 'CPT_Years' in solar_csv.columns:
                solar_csv['CPT_Days'] = solar_csv['CPT_Years'] * 365.25
            else:
                print("  Warning: 'CPT_Years' column not found in Solar CSV!")

            # Merge data (Left Join)
            solar_merged = solar_gdf.merge(solar_csv, on='fid', how='left')
            
            # Output path
            output_solar_path = os.path.join(chart_path, "5.1.光伏碳回本周期", scenario_cn, "Solar_CPBT_Vector.shp")
            print(f"  Saving Solar Vector to: {output_solar_path}")
            
            # Save as Shapefile
            try:
                solar_merged.to_file(output_solar_path, encoding='utf-8')
            except Exception as e:
                print(f"  Error saving Solar Shapefile: {e}")
        else:
            print(f"  Error: 'fid' column not found in Solar CSV!")
    else:
        print(f"  Warning: Solar CSV not found: {solar_csv_path}")

print("\nAll processing complete.")
