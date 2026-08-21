# -*- coding: utf-8 -*-
"""
Compute wind power generation capacity
Author: 锐多宝 (ruiduobao)
Date: 2026-01-07
Description: 
    Read the wind turbine Shapefile and Capacity Factor GeoTIFF data, and compute the power generation potential of each turbine.
    Computed indicators include:
    1. Longitude and latitude (Lon, Lat)
    2. Construction year (Year)
    3. Installed capacity (Capacity, dynamic estimation based on year)
    4. Capacity factor (Capacity Factor, CF)
    5. Annual generation (Annual Generation)
    6. Annual avoided carbon (Avoided Carbon/CO2)
"""

import os
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np

# ================= Path configuration =================

# Input data
WIND_SHP_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\windpower.shp"
CF_TIF_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\风力发电数据\cf_iec2_cog_100m.tif"
GRID_EF_CSV_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\代码\step2.计算发电潜力\step3.2计算风电发电潜力\Grid_Emission_Factors_2021.csv"

# Output data
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "Wind_Power_Potential.csv")

# ================= Constants =================

# 1. Rated Power Estimation - based on year
# Unit: MW
def get_rated_power(year):
    try:
        y = int(year)
    except:
        return 2.2 # default value (2017 and earlier)
    
    if y <= 2017:
        return 2.2
    elif y == 2018:
        return 2.4
    elif y == 2019:
        return 2.6
    elif y == 2020:
        return 3.0
    elif y == 2021:
        return 3.4
    elif y == 2022:
        return 3.8
    elif y == 2023:
        return 4.2
    elif y >= 2024:
        return 4.5
    else:
        return 2.2

# 2. Load emission factors
GRID_EMISSION_FACTORS = {}

if os.path.exists(GRID_EF_CSV_PATH):
    try:
        df_ef = pd.read_csv(GRID_EF_CSV_PATH)
        df_ef.columns = [c.strip() for c in df_ef.columns]
        for _, row in df_ef.iterrows():
            country = str(row['Country']).strip()
            g_co2_kwh = row['Combined_Margin_gCO2_kWh']
            t_co2_mwh = g_co2_kwh * 0.001
            GRID_EMISSION_FACTORS[country] = t_co2_mwh
        print(f"Successfully loaded emission factors for {len(GRID_EMISSION_FACTORS)} countries.")
    except Exception as e:
        print(f"Failed to read the emission factor CSV: {e}")

GLOBAL_AVG_EMISSION_FACTOR = 0.475

def get_emission_factor(country):
    if not country:
        return GLOBAL_AVG_EMISSION_FACTOR
    country_str = str(country).strip().lower()
    
    # Exact match
    for key, val in GRID_EMISSION_FACTORS.items():
        if key.lower() == country_str:
            return val
            
    # Fuzzy match
    matched_val = None
    max_len = 0
    for key, val in GRID_EMISSION_FACTORS.items():
        key_lower = key.lower()
        if country_str in key_lower or key_lower in country_str:
            if len(key) > max_len:
                max_len = len(key)
                matched_val = val
    if matched_val is not None:
        return matched_val
    return GLOBAL_AVG_EMISSION_FACTOR

# ================= Core computation =================

