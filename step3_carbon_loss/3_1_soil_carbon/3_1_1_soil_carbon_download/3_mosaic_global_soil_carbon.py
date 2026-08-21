# -*- coding: utf-8 -*-
"""
Purpose: efficiently mosaic a large number (about 13,000) of small GeoTIFF files into one global large file (BigTIFF).
Features:
1. Use rasterio's Window read-write mode, with extremely low memory usage (only the memory of a single small image is occupied).
2. Automatically compute the global extent.
3. Support multithreaded file header scanning to speed up metadata acquisition.
4. Sequential writing ensures file safety, and LZW compression reduces the size.
"""

import os
import time
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
import concurrent.futures
from threading import Lock
import math

# Configuration information
# Input folder: contains all unmosaicked .tif files
INPUT_DIR = r"D:\浏览器下载\土壤碳\下载链接拆分\土壤碳\未镶嵌数据"
# Output folder
OUTPUT_DIR = r"D:\浏览器下载\土壤碳\下载链接拆分\土壤碳\镶嵌后"
# Output file name
OUTPUT_FILENAME = "Global_Soil_Carbon_Mosaic2.tif"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

def get_tif_files(directory):
    """Recursively get all .tif files"""
    tif_files = []
    print(f"Scanning the folder: {directory} ...")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.tif'):
                tif_files.append(os.path.join(root, file))
    print(f"Found {len(tif_files)} GeoTIFF files in total.")
    return tif_files

def get_bounds_and_profile(file_path):
    """Read the bounds and profile of a single file"""
    try:
        with rasterio.open(file_path) as src:
            return src.bounds, src.profile
    except Exception as e:
        print(f"Read error {file_path}: {e}")
        return None, None

def calculate_global_bounds(tif_files):
    """
    Compute the total bounds of all files.
    Use multithreading to speed up file header reading.
    """
    print("Computing the global data extent (reading all file headers)...")
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    # Get the profile of the first file as the template
    first_profile = None
    with rasterio.open(tif_files[0]) as src:
        first_profile = src.profile.copy()
        # Ensure the use of BigTIFF
        first_profile.update(driver='GTiff', bigtiff='YES')
    
    # Thread safety lock
    lock = Lock()
    
    # Progress count
    total = len(tif_files)
    count = 0
    
    # Use a thread pool to read Bounds concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        future_to_file = {executor.submit(get_bounds_and_profile, f): f for f in tif_files}
        
        for future in concurrent.futures.as_completed(future_to_file):
            bounds, _ = future.result()
            if bounds:
                with lock:
                    min_x = min(min_x, bounds.left)
                    min_y = min(min_y, bounds.bottom)
                    max_x = max(max_x, bounds.right)
                    max_y = max(max_y, bounds.top)
                    count += 1
                    if count % 1000 == 0:
                        print(f"Scanned {count}/{total} files...")

    print(f"Global extent computed: Left={min_x}, Bottom={min_y}, Right={max_x}, Top={max_y}")
    return (min_x, min_y, max_x, max_y), first_profile

def mosaic_process():
    start_time = time.time()
    
    # 1. Get the file list
    tif_files = get_tif_files(INPUT_DIR)
    if not tif_files:
        print("No TIF files found, the program ends.")
        return

    # 2. Compute the global extent
    global_bounds, profile = calculate_global_bounds(tif_files)
    min_x, min_y, max_x, max_y = global_bounds
    
    # 3. Compute the dimensions of the output file
    # Get the resolution (assume all files have the same resolution, take the first one)
    with rasterio.open(tif_files[0]) as src:
        res_x, res_y = src.res
        nodata = src.nodata
    
    # Width = (max X - min X) / resolution
    width = int(round((max_x - min_x) / res_x))
    height = int(round((max_y - min_y) / res_y)) # res_y is usually positive when computing the size
    
    print(f"Output image size: Width={width}, Height={height}")
    print(f"Resolution: X={res_x}, Y={res_y}")
    
    # 4. Update the Profile
    profile.update({
        'height': height,
        'width': width,
        'transform': rasterio.transform.from_origin(min_x, max_y, res_x, res_y),
        'compress': 'lzw',   # use LZW compression
        'tiled': True,       # enable tiling, which is critical for reading/writing large files
        'blockxsize': 256,   # block size
        'blockysize': 256,
        'bigtiff': 'YES',    # force BigTIFF
        'interleave': 'band'
    })
    
    # 5. Create and write the large file
    print(f"Start creating and writing the mosaic file: {OUTPUT_PATH}")
    print("This may take a few minutes to tens of minutes, depending on the disk speed...")
    
    # Use rasterio to open the target file for writing
    with rasterio.open(OUTPUT_PATH, 'w', **profile) as dst:
        total = len(tif_files)
        for idx, file_path in enumerate(tif_files):
            try:
                with rasterio.open(file_path) as src:
                    # Read the data (usually only 1 band)
                    # Considering the small data volume, read the whole array directly
                    data = src.read()
                    
                    # Compute the Window position of the current small image in the full image
                    # Use the rasterio.windows.from_bounds method
                    # Note: src.bounds is the geographic extent of the small image, dst.transform is the coordinate transform parameters of the large image
                    window = from_bounds(
                        src.bounds.left, src.bounds.bottom, 
                        src.bounds.right, src.bounds.top, 
                        transform=dst.transform
                    )
                    
                    # Write the data to the specified Window
                    # round_offsets=True and pixel_precision can help handle floating-point coordinate errors
                    dst.write(data, window=window)
                
                if (idx + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    speed = (idx + 1) / elapsed
                    remaining = (total - (idx + 1)) / speed
                    print(f"Progress: {idx + 1}/{total} ({(idx+1)/total*100:.1f}%) - estimated remaining time: {remaining/60:.1f} minutes")
                    
            except Exception as e:
                print(f"Failed to process the file {file_path}: {e}")

    end_time = time.time()
    print("-" * 30)
    print(f"Mosaicking completed!")
    print(f"Total time: {(end_time - start_time)/60:.2f} minutes")
    print(f"Output file: {OUTPUT_PATH}")

if __name__ == "__main__":
    mosaic_process()
