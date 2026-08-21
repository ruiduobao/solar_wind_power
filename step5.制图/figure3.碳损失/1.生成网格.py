"""
Generate a global 0.1-degree lon/lat grid (3600*1800) shapefile
Author: 锐多宝 (ruiduobao)
Date: 2026-02-03
Purpose: provide the base grid data for the global carbon debt composition analysis
CRS: WGS84 (EPSG:4326)
Output: global 0.1-degree grid shapefile
Optimization: multiprocessing (20 cores) greatly speeds up generation
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, box
import os
import time
from datetime import datetime
import multiprocessing as mp
import shutil
import pandas as pd

def process_latitude_band(args):
    """
    Generate the grid for one latitude band
    Args:
        args: (band_id, lat_start_idx, lat_end_idx, n_lon, grid_size, lon_min, lat_min, temp_dir)
    Returns:
        str: path of the generated temporary file
    """
    band_id, lat_start_idx, lat_end_idx, n_lon, grid_size, lon_min, lat_min, temp_dir = args
    
    try:
        # Preallocate lists
        geoms = []
        ids = []
        lon_indices = []
        lat_indices = []
        lefts = []
        rights = []
        bottoms = []
        tops = []
        center_lons = []
        center_lats = []
        
        # Optimization: use numpy to generate coordinate arrays, avoiding repeated computation in nested loops
        # Generate all latitude coordinates of this band (bottom edges)
        lat_indices_arr = np.arange(lat_start_idx, lat_end_idx)
        lat_bottoms = lat_min + lat_indices_arr * grid_size
        
        # Generate all longitude coordinates (left edges)
        lon_indices_arr = np.arange(n_lon)
        lon_lefts = lon_min + lon_indices_arr * grid_size
        
        # Use meshgrid to generate the coordinate matrices
        # Note: the matrix shape here is (len(lat_indices_arr), len(lon_indices_arr))
        # We need to flatten it for processing
        xx, yy = np.meshgrid(lon_lefts, lat_bottoms)
        xx_idx, yy_idx = np.meshgrid(lon_indices_arr, lat_indices_arr)
        
        # Flatten arrays
        flat_lefts = xx.flatten()
        flat_bottoms = yy.flatten()
        flat_lon_idxs = xx_idx.flatten()
        flat_lat_idxs = yy_idx.flatten()
        
        count = len(flat_lefts)
        
        # Vectorized computation of the other attributes
        flat_rights = flat_lefts + grid_size
        flat_tops = flat_bottoms + grid_size
        flat_center_lons = flat_lefts + grid_size / 2
        flat_center_lats = flat_bottoms + grid_size / 2
        
        # Batch create Polygons
        # Compared with Polygon([(x, y), ...]), box(minx, miny, maxx, maxy) is usually faster
        geoms = [box(l, b, r, t) for l, b, r, t in zip(flat_lefts, flat_bottoms, flat_rights, flat_tops)]
        
        # Create DataFrame
        df = pd.DataFrame({
            'lon_index': flat_lon_idxs,
            'lat_index': flat_lat_idxs,
            'left': flat_lefts,
            'right': flat_rights,
            'bottom': flat_bottoms,
            'top': flat_tops,
            'center_lon': flat_center_lons,
            'center_lat': flat_center_lats
        })
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(df, geometry=geoms, crs='EPSG:4326')
        
        # Save as pickle (fast, preserves dtypes)
        output_file = os.path.join(temp_dir, f'band_{band_id}.pkl')
        gdf.to_pickle(output_file)
        
        return output_file
        
    except Exception as e:
        print(f"Error processing latitude band {band_id}: {str(e)}")
        return None

def generate_global_grid_multiprocess(grid_size=0.1, output_path=None, n_processes=20):
    """
    Generate the global grid with multiprocessing
    """
    print(f"Generating global {grid_size}-degree grid (multiprocess optimized)...")
    print(f"Processes: {n_processes}")
    start_time = time.time()
    
    # Set the global extent
    lon_min, lon_max = -180, 180
    lat_min, lat_max = -90, 90
    
    # Compute the number of grid cells
    n_lon = int(round((lon_max - lon_min) / grid_size))  # 3600
    n_lat = int(round((lat_max - lat_min) / grid_size))  # 1800
    total_grids = n_lon * n_lat
    
    print(f"Grid dimensions: {n_lon} x {n_lat} = {total_grids} cells")
    
    # Create temporary directory
    temp_dir = os.path.join(os.path.dirname(output_path), 'temp_mp')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Prepare task parameters
    # Split the latitude direction into n_processes chunks
    lat_chunk_size = (n_lat + n_processes - 1) // n_processes
    tasks = []
    
    for i in range(n_processes):
        lat_start = i * lat_chunk_size
        lat_end = min((i + 1) * lat_chunk_size, n_lat)
        
        if lat_start >= n_lat:
            break
            
        tasks.append((i, lat_start, lat_end, n_lon, grid_size, lon_min, lat_min, temp_dir))
    
    print(f"Tasks assigned: {len(tasks)} subtasks in total")
    print("Starting parallel processing...")
    
    # Use a process pool to execute tasks
    temp_files = []
    with mp.Pool(processes=n_processes) as pool:
        results = pool.map(process_latitude_band, tasks)
        temp_files = [f for f in results if f is not None]
    
    print(f"Parallel processing done; generated {len(temp_files)} temporary files")
    
    # Merge results
    print("Starting to merge results...")
    merge_start = time.time()
    
    try:
        # Merge in batches to save memory
        # Assume merging 5 files at a time
        batch_size = 5
        intermediate_files = []
        
        current_batch = []
        batch_count = 0
        
        for i, file_path in enumerate(temp_files):
            current_batch.append(pd.read_pickle(file_path))
            
            if len(current_batch) >= batch_size or i == len(temp_files) - 1:
                batch_count += 1
                print(f"Merging batch {batch_count}...")
                
                # Merge the current batch
                batch_gdf = pd.concat(current_batch, ignore_index=True)
                
                # Save the intermediate result
                intermediate_file = os.path.join(temp_dir, f'merged_{batch_count}.pkl')
                batch_gdf.to_pickle(intermediate_file)
                intermediate_files.append(intermediate_file)
                
                # Free memory
                del batch_gdf
                del current_batch
                current_batch = []
        
        print("Final merge...")
        # Read all intermediate files and merge into the final GeoDataFrame
        final_dfs = [pd.read_pickle(f) for f in intermediate_files]
        final_gdf = gpd.GeoDataFrame(pd.concat(final_dfs, ignore_index=True), crs='EPSG:4326')
        
        # Add a global grid_id
        print("Generating global Grid ID...")
        final_gdf['grid_id'] = range(len(final_gdf))
        
        # Reorder columns
        cols = ['grid_id', 'lon_index', 'lat_index', 'left', 'right', 'bottom', 'top', 
               'center_lon', 'center_lat', 'geometry']
        final_gdf = final_gdf[cols]
        
        print(f"Merge complete: {len(final_gdf)} grid cells in total")
        print(f"Merge time: {(time.time() - merge_start):.2f} seconds")
        
        # Save to file
        if output_path:
            save_start = time.time()
            print(f"Saving to: {output_path}")
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save as shapefile
            final_gdf.to_file(output_path, driver='ESRI Shapefile', encoding='utf-8')
            print(f"Shapefile save time: {(time.time() - save_start):.2f} seconds")
            
        # Clean up the temporary directory
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
        
        end_time = time.time()
        print(f"Total time: {(end_time - start_time)/60:.2f} minutes")
        
        return final_gdf
        
    except Exception as e:
        print(f"Error during merge or save: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function"""
    # Set the output path
    output_dir = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\制图\figure3_全球碳债务构成\数据"
    output_filename = "全球0.1度网格_WGS84.shp"
    output_path = os.path.join(output_dir, output_filename)
    
    # Set the log file path
    log_dir = os.path.join(output_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"生成网格_多进程_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Redirect output to the log file
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    # Open the log file
    log_f = open(log_file, 'w', encoding='utf-8')
    
    # Save the original stdout
    import sys
    original_stdout = sys.stdout
    
    try:
        # Redirect stdout
        sys.stdout = Tee(sys.stdout, log_f)
        
        print("="*60)
        print("Global 0.1-degree grid generator (multiprocess fast version)")
        print("="*60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output path: {output_path}")
        print(f"Log file: {log_file}")
        print("-"*60)
        
        # Multiprocessing must run under if __name__ == "__main__"
        generate_global_grid_multiprocess(grid_size=0.1, output_path=output_path, n_processes=20)
        
        print("-"*60)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Program completed!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Restore the original stdout
        sys.stdout = original_stdout
        log_f.close()
        
        print(f"\nLog saved to: {log_file}")

if __name__ == "__main__":
    mp.freeze_support()  # multiprocessing support on Windows
    main()
