# -*- coding: utf-8 -*-
"""
Biomass carbon NetCDF to GeoTIFF conversion tool (blocked parallel ultra-fast version)
Author: 锐多宝 (Trae AI)
Date: 2026-01-07

Functions:
    Split the global NetCDF into N x M tiles, and convert them in parallel with multiprocessing.
    This method maximizes the use of the SSD's random read/write capability and multi-core CPU, avoiding the single-file write lock bottleneck.
    
    Outputs:
    1. Create a tiles folder in the target directory to store the tiled TIFs.
    2. Generate a .vrt (virtual raster) file at the target path, which can be used directly in GIS as a complete image.
    3. (Optional) Finally convert the VRT to a single large TIF (if needed).

"""

import os
import subprocess
import time
import multiprocessing
import math
import glob

def get_gdal_src_path(input_nc):
    """Get the GDAL read path (subdataset) of the NetCDF"""
    try:
        # Pay attention to the encoding on Windows, try utf-8 or gbk
        info_cmd = ['gdalinfo', input_nc]
        # creationflags=0x08000000 (CREATE_NO_WINDOW) prevents a cmd window from popping up
        result = subprocess.run(info_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', creationflags=0x08000000)
        output = result.stdout
        
        subdataset_name = None
        for line in output.splitlines():
            if "SUBDATASET_1_NAME=" in line:
                subdataset_name = line.split("=")[1].strip()
                break
        
        if subdataset_name:
            return subdataset_name
        else:
            return f'NETCDF:"{input_nc}":agb' # default guess
            
    except Exception as e:
        print(f"Failed to get the metadata: {e}")
        return input_nc

def convert_tile_task(args):
    """Conversion task of a single tile"""
    src_path, tile_path, ulx, uly, lrx, lry = args
    
    if os.path.exists(tile_path):
        return True, f"Skipped {os.path.basename(tile_path)}"

    cmd = [
        'gdal_translate',
        src_path,
        tile_path,
        '-of', 'GTiff',
        '-projwin', str(ulx), str(uly), str(lrx), str(lry), # clipping extent
        '-co', 'COMPRESS=LZW',
        '-co', 'PREDICTOR=2',
        '-co', 'TILED=YES',
        '-a_srs', 'EPSG:4326',
        '-ot', 'Float32',
        '-q' # silent mode
    ]
    
    try:
        subprocess.run(cmd, check=True, creationflags=0x08000000)
        return True, f"Finished {os.path.basename(tile_path)}"
    except subprocess.CalledProcessError as e:
        return False, f"Error converting {os.path.basename(tile_path)}: {e}"

def convert_nc_to_tif_blocked(input_nc, output_tif, num_processes=16):
    # 1. Prepare the paths
    if not os.path.exists(input_nc):
        print(f"Error: input file not found {input_nc}")
        return

    out_dir = os.path.dirname(output_tif)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    # Create the tiles subdirectory
    tiles_dir = os.path.join(out_dir, "tiles_temp")
    if not os.path.exists(tiles_dir):
        os.makedirs(tiles_dir)

    print(f"Start blocked parallel conversion (CPU: {num_processes} cores)...")
    print(f"Input: {input_nc}")
    print(f"Intermediate tile directory: {tiles_dir}")
    
    # 2. Get the source path
    src_path = get_gdal_src_path(input_nc)
    print(f"GDAL source path: {src_path}")
    
    # 3. Generate the tile tasks
    # Global extent: -180, 90, 180, -90
    # Split into 4x4 = 16 tiles
    # Longitude span 360 -> 90 degrees per tile
    # Latitude span 180 -> 45 degrees per tile
    
    tasks = []
    x_steps = 4
    y_steps = 4
    
    lon_min, lon_max = -180, 180
    lat_min, lat_max = -90, 90
    
    lon_step = (lon_max - lon_min) / x_steps
    lat_step = (lat_max - lat_min) / y_steps
    
    for i in range(x_steps):
        for j in range(y_steps):
            ulx = lon_min + i * lon_step
            lrx = ulx + lon_step
            
            uly = lat_max - j * lat_step
            lry = uly - lat_step
            
            tile_name = f"tile_{i}_{j}.tif"
            tile_path = os.path.join(tiles_dir, tile_name)
            
            tasks.append((src_path, tile_path, ulx, uly, lrx, lry))
            
    total_tasks = len(tasks)
    print(f"\nAbout to process {total_tasks} tile tasks...")
    
    start_time = time.time()
    
    # 4. Multiprocessing execution
    completed = 0
    # On Windows, multiprocessing needs attention; here the Pool is used inside the function
    with multiprocessing.Pool(processes=num_processes) as pool:
        # Use imap_unordered to get results in real time
        for success, msg in pool.imap_unordered(convert_tile_task, tasks):
            completed += 1
            if success:
                print(f"[{completed}/{total_tasks}] {msg}")
            else:
                print(f"[{completed}/{total_tasks}] [ERROR] {msg}")

    # 5. Build the VRT (virtual mosaicking)
    vrt_path = output_tif.replace('.tif', '.vrt')
    print(f"\nBuilding the virtual dataset (VRT)...")
    
    # Get all generated tifs
    tif_files = glob.glob(os.path.join(tiles_dir, "*.tif"))
    
    # Write the file list for gdalbuildvrt
    list_file = os.path.join(tiles_dir, "filelist.txt")
    with open(list_file, 'w') as f:
        for tf in tif_files:
            f.write(tf + '\n')
            
    vrt_cmd = ['gdalbuildvrt', '-input_file_list', list_file, vrt_path]
    subprocess.run(vrt_cmd, check=True, creationflags=0x08000000)
    
    print(f"VRT built: {vrt_path}")
    print("Tip: the VRT file can be used directly in ArcGIS/QGIS/Python like a TIF, without physical merging.")
    
    # 6. (Optional) Convert to a single large TIF
    # If the user insists on a tif, gdal_translate can convert the VRT to a TIF, which is much faster than converting from the NC
    # But for 17GB of data, it is recommended to use the VRT directly
    
    end_time = time.time()
    print(f"\nAll done! Total time: {end_time - start_time:.1f} s")
    print(f"Your data is ready: {vrt_path}")
    print(f"If you really need a single .tif file, please run: gdal_translate -of GTiff -co COMPRESS=LZW -co BIGTIFF=YES {vrt_path} {output_tif}")

if __name__ == "__main__":
    # The multiprocessing must run under if __name__ == "__main__":
    
    # Configure the paths
    INPUT_NC = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\地面碳数据\NC\ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv6.0.nc"
    # Note: the output here is the base of the VRT path; we will generate a .vrt with the same name
    OUTPUT_TIF = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\地面碳数据\ESACCI_Biomass_2017_100m.tif"
    
    # Use 16 processes (based on your 20-core CPU, leave a few cores for the system)
    convert_nc_to_tif_blocked(INPUT_NC, OUTPUT_TIF, num_processes=8)
