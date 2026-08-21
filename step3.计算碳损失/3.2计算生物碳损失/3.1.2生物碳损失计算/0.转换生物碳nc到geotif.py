# -*- coding: utf-8 -*-
"""
Biomass Carbon NetCDF to GeoTIFF Conversion Tool
Author: 锐多宝 (Trae AI)
Date: 2026-01-07

Functions:
    Convert ESA CCI Biomass NetCDF (.nc) files to GeoTIFF format.
    Since the file is huge (17GB), chunked processing is used to avoid
    running out of memory.

Dependencies:
    pip install xarray rioxarray netcdf4 dask

Notes:
    Make sure the environment has the HDF5/NetCDF4 drivers installed.
    If it fails, try running in Anaconda Prompt: conda install -c conda-forge netcdf4 rioxarray
"""

import os
import sys
import time

def install_dependencies():
    """Try to auto-install dependencies (only attempted in non-standard environments)"""
    try:
        import xarray
        import rioxarray
        import netCDF4
        import dask
    except ImportError as e:
        print(f"Missing dependency: {e.name}")
        print("Suggested command: conda install -c conda-forge rioxarray netcdf4 dask")
        return False
    return True

def convert_nc_to_tif(input_nc, output_tif):
    import xarray as xr
    import rioxarray
    from dask.diagnostics import ProgressBar
    
    # Check input
    if not os.path.exists(input_nc):
        print(f"Error: input file not found {input_nc}")
        return

    # Check output directory
    out_dir = os.path.dirname(output_tif)
    if not os.path.exists(out_dir):
        print(f"Creating output directory: {out_dir}")
        os.makedirs(out_dir)

    print(f"Starting conversion...")
    print(f"Input: {input_nc}")
    print(f"Output: {output_tif}")
    
    start_time = time.time()

    try:
        # 1. Open the dataset with xarray
        # chunks={'lat': 1000, 'lon': 1000} enables Dask lazy loading, preventing everything from being read into memory at once
        # The ESA CCI Biomass variable is usually named 'agb' (Above Ground Biomass)
        ds = xr.open_dataset(input_nc, chunks={'lat': 2000, 'lon': 2000})
        
        print("\nDataset info:")
        print(ds)
        
        # Automatically find the variable name (usually agb or biomass)
        var_name = None
        for v in ds.data_vars:
            if 'agb' in v.lower() or 'biomass' in v.lower():
                var_name = v
                break
        
        if var_name is None:
            # If not found, default to the first data variable
            var_name = list(ds.data_vars)[0]
            
        print(f"\nSelected variable for conversion: {var_name}")
        
        # Get the DataArray
        da = ds[var_name]

        # 0. Reduce dimensions (remove the time dimension)
        if 'time' in da.dims:
            print("Reducing dimensions: removing time dimension")
            da = da.squeeze(dim='time', drop=True)
        
        # 1. Clean up the grid_mapping attribute that may cause conflicts
        # xarray/rioxarray will raise an error when writing if both attrs and encoding have grid_mapping
        if 'grid_mapping' in da.attrs:
            del da.attrs['grid_mapping']
        if 'grid_mapping' in da.encoding:
            del da.encoding['grid_mapping']
        
        # 2. Set CRS and Transform (if missing)
        # ESA CCI data is usually WGS84 (EPSG:4326)
        if da.rio.crs is None:
            print("Warning: dataset is missing CRS, defaulting to EPSG:4326")
            da.rio.write_crs("EPSG:4326", inplace=True)
            
        # 3. Write GeoTIFF
        # tiled=True, compress='LZW', bigtiff='YES' are the key parameters for large files
        # windowed=True (controlled by the lock parameter in to_raster, but rioxarray handles dask chunks automatically)
        print("\nWriting GeoTIFF (this may take a few minutes, please be patient)...")
        
        # Use the dask ProgressBar to show conversion progress
        with ProgressBar():
            da.rio.to_raster(
                output_tif,
                tiled=True,
                compress='LZW',
                bigtiff='YES',     # must be enabled because the file > 4GB
                num_threads=4,     # multi-threaded compression
                driver='GTiff'
            )
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"\nConversion succeeded! Time taken: {duration:.1f} seconds")
        print(f"File saved to: {output_tif}")

    except Exception as e:
        print(f"\n[ERROR] Conversion failed: {e}")
        print("Common causes: insufficient disk space, out of memory, or missing NetCDF4 driver.")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Configure paths
    INPUT_NC = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\地面碳数据\NC\ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv6.0.nc"
    OUTPUT_TIF = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\地面碳数据\ESACCI_Biomass_2017_100m.tif"
    
    # Check environment
    if install_dependencies():
        convert_nc_to_tif(INPUT_NC, OUTPUT_TIF)
    else:
        print("Please install the missing libraries first, then run again.")
