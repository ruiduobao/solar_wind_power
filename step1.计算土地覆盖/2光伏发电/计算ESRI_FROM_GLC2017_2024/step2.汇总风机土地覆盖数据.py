# -*- coding: utf-8 -*-
"""
Summarize ESRI and FROM-GLC10 land cover statistics (solar power version)
Author: 锐多宝 (ruiduobao)
Date: 2026-01-06
Description: 
    This script reads the batch CSV files exported from GEE, parses the JSON statistics in them,
    and aggregates the results into a single CSV file.
    The data contains land cover codes, pixel counts and areas.
    Multiprocessing is used to speed up the file reading and parsing process.
"""

import os
import glob
import json
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

# ================= Path configuration =================
# Folder containing the input data
INPUT_DIR_2018_2024 = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2017_2024的数据在2017年的土地覆盖上\GEE_solar_Analysis_2018_2024"
INPUT_DIR_2017 = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2017_2024的数据在2017年的土地覆盖上\GEE_solar_Analysis_2017"
# Output results folder
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\合并结果"

# Ensure the output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")

# ================= Class definitions =================

# ESRI 10m Land Cover Class Definitions
ESRI_CLASS_MAP = {
    1: "Water",
    2: "Trees",
    4: "Flooded Vegetation",
    5: "Crops",
    7: "Built Area",
    8: "Bare Ground",
    9: "Snow/Ice",
    10: "Clouds",
    11: "Rangeland"
}

# FROM-GLC10 Class Definitions
FROM_CLASS_MAP = {
    0: "Background",
    10: "Cropland",
    20: "Forest",
    30: "Grass",
    40: "Shrub",
    60: "Water",
    80: "Impervious",
    90: "Bareland",
    100: "Snow/Ice",
    120: "Cloud"
}
IMPERVIOUS_CODE_FROM = 80

# ================= Core processing functions =================

