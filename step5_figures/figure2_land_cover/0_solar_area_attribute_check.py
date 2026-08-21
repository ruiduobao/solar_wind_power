# -*- coding: utf-8 -*-
"""
Script: 0.光伏面积属性检验是否为真.py
Description: Randomly sample 1000 photovoltaic station polygon features and verify whether their 'area' attribute values are consistent with the true surface area computed from the geometry.
Author: 锐多宝
Date: 2026-02-02
"""

import geopandas as gpd
import pandas as pd
import random
import logging
import os
import sys

# Set up logging configuration
# Output to both console and file
log_file = os.path.join(os.path.dirname(__file__), 'area_check_log.txt')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_area_accuracy(shp_path, sample_size=1000):
    """
    Read the Shapefile, randomly sample features, and compare the area attribute with the reprojected geometry area.
    """
    logger.info(f"Start processing file: {shp_path}")
    
    # 1. Read data
    if not os.path.exists(shp_path):
        logger.error(f"File does not exist: {shp_path}")
        return

    try:
        gdf = gpd.read_file(shp_path)
        logger.info(f"Data read successfully, {len(gdf)} features in total.")
    except Exception as e:
        logger.error(f"Failed to read Shapefile: {e}")
        return

    # 2. Check whether an 'area' field exists
    # Note: Shapefile field names usually have length limits, and may be 'area', 'AREA', 'Area', etc.
    area_col = None
    for col in gdf.columns:
        if col.lower() == 'area':
            area_col = col
            break
    
    if area_col is None:
        logger.error("No attribute field named 'area' (case-insensitive) was found, comparison cannot be performed. Existing fields: " + ", ".join(gdf.columns))
        return
    else:
        logger.info(f"Area attribute field found: {area_col}")

    # 3. Randomly sample features
    total_count = len(gdf)
    if total_count > sample_size:
        # Use random.sample to get indices
        sample_indices = random.sample(range(total_count), sample_size)
        sample_gdf = gdf.iloc[sample_indices].copy()
        logger.info(f"Data size is larger than {sample_size}, {sample_size} samples were randomly drawn.")
    else:
        sample_gdf = gdf.copy()
        logger.info(f"Data size is less than or equal to {sample_size}, using all data for the check.")

    # 4. Compute geometry area
    # If the CRS is geographic (e.g. WGS84, EPSG:4326), computing area directly yields square degrees, which is meaningless.
    # Reprojection to an equal-area projection is required to obtain accurate square-meter areas.
    # Here World Cylindrical Equal Area (EPSG:54034) or Mollweide (ESRI:54009) is used.
    # For generality, EPSG:6933 (EASE-Grid 2.0 Global) is also a good choice, or simply an equal-area projection string.
    
    original_crs = sample_gdf.crs
    logger.info(f"Original CRS: {original_crs}")

    target_crs = 'EPSG:6933' # NSIDC EASE-Grid 2.0 Global
    
    try:
        # Try reprojection
        logger.info(f"Reprojecting to {target_crs} to compute the true surface area...")
        sample_gdf_proj = sample_gdf.to_crs(target_crs)
    except Exception as e:
        logger.warning(f"Reprojection to {target_crs} failed, trying World Cylindrical Equal Area (EPSG:54034)... Error: {e}")
        try:
            target_crs = 'EPSG:54034'
            sample_gdf_proj = sample_gdf.to_crs(target_crs)
        except Exception as e2:
             logger.error(f"Reprojection failed, accurate area cannot be computed. Error: {e2}")
             return

    # Compute calculated area (square meters)
    sample_gdf_proj['calc_area'] = sample_gdf_proj.geometry.area
    
    # 5. Comparison analysis
    # Make sure the attribute column is numeric
    try:
        sample_gdf_proj[area_col] = pd.to_numeric(sample_gdf_proj[area_col])
    except ValueError:
         logger.error(f"Attribute field {area_col} contains non-numeric data, comparison cannot be performed.")
         return

    # Compute the differences
    # Absolute error = |calculated area - attribute area|
    # Relative error = |calculated area - attribute area| / calculated area * 100%
    
    sample_gdf_proj['diff_abs'] = (sample_gdf_proj['calc_area'] - sample_gdf_proj[area_col]).abs()
    sample_gdf_proj['diff_rel_pct'] = (sample_gdf_proj['diff_abs'] / sample_gdf_proj['calc_area']) * 100
    
    # 6. Output result statistics
    logger.info("-" * 30)
    logger.info("Check result statistics:")
    logger.info(f"Mean absolute error: {sample_gdf_proj['diff_abs'].mean():.2f} square meters")
    logger.info(f"Max absolute error: {sample_gdf_proj['diff_abs'].max():.2f} square meters")
    logger.info(f"Mean relative error: {sample_gdf_proj['diff_rel_pct'].mean():.4f}%")
    logger.info(f"Max relative error: {sample_gdf_proj['diff_rel_pct'].max():.4f}%")
    
    # Set a threshold, e.g. relative error > 1% is considered inconsistent
    threshold_pct = 1.0
    large_diff = sample_gdf_proj[sample_gdf_proj['diff_rel_pct'] > threshold_pct]
    
    if len(large_diff) > 0:
        logger.warning(f"Found {len(large_diff)} features whose area difference exceeds {threshold_pct}% !")
        logger.warning("Top 10 samples with the largest differences:")
        top_10 = large_diff.nlargest(10, 'diff_rel_pct')
        for idx, row in top_10.iterrows():
            logger.info(f"FID: {idx}, attribute area: {row[area_col]:.2f}, calculated area: {row['calc_area']:.2f}, relative error: {row['diff_rel_pct']:.2f}%")
    else:
        logger.info(f"All sampled features have area errors within {threshold_pct}%, the attribute data is reliable.")

    logger.info("-" * 30)
    logger.info(f"Detailed log saved to: {log_file}")

if __name__ == "__main__":
    # Input file path
    input_shp = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\solarpower.shp"
    
    check_area_accuracy(input_shp)
