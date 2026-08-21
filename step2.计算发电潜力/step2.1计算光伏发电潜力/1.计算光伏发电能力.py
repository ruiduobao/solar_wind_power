# -*- coding: utf-8 -*-
"""
Calculate solar PV generation capacity
Author: 锐多宝 (ruiduobao)
Date: 2026-01-06
Description:
    Read the solar PV plant Shapefile and the PVOUT GeoTIFF data to compute the
    generation potential of each plant.
    Metrics include:
    1. Longitude and latitude (Lon, Lat)
    2. Area (Area)
    3. Installed capacity (Capacity, estimated from area)
    4. Solar generation potential (Specific Yield, PVOUT)
    5. Annual generation (Annual Generation)
    6. Annual carbon emission avoidance (Avoided Carbon/CO2)
"""

import os
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from shapely.geometry import mapping

# ================= Path configuration =================

# Input data
SOLAR_SHP_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\solarpower.shp"

# PVOUT candidate paths (auto search)
PVOUT_CANDIDATES = [
    r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\光伏发电潜力\World_PVOUT_GISdata_LTAy_AvgDailyTotals_GlobalSolarAtlas-v2_GEOTIFF\PVOUT.tif",
]


# Output data
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.1光伏发电潜力计算"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "Solar_Power_Potential.csv")

# ================= Constants =================

# 1. Power Density
# Used to convert area to installed capacity
# Dynamically match power density by installation_year (MW/km2)
# Data source: User provided
POWER_DENSITY_BY_YEAR_MW_PER_KM2 = {
    2017: 32.0,
    2018: 34.3,
    2019: 36.6,
    2020: 38.9,
    2021: 41.1,
    2022: 43.4,
    2023: 45.7,
    2024: 48.0
}
# Default value (if the year is out of range)
DEFAULT_POWER_DENSITY_MW_PER_KM2 = 45.0

# 2. Grid Emission Factors
# Read from a CSV in the same directory as this script
GRID_EF_CSV_PATH = os.path.join(os.path.dirname(__file__), "Grid_Emission_Factors_2021.csv")

# Load emission factors into a dict
GRID_EMISSION_FACTORS = {}

if os.path.exists(GRID_EF_CSV_PATH):
    try:
        df_ef = pd.read_csv(GRID_EF_CSV_PATH)
        # Clean column name whitespace
        df_ef.columns = [c.strip() for c in df_ef.columns]
        
        # Build dict: Country -> gCO2/kWh
        # Note: the CSV stores gCO2/kWh; we need tCO2/MWh
        # Conversion: 1 gCO2/kWh = 1 kgCO2/MWh = 0.001 tCO2/MWh
        for _, row in df_ef.iterrows():
            country = str(row['Country']).strip()
            # Use the Combined Margin (first data column)
            g_co2_kwh = row['Combined_Margin_gCO2_kWh']
            t_co2_mwh = g_co2_kwh * 0.001
            GRID_EMISSION_FACTORS[country] = t_co2_mwh
            
        print(f"Loaded emission factors for {len(GRID_EMISSION_FACTORS)} countries.")
    except Exception as e:
        print(f"Failed to read emission factor CSV: {e}")
else:
    print(f"Warning: Emission factor file not found {GRID_EF_CSV_PATH}; using defaults.")

GLOBAL_AVG_EMISSION_FACTOR = 0.475 # global average (tCO2/MWh)

# ================= Core functions =================

def get_emission_factor(country):
    """Get the grid emission factor for a country (tCO2/MWh)"""
    if not country:
        return GLOBAL_AVG_EMISSION_FACTOR
    
    country_str = str(country).strip().lower()
    
    # 1. Exact match (case-insensitive)
    for key, val in GRID_EMISSION_FACTORS.items():
        if key.lower() == country_str:
            return val
            
    # 2. Fuzzy match (containment)
    # Prefer longer names to avoid mismatches (e.g. 'Sudan' should not match 'South Sudan')
    matched_val = None
    max_len = 0
    
    for key, val in GRID_EMISSION_FACTORS.items():
        key_lower = key.lower()
        # Check whether country contains key (e.g. 'China' matches 'China (PRC...)')
        # Or key contains country (e.g. 'United States' matches 'United States of America')
        if country_str in key_lower or key_lower in country_str:
            if len(key) > max_len:
                max_len = len(key)
                matched_val = val
                
    if matched_val is not None:
        return matched_val
            
    return GLOBAL_AVG_EMISSION_FACTOR