def parse_single_file(file_path, is_2017_correction=False):
    """
    Read a single CSV file and parse the stats_json column in it (for 2017 FROM data, ring_stats_json can also be parsed)
    :param file_path: CSV file path
    :param is_2017_correction: whether to apply the neighborhood inference correction for 2017 data
    :return: (parsed_data, change_record_list)
             parsed_data: list of dicts, land cover statistics
             change_record_list: list of dicts, records of replaced FIDs and impervious area reductions
    """
    try:
        # Determine the columns to read
        cols = ['fid', 'stats_json']
        if is_2017_correction:
            cols.append('ring_stats_json')
            
        # Read CSV
        df = pd.read_csv(file_path, usecols=cols)
        
        parsed_data = []
        change_records = []
        
        for _, row in df.iterrows():
            fid = row['fid']
            json_str = row['stats_json']
            
            # Skip empty values
            if pd.isna(json_str) or json_str == "":
                continue
                
            try:
                # Parse the inner JSON string
                stats_list = json.loads(json_str)
                
                # ----------------- 2017 neighborhood background inference logic -----------------
                replaced = False
                
                if is_2017_correction:
                    ring_json_str = row.get('ring_stats_json')
                    
                    if not pd.isna(ring_json_str) and ring_json_str != "":
                        try:
                            # 1. Compute inner statistics
                            inner_total_area = 0
                            inner_impervious_area = 0
                            
                            for item in stats_list:
                                code = item.get('code')
                                area = item.get('sum', [0, 0])[1]
                                inner_total_area += area
                                if code == IMPERVIOUS_CODE_FROM:
                                    inner_impervious_area += area
                                    
                            if inner_total_area > 0:
                                inner_imp_ratio = inner_impervious_area / inner_total_area
                                
                                # Trigger condition: impervious share > 30%
                                if inner_imp_ratio > 0.3:
                                    # 2. Parse ring statistics
                                    ring_stats_list = json.loads(ring_json_str)
                                    ring_total_area = 0
                                    ring_impervious_area = 0
                                    
                                    for item in ring_stats_list:
                                        code = item.get('code')
                                        area = item.get('sum', [0, 0])[1]
                                        ring_total_area += area
                                        if code == IMPERVIOUS_CODE_FROM:
                                            ring_impervious_area += area
                                            
                                    if ring_total_area > 0:
                                        ring_imp_ratio = ring_impervious_area / ring_total_area
                                        
                                        # Replacement condition: ring impervious share < inner impervious share
                                        if ring_imp_ratio < inner_imp_ratio:
                                            # Execute replacement: force the ring proportions to allocate the inner total area
                                            new_stats_list = []
                                            new_impervious_area_in_stats = 0
                                            
                                            for item in ring_stats_list:
                                                code = item.get('code')
                                                # Get the proportions in the ring
                                                r_pixel_count = item.get('sum', [0, 0])[0]
                                                r_area = item.get('sum', [0, 0])[1]
                                                
                                                ratio_pixel = r_pixel_count / ring_total_area # here pixel is actually linearly related to area, simplified
                                                ratio_area = r_area / ring_total_area
                                                
                                                # Compute the new values
                                                new_area = ratio_area * inner_total_area
                                                # Estimate pixel count (assuming pixel count is proportional to area, or it does not matter)
                                                # Simply estimating pixel count by area proportion here is not fully accurate (pixel area differs by latitude), but is sufficient as a statistical approximation
                                                # A more accurate approach would use the original inner pixel total * ring pixel ratio
                                                # But we do not know the inner total pixel, which needs to be re-accumulated.
                                                # Simplified: set pixel_count to 0 or also proportional. It does not affect the area calculation here.
                                                new_pixel = 0 
                                                
                                                new_stats_list.append({
                                                    'code': code,
                                                    'sum': [new_pixel, new_area]
                                                })
                                                
                                                if code == IMPERVIOUS_CODE_FROM:
                                                    new_impervious_area_in_stats += new_area
                                            
                                            # Replace the data source
                                            stats_list = new_stats_list
                                            replaced = True
                                            
                                            # Record the change
                                            reduced_area = inner_impervious_area - new_impervious_area_in_stats
                                            change_records.append({
                                                'fid': fid,
                                                'reduced_area': reduced_area
                                            })
                                            
                        except Exception as e_ring:
                            # An error in the ring processing does not affect the main flow, only print a warning
                            print(f"Ring processing warning fid {fid}: {e_ring}")
                
                # ----------------- Output results -----------------
                for item in stats_list:
                    class_code = item.get('code')
                    sums = item.get('sum', [0, 0])
                    pixel_count = sums[0]
                    area_sqm = sums[1]
                    
                    parsed_data.append({
                        'fid': fid,
                        'class_code': class_code,
                        'pixel_count': pixel_count,
                        'area_sqm': area_sqm,
                        'is_reconstructed': replaced # mark whether it was reconstructed
                    })
                    
            except json.JSONDecodeError as e:
                print(f"JSON parse error in file {os.path.basename(file_path)}, fid {fid}: {e}")
            except Exception as e:
                print(f"Row processing error in file {os.path.basename(file_path)}, fid {fid}: {e}")
                
        return parsed_data, change_records
        
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return [], []

