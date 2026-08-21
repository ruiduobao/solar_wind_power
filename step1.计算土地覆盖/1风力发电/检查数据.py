# -*- coding: utf-8 -*-
"""
Check whether the FIDs in CSV files continuously and completely cover the specified range
Author: 锐多宝 (ruiduobao)
Date: 2026-02-05
Description:
    Check the data in both the 2017 and 2018-2024 directories to verify FID coverage.
"""

import os
import glob
import pandas as pd

def check_fid_completeness_multi_source(source_configs, start_id, end_id):
    """
    Check whether the FIDs of all matching CSV files under multiple source folders cover [start_id, end_id]
    :param source_configs: list of dict, each dict contains 'dir' and 'pattern'
    """
    all_files = []
    
    print(">>> Start collecting files...")
    for config in source_configs:
        input_dir = config['dir']
        pattern = config['pattern']
        
        search_pattern = os.path.join(input_dir, pattern)
        files = glob.glob(search_pattern)
        print(f"  - Directory: {input_dir}")
        print(f"    Pattern: {pattern}")
        print(f"    Found: {len(files)} files")
        
        all_files.extend(files)
        
    if not all_files:
        print("❌ No matching files found!")
        return

    print(f"\nFound {len(all_files)} files in total, start reading FIDs...")
    
    all_fids = set()
    
    # Check which files contain the 1-31 range
    fids_1_to_31_sources = {}
    
    for i, file_path in enumerate(all_files):
        try:
            # Read only the fid column
            df = pd.read_csv(file_path, usecols=['fid'])
            current_fids = set(df['fid'].unique())
            all_fids.update(current_fids)
            
            # Check whether it contains 1-31
            intersection = current_fids.intersection(set(range(1, 32)))
            if intersection:
                fids_1_to_31_sources[os.path.basename(file_path)] = sorted(list(intersection))
            
            if (i + 1) % 20 == 0:
                print(f"Processed {i + 1}/{len(all_files)} files... (current unique FID count: {len(all_fids)})", end='\r')
                
        except Exception as e:
            print(f"\nFailed to read file {os.path.basename(file_path)}: {e}")
            
    print(f"\n\nAll files have been read.")
    print(f"Total unique FIDs extracted: {len(all_fids)}")
    
    # Output the source of 1-31
    if fids_1_to_31_sources:
        print("\n✅ Source files containing FID 1-31 found:")
        for fname, fids in fids_1_to_31_sources.items():
            print(f"  - {fname}: contains {len(fids)} (e.g. {fids[:5]}...)")
    else:
        print("\n❌ FID 1-31 not found in any file!")
    
    # Check completeness
    expected_fids = set(range(start_id, end_id + 1))
    missing_fids = sorted(list(expected_fids - all_fids))
    
    if not missing_fids:
        print("\n✅ FID fully covers the entire range! No missing IDs.")
    else:
        print(f"\n❌ Found {len(missing_fids)} missing FIDs!")
        print(f"Coverage: {(len(all_fids) / len(expected_fids)) * 100:.2f}%")
        
        # Print some missing IDs
        if len(missing_fids) <= 20:
            print(f"Missing FIDs: {missing_fids}")
        else:
            print(f"First 10 missing: {missing_fids[:10]}")
            print(f"Last 10 missing: {missing_fids[-10:]}")
            
            # Try to merge consecutive ranges for display
            ranges = []
            if missing_fids:
                start = missing_fids[0]
                prev = missing_fids[0]
                
                for fid in missing_fids[1:]:
                    if fid != prev + 1:
                        if start == prev:
                            ranges.append(f"{start}")
                        else:
                            ranges.append(f"{start}-{prev}")
                        start = fid
                    prev = fid
                
                # Add the last one
                if start == prev:
                    ranges.append(f"{start}")
                else:
                    ranges.append(f"{start}-{prev}")
            
            print(f"\nOverview of missing ranges (up to first 50 shown):")
            print(", ".join(ranges[:50]))
            if len(ranges) > 50:
                print("...")

if __name__ == "__main__":
    # Configure the two data sources
    INPUT_DIR_2017 = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\GEE_Wind_Analysis_2017"
    INPUT_DIR_2018_2024 = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\GEE_Wind_Analysis_2018_2024"
    
    sources = [
        {
            'dir': INPUT_DIR_2017,
            'pattern': "WIND_FROM_2017_WithRing*.csv"
        },
        {
            'dir': INPUT_DIR_2018_2024,
            'pattern': "FROM_2017_Stats_For2018_2024*.csv"
        }
    ]
    
    check_fid_completeness_multi_source(sources, 1, 375197)