def calculate_potential():
    # 1. Prepare the output directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    # 2. Read the solar PV vector data
    print(f"Reading solar PV Shapefile: {SOLAR_SHP_PATH}")
    gdf = gpd.read_file(SOLAR_SHP_PATH)
    print(f"Loaded {len(gdf)} solar PV plants.")
    
    # Filter invalid geometries
    gdf = gdf[gdf.geometry.notnull()]
    print(f"{len(gdf)} solar PV plants remain after filtering invalid geometries.")

    # Ensure fid and area exist
    if 'fid' not in gdf.columns or 'area' not in gdf.columns:
        print("Error: The Shapefile is missing 'fid' or 'area' fields.")
        return

    # 3. Read the PVOUT raster data
    pvout_path = None
    for path in PVOUT_CANDIDATES:
        if os.path.exists(path):
            pvout_path = path
            break
            
    if not pvout_path:
        print(f"Error: PVOUT.tif not found in any of the following paths:")
        for p in PVOUT_CANDIDATES:
            print(f"  - {p}")
        print("Please make sure the PVOUT GeoTIFF is downloaded and placed in one of the paths above.")
        return

    print(f"Reading PVOUT Raster: {pvout_path}")

    results = []

    with rasterio.open(pvout_path) as src:
        print("Calculating generation potential for each plant (this may take a while)...")
        
        # Check CRS and reproject if necessary
        # Note: rasterio mask requires the geometry and the raster to be in the same CRS
        # Assume PVOUT is WGS84 (EPSG:4326), as most global datasets are
        if gdf.crs != src.crs:
            print(f"Converting Shapefile CRS from {gdf.crs} to {src.crs} ...")
            gdf_proj = gdf.to_crs(src.crs)
        else:
            gdf_proj = gdf

        count = 0
        total = len(gdf_proj)

        for idx, row in gdf_proj.iterrows():
            fid = row['fid']
            country = row['COUNTRY']
            area_m2 = row['area'] # assume area is in square meters; depends on the source projection
            
            # Get the geometry
            geom = row['geometry']
            
            if geom is None or geom.is_empty:
                continue

            # Compute the centroid (lon/lat)
            # If WGS84, take the centroid directly; if projected, convert back to WGS84 for the centroid
            centroid = geom.centroid
            if src.crs == "EPSG:4326":
                lon, lat = centroid.x, centroid.y
            else:
                # For simplicity, use the converted geom (already in src.crs)
                # If src.crs is WGS84, then these are lon/lat
                lon, lat = centroid.x, centroid.y

            # Extract the PVOUT value
            try:
                # Use the geometry mask to extract raster values
                try:
                    out_image, out_transform = mask(src, [geom], crop=True)
                    # PVOUT unit: kWh/kWp/day
                    # Handle nodata (usually negative or extreme; assume valid values > 0)
                    valid_data = out_image[out_image > 0]
                    
                    if valid_data.size > 0:
                        pvout_val = np.mean(valid_data)
                    else:
                        raise ValueError("No valid data in mask")
                        
                except (ValueError, Exception):
                    # If the polygon is too small to hit a pixel center, or does not overlap, sample the value
                    # Use sample
                    sample_gen = src.sample([(lon, lat)])
                    try:
                        val = next(sample_gen)[0]
                        if val > 0:
                            pvout_val = val
                        else:
                            pvout_val = 0 # no-data region
                    except StopIteration:
                        pvout_val = 0
                        
            except Exception as e:
                # Only print exceptions other than overlap errors to avoid flooding the console
                if "overlap" not in str(e):
                    print(f"FID {fid} PVOUT extraction failed: {e}")
                pvout_val = 0

            # --- Compute metrics ---
            
            # 1. Installed capacity (MW)
            # Get the power density by construction year (constructi)
            # If the raw data has no capacity, estimate it from the area
            try:
                install_year = int(row['constructi'])
            except (ValueError, TypeError):
                install_year = 0 # invalid year
            
            # Get power density (MW/km2) -> convert to MW/m2
            power_density_mw_km2 = POWER_DENSITY_BY_YEAR_MW_PER_KM2.get(install_year, DEFAULT_POWER_DENSITY_MW_PER_KM2)
            power_density_mw_m2 = power_density_mw_km2 / 1_000_000
            
            capacity_mw = area_m2 * power_density_mw_m2
            
            # 2. Annual generation (MWh)
            # Formula: Capacity (MW) * PVOUT (kWh/kWp/day) * 365.25
            # Unit check: MW * kWh/kW = MWh
            if pvout_val > 0:
                annual_gen_mwh = capacity_mw * pvout_val * 365.25
            else:
                annual_gen_mwh = 0
                
            # 3. Carbon emission avoidance
            ef = get_emission_factor(country)
            avoided_co2_ton = annual_gen_mwh * ef
            avoided_c_ton = avoided_co2_ton * (12 / 44) # C atomic weight 12, CO2 molecular weight 44

            results.append({
                'fid': fid,
                'lon': lon,
                'lat': lat,
                'country': country,
                'area_m2': area_m2,
                'capacity_mw_est': round(capacity_mw, 4),
                'pvout_daily_kwh_kwp': round(pvout_val, 4),
                'annual_gen_mwh': round(annual_gen_mwh, 2),
                'avoided_co2_ton': round(avoided_co2_ton, 2),
                'avoided_c_ton': round(avoided_c_ton, 2),
                'grid_ef': ef
            })
            
            count += 1
            if count % 1000 == 0:
                print(f"Progress: {count}/{total}...", end='\r')

    print("\nCalculation finished; saving results...")
    
    # Convert to DataFrame
    df_res = pd.DataFrame(results)
    
    # Save CSV
    df_res.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Results saved to: {OUTPUT_CSV}")
    print(f"Total processed: {len(df_res)} records")

if __name__ == "__main__":
    calculate_potential()