def process_dataset(name_prefix, output_filename, input_dir, class_map=None, is_2017_correction=False):
    """
    Process datasets with a specific prefix (e.g. ESRI or FROM)
    :param name_prefix: file name prefix
    :param output_filename: output file name
    :param input_dir: input folder path
    :param class_map: class mapping
    :param is_2017_correction: whether to enable the 2017 neighborhood background inference correction
    """
    print(f"\nStart processing {name_prefix} data (directory: {input_dir})...")
    start_time = time.time()
    
    # Find matching files
    search_pattern = os.path.join(input_dir, f"{name_prefix}*.csv")
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"No matching files found: {search_pattern}")
        return None

    print(f"Found {len(files)} files, preparing for multiprocessing...")
    
    all_results = []
    
    # Use multiprocessing for parallel processing
    # Set max_workers based on the CPU core count, usually set to cpu_count
    max_workers = min(os.cpu_count(), 16) # cap at 16 processes to avoid excessive overhead
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(parse_single_file, f, is_2017_correction): f for f in files}
        
        # Get results
        completed_count = 0
        total_files = len(files)
        
        # Statistics variables
        total_replaced_count = 0
        total_reduced_impervious_area = 0
        
        for future in as_completed(future_to_file):
            data, changes = future.result()
            if data:
                all_results.extend(data)
            if changes:
                total_replaced_count += len(changes)
                total_reduced_impervious_area += sum(item['reduced_area'] for item in changes)
            
            completed_count += 1
            if completed_count % 10 == 0:
                print(f"Progress: {completed_count}/{total_files} files processed...", end='\r')
                
    print(f"\nAll files processed. Merging data...")
    
    if is_2017_correction:
        print(f"!!! 2017 neighborhood background inference statistics !!!")
        print(f"  - Number of facilities triggering replacement: {total_replaced_count}")
        print(f"  - Total reduced impervious area: {total_reduced_impervious_area:.2f} m2 ({total_reduced_impervious_area/1e6:.4f} km2)")

    # Convert to DataFrame
    if not all_results:
        print("No data extracted.")
        return None

    result_df = pd.DataFrame(all_results)
    
    # Add class names
    if class_map:
        print("Mapping class names...")
        result_df['class_name'] = result_df['class_code'].map(class_map)
        # Fill unknown classes
        result_df['class_name'] = result_df['class_name'].fillna('Unknown')
    else:
        result_df['class_name'] = 'Unknown'

    # Adjust column order
    cols = ['fid', 'class_code', 'class_name', 'pixel_count', 'area_sqm']
    if 'is_reconstructed' in result_df.columns:
        cols.append('is_reconstructed')
        # Fill missing values
        result_df['is_reconstructed'] = result_df['is_reconstructed'].fillna(False)
        
    result_df = result_df[cols]
    
    # Sort by fid and class_code
    result_df.sort_values(by=['fid', 'class_code'], inplace=True)
    
    # Save results
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"Processing completed!")
    print(f"Save path: {output_path}")
    print(f"Total time: {end_time - start_time:.2f} s")
    print(f"Total rows: {len(result_df)}")
    
    return result_df

# ================= Main program =================

if __name__ == '__main__':
    # ================= Process 2017 data =================
    print(">>> Processing 2017 data...")
    # Process ESRI data (ESRI data does not undergo neighborhood inference, keep as is)
    # Note: if there is no ESRI 2017 data in the directory, "no matching files found" will be printed here and skipped
    # process_dataset("SOLAR_ESRI_2017_Stats", "SOLAR_ESRI_2017_LandCover_Summary.csv", INPUT_DIR_2017, ESRI_CLASS_MAP)
    
    # Process FROM-GLC10 data (with neighborhood inference correction enabled)
    # Note: the file name prefix has been changed to "SOLAR_FROM_2017_WithRing"
    df_2017 = process_dataset("SOLAR_FROM_2017_WithRing", "SOLAR_FROM_2017_LandCover_Summary.csv", INPUT_DIR_2017, FROM_CLASS_MAP, is_2017_correction=True)

    # ================= Process 2018-2024 data =================
    print("\n>>> Processing 2018-2024 data...")
    # Process ESRI data
    # process_dataset("SOLAR_ESRI_2017_Stats", "SOLAR_ESRI_2018_2024_LandCover_Summary.csv", INPUT_DIR_2018_2024, ESRI_CLASS_MAP)
    
    # Process FROM-GLC10 data
    df_2018_2024 = process_dataset("SOLAR_FROM_2017_Stats", "SOLAR_FROM_2018_2024_LandCover_Summary.csv", INPUT_DIR_2018_2024, FROM_CLASS_MAP)
    
    # ================= Merge all data =================
    if df_2017 is not None and df_2018_2024 is not None:
        print("\n>>> Merging 2017 and 2018-2024 data...")
        df_merged = pd.concat([df_2017, df_2018_2024], ignore_index=True)
        
        # Sort by fid and class_code (optional)
        df_merged.sort_values(by=['fid', 'class_code'], inplace=True)
        
        merged_output_path = os.path.join(OUTPUT_DIR, "SOLAR_FROM_2017_2024_LandCover_Summary.csv")
        df_merged.to_csv(merged_output_path, index=False, encoding='utf-8-sig')
        print(f"Merged! Save path: {merged_output_path}")
        print(f"Total rows: {len(df_merged)}")
    else:
        print("\n!!! Merge failed: missing 2017 or 2018-2024 data.")
        
    print("\nAll tasks completed!")
