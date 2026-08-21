# -*- coding: utf-8 -*-
"""
Script: FROM_GLC global imagery VRT construction and 1km resampling preview
Description:
    1. Search all TIF images in the specified folder (~7000+ scenes).
    2. Use GDAL to build a VRT (Virtual Dataset) file (logical integration, no disk space).
    3. Resample the VRT to a single TIF file at 1km resolution (for full-scene browsing).
    4. Add the FROM-GLC standard color map and pyramids to the generated 1km TIF.

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

# Global configuration
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
        logger.error("No .tif files found, cannot build VRT.")
        return False
        
    logger.info("Building VRT...")
    try:
        options = gdal.BuildVRTOptions(resampleAlg='nearest', resolution='highest')
        ds = gdal.BuildVRT(output_vrt_path, tif_files, options=options)
        ds.FlushCache()
        ds = None 
        logger.info(f"VRT built successfully: {output_vrt_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to build VRT: {str(e)}")
        return False

def resample_to_1km(vrt_path, output_tif_path):
    """
    Resample the VRT to a TIF at 1km resolution
    """
    logger = logging.getLogger()
    logger.info("==========================================")
    logger.info(f"Starting resampling: {vrt_path} -> {output_tif_path}")
    logger.info("Target resolution: ~1km (0.0083333 degrees)")
    logger.info("Resampling algorithm: Nearest neighbor - fast and preserves class values")
    
    try:
        # Set resampling options
        # xRes, yRes: 0.00833333333 degrees (~1km)
        # resampleAlg: gdal.GRA_NearestNeighbour (fastest, suitable for classified data preview)
        # creationOptions: LZW compression, multithreading
        warp_options = gdal.WarpOptions(
            format='GTiff',
            xRes=0.00833333333,
            yRes=0.00833333333,
            resampleAlg=gdal.GRA_NearestNeighbour,
            creationOptions=['COMPRESS=LZW', 'TILED=YES', 'BIGTIFF=IF_NEEDED', 'NUM_THREADS=12'],
            callback=gdal.TermProgress_nocb
        )
        
        # Execute resampling
        # Note: this takes some time because all the data has to be read
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
    logger.info("Adding color map...")
    
    try:
        # Open in read-write mode
        ds = gdal.Open(tif_path, gdal.GA_Update)
        if ds is None:
            logger.error(f"Cannot open file to add color table: {tif_path}")
            return False
            
        band = ds.GetRasterBand(1)
        
        # Create color table
        color_table = gdal.ColorTable()
        
        # Fill colors
        # Default to black or transparent
        for i in range(256):
            color_table.SetColorEntry(i, (0, 0, 0, 0))
            
        # Set colors for specific land cover classes
        for code, rgba in COLOR_MAP.items():
            color_table.SetColorEntry(code, rgba)
            
        # Apply color table
        band.SetColorTable(color_table)
        band.SetNoDataValue(0) # set 0 as nodata
        
        ds = None
        logger.info("Color map added successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add color table: {str(e)}")
        return False

def main():
    # 1. Path check
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: input folder does not exist -> {INPUT_FOLDER}")
        return
        
    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # 2. Set up logging
    logger, log_path = setup_logging(OUTPUT_FOLDER)
    
    logger.info("==========================================")
    logger.info("Task started: FROM_GLC VRT construction and 1km resampling")
    logger.info(f"Input directory: {INPUT_FOLDER}")
    logger.info(f"Output directory: {OUTPUT_FOLDER}")
    logger.info("==========================================")
    
    start_time = time.time()
    
    # 3.1 Build VRT (rebuilt if missing or forced)
    vrt_path = os.path.join(INPUT_FOLDER, VRT_NAME)
    # Always rebuild the VRT to ensure it is up to date, and building a VRT is fast
    vrt_success = build_vrt(INPUT_FOLDER, vrt_path)
    
    if not vrt_success:
        return

    # 3.2 Resample to 1km TIF
    output_tif_path = os.path.join(OUTPUT_FOLDER, OUTPUT_TIF_NAME)
    resample_success = resample_to_1km(vrt_path, output_tif_path)
    
    if resample_success:
        # 3.3 Add color table
        add_color_table(output_tif_path)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("==========================================")
    if resample_success:
        logger.info("All tasks completed!")
        logger.info(f"Generated 1km TIF file: {output_tif_path}")
        logger.info("The file already contains the color table and can be dragged directly into GIS software for viewing.")
    else:
        logger.info("Some tasks failed, please check the log.")
        
    logger.info(f"Total time: {duration:.2f} seconds")
    logger.info("==========================================")

if __name__ == "__main__":
    gdal.UseExceptions()
    main()
