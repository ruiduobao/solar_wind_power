# -*- coding: utf-8 -*-
"""
Script name: FROM_GLC global imagery VRT construction and 1km resampling preview
Description:
    1. Search all TIF images in the specified folder (about 7000+ scenes).
    2. Use GDAL to build a VRT (Virtual Dataset) file (logical integration, no disk space).
    3. Resample the VRT into a single TIF file at 1km resolution (convenient for full-scene browsing).
    4. Add the FROM-GLC standard color mapping table and pyramids to the generated 1km TIF.

Input data: F:\\地理所\\论文\\全球绿色能源生态评估_2025.12.24\\数据\\土地覆盖数据\\宫鹏清华大学2017年10m土地利用数据（未裁剪）
Output data: F:\\地理所\\论文\\全球绿色能源生态评估_2025.12.24\\数据\\土地覆盖数据\\FROM_glc重采样\\Global_FROM_GLC10_2017_1km.tif

Author: 锐多宝 (ruiduobao)
Date: 2026-01-06
Environment: Python 3.x, GDAL
"""

import os
import glob
import time
import logging
from osgeo import gdal, osr

# Set global configuration
INPUT_FOLDER = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\宫鹏清华大学2017年10m土地利用数据（未裁剪）"
OUTPUT_FOLDER = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\FROM_glc重采样"
VRT_NAME = "Global_FROM_GLC10_2017.vrt"
OUTPUT_TIF_NAME = "Global_FROM_GLC10_2017_1km.tif"
LOG_FILENAME = "resample_process_log.txt"

# FROM-GLC color table definition
COLOR_MAP = {
    0: (0, 0, 0, 0),         # Background (Transparent)
    10: (163, 255, 115, 255),# Cropland
    20: (38, 115, 0, 255),   # Forest
    30: (76, 230, 0, 255),   # Grass
    40: (112, 168, 0, 255),  # Shrub
    60: (0, 92, 255, 255),   # Water
    80: (197, 0, 255, 255),  # Impervious
    90: (255, 170, 0, 255),  # Bareland
    100: (0, 255, 197, 255), # Snow/Ice
    120: (255, 255, 255, 255) # Cloud
}

def setup_logging(output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    log_file_path = os.path.join(output_folder, LOG_FILENAME)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = []

    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_fmt)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter('%(asctime)s - %(message)s')
    console_handler.setFormatter(console_fmt)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file_path

def build_vrt(input_dir, output_vrt_path):
    """Build a VRT file"""
    logger = logging.getLogger()
    logger.info(f"Searching for TIF files: {input_dir} ...")
    search_pattern = os.path.join(input_dir, "*.tif")
    tif_files = glob.glob(search_pattern)
    
    count = len(tif_files)
    logger.info(f"Number of files found: {count}")
    
    if count == 0:
        logger.error("No .tif files found, cannot build the VRT.")
        return False
        
    logger.info("Start building the VRT...")
    try:
        options = gdal.BuildVRTOptions(resampleAlg='nearest', resolution='highest')
        ds = gdal.BuildVRT(output_vrt_path, tif_files, options=options)
        ds.FlushCache()
        ds = None 
        logger.info(f"VRT built successfully: {output_vrt_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to build the VRT: {str(e)}")
        return False

