# -*- coding: utf-8 -*-
"""
Script name: Obtain the spatial extent of FROM_GLC images and generate a Shapefile
Function description:
    1. Iterate over all TIF images in the specified folder.
    2. Use multi-process parallel reading to get the spatial extent (bounding coordinates) of each TIF image.
    3. Create a Shapefile containing the bounding polygon and file name attribute of each image.
    4. Output the processing log to the console and a log file.

Input data: .tif files under F:\\地理所\\论文\\全球绿色能源生态评估_2025.12.24\\数据\\土地覆盖数据\\FROM_glc覆盖范围
Output data: FROM_GLC_Index.shp in the same directory

Author: 锐多宝 (ruiduobao)
Date: 2026-01-06
Environment: Python 3.x, GDAL
"""

import os
import glob
import time
import logging
import datetime
from multiprocessing import Pool, cpu_count
from osgeo import gdal, ogr, osr

# Set the global configuration
INPUT_FOLDER = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\宫鹏清华大学2017年10m土地利用数据（未裁剪）"
OUTPUT_SHP_NAME = "FROM_GLC_Index.shp"
LOG_FILENAME = "process_log.txt"

def setup_logging(output_folder):
    """
    Configure the logging system, outputting to both the console and a file
    """
    log_file_path = os.path.join(output_folder, LOG_FILENAME)
    
    # Create the logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear old handlers
    logger.handlers = []

    # Create a file handler
    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_fmt)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter('%(asctime)s - %(message)s')
    console_handler.setFormatter(console_fmt)
    
    # Add the handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file_path

def get_raster_extent(tif_path):
    """
    Read the extent information of a single raster file
    
    Parameters:
        tif_path: absolute path of the TIF file
    
    Returns:
        dict: containing the file name, bounding coordinates and projection WKT; returns None on failure
    """
    try:
        # Open in read-only mode
        ds = gdal.Open(tif_path, gdal.GA_ReadOnly)
        if not ds:
            return {"error": f"Cannot open file: {tif_path}"}

        # Get the geotransform parameters
        # geotransform[0] = top-left x
        # geotransform[1] = pixel width (east-west)
        # geotransform[2] = rotation parameter (usually 0)
        # geotransform[3] = top-left y
        # geotransform[4] = rotation parameter (usually 0)
        # geotransform[5] = pixel height (north-south, usually negative)
        gt = ds.GetGeoTransform()
        width = ds.RasterXSize
        height = ds.RasterYSize
        
        min_x = gt[0]
        max_x = gt[0] + width * gt[1] + height * gt[2]
        max_y = gt[3]
        min_y = gt[3] + width * gt[4] + height * gt[5]
        
        # Get the projection information
        proj = ds.GetProjection()
        
        filename = os.path.basename(tif_path)
        
        ds = None # Close the dataset
        
        return {
            "filename": filename,
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "wkt": proj,
            "path": tif_path
        }
        
    except Exception as e:
        return {"error": f"Processing error {tif_path}: {str(e)}"}

def create_index_shapefile(result_list, output_path):
    """
    Create a Shapefile from the extracted result list
    """
    # Get the driver
    driver = ogr.GetDriverByName("ESRI Shapefile")
    
    # Delete the file if it exists
    if os.path.exists(output_path):
        driver.DeleteDataSource(output_path)
        
    # Create the data source
    ds = driver.CreateDataSource(output_path)
    
    # Define the spatial reference
    # Try the projection of the first successful result; default to WGS84 if none
    srs = osr.SpatialReference()
    valid_results = [r for r in result_list if "error" not in r]
    
    if valid_results and valid_results[0]['wkt']:
        srs.ImportFromWkt(valid_results[0]['wkt'])
    else:
        # Default WGS84
        srs.ImportFromEPSG(4326) 
        
    # Create the layer
    layer_name = os.path.splitext(os.path.basename(output_path))[0]
    layer = ds.CreateLayer(layer_name, srs, ogr.wkbPolygon)
    
    # Create the attribute field: file name
    field_name = ogr.FieldDefn("FileName", ogr.OFTString)
    field_name.SetWidth(254)
    layer.CreateField(field_name)
    
    # Create the attribute field: full path
    field_path = ogr.FieldDefn("Path", ogr.OFTString)
    field_path.SetWidth(254)
    layer.CreateField(field_path)

    count = 0
    for res in result_list:
        if "error" in res:
            logging.error(res["error"])
            continue
            
        # Create the ring
        ring = ogr.Geometry(ogr.wkbLinearRing)
        # Close the polygon: top-left -> top-right -> bottom-right -> bottom-left -> top-left
        # min_x, max_y (top-left)
        # max_x, max_y (top-right)
        # max_x, min_y (bottom-right)
        # min_x, min_y (bottom-left)
        
        ring.AddPoint(res['min_x'], res['max_y'])
        ring.AddPoint(res['max_x'], res['max_y'])
        ring.AddPoint(res['max_x'], res['min_y'])
        ring.AddPoint(res['min_x'], res['min_y'])
        ring.AddPoint(res['min_x'], res['max_y']) # Close
        
        # Create the polygon
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        
        # Create the feature
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(poly)
        feature.SetField("FileName", res['filename'])
        feature.SetField("Path", res['path'])
        
        # Write to the layer
        layer.CreateFeature(feature)
        
        # Clean up
        feature = None
        count += 1
        
    ds = None # Close and save
    return count

def main():
    # 1. Set the input/output paths
    input_dir = INPUT_FOLDER
    output_shp = os.path.join(INPUT_FOLDER, OUTPUT_SHP_NAME)
    
    # Ensure the input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: input directory does not exist -> {input_dir}")
        return

    # 2. Set up logging
    logger, log_path = setup_logging(input_dir)
    logger.info("==========================================")
    logger.info(f"Starting task: generating the image index Shapefile")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output file: {output_shp}")
    logger.info("==========================================")

    # 3. Get all TIF files
    search_pattern = os.path.join(input_dir, "*.tif")
    tif_files = glob.glob(search_pattern)
    
    total_files = len(tif_files)
    logger.info(f"Number of TIF files found: {total_files}")
    
    if total_files == 0:
        logger.warning("No .tif files found; the program ends.")
        return

    # 4. Multi-process processing
    start_time = time.time()
    
    # Determine the number of processes, reserving one core for the system
    num_processes = max(1, cpu_count() - 1)
    logger.info(f"Starting multi-process processing, using cores: {num_processes}")
    
    results = []
    # Use Pool for parallel processing
    with Pool(processes=num_processes) as pool:
        # imap_unordered may be slightly faster, but the list is small here, so direct map works
        # Add a progress display
        for i, res in enumerate(pool.imap_unordered(get_raster_extent, tif_files), 1):
            results.append(res)
            if i % 10 == 0 or i == total_files:
                print(f"Progress: {i}/{total_files} ({(i/total_files)*100:.1f}%)", end='\r')
    
    print("") # New line
    logger.info("Metadata reading complete; starting to generate the Shapefile...")

    # 5. Generate the Shapefile
    success_count = create_index_shapefile(results, output_shp)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("==========================================")
    logger.info(f"Processing complete!")
    logger.info(f"Number of features successfully generated: {success_count}")
    logger.info(f"Total elapsed time: {duration:.2f} seconds")
    logger.info(f"Log file saved to: {log_path}")
    logger.info("==========================================")

if __name__ == "__main__":
    # To support multi-process on Windows, it must run under if __name__ == "__main__":
    gdal.UseExceptions() # Enable GDAL exception capture
    main()