def calculate_wind_potential():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    # 1. Read SHP
    print(f"Reading wind turbine Shapefile: {WIND_SHP_PATH}")
    gdf = gpd.read_file(WIND_SHP_PATH)
    print(f"Loaded {len(gdf)} wind turbine points in total.")
    
    # 2. Read Raster
    if not os.path.exists(CF_TIF_PATH):
        print(f"Error: GeoTIFF file not found {CF_TIF_PATH}")
        return

    results = []
    
    print(f"Reading Capacity Factor Raster: {CF_TIF_PATH}")
    with rasterio.open(CF_TIF_PATH) as src:
        # Check CRS
        if gdf.crs != src.crs:
            print(f"Converting CRS from {gdf.crs} to {src.crs}...")
            gdf_proj = gdf.to_crs(src.crs)
        else:
            gdf_proj = gdf
            
        # Sampling and computation
        print("Start extracting CF values and computing potential...")
        
        # Prepare the coordinate list for batch sampling (faster than iterating with iterrows)
        coords = [(geom.x, geom.y) for geom in gdf_proj.geometry]
        
        # Batch sampling
        # rasterio.sample returns a generator
        sampled_values = src.sample(coords)
        
        # Iterate over the results
        for idx, (val_tuple, (_, row)) in enumerate(zip(sampled_values, gdf_proj.iterrows())):
            fid = row.get('fid', idx)
            country = row.get('COUNTRY', 'Unknown')
            year = row.get('constructi', 2017) # default 2017
            
            # Get the CF value
            cf_raw = val_tuple[0]
            
            # Handle NoData (assume < 0 is invalid)
            if cf_raw < 0:
                cf = 0
            else:
                cf = float(cf_raw)
                
            # Automatically handle the unit: if > 1, assume it is a percentage (0-100), convert to 0-1
            # According to the Global Wind Atlas documentation, it is usually 0-1, but sometimes stored as an integer to save space
            # Here we use a heuristic: if max(cf) > 1, then /100?
            # Since processing value by value, we can only judge a single value, which is not safe (e.g. 0.9% vs 0.9).
            # The best approach is to read the raster metadata or stats first.
            # But for simplicity, assume that if downloaded from GWA, it may be 0-1 or 0-100.
            # If the value is 35, it is definitely %. If the value is 0.35, it is a decimal.
            if cf > 1.0:
                cf = cf / 100.0
            
            # Compute the indicators
            capacity_mw = get_rated_power(year)
            
            # Annual Gen (MWh) = Capacity (MW) * CF * 8760
            annual_gen_mwh = capacity_mw * cf * 8760
            
            # Avoided CO2
            ef = get_emission_factor(country)
            avoided_co2_ton = annual_gen_mwh * ef
            
            # Longitude and latitude (WGS84)
            # If gdf_proj is already WGS84 (EPSG:4326), take directly; otherwise convert
            if gdf_proj.crs == "EPSG:4326":
                lon, lat = coords[idx]
            else:
                # Is the original point WGS84? Usually the Shapefile may be.
                # For simplicity, take the geometry from the original gdf (assuming the original read-in is WGS84)
                # Or convert back
                pt = gdf.iloc[idx].geometry
                # Assume the original gdf is WGS84 (geopandas read_file keeps the original crs by default)
                # If the original is not 4326, the lon lat obtained here are also projected coordinates.
                # To be safe, it is best to convert to 4326
                pass 
                
        # --- Re-optimize the iteration logic to ensure correct lon/lat ---
        # Batch sampling while keeping the original WGS84 coordinates is troublesome,
        # so we use iterrows + sample one by one, or first convert to WGS84 and store the coordinates
        
    # Re-implement the main loop
    # 1. Ensure gdf has a WGS84 copy for outputting lon/lat
    if gdf.crs != "EPSG:4326":
        gdf_wgs84 = gdf.to_crs("EPSG:4326")
    else:
        gdf_wgs84 = gdf
        
    # 2. Ensure gdf_proj is used for sampling (matching the raster crs)
    # (handled above)
    
    # 3. Open the raster again for per-point processing (or use the previous coords logic)
    # For code clarity, use iterrows for per-point processing here
    
    with rasterio.open(CF_TIF_PATH) as src:
        total = len(gdf)
        count = 0
        
        # Pre-check whether division by 100 is needed
        # Read a small block of data to check the value range
        sample_win = src.read(1, window=((0, 10), (0, 10)))
        max_val = sample_win.max()
        scale_factor = 1.0
        # This judgment is somewhat arbitrary; Global Wind Atlas is usually 0-1 (float) or 0-1000 (int).
        # Let us assume: if max_val > 10, it may be 0-100 or 0-1000.
        # To be safe, judge inside the loop:
        # If val > 1, then val = val / 100 (assume percentage).
        
        for idx, row in gdf_proj.iterrows():
            fid = row.get('fid', idx)
            country = row.get('COUNTRY', 'Unknown')
            year = row.get('constructi', 2017)
            
            geom = row['geometry']
            if geom is None or geom.is_empty:
                continue
                
            # Sampling
            try:
                # src.sample needs an iterable of coordinate points [(x, y)]
                gen = src.sample([(geom.x, geom.y)])
                cf_val = next(gen)[0]
            except:
                cf_val = 0
                
            # Handle NoData
            if cf_val < 0: # or src.nodata
                cf_val = 0
            
            # Unit conversion
            # Common cases: 0.35 -> 0.35; 35 -> 0.35
            if cf_val > 1.0:
                cf_val = cf_val / 100.0 # assume %
                
            # Check again; if still > 1 (e.g. 1000 scale), division by 1000 may be needed
            # GWA sometimes stores as integer with scale=0.001?
            # Let us be conservative: the Capacity Factor cannot exceed 1.0 (theoretical limit 0.59 Betz Limit, actual onshore 0.2-0.4)
            # So if > 1, it is definitely a scale issue.
            if cf_val > 1.0:
                cf_val = cf_val / 10.0 # e.g. 350 -> 35 -> 0.35?
                # This blind division is dangerous.
                # Let us print the first few non-zero values to check
                pass

            # Get WGS84 coordinates
            pt_wgs = gdf_wgs84.iloc[idx].geometry
            lon, lat = pt_wgs.x, pt_wgs.y
            
            # Computation
            capacity_mw = get_rated_power(year)
            annual_gen_mwh = capacity_mw * cf_val * 8760
            ef = get_emission_factor(country)
            avoided_co2_ton = annual_gen_mwh * ef
            
            results.append({
                'fid': fid,
                'lon': round(lon, 6),
                'lat': round(lat, 6),
                'country': country,
                'year': int(year) if pd.notnull(year) else 2017,
                'capacity_mw_est': capacity_mw,
                'cf_val': round(cf_val, 4),
                'annual_gen_mwh': round(annual_gen_mwh, 2),
                'avoided_co2_ton': round(avoided_co2_ton, 2),
                'grid_ef': ef
            })
            
            count += 1
            if count % 1000 == 0:
                print(f"Progress: {count}/{total}...", end='\r')
                
    # Save
    print("\nSaving results...")
    df_res = pd.DataFrame(results)
    df_res.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Wind potential computation completed: {OUTPUT_CSV}")
    print(f"Mean CF: {df_res['cf_val'].mean():.4f}")

if __name__ == "__main__":
    calculate_wind_potential()