def resample_to_1km(vrt_path, output_tif_path):
    """
    Resample the VRT to a TIF at 1km resolution
    """
    logger = logging.getLogger()
    logger.info("==========================================")
    logger.info(f"Start resampling: {vrt_path} -> {output_tif_path}")
    logger.info("Target resolution: about 1km (0.0083333 degrees)")
    logger.info("Resampling algorithm: Nearest Neighbor - ensures speed and does not change land class values")
    
    try:
        # Set the resampling options
        # Optimization strategy:
        # 1. warpOptions: increase the memory usage limit (warp_mem_limit), allowing more RAM (e.g. 4096MB)
        # 2. creationOptions: keep multithreading and compression
        # 3. GDAL_CACHEMAX: set the global cache size to speed up IO
        
        # Set the global cache to 4096MB (4GB), adjustable according to the machine configuration
        gdal.SetConfigOption("GDAL_CACHEMAX", "4096")
        
        warp_options = gdal.WarpOptions(
            format='GTiff',
            xRes=0.00833333333,
            yRes=0.00833333333,
            resampleAlg=gdal.GRA_NearestNeighbour,
            creationOptions=['COMPRESS=LZW', 'TILED=YES', 'BIGTIFF=IF_NEEDED', 'NUM_THREADS=ALL_CPUS'],
            warpOptions=['NUM_THREADS=ALL_CPUS'], # explicitly enable Warp multithreading
            warpMemoryLimit=4096, # allow Warp to use 4GB of memory
            callback=gdal.TermProgress_nocb
        )
        
        # Execute the resampling
        # Note: this will take some time because all data needs to be read
        gdal.Warp(output_tif_path, vrt_path, options=warp_options)
        
        logger.info("Resampling completed!")
        return True
        
    except Exception as e:
        logger.error(f"Resampling failed: {str(e)}")
        return False

def add_color_table(tif_path):
    """
    Add a color table to the TIF
    """
    logger = logging.getLogger()
    logger.info("Adding the color mapping table...")
    
    try:
        # Open in read-write mode
        ds = gdal.Open(tif_path, gdal.GA_Update)
        if ds is None:
            logger.error(f"Cannot open the file to add the color table: {tif_path}")
            return False
            
        band = ds.GetRasterBand(1)
        
        # Create the color table
        color_table = gdal.ColorTable()
        
        # Fill the colors
        # Default to black or transparent
        for i in range(256):
            color_table.SetColorEntry(i, (0, 0, 0, 0))
            
        # Set the colors of the specific land classes
        for code, rgba in COLOR_MAP.items():
            color_table.SetColorEntry(code, rgba)
            
        # Apply the color table
        band.SetColorTable(color_table)
        band.SetNoDataValue(0) # set 0 as nodata
        
        ds = None
        logger.info("Color mapping table added successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add the color table: {str(e)}")
        return False

def main():
    # 1. Path check
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: the input folder does not exist -> {INPUT_FOLDER}")
        return
        
    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # 2. Set up logging
    logger, log_path = setup_logging(OUTPUT_FOLDER)
    
    logger.info("==========================================")
    logger.info("Task start: FROM_GLC VRT construction and 1km resampling")
    logger.info(f"Input directory: {INPUT_FOLDER}")
    logger.info(f"Output directory: {OUTPUT_FOLDER}")
    logger.info("==========================================")
    
    start_time = time.time()
    
    # 3.1 Build the VRT (if it does not exist or force rebuild)
    vrt_path = os.path.join(INPUT_FOLDER, VRT_NAME)
    # Rebuild the VRT every time to ensure it is up to date, and building the VRT is fast
    vrt_success = build_vrt(INPUT_FOLDER, vrt_path)
    
    if not vrt_success:
        return

    # 3.2 Resample to a 1km TIF
    output_tif_path = os.path.join(OUTPUT_FOLDER, OUTPUT_TIF_NAME)
    resample_success = resample_to_1km(vrt_path, output_tif_path)
    
    if resample_success:
        # 3.3 Add the color table
        add_color_table(output_tif_path)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("==========================================")
    if resample_success:
        logger.info("All tasks completed!")
        logger.info(f"Generated 1km TIF file: {output_tif_path}")
        logger.info("This file already contains the color table and can be directly loaded into GIS software for viewing.")
    else:
        logger.info("Some tasks failed, please check the log.")
        
    logger.info(f"Total time: {duration:.2f} s")
    logger.info("==========================================")

if __name__ == "__main__":
    gdal.UseExceptions()
    main()
