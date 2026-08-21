import xarray as xr

# File path
input_nc = r"F:\地理所\论文\全球绿色能源生态评估_2025.12.24\数据\地面碳数据\NC\ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv6.0.nc"

try:
    # Use chunks={} to enable dask lazy loading, preventing the 510GB data from flooding into memory
    # decode_times=False can avoid errors from some non-standard time formats
    ds = xr.open_dataset(input_nc, chunks={}, decode_times=True)
    
    print("-" * 30)
    print("=== Variable agb info ===")
    if 'agb' in ds.variables:
        agb_attrs = ds['agb'].attrs
        # Focus on the units attribute
        unit = agb_attrs.get('units', 'undefined')
        long_name = agb_attrs.get('long_name', 'undefined')
        
        print(f"Units: {unit}")
        print(f"Long Name: {long_name}")
        print("All attributes:", agb_attrs)
    else:
        print("Error: 'agb' variable not found in the file")

    print("-" * 30)
    print("=== Global attributes (optional) ===")
    # Sometimes the unit is written in the global title or comment
    print(f"Title: {ds.attrs.get('title')}")
    
    ds.close()

except Exception as e:
    print(f"Failed to read: {e}")
