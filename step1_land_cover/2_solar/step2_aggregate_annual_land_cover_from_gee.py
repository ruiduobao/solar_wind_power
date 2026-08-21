import pandas as pd
import json
import os
import glob

# ================= Configuration =================
# Input folder path (use r"" raw string to avoid escape errors)
INPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\风力发电\GEE结果"

# Output folder path
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\风力发电\土地覆盖合并统计"

# Output filename
OUTPUT_FILENAME = "Wind_Analysis_Decoded_Merged.csv"

# ================= Core logic =================

# Dynamic World Class Mapping
CLASS_NAMES = {
    0: 'Water',
    1: 'Trees',
    2: 'Grass',
    3: 'Flooded_vegetation',
    4: 'Crops',
    5: 'shrub_and_scrub',
    6: 'Built',
    7: 'Bare',
    8: 'snow_and_ice'
}

def parse_transition(json_str):
    """
    Parse the stats_json column to extract the Pre (2015) and Post (2024) areas
    for all land cover types, along with specific transition indicators.
    """
    # Initialize the statistics dict
    stats = {'total_area_m2': 0.0}
    
    # Initialize all Pre and Post columns to 0.0
    for code, name in CLASS_NAMES.items():
        stats[f'pre_{name}'] = 0.0
        stats[f'post_{name}'] = 0.0
        
    # Initialize the specific Loss indicators (kept for compatibility with later scripts)
    target_loss_cols = ['loss_Trees_to_Built', 'loss_Grass_to_Built', 'loss_Shrub_to_Built', 'loss_Crops_to_Built']
    for col in target_loss_cols:
        stats[col] = 0.0

    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        # Return an all-zero Series when data is corrupted or empty
        return pd.Series(stats)

    for item in data:
        code = int(item['code'])
        area = float(item['sum'])
        
        # === Decode Code ===
        pre_class = code // 100   # 2015 class
        post_class = code % 100   # 2024 class
        
        stats['total_area_m2'] += area
        
        # === Tally Pre (2015) ===
        if pre_class in CLASS_NAMES:
            stats[f'pre_{CLASS_NAMES[pre_class]}'] += area
            
        # === Tally Post (2024) ===
        if post_class in CLASS_NAMES:
            stats[f'post_{CLASS_NAMES[post_class]}'] += area
        
        # === Tally core loss (Pre -> Built) ===
        if post_class == 6: # Built
            if pre_class == 1: stats['loss_Trees_to_Built'] += area
            elif pre_class == 2: stats['loss_Grass_to_Built'] += area
            elif pre_class == 5: stats['loss_Shrub_to_Built'] += area
            elif pre_class == 4: stats['loss_Crops_to_Built'] += area

    return pd.Series(stats)

def main():
    # 1. Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        print(f"Creating output directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

    # 2. Find all CSV files (Wind_Analysis_Batch_*.csv)
    search_pattern = os.path.join(INPUT_DIR, "Wind_Analysis_Batch_*.csv")
    csv_files = glob.glob(search_pattern)

    if not csv_files:
        print(f"Error: no files matching 'Wind_Analysis_Batch_*.csv' were found under {INPUT_DIR}.")
        return

    print(f"Found {len(csv_files)} files, starting processing...")
    
    # 3. Read and process each file in a loop
    df_list = []
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        # print(f"Parsing: {file_name}")
        
        try:
            df = pd.read_csv(file_path)
            
            # Check whether the key column exists
            if 'stats_json' not in df.columns:
                print(f"Skipping {file_name}: missing 'stats_json' column")
                continue
                
            # Apply the parsing function
            parsed_df = df['stats_json'].apply(parse_transition)
            
            # Merge the raw data with the parsed results
            combined_df = pd.concat([df, parsed_df], axis=1)
            
            # Drop the original large JSON string to reduce memory usage (optional; comment this line out to keep it)
            # combined_df.drop(columns=['stats_json'], inplace=True)
            
            df_list.append(combined_df)
            
        except Exception as e:
            print(f"Error while processing {file_name}: {str(e)}")

    # 4. Merge all results and export
    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
        
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig') # Use utf-8-sig for compatibility with Chinese text in Excel
        print(f"Done. Merged file saved to: \n{output_path}")
        
        # Print a preview of the first rows
        print("\nData preview (first 3 rows):")
        print(final_df[['total_area_m2', 'pre_Trees', 'post_Built', 'pre_Crops', 'post_Crops']].head(3).to_string())
        
    else:
        print("No data was generated.")

if __name__ == "__main__":
    main()
